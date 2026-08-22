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
- Never fabricates a product photo. Amazon's robots.txt disallows scraping
  product pages (confirmed 2026-08-18), and RIO has no Amazon Product
  Advertising API credentials yet, so this script does NOT attempt to pull
  a real product photo. Instead it uses a pre-rendered branded card image
  (site/social/<offer_id>.png) built from the SAME verified product_name/
  cluster data already in offer_identity_registry.csv — never invented
  copy. If no card exists yet for an offer, that offer is skipped (logged),
  not posted with a placeholder.
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
from datetime import datetime, timezone, timedelta

ROOT = os.path.join(os.path.dirname(__file__), "..")
IST = timezone(timedelta(hours=5, minutes=30))
REPO = os.environ.get("GITHUB_REPOSITORY", "vickykenin-lang/rio-affiliate-engine")
OWNER, REPO_NAME = REPO.split("/") if "/" in REPO else ("vickykenin-lang", "rio-affiliate-engine")

REG_CSV = os.path.join(ROOT, "data", "offer_identity_registry.csv")
STATE_JSON = os.path.join(ROOT, "data", "ig_published.json")
CONTROL_JSON = os.path.join(ROOT, "data", "control.json")
STATUS_JSON = os.path.join(ROOT, "data", "status.json")
REPORT_MD = os.path.join(ROOT, "data", "rio_report_to_victor.md")
CARD_DIR = os.path.join(ROOT, "site", "social")

GRAPH_VERSION = "v26.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

# An offer whose data/offer_identity_registry.csv "destination_checked_at"
# is older than this many days is treated as stale and skipped (not
# posted), even if publish_status/availability_status still say READY/
# IN_STOCK. This is the only safety net against posting a dead or
# out-of-stock Amazon link — this script cannot live-check Amazon itself
# (robots.txt disallows scraping, no PA-API credentials exist). Re-checking
# a stale offer on Amazon and updating destination_checked_at is a Founder/
# Victor task, not something this script can do on its own.
STALENESS_DAYS = 21

IG_USER_ID = os.environ.get("IG_USER_ID_RIO", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN_RIO", "")
PUBLIC_SITE_BASE = os.environ.get(
    "RIO_PUBLIC_SITE_BASE",
    f"https://{OWNER}.github.io/{REPO_NAME}",
).rstrip("/")

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


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def graph_call(path, params, method="POST"):
    url = f"{GRAPH_BASE}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}", method="GET")
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
        f"{PUBLIC_SITE_BASE}/?utm_source=instagram&utm_medium=organic"
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
        print("[publish_instagram] IG_USER_ID_RIO / IG_ACCESS_TOKEN_RIO not set — nothing to do.")
        return 0

    control = jload(CONTROL_JSON, {"kill_switch": False})
    if control.get("kill_switch"):
        print("[publish_instagram] kill switch is ON — skipping this run.")
        return 0

    status = jload(STATUS_JSON, {})
    if status.get("all_validators_pass") is not True:
        print("[publish_instagram] validators are not known-passing (data/status.json) — "
              "skipping this run. Nothing should be published while any validator fails.")
        return 0

    offers = load_csv(REG_CSV)
    ready = [
        o for o in offers
        if o.get("publish_status") == "READY"
        and o.get("affiliate_status") == "ACTIVE"
        and o.get("identity_status") == "VERIFIED"
        and o.get("availability_status") == "IN_STOCK"
    ]

    state = jload(STATE_JSON, {"posted": {}})
    posted = state.setdefault("posted", {})

    candidate = None
    skipped_no_card = []
    skipped_stale = []
    for o in ready:
        oid = o["offer_id"]
        if oid in posted:
            continue
        age = days_since(o.get("destination_checked_at", ""))
        if age is None or age > STALENESS_DAYS:
            skipped_stale.append(f"{oid} ({'unparseable date' if age is None else f'{age}d old'})")
            continue
        card_path = os.path.join(CARD_DIR, f"{oid}.png")
        if not os.path.isfile(card_path):
            skipped_no_card.append(oid)
            continue
        candidate = o
        break

    if skipped_stale:
        print(f"[publish_instagram] destination_checked_at older than {STALENESS_DAYS}d (or unparseable), "
              f"needs a human re-check on Amazon before it can post: {', '.join(skipped_stale)}")
    if skipped_no_card:
        print(f"[publish_instagram] no social card yet for: {', '.join(skipped_no_card)} — skipped, not posted.")

    if candidate is None:
        print("[publish_instagram] no eligible un-posted offer with a ready social card this run.")
        return 0

    oid = candidate["offer_id"]
    image_url = f"{PUBLIC_SITE_BASE}/social/{oid}.png"
    try:
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "RIO-Instagram-Preflight/1.0", "Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "").casefold()
            if response.status not in (200, 206) or not content_type.startswith("image/"):
                raise RuntimeError(
                    f"public social card preflight failed: HTTP {response.status}, "
                    f"content-type {content_type or '(missing)'}"
                )
    except Exception as exc:
        raise RuntimeError(
            f"public social card is not reachable at {image_url}; "
            f"Instagram cannot publish it: {exc}"
        ) from exc
    caption = build_caption(candidate)

    print(f"[publish_instagram] publishing {oid} ({candidate['creative_product_name']}) ...")

    creation = graph_call(
        f"{IG_USER_ID}/media",
        {"image_url": image_url, "caption": caption, "access_token": IG_ACCESS_TOKEN},
    )
    creation_id = creation.get("id")
    if not creation_id:
        raise RuntimeError(f"media creation returned no id: {creation}")

    published = graph_call(
        f"{IG_USER_ID}/media_publish",
        {"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
    )
    media_id = published.get("id")
    if not media_id:
        raise RuntimeError(f"media_publish returned no id: {published}")

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
