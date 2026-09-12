#!/usr/bin/env python3
"""Import confirmed pre-Step-2 Instagram posts as immutable legacy campaigns.

The migration is idempotent. It never fabricates the two new Founder approvals
and never changes data/ig_published.json or data/instagram_approval.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = ROOT / "data" / "campaigns"
OFFERS_PATH = ROOT / "data" / "offer_identity_registry.csv"
CANDIDATES_PATH = ROOT / "data" / "product_candidates.csv"
IMAGES_PATH = ROOT / "data" / "product_image_registry.json"
POSTED_PATH = ROOT / "data" / "ig_published.json"


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _safe_campaign_id(raw: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9_:-]", "_", raw.upper())
    return cleaned or "LEGACY_CAMPAIGN"


def build_legacy_campaigns() -> list[dict[str, Any]]:
    offers = {row["offer_id"]: row for row in _load_csv(OFFERS_PATH)}
    candidates = {row["merchant_product_id"]: row for row in _load_csv(CANDIDATES_PATH)}
    images_doc = json.loads(IMAGES_PATH.read_text(encoding="utf-8"))
    images = {row["asin"]: row for row in images_doc.get("images", [])}
    posted = json.loads(POSTED_PATH.read_text(encoding="utf-8")).get("posted", {})

    campaigns: list[dict[str, Any]] = []
    for offer_id, post in sorted(posted.items()):
        if offer_id not in offers:
            raise ValueError(f"posted offer {offer_id} is missing from offer registry")
        offer = offers[offer_id]
        asin = offer["merchant_product_id"]
        candidate = candidates.get(asin)
        if not candidate:
            raise ValueError(f"offer {offer_id} ASIN {asin} has no candidate record")
        image = images.get(asin, {})
        campaign_id = _safe_campaign_id(offer.get("campaign_id") or f"CMP_{offer_id}")
        posted_at = post["posted_at"]
        affiliate_url = image.get("affiliate_url") or f"{offer['canonical_url']}?tag=rioaffiliate-21"
        event = {
            "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"rio:{campaign_id}:legacy-import")),
            "campaign_id": campaign_id,
            "revision": 0,
            "action": "LEGACY_INSTAGRAM_POST_IMPORTED",
            "actor": {"id": "step-3-migration", "role": "MIGRATION"},
            "at": posted_at,
            "from_state": None,
            "to_state": "INSTAGRAM_POSTED",
            "details": {
                "source": "data/ig_published.json",
                "approval_model": "PRE_STEP_2_LEGACY",
                "approvals_fabricated": False,
            },
        }
        score_raw = candidate.get("commercial_score", "").strip()
        campaigns.append(
            {
                "schema_version": 1,
                "campaign_id": campaign_id,
                "state": "INSTAGRAM_POSTED",
                "revision": 0,
                "identity": {
                    "candidate_id": candidate["candidate_id"],
                    "offer_id": offer_id,
                    "merchant": offer["merchant"],
                    "asin": asin,
                    "product_title": candidate.get("product_title") or offer["product_name"],
                    "variant": offer.get("variant", ""),
                    "canonical_url": offer["canonical_url"],
                    "affiliate_url": affiliate_url,
                    "landing_page_url": "",
                    "candidate_score": float(score_raw) if score_raw else None,
                    "candidate_status": candidate.get("status") or "UNKNOWN",
                    "selected_at": posted_at,
                    "offer_verified_at": offer.get("destination_checked_at") or None,
                    "availability": offer.get("availability_status") or "UNKNOWN",
                    "evidence_refs": [
                        "data/ig_published.json",
                        "data/offer_identity_registry.csv",
                        "data/product_candidates.csv",
                    ],
                },
                "creative": None,
                "approvals": {"creative": None, "publish": None},
                "publish": {
                    "attempts": 1,
                    "idempotency_key": f"legacy:{post['media_id']}",
                    "precheck": None,
                    "media_id": post["media_id"],
                    "permalink": post.get("permalink"),
                    "error": None,
                },
                "governance": {
                    "approval_model": "PRE_STEP_2_LEGACY",
                    "legacy_import": True,
                    "previous_state": None,
                },
                "created_at": posted_at,
                "updated_at": posted_at,
                "history": [event],
            }
        )
    return campaigns


def write_campaigns(campaigns: list[dict[str, Any]]) -> tuple[int, int]:
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    unchanged = 0
    for campaign in campaigns:
        path = CAMPAIGN_DIR / f"{campaign['campaign_id']}.json"
        rendered = json.dumps(campaign, indent=2, ensure_ascii=False) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != rendered:
                raise RuntimeError(f"refusing to overwrite changed campaign: {path}")
            unchanged += 1
            continue
        path.write_text(rendered, encoding="utf-8", newline="\n")
        created += 1
    return created, unchanged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write idempotent legacy records")
    args = parser.parse_args()
    campaigns = build_legacy_campaigns()
    if not args.write:
        print(f"dry-run: {len(campaigns)} confirmed posts are ready for legacy import")
        return
    created, unchanged = write_campaigns(campaigns)
    print(f"legacy migration complete: created={created}, unchanged={unchanged}")


if __name__ == "__main__":
    main()
