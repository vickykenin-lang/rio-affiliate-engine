#!/usr/bin/env python3
"""RIO — Heartbeat: reads owner messages & kill switch (GitHub issues),
regenerates the CEO dashboard from the live CSVs, runs the publish-safety
validators, and writes a fresh data/status.json so Victor (and RIO's own
operating agent) can verify freshness without guessing. Runs on cron +
on issue events + manual workflow_dispatch. Uses GITHUB_TOKEN from Actions.

Modeled on design-infra-marketing/scripts/heartbeat.py (AURA's heartbeat),
adapted to RIO's CSV-based data model and its "no daily publish, no owner
approval-per-post" shape — RIO has no calendar.json/approvals.json
equivalent; its "publish gate" is the four validate_*.py scripts plus the
founder publication-approval policy described in README.md / Section 5-7
of RIO_OPERATING_AGENT_BRIEF.md, not a per-post GitHub-issue approval flow.
"""
import json, os, subprocess, sys, urllib.error, urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.path.join(os.path.dirname(__file__), "..")
IST = timezone(timedelta(hours=5, minutes=30))
REPO = os.environ.get("GITHUB_REPOSITORY", "vickykenin-lang/rio-affiliate-engine")
TOK = os.environ.get("GITHUB_TOKEN", "")
OWNER = "vickykenin-lang"


