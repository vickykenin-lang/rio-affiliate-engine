#!/usr/bin/env python3
"""
Regenerates RIO's CEO dashboard (site/dashboard/index.html), the machine
snapshot (data/dashboard_snapshot.json) and the human action queue
(data/ceo_action_queue.csv) FROM the real underlying data files, instead of
those being hand-edited once and left to go stale.

Run this any time product_candidates.csv, offer_identity_registry.csv or
content_queue.csv change, and before every push. Mirrors the fix already
applied to AURA's heartbeat.py (same stale-dashboard failure mode).

revenue_inr / cost_inr / net_profit_inr / production_verified are NEVER
inferred here -- they stay at 0 / false. Those require real tracked
conversions and a human production sign-off respectively, per RIO's
no-earnings-claims policy and validate_dashboard.py's hard gate.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND_CSV = ROOT / "data" / "product_candidates.csv"
REG_CSV = ROOT / "data" / "offer_identity_registry.csv"
QUEUE_CSV = ROOT / "data" / "content_queue.csv"
SNAPSHOT_JSON = ROOT / "data" / "dashboard_snapshot.json"
ACTION_QUEUE_CSV = ROOT / "data" / "ceo_action_queue.csv"
DASHBOARD_HTML = ROOT / "site" / "dashboard" / "index.html"
PRODUCTION_JSON = ROOT / "data" / "production_status.json"


def load_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    candidates = load_csv(CAND_CSV)
    try:
        production = json.loads(PRODUCTION_JSON.read_text(encoding="utf-8"))
    except Exception:
        production = {"verified": False}
    offers = load_csv(REG_CSV)
    queue = load_csv(QUEUE_CSV)

    ready_offers = [o for o in offers if o["publish_status"] == "READY"]
    blocked_offers = [o for o in offers if o["publish_status"] != "READY"]
    rejected_products = [c for c in candidates if c["status"] == "REJECTED"]
    ready_products = [c for c in candidates if c["status"] == "READY"]
    verified_products = [c for c in candidates if c["identity_confidence"] == "VERIFIED_LIVE"]
    discovered_products = [c for c in candidates if c["status"] != "DISCOVERY_REQUIRED"]

    snapshot = {
        "product_candidates": len(candidates),
        "offers": len(offers),
        "ready_offers": len(ready_offers),
        "blocked_offers": len(blocked_offers),
        "rejected_products": len(rejected_products),
        "content_items": len(queue),
        "revenue_inr": 0,
        "cost_inr": 0,
        "net_profit_inr": 0,
        "x_to_x_failures": 0,
        "production_verified": bool(production.get("verified")),
        "discovered_products": len(discovered_products),
        "verified_products": len(verified_products),
        "ready_products": len(ready_products),
    }
    SNAPSHOT_JSON.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    # --- CEO action queue: derive real, current blockers instead of hand-maintained stale rows ---
    rows = []
    in_review = [c for c in candidates if c["status"] in ("IDENTITY_REVIEW", "SPEC_REVIEW", "SCORED")]
    if in_review:
        rows.append(("WAIT", "RIO", "Advance remaining candidates through scoring/spec review",
                      f"{len(in_review)} candidate(s) still short of READY: "
                      + ", ".join(c["candidate_id"] for c in in_review) + "."))
    pending_live_check = [c for c in candidates if c["status"] == "SCORED"]
    if pending_live_check:
        rows.append(("BLOCKED", "RIO", "Live re-verify SCORED candidates on Amazon.in before promotion",
                      "Price-sensitive creative must be refreshed at publish time -- "
                      + ", ".join(c["candidate_id"] for c in pending_live_check) + " need a fresh live check."))
    if blocked_offers:
        rows.append(("BLOCKED", "RIO", "Keep remaining offers inactive until identity/availability verified",
                      f"{len(blocked_offers)} offer(s) still BLOCKED: "
                      + ", ".join(o["offer_id"] for o in blocked_offers) + "."))
    if ready_offers:
        offer_state = "LIVE" if snapshot["production_verified"] else "DATA_READY"
        action = (
            f"{len(ready_offers)} offer(s) public and earning-eligible"
            if snapshot["production_verified"]
            else f"{len(ready_offers)} offer(s) validated but public production is offline"
        )
        reason = (
            ", ".join(o["offer_id"] for o in ready_offers)
            + " -- Amazon Associates tag is configured; earning eligibility requires the production health gate to pass."
        )
        rows.append((offer_state, "RIO", action, reason))
    rows.append(("NEXT", "RIO", "Design the EarnKaro link-import workflow",
                  "The Founder already created the EarnKaro account, but it exposes no self-serve API; use an evidence-backed manual import gate until API access exists."))

    with ACTION_QUEUE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["severity", "owner", "action", "reason"])
        w.writerows(rows)

    # --- dashboard HTML ---
    xtox_rows = "".join(
        f"<tr><td>{esc(o['offer_id'])}</td><td>{esc(o['product_name'])}</td>"
        f"<td>{esc(o['identity_status'])}</td><td>{esc(o['affiliate_status'])}</td>"
        f"<td>{esc(o['publish_status'])}</td></tr>"
        for o in offers
    )
    disc_rows = "".join(
        f"<tr><td>{esc(c['candidate_id'])}</td><td>{esc(c['cluster'])}</td><td>{esc(c['brand'])}</td>"
        f"<td>{esc(c['merchant_product_id'])}</td><td>&#8377;{esc(c['price_observed'])}</td>"
        f"<td>{esc(c['observed_at'])}</td><td>{esc(c['status'])}</td><td>{esc(c['identity_confidence'])}</td></tr>"
        for c in candidates
    )
    action_rows = "".join(
        f"<tr><td class=\"blocked\">{esc(r[0])}</td><td>{esc(r[1])}</td><td>{esc(r[2])}</td><td>{esc(r[3])}</td></tr>"
        for r in rows
    )
    badges = "<span class=\"badge\">BUILT</span><span class=\"badge\">LOCAL QA</span>"
    if ready_offers:
        badges += (
            " <span class=\"badge\">LIVE OFFERS</span>"
            if snapshot["production_verified"]
            else " <span class=\"badge\">DATA-READY OFFERS</span>"
        )
    badges += (
        "<span class=\"badge\">PRODUCTION VERIFIED</span>"
        if snapshot["production_verified"]
        else "<span class=\"badge\">PRODUCTION OFFLINE</span>"
    )

    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RIO CEO Dashboard</title><style>
body{{font-family:system-ui;margin:0;background:#f5f5f5;color:#161616}}main{{max-width:1180px;margin:auto;padding:28px}}
h1{{margin-bottom:4px}}.sub{{color:#555}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:24px 0}}
.card{{background:white;padding:18px;border-radius:12px;border:1px solid #ddd}}.card span{{display:block;color:#666;font-size:13px}}.card strong{{font-size:28px}}
.panel{{background:white;padding:18px;border:1px solid #ddd;border-radius:12px;margin:16px 0;overflow:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left}}.blocked{{font-weight:700}}
.badge{{display:inline-block;padding:5px 9px;border:1px solid #bbb;border-radius:999px;margin-right:6px}}
</style><link rel="canonical" href="https://vickykenin-lang.github.io/rio-affiliate-engine/dashboard/"></head><body><main><h1>RIO CEO Dashboard v2</h1><p class="sub">Single source of truth &middot; Build state, commercial gates, P&amp;L and human actions</p>
<div>{badges}</div>
<div class="grid"><section class="card"><span>Product candidates</span><strong>{snapshot['product_candidates']}</strong></section><section class="card"><span>Offers READY</span><strong>{snapshot['ready_offers']}</strong></section><section class="card"><span>Offers BLOCKED</span><strong>{snapshot['blocked_offers']}</strong></section><section class="card"><span>Content queue</span><strong>{snapshot['content_items']}</strong></section><section class="card"><span>Revenue</span><strong>&#8377;{snapshot['revenue_inr']}</strong></section><section class="card"><span>Net P&amp;L</span><strong>&#8377;{snapshot['net_profit_inr']}</strong></section></div>
<section class="panel"><h2>CEO Action Queue</h2><table><tr><th>Status</th><th>Owner</th><th>Action</th><th>Why</th></tr>{action_rows}</table></section>
<section class="panel"><h2>X&rarr;X Offer Control</h2><table><tr><th>Offer</th><th>Product</th><th>Identity</th><th>Affiliate</th><th>Publish</th></tr>{xtox_rows}</table></section>

<section class="panel"><h2>Real Product Discovery &mdash; Pilot</h2>
<p>These are sourced candidates, not approved promotions unless status is READY. Live Amazon listing verification is required before scoring or X&rarr;X activation.</p>
<table><tr><th>Candidate</th><th>Cluster</th><th>Brand</th><th>ASIN</th><th>Observed price</th><th>Evidence date</th><th>State</th><th>Identity</th></tr>
{disc_rows}</table></section>
<section class="panel"><h2>P&amp;L</h2><p>Revenue &#8377;{snapshot['revenue_inr']} &middot; Cost &#8377;{snapshot['cost_inr']} &middot; Net &#8377;{snapshot['net_profit_inr']}. No revenue is inferred before an approved affiliate report exists.</p></section>
<section class="panel"><h2>Release doctrine</h2><p>Creative X &rarr; CTA X &rarr; Campaign X &rarr; Offer X &rarr; exact Product/Variant X. No silent substitution. Production status: {'VERIFIED' if snapshot['production_verified'] else 'OFFLINE / NOT VERIFIED'}.</p></section>
</main></body></html>"""
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    print(f"Dashboard regenerated: {snapshot['ready_offers']} ready offers, "
          f"{snapshot['ready_products']} ready products, {snapshot['product_candidates']} total candidates.")


if __name__ == "__main__":
    main()
