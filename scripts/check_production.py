#!/usr/bin/env python3
"""Verify that RIO is genuinely reachable in production."""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IST = timezone(timedelta(hours=5, minutes=30))
BASE = os.environ.get("RIO_PUBLIC_SITE_BASE", "https://vickykenin-lang.github.io/rio-affiliate-engine").rstrip("/")
OUT = ROOT / "data" / "production_status.json"
TIMEOUT = 25
AFFILIATE_CHECK_PATH = "/articles/best-bathroom-storage-organizers-india.html"
CONTROL_ROOM_PATH = "/control-room/"
CONTROL_ROOM_CANONICAL = "https://vickykenin-lang.github.io/rio-affiliate-engine/control-room/"

def fetch(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "RIO-Production-Health/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return {"ok": response.status == 200, "status": response.status, "content_type": response.headers.get("Content-Type", ""), "body": response.read(2000000), "url": response.geturl()}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "content_type": exc.headers.get("Content-Type", ""), "body": b"", "url": url}
    except Exception as exc:
        return {"ok": False, "status": None, "content_type": "", "body": b"", "url": url, "error": str(exc)}

checks = {}
home = fetch("/")
home_text = home["body"].decode("utf-8", errors="replace")
checks["homepage_200"] = home["ok"]
checks["disclosure_present"] = "affiliate disclosure" in home_text.casefold()

# Verify the affiliate tag where a real, published affiliate offer actually exists.
# The homepage is not required to contain a merchant link merely to satisfy health checks.
affiliate_page = fetch(AFFILIATE_CHECK_PATH)
affiliate_text = affiliate_page["body"].decode("utf-8", errors="replace")
checks["affiliate_offer_page_200"] = affiliate_page["ok"]
checks["affiliate_tag_present"] = affiliate_page["ok"] and "tag=rioaffiliate-21" in affiliate_text

# Certify the Founder-facing Control Room itself, not just the base site.
control_room = fetch(CONTROL_ROOM_PATH)
control_room_text = control_room["body"].decode("utf-8", errors="replace")
control_room_lower = control_room_text.casefold()
checks["control_room_200"] = control_room["ok"]
checks["control_room_title_present"] = control_room["ok"] and "rio control room" in control_room_lower
checks["control_room_canonical_present"] = control_room["ok"] and CONTROL_ROOM_CANONICAL in control_room_text
checks["control_room_instagram_embed_present"] = control_room["ok"] and "instagram.com/p/" in control_room_lower and "/embed/" in control_room_lower
checks["control_room_instagram_open_link_present"] = control_room["ok"] and "open on instagram" in control_room_lower and "instagram.com/p/" in control_room_lower

sitemap = fetch("/sitemap.xml")
checks["sitemap_200"] = sitemap["ok"]
absolute_locs = False
if sitemap["ok"]:
    try:
        root = ET.fromstring(sitemap["body"])
        locs = [el.text.strip() for el in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc") if el.text]
        absolute_locs = bool(locs) and all(urlparse(loc).scheme in ("http", "https") and urlparse(loc).netloc for loc in locs)
    except Exception:
        absolute_locs = False
checks["sitemap_absolute_urls"] = absolute_locs

card = fetch("/social/UNDER_SINK_001.png")
checks["social_card_200"] = card["ok"] and card["content_type"].casefold().startswith("image/")

verified = all(checks.values())
status = {
    "checked_at": datetime.now(IST).isoformat(timespec="seconds"),
    "base_url": BASE,
    "verified": verified,
    "checks": checks,
    "responses": {
        "homepage": {"status": home.get("status"), "url": home.get("url"), "error": home.get("error")},
        "affiliate_offer_page": {"status": affiliate_page.get("status"), "url": affiliate_page.get("url"), "error": affiliate_page.get("error")},
        "control_room": {"status": control_room.get("status"), "url": control_room.get("url"), "error": control_room.get("error")},
        "sitemap": {"status": sitemap.get("status"), "url": sitemap.get("url"), "error": sitemap.get("error")},
        "social_card": {"status": card.get("status"), "url": card.get("url"), "content_type": card.get("content_type"), "error": card.get("error")}
    }
}
OUT.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("PRODUCTION HEALTH GATE: " + ("PASS" if verified else "FAIL"))
print(json.dumps(status, ensure_ascii=False))
sys.exit(0 if verified else 1)
