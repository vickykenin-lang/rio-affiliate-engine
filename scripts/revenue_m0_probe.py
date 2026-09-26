#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://vickykenin-lang.github.io/rio-affiliate-engine"
TRACKING_TAG = "rioaffiliate-21"
CLICK_COLLECTOR = "https://rio-click-telemetry.vickykenin.workers.dev"
FUNNELS = [
    {"offer_id": "SPICE_RACK_001", "path": "/products/SPICE_RACK_001.html", "asin": "B07P5Z9SQN"},
    {"offer_id": "UNDER_SINK_001", "path": "/products/UNDER_SINK_001.html", "asin": "B0C1KNTF2Y"},
    {"offer_id": "TROLLEY_001", "path": "/products/TROLLEY_001.html", "asin": "B08BVJYLZ3"},
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
        "click_telemetry_script_present": False,
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
        result["click_telemetry_script_present"] = 'click-telemetry.js' in text
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


def check_collector() -> dict[str, object]:
    result: dict[str, object] = {
        "health_http_200": False,
        "health_ready": False,
        "synthetic_acceptance_http_202": False,
        "synthetic_not_persisted": False,
        "verified": False,
    }
    try:
        status, body = fetch(CLICK_COLLECTOR + "/health")
        health = json.loads(body)
        result["health_http_200"] = status == 200
        result["health_ready"] = health.get("status") == "READY"

        payload = json.dumps({
            "offer_id": "SPICE_RACK_001",
            "path": "/products/SPICE_RACK_001.html",
            "target": "https://www.amazon.in/dp/B07P5Z9SQN?tag=rioaffiliate-21",
            "test": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            CLICK_COLLECTOR + "/click",
            data=payload,
            method="POST",
            headers={
                "User-Agent": "RIO-Revenue-M0-Probe/1.0",
                "Content-Type": "application/json",
                "Origin": "https://vickykenin-lang.github.io",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            accepted = json.loads(response.read().decode("utf-8", errors="replace"))
            result["synthetic_acceptance_http_202"] = int(response.status) == 202
            result["synthetic_not_persisted"] = accepted.get("synthetic") is True and accepted.get("persisted") is False
        result["verified"] = all(
            result[key]
            for key in (
                "health_http_200",
                "health_ready",
                "synthetic_acceptance_http_202",
                "synthetic_not_persisted",
            )
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    funnels = [check_funnel(item) for item in FUNNELS]
    collector = check_collector()
    live_funnel_verified = all(x["verified"] for x in funnels)
    instrumentation_verified = all(x["click_telemetry_script_present"] for x in funnels)
    outbound_collection_verified = bool(collector["verified"] and instrumentation_verified)

    if live_funnel_verified and outbound_collection_verified:
        milestone = "M0B"
        status = "M0B_CLICK_COLLECTION_PATH_VERIFIED"
    elif live_funnel_verified:
        milestone = "M0"
        status = "M0_THREE_OFFER_LIVE_FUNNEL_VERIFIED"
    else:
        milestone = "M0"
        status = "M0_NOT_VERIFIED"

    result = {
        "schema_version": 2,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "milestone": milestone,
        "status": status,
        "scope": "LIVE_BUYER_INTENT_PAGE_TO_DISCLOSED_TAGGED_MERCHANT_DESTINATION_WITH_OUTBOUND_CLICK_COLLECTION",
        "funnels": funnels,
        "click_collector": collector,
        "outbound_click_event_collection_verified": outbound_collection_verified,
        "real_outbound_click_observed": False,
        "merchant_report_ingestion_verified": False,
        "revenue_claimed": False,
        "truth_rule": "M0B proves that live affiliate links are instrumented and the privacy-minimal collector accepts valid browser events. It does not claim a real visitor click, merchant order, commission, or payment until independent evidence exists.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if status in {"M0_THREE_OFFER_LIVE_FUNNEL_VERIFIED", "M0B_CLICK_COLLECTION_PATH_VERIFIED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
