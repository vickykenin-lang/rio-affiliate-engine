import json
import unittest
from pathlib import Path

from scripts.campaign_state import (
    ApprovalError,
    CampaignError,
    RevisionConflict,
    TransitionError,
    approval_is_valid,
    new_campaign,
    transition_campaign,
    update_material_data,
)
from scripts.migrate_instagram_campaigns import build_legacy_campaigns


NOW = "2026-09-12T10:00:00+00:00"
FOUNDER = ("Vicky Gautam", "FOUNDER")
SYSTEM = ("rio-system", "SYSTEM")
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def identity():
    return {
        "candidate_id": "CAND_CO_001",
        "offer_id": "CONTAINER_001",
        "merchant": "amazon.in",
        "asin": "B0753ZQDR7",
        "product_title": "Verified container set",
        "variant": "Set of 4",
        "canonical_url": "https://www.amazon.in/dp/B0753ZQDR7",
        "affiliate_url": "https://www.amazon.in/dp/B0753ZQDR7?tag=rioaffiliate-21",
        "landing_page_url": "https://example.invalid/offers/container",
        "candidate_score": 95,
        "candidate_status": "READY",
        "selected_at": NOW,
        "offer_verified_at": NOW,
        "availability": "IN_STOCK",
        "evidence_refs": ["data/product_candidates.csv"],
    }


def creative(version=1):
    return {
        "version": version,
        "asset_path": f"site/creatives/container-v{version}.png",
        "creative_sha256": HASH_A,
        "caption_version": version,
        "caption_text": "Useful storage idea. #ad",
        "caption_sha256": HASH_B,
        "landing_page_sha256": HASH_C,
        "source_policy": "ORIGINAL_CONTEXTUAL",
        "provider": "amazon-bedrock",
        "model": "amazon.nova-canvas-v1:0",
        "request_id": "req-1",
        "generated_at": NOW,
        "attempt": 1,
        "estimated_cost": None,
        "actual_cost": None,
    }


def transition(campaign, action, actor=SYSTEM, payload=None):
    return transition_campaign(
        campaign,
        action,
        actor[0],
        actor[1],
        campaign["revision"],
        payload or {},
        NOW,
    )


def campaign_in_creative_review():
    campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
    campaign = transition(campaign, "APPROVE_FOR_CREATIVE", FOUNDER)
    campaign = transition(campaign, "START_CREATIVE_GENERATION", payload={"attempt": 1})
    return transition(campaign, "CREATIVE_GENERATION_SUCCEEDED", payload=creative())


