#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://vickykenin-lang.github.io/rio-affiliate-engine"
TRACKING_TAG = "rioaffiliate-21"
FUNNELS = [
    {"offer_id": "SPICE_RACK_001", "path": "/products/SPICE_RACK_001.html", "asin": "B07P5Z9SQN"},
    {"offer_id": "UNDER_SINK_001", "path": "/products/UNDER_SINK_001.html", "asin": "B0BZQYJZ6R"},
    {"offer_id": "TROLLEY_001", "path": "/products/TROLLEY_001.html", "asin": "B09XJZ7Y2M"},
]
OUT = Path("data/revenue_m0_live_probe.json")


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "RIO-Revenue-M0-Probe/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return int(response.status), response.read().decode("utf-8", errors="replace")


def check_funnel(item: dict[str, str]) -> dict[str, object]:
    url = BASE + item["path"]
    result: dict[str, object] = {
        "offer_id": item["offer_id"],
        "page_url": url,
        "expected_asin": item["asin"],
        "page_http_200": False,
        "affiliate_disclosure_present": False,
        "tagged_amazon_destination_present": False,
        "exact_asin_destination_present": False,
        "sponsored_rel_present": False,
        "verified": False,
    }
    try:
        status, text = fetch(url)
        result["page_http_200"] = status == 200
        lower = text.lower()
        result["affiliate_disclosure_present"] = "affiliate disclosure" in lower and "qualifying purchases" in lower
        links = re.findall(r'href=["\'](https://www\.amazon\.in/[^"\']+)["\']', text, flags=re.I)
        result["tagged_amazon_destination_present"] = any(f"tag={TRACKING_TAG}" in link for link in links)
        result["exact_asin_destination_present"] = any(f"/dp/{item['asin']}" in link and f"tag={TRACKING_TAG}" in link for link in links)
        result["sponsored_rel_present"] = bool(re.search(r'rel=["\'][^"\']*sponsored[^"\']*["\']', text, flags=re.I))
        result["verified"] = all(
            result[key]
            for key in (
                "page_http_200",
                "affiliate_disclosure_present",
                "tagged_amazon_destination_present",
                "exact_asin_destination_present",
                "sponsored_rel_present",
            )
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    funnels = [check_funnel(item) for item in FUNNELS]
    result = {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "milestone": "M0",
        "status": "M0_THREE_OFFER_LIVE_FUNNEL_VERIFIED" if all(x["verified"] for x in funnels) else "M0_NOT_VERIFIED",
        "scope": "LIVE_BUYER_INTENT_PAGE_TO_DISCLOSED_TAGGED_MERCHANT_DESTINATION",
        "funnels": funnels,
        "outbound_click_event_collection_verified": False,
        "merchant_report_ingestion_verified": False,
        "revenue_claimed": False,
        "truth_rule": "This probe verifies the live conversion path only. It does not prove a visitor click, order, commission, or payment.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "M0_THREE_OFFER_LIVE_FUNNEL_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
