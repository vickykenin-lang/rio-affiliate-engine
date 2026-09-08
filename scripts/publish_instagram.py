#!/usr/bin/env python3
"""RIO — Instagram publisher.

Posts ONE verified, in-stock, affiliate-active offer per run to RIO's
Instagram Business account (@riosallerior), using the Instagram Graph API
("API setup with Instagram login" flow). Built by Victor on 2026-08-18 once
IG_USER_ID_RIO / IG_ACCESS_TOKEN_RIO existed as GitHub secrets (see
data/victor_instructions.md, 2026-08-18 entry).

Design constraints, on purpose:
- stdlib only (urllib/json/csv) — matches heartbeat.py / generate_dashboard.py
  / content_review.py; no pip install step exists in rio.yml, so no new
  dependency gets silently required here.
- Uses the exact-product image URL already approved in
  data/product_image_registry.json. The mapped ASIN and affiliate destination
  must match the eligible offer; legacy branded cards are not primary creatives.
- One post per run. Cadence is controlled entirely by the GitHub Actions
  schedule in .github/workflows/rio.yml (Vicky/Victor's choice), not by
  this script — this script just does "post the next eligible offer, once,
  if nothing is blocking it."
- Respects the kill switch (data/control.json) and the four validators'
  last-known status (data/status.json) — will not publish if either says
  stop, exactly like heartbeat.py's own publish-safety rule.
- Every offer_id this script HAS successfully posted is recorded in
  data/ig_published.json so it is never posted twice.
- Always includes a plain-language affiliate disclosure in the caption
  (ASCI/FTC-style) — never a bare link with no disclosure.
- NEVER live-verifies the Amazon listing at post time — cannot, same
  robots.txt/no-PA-API blocker as the image problem above. It only trusts
  offer_identity_registry.csv's cached availability_status/
  destination_checked_at. Added 2026-08-18 after Vicky asked "what if the
  product goes off Amazon, will I get an error?" — answer: no error, the
  script never touches Amazon directly, but a stale listing could get
  posted with a dead/OOS link and nobody would know. STALENESS_DAYS below
  is the mitigation: an offer whose destination_checked_at is older than
  that many days is skipped, not posted, until a human re-checks it on
  Amazon and updates the CSV. This is a deadline-forcing function, not a
  live check — there is no substitute yet for Vicky/Victor periodically
  re-verifying offers by hand.

RIO's operating agent should run this via .github/workflows/rio.yml on its
own schedule; it commits data/ig_published.json (state) and appends a status
line to data/rio_report_to_victor.md on every successful publish, same
reporting direction as the rest of RIO -> Victor communication.
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import time
from datetime import datetime, timezone, timedelta

ROOT = os.path.join(os.path.dirname(__file__), "..")
IST = timezone(timedelta(hours=5, minutes=30))
REPO = os.environ.get("GITHUB_REPOSITORY", "vickykenin-lang/rio-affiliate-engine")
OWNER, REPO_NAME = REPO.split("/") if "/" in REPO else ("vickykenin-lang", "rio-affiliate-engine")

REG_CSV = os.path.join(ROOT, "data", "offer_identity_registry.csv")
STATE_JSON = os.path.join(ROOT, "data", "ig_published.json")
APPROVAL_JSON = os.path.join(ROOT, "data", "instagram_approval.json")
RUN_STATUS_JSON = os.path.join(ROOT, "data", "instagram_run_status.json")
CONTROL_JSON = os.path.join(ROOT, "data", "control.json")
STATUS_JSON = os.path.join(ROOT, "data", "status.json")
REPORT_MD = os.path.join(ROOT, "data", "rio_report_to_victor.md")
IMAGE_REGISTRY_JSON = os.path.join(ROOT, "data", "product_image_registry.json")

GRAPH_VERSION = "v22.0"
# Instagram Login tokens (start with IGAA...) must use graph.instagram.com.
# Facebook Login tokens use graph.facebook.com. Auto-detect at runtime.

# An offer whose data/offer_identity_registry.csv "destination_checked_at"
# is older than this many days is treated as stale and skipped (not
# posted), even if publish_status/availability_status still say READY/
# IN_STOCK. This is the only safety net against posting a dead or
# out-of-stock Amazon link — this script cannot live-check Amazon itself
# (robots.txt disallows scraping, no PA-API credentials exist). Re-checking
# a stale offer on Amazon and updating destination_checked_at is a Founder/
# Victor task, not something this script can do on its own.
STALENESS_DAYS = 21

def clean_secret(value):
    """Remove common copy/paste wrappers without ever logging the secret."""
    value = (value or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1].strip()
    if value.casefold().startswith("bearer "):
        value = value[7:].strip()
    return value


IG_USER_ID = clean_secret(os.environ.get("IG_USER_ID_RIO", ""))
IG_ACCESS_TOKEN = clean_secret(os.environ.get("IG_ACCESS_TOKEN_RIO", ""))
PUBLIC_SITE_BASE = os.environ.get(
    "RIO_PUBLIC_SITE_BASE",
    f"https://{OWNER}.github.io/{REPO_NAME}",
).rstrip("/")

# Detect token type: Instagram Login tokens start with IGAA / IGAAR etc.
if IG_ACCESS_TOKEN.upper().startswith("IGAA"):
    GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"
else:
    GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Cosmetic-only cluster labels for captions/cards. Not present as a column
# in offer_identity_registry.csv today — assigned by Victor from the same
# creative_product_name data, purely for a readable category tag. If this
# drifts from reality as new offers are added, it's a caption-quality issue,
# never a data-integrity one (the registry itself is untouched).
CLUSTER_LABELS = {
    "UNDER_SINK_001": "Kitchen Storage",
    "SPICE_RACK_001": "Kitchen Storage",
    "TROLLEY_001": "Kitchen Storage",
    "CONTAINER_001": "Kitchen Storage",
    "DRAWER_001": "Kitchen Storage",
    "NODRILL_001": "Apartment Storage",
    "BATHROOM_SHELF_001": "Bathroom Storage",
    "BATHROOM_NODRILL_001": "Bathroom Storage",
    "HOMEOFFICE_CABLE_001": "Home Office",
    "BALCONY_BROOM_001": "Balcony Storage",
    "BABY_CORNERGUARD_001": "Baby Safety",
    "BABY_SAFETYGATE_001": "Baby Safety",
    "BABY_CABINETLOCK_001": "Baby Safety",
    "BABY_SOCKETCOVER_001": "Baby Safety",
    "WARDROBE_DRAWERORG_001": "Wardrobe Storage",
    "UNDERBED_STORAGEBAG_001": "Bedroom Storage",
    "FOLDABLE_LAPDESK_001": "Home Office",
}


def jload(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def jsave(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def save_run_status(status, detail, offer_id=None, posted_count=0, pending_count=0):
    jsave(RUN_STATUS_JSON, {
        "updated_at": datetime.now(IST).isoformat(timespec="minutes"),
        "status": status,
        "offer_id": offer_id,
        "detail": detail,
        "posted_count": posted_count,
        "pending_count": pending_count,
    })


def update_approval(approvals_doc, offer_id, status, detail=None):
    approval = approvals_doc.setdefault("approvals", {}).setdefault(offer_id, {})
    approval["status"] = status
    approval["updated_at"] = datetime.now(IST).isoformat(timespec="minutes")
    if detail:
        approval["last_detail"] = detail
    jsave(APPROVAL_JSON, approvals_doc)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_product_images():
    images = jload(IMAGE_REGISTRY_JSON, {"images": []}).get("images", [])
    return {item.get("asin"): item for item in images if item.get("asin")}


def graph_call(path, params, method="POST"):
    url = f"{GRAPH_BASE}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        separator = "&" if "?" in url else "?"
        req = urllib.request.Request(f"{url}{separator}{data.decode()}", method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Graph API {method} {path} failed ({e.code}): {body}") from e


def days_since(date_str):
    """Returns days between date_str (YYYY-MM-DD) and today (IST), or None if unparseable."""
    try:
        checked = datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(tzinfo=IST)
    except Exception:
        return None
    return (datetime.now(IST) - checked).days


def build_caption(offer):
    name = offer["creative_product_name"]
    cluster = CLUSTER_LABELS.get(offer["offer_id"], "Home Storage")
    landing_url = (
        f"{PUBLIC_SITE_BASE}/products/{offer['offer_id']}.html?utm_source=instagram&utm_medium=organic"
        f"&utm_campaign=rio_offer_{offer['offer_id'].casefold()}"
    )
    checked_at = offer.get("destination_checked_at", "").strip() or "an earlier date"
    return (
        f"{name}\n\n"
        f"Category: {cluster}\n\n"
        f"Identity and stock last verified {checked_at} "
        f"(availability_status on file: {offer['availability_status']}). "
        f"Prices and stock on Amazon change often — always confirm the current "
        f"price and availability on the product page before buying. "
        f"Full guide and tagged affiliate link: {landing_url}\n\n"
        f"Affiliate link — RIO may earn a small commission on Amazon.in purchases "
        f"made through this link, at no extra cost to you. #ad #affiliate\n\n"
        f"#HomeOrganization #IndianHomes #SpaceSaving #StorageHacks"
    )


def main():
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        detail = "IG_USER_ID_RIO / IG_ACCESS_TOKEN_RIO is missing from GitHub Actions secrets."
        save_run_status("BLOCKED_CREDENTIALS", detail)
        print(f"[publish_instagram] {detail}")
        return 2

    control = jload(CONTROL_JSON, {"kill_switch": False})
    if control.get("kill_switch"):
        detail = "RIO kill switch is ON; Instagram publishing is blocked."
        save_run_status("BLOCKED_KILL_SWITCH", detail)
        print(f"[publish_instagram] {detail}")
        return 2
    if control.get("instagram_auto_publish") is not True:
        detail = "Instagram auto-publishing is paused by Founder control."
        save_run_status("BLOCKED_FOUNDER_PAUSE", detail)
        print(f"[publish_instagram] {detail}")
        return 2

    status = jload(STATUS_JSON, {})
    if status.get("all_validators_pass") is not True:
        detail = ("RIO validators are not known-passing; nothing can publish until "
                  "data/status.json.all_validators_pass is true.")
        save_run_status("BLOCKED_VALIDATION", detail)
        print(f"[publish_instagram] {detail}")
        return 2

    print(f"[publish_instagram] using API base: {GRAPH_BASE}")

    offers = load_csv(REG_CSV)
    product_images = load_product_images()
    ready = [
        o for o in offers
        if o.get("publish_status") == "READY"
        and o.get("affiliate_status") == "ACTIVE"
        and o.get("identity_status") == "VERIFIED"
        and o.get("availability_status") == "IN_STOCK"
    ]

    state = jload(STATE_JSON, {"posted": {}})
    posted = state.setdefault("posted", {})
    approvals_doc = jload(APPROVAL_JSON, {"approvals": {}})
    approvals = approvals_doc.get("approvals", {})
    approved_states = {"APPROVED", "POST_PENDING", "FAILED_RETRY"}
    autonomous_policy_approval = control.get("approval_mode") == "AUTONOMOUS_POLICY_VALIDATED"

    candidate = None
    skipped_no_image = []
    skipped_stale = []
    for o in ready:
        oid = o["offer_id"]
        if oid in posted:
            continue
        if not autonomous_policy_approval and approvals.get(oid, {}).get("status") not in approved_states:
            continue
        age = days_since(o.get("destination_checked_at", ""))
        if age is None or age > STALENESS_DAYS:
            skipped_stale.append(f"{oid} ({'unparseable date' if age is None else f'{age}d old'})")
            continue
        image = product_images.get(o.get("merchant_product_id"))
        if not image or f"/dp/{o.get('merchant_product_id')}" not in image.get("affiliate_url", "") or "tag=rioaffiliate-21" not in image.get("affiliate_url", ""):
            skipped_no_image.append(oid)
            continue
        o["publish_image_url"] = image.get("image_url", "")
        o["verified_affiliate_url"] = image.get("affiliate_url", "")
        if not o["publish_image_url"].startswith("https://"):
            skipped_no_image.append(oid)
            continue
        candidate = o
        break

    if skipped_stale:
        print(f"[publish_instagram] destination_checked_at older than {STALENESS_DAYS}d (or unparseable), "
              f"needs a human re-check on Amazon before it can post: {', '.join(skipped_stale)}")
    if skipped_no_image:
        print(f"[publish_instagram] missing exact-product image/link mapping: {', '.join(skipped_no_image)} — skipped.")

    if candidate is None:
        pending_count = sum(1 for o in ready if o.get("offer_id") not in posted) if autonomous_policy_approval else sum(
            1 for oid, approval in approvals.items() if approval.get("status") in approved_states and oid not in posted
        )
        if pending_count and (skipped_stale or skipped_no_image):
            reasons = []
            if skipped_stale:
                reasons.append("stale verification: " + ", ".join(skipped_stale))
            if skipped_no_image:
                reasons.append("missing exact-product image/link mapping: " + ", ".join(skipped_no_image))
            detail = "Approved post is blocked — " + "; ".join(reasons)
            save_run_status("BLOCKED_OFFER", detail, posted_count=len(posted), pending_count=pending_count)
            print(f"[publish_instagram] {detail}")
            return 2
        detail = "No eligible policy-validated, un-posted offer is ready this run."
        save_run_status("IDLE", detail, posted_count=len(posted), pending_count=pending_count)
        print(f"[publish_instagram] {detail}")
        return 0

    oid = candidate["offer_id"]
    image_url = candidate["publish_image_url"]
    try:
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "RIO-Instagram-Preflight/1.0", "Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "").casefold()
            if response.status not in (200, 206) or not content_type.startswith("image/"):
                raise RuntimeError(
                    f"exact-product image preflight failed: HTTP {response.status}, "
                    f"content-type {content_type or '(missing)'}"
                )
    except Exception as exc:
        error = RuntimeError(
            f"exact-product image is not reachable at {image_url}; "
            f"Instagram cannot publish it: {exc}"
        )
        detail = str(error)
        update_approval(approvals_doc, oid, "FAILED_RETRY", detail)
        save_run_status("FAILED_RETRY", detail, oid, posted_count=len(posted), pending_count=1)
        raise error from exc
    caption = build_caption(candidate)

    update_approval(approvals_doc, oid, "POST_PENDING", "Meta publish request started.")
    save_run_status(
        "POST_PENDING",
        "Founder-approved offer is being submitted to Meta.",
        oid,
        posted_count=len(posted),
        pending_count=1,
    )
    print(f"[publish_instagram] publishing {oid} ({candidate['creative_product_name']}) ...")

    try:
        creation = graph_call(
            f"{IG_USER_ID}/media",
            {"image_url": image_url, "caption": caption, "access_token": IG_ACCESS_TOKEN},
        )
        creation_id = creation.get("id")
        if not creation_id:
            raise RuntimeError(f"media creation returned no id: {creation}")

        for _ in range(10):
            container = graph_call(
                f"{creation_id}?fields=status_code,status",
                {"access_token": IG_ACCESS_TOKEN},
                method="GET",
            )
            container_status = container.get("status_code")
            if container_status == "FINISHED":
                break
            if container_status in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Meta media container failed: {container}")
            time.sleep(3)
        else:
            raise RuntimeError("Meta media container did not become ready within 30 seconds.")

        published = graph_call(
            f"{IG_USER_ID}/media_publish",
            {"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        )
        media_id = published.get("id")
        if not media_id:
            raise RuntimeError(f"media_publish returned no id: {published}")
    except Exception as exc:
        detail = str(exc)
        update_approval(approvals_doc, oid, "FAILED_RETRY", detail)
        save_run_status(
            "FAILED_RETRY", detail, oid,
            posted_count=len(posted), pending_count=1,
        )
        raise

    permalink = None
    try:
        info = graph_call(f"{media_id}?fields=permalink", {"access_token": IG_ACCESS_TOKEN}, method="GET")
        permalink = info.get("permalink")
    except Exception as e:
        print(f"[publish_instagram] could not fetch permalink (non-fatal): {e}")

    now = datetime.now(IST).isoformat(timespec="minutes")
    posted[oid] = {
        "posted_at": now,
        "media_id": media_id,
        "permalink": permalink,
        "product_name": candidate["creative_product_name"],
    }
    jsave(STATE_JSON, state)
    update_approval(approvals_doc, oid, "INSTAGRAM_POSTED", f"Meta media ID {media_id}")
    save_run_status(
        "INSTAGRAM_POSTED",
        f"Successfully posted to Instagram as Meta media {media_id}.",
        oid,
        posted_count=len(posted),
        pending_count=0,
    )

    report_line = (
        f"\n- {now} IST — posted **{candidate['creative_product_name']}** "
        f"(offer `{oid}`) to Instagram @riosallerior. "
        f"Media ID `{media_id}`."
        + (f" Permalink: {permalink}" if permalink else "")
        + "\n"
    )
    try:
        with open(REPORT_MD, "a", encoding="utf-8") as f:
            f.write(report_line)
    except Exception as e:
        print(f"[publish_instagram] could not append to {REPORT_MD} (non-fatal): {e}")

    print(f"[publish_instagram] done: {oid} -> media {media_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