class CampaignStateTests(unittest.TestCase):
    def test_only_ready_candidate_can_create_campaign(self):
        candidate = identity()
        candidate["candidate_status"] = "DISCOVERY_REQUIRED"
        with self.assertRaises(CampaignError):
            new_campaign("CMP_TEST_001", candidate, at=NOW)

    def test_system_cannot_grant_founder_approvals(self):
        campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
        with self.assertRaises(ApprovalError):
            transition(campaign, "APPROVE_FOR_CREATIVE")

    def test_full_happy_path_requires_both_approvals(self):
        campaign = campaign_in_creative_review()
        campaign = transition(campaign, "APPROVE_TO_PUBLISH", FOUNDER)
        self.assertTrue(approval_is_valid(campaign, "creative"))
        self.assertTrue(approval_is_valid(campaign, "publish"))
        campaign = transition(
            campaign,
            "START_PUBLISH_PRECHECK",
            payload={"idempotency_key": "cmp-test-001:v1"},
        )
        campaign = transition(campaign, "PUBLISH_PRECHECK_PASSED", payload={"passed": True})
        campaign = transition(
            campaign,
            "PUBLISH_SUCCEEDED",
            payload={"media_id": "12345", "permalink": "https://instagram.com/p/test"},
        )
        self.assertEqual(campaign["state"], "INSTAGRAM_POSTED")
        self.assertEqual(campaign["publish"]["attempts"], 1)

    def test_publish_cannot_start_without_second_approval(self):
        campaign = campaign_in_creative_review()
        with self.assertRaises(TransitionError):
            transition(
                campaign,
                "START_PUBLISH_PRECHECK",
                payload={"idempotency_key": "cmp-test-001:v1"},
            )

    def test_identity_change_invalidates_both_approvals(self):
        campaign = campaign_in_creative_review()
        campaign = transition(campaign, "APPROVE_TO_PUBLISH", FOUNDER)
        campaign = update_material_data(
            campaign,
            {"identity": {"affiliate_url": "https://www.amazon.in/dp/DIFFERENT?tag=rioaffiliate-21"}},
            SYSTEM[0],
            SYSTEM[1],
            campaign["revision"],
            NOW,
        )
        self.assertEqual(campaign["state"], "CANDIDATE_REVIEW")
        self.assertFalse(approval_is_valid(campaign, "creative"))
        self.assertFalse(approval_is_valid(campaign, "publish"))

    def test_caption_hash_change_invalidates_publish_only(self):
        campaign = campaign_in_creative_review()
        campaign = transition(campaign, "APPROVE_TO_PUBLISH", FOUNDER)
        campaign = update_material_data(
            campaign,
            {"creative": {"caption_sha256": "d" * 64}},
            SYSTEM[0],
            SYSTEM[1],
            campaign["revision"],
            NOW,
        )
        self.assertEqual(campaign["state"], "CREATIVE_REVIEW")
        self.assertTrue(approval_is_valid(campaign, "creative"))
        self.assertFalse(approval_is_valid(campaign, "publish"))

    def test_caption_text_change_invalidates_publish_even_if_hash_is_not_updated(self):
        campaign = campaign_in_creative_review()
        campaign = transition(campaign, "APPROVE_TO_PUBLISH", FOUNDER)
        campaign = update_material_data(
            campaign,
            {"creative": {"caption_text": "Changed after approval"}},
            SYSTEM[0],
            SYSTEM[1],
            campaign["revision"],
            NOW,
        )
        self.assertEqual(campaign["state"], "CREATIVE_REVIEW")
        self.assertFalse(approval_is_valid(campaign, "publish"))

    def test_feedback_requires_category_and_text(self):
        campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
        with self.assertRaises(CampaignError):
            transition(campaign, "REQUEST_CANDIDATE_CHANGES", FOUNDER, {"category": "OTHER"})

    def test_optimistic_lock_rejects_stale_update(self):
        campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
        with self.assertRaises(RevisionConflict):
            transition_campaign(campaign, "APPROVE_FOR_CREATIVE", *FOUNDER, 99, at=NOW)

    def test_pause_resumes_exact_previous_state(self):
        campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
        campaign = transition(campaign, "PAUSE_CAMPAIGN", FOUNDER)
        self.assertEqual(campaign["state"], "PAUSED")
        campaign = transition(campaign, "RESUME_CAMPAIGN")
        self.assertEqual(campaign["state"], "CANDIDATE_REVIEW")

    def test_generation_limit_escalates_instead_of_retrying_forever(self):
        campaign = new_campaign("CMP_TEST_001", identity(), at=NOW)
        campaign = transition(campaign, "APPROVE_FOR_CREATIVE", FOUNDER)
        campaign = transition(campaign, "START_CREATIVE_GENERATION", payload={"attempt": 4})
        self.assertEqual(campaign["state"], "FOUNDER_ACTION_REQUIRED")
        self.assertEqual(campaign["history"][-1]["details"]["limit_reason"], "CREATIVE_GENERATION_ATTEMPT_LIMIT")

    def test_publish_retry_limit_escalates(self):
        campaign = campaign_in_creative_review()
        campaign = transition(campaign, "APPROVE_TO_PUBLISH", FOUNDER)
        campaign = transition(
            campaign,
            "START_PUBLISH_PRECHECK",
            payload={"idempotency_key": "cmp-test-001:v1"},
        )
        for attempt in range(3):
            campaign = transition(campaign, "PUBLISH_PRECHECK_PASSED", payload={"passed": True})
            campaign = transition(campaign, "PUBLISH_RETRYABLE_FAILED", payload={"error": "timeout"})
            if attempt < 2:
                campaign = transition(campaign, "RETRY_PUBLISH")
        self.assertEqual(campaign["state"], "FOUNDER_ACTION_REQUIRED")
        self.assertEqual(campaign["publish"]["attempts"], 3)

class LegacyMigrationTests(unittest.TestCase):
    def test_imports_every_confirmed_post_without_fabricated_approval(self):
        campaigns = build_legacy_campaigns()
        posted = json.loads(
            (Path(__file__).resolve().parents[1] / "data" / "ig_published.json").read_text(
                encoding="utf-8"
            )
        )["posted"]
        self.assertEqual(len(campaigns), len(posted))
        self.assertTrue(all(item["state"] == "INSTAGRAM_POSTED" for item in campaigns))
        self.assertTrue(all(item["approvals"] == {"creative": None, "publish": None} for item in campaigns))
        self.assertTrue(all(item["governance"]["legacy_import"] for item in campaigns))

    def test_migration_projection_is_deterministic(self):
        self.assertEqual(build_legacy_campaigns(), build_legacy_campaigns())


if __name__ == "__main__":
    unittest.main()