def gh(path, data=None, method=None):
    req = urllib.request.Request(f"https://api.github.com/{path}", method=method,
        headers={"Authorization": f"Bearer {TOK}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    body = json.dumps(data).encode() if data is not None else None
    with urllib.request.urlopen(req, body, timeout=30) as r:
        return json.load(r) if r.status != 204 else {}


def jload(p, default):
    try:
        return json.load(open(os.path.join(ROOT, p)))
    except Exception:
        return default


def jsave(p, obj):
    path = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, ensure_ascii=False)


control = jload("data/control.json", {"kill_switch": False, "kill_reason": None, "last_test": None})
inbox = jload("data/inbox.json", {"messages": []})
now = datetime.now(IST).isoformat(timespec="minutes")

# --- 1. Read open issues: KILL SWITCH / RESUME / MESSAGE TO RIO -----------
try:
    issues = gh(f"repos/{REPO}/issues?state=open&per_page=50")
except Exception as e:
    print(f"[heartbeat] could not list issues: {e}")
    issues = []

for i in issues:
    labels = [l["name"] for l in i.get("labels", [])]
    title = (i.get("title") or "").upper()
    body = i.get("body") or ""
    try:
        if "kill-switch" in labels or "KILL SWITCH" in title:
            control["kill_switch"] = True
            control["kill_reason"] = f"Issue #{i['number']} by {i['user']['login']} at {now}"
            gh(f"repos/{REPO}/issues/{i['number']}/comments",
               {"body": "🔴 Kill switch ACTIVATED — RIO's heartbeat will stop touching the dashboard/data "
                        "until resumed. Resume: open an issue titled 'RESUME RIO'."})
            gh(f"repos/{REPO}/issues/{i['number']}", {"state": "closed"}, "PATCH")
            print("kill switch activated via issue", i["number"])
        elif title.startswith("RESUME") and i["user"]["login"] == OWNER:
            control["kill_switch"] = False
            control["kill_reason"] = None
            gh(f"repos/{REPO}/issues/{i['number']}/comments",
               {"body": "🟢 Resumed — heartbeat is active again."})
            gh(f"repos/{REPO}/issues/{i['number']}", {"state": "closed"}, "PATCH")
            print("kill switch resumed via issue", i["number"])
        elif "owner-message" in labels or "MESSAGE TO RIO" in title:
            inbox["messages"].append({"at": now, "from": i["user"]["login"],
                                      "issue": i["number"], "text": body[:2000]})
            gh(f"repos/{REPO}/issues/{i['number']}/comments",
               {"body": "✅ Message received — logged to data/inbox.json for the next working session."})
            gh(f"repos/{REPO}/issues/{i['number']}", {"state": "closed"}, "PATCH")
            print("owner message stored from issue", i["number"])
    except Exception as e:
        print(f"[heartbeat] failed handling issue #{i.get('number')}: {e}")

jsave("data/control.json", control)
jsave("data/inbox.json", inbox)

if control.get("kill_switch"):
    print("[heartbeat] kill switch is ON — skipping dashboard regen and validators this run.")
    status = jload("data/status.json", {})
    status["updated"] = now
    status["kill_switch"] = True
    status["note_en"] = f"Paused by kill switch. {control.get('kill_reason', '')}"
    jsave("data/status.json", status)
    sys.exit(0)

# --- 2. Regenerate the CEO dashboard from the live CSVs --------------------
SCRIPTS = os.path.join(ROOT, "scripts")


def run_script(name):
    """Runs a scripts/<name>.py with no args, exactly as it's meant to be invoked
    (none of RIO's validator/generator scripts take CLI args — confirmed by reading
    each one directly, not assumed). Returns (ok, combined_output)."""
    path = os.path.join(SCRIPTS, name)
    try:
        r = subprocess.run([sys.executable, path], cwd=ROOT, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return r.returncode == 0, out.strip()
    except Exception as e:
        return False, f"failed to run {name}: {e}"


production_ok, production_out = run_script("check_production.py")
print(f"[heartbeat] check_production.py {'OK' if production_ok else 'FAILED'}:\n{production_out}")

dash_ok, dash_out = run_script("generate_dashboard.py")
print(f"[heartbeat] generate_dashboard.py {'OK' if dash_ok else 'FAILED'}:\n{dash_out}")

# --- 3. Run the publish-safety validators (never publish on a failure) -----
validator_scripts = {
    "production_live": None,
    "offer_integrity": "validate_offer_integrity.py",
    "product_candidates": "validate_product_candidates.py",
    "dashboard": "validate_dashboard.py",
    "production_offer_gate": "validate_production_offer_gate.py",
}
validators = {}
for key, script in validator_scripts.items():
    if key == "production_live":
        ok, out = production_ok, production_out
    else:
        ok, out = run_script(script)
    # Keep only the last few lines (the PASS/FAIL summary + any error list) —
    # full stdout still goes to the Actions log via the print() below.
    tail = "\n".join(out.splitlines()[-15:])
    validators[key] = {"pass": ok, "detail": tail}
    print(f"[heartbeat] {script}: {'PASS' if ok else 'FAIL'}\n{out}")

all_pass = all(v["pass"] for v in validators.values())

# --- 4. Pull real counts from dashboard_snapshot.json (never inferred) -----
snap = jload("data/dashboard_snapshot.json", {})
counts = {
    "product_candidates": snap.get("product_candidates", 0),
    "ready_offers": snap.get("ready_offers", 0),
    "blocked_offers": snap.get("blocked_offers", 0),
    "rejected_products": snap.get("rejected_products", 0),
    "content_items": snap.get("content_items", 0),
    # revenue/cost/profit stay at whatever generate_dashboard.py computed
    # (policy: hardcoded 0 until real tracked conversions exist — never
    # inferred here, see RIO_OPERATING_AGENT_BRIEF.md Section 5).
    "revenue_inr": snap.get("revenue_inr", 0),
    "cost_inr": snap.get("cost_inr", 0),
    "net_profit_inr": snap.get("net_profit_inr", 0),
    "production_verified": bool(production_ok),
}

status = jload("data/status.json", {})
status["updated"] = now
status["kill_switch"] = False
status["dashboard_regenerated"] = dash_ok
status["validators"] = validators
status["all_validators_pass"] = all_pass
status["counts"] = counts
status["note_en"] = (
    f"Heartbeat OK — dashboard regenerated, {sum(1 for v in validators.values() if v['pass'])}/{len(validators)} validators passing. "
    f"{counts['ready_offers']} ready offers, {counts['content_items']} content items, revenue ₹{counts['revenue_inr']}."
    if all_pass else
    f"⚠ {sum(1 for v in validators.values() if not v['pass'])}/{len(validators)} validators FAILING — see data/status.json.validators for detail. "
    "Nothing should be published/deployed until these pass again."
)
jsave("data/status.json", status)
print("heartbeat done:", json.dumps({"all_validators_pass": all_pass, "counts": counts}))
