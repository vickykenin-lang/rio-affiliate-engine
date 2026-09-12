#!/usr/bin/env python3
"""RIO Step 3 campaign state engine.

This module is deliberately deterministic and stdlib-only. It owns legal state
transitions, Founder-only approvals, optimistic locking, append-only events,
and hash-bound approval invalidation. External workers may request transitions;
they must not write campaign state directly.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_MACHINE_PATH = ROOT / "data" / "campaign_state_machine.json"
CAMPAIGN_DIR = ROOT / "data" / "campaigns"

MAX_CREATIVE_GENERATION_ATTEMPTS = 3
MAX_PUBLISH_ATTEMPTS = 3

IDENTITY_BOUND_FIELDS = (
    "candidate_id",
    "offer_id",
    "merchant",
    "asin",
    "product_title",
    "variant",
    "canonical_url",
    "affiliate_url",
    "landing_page_url",
    "candidate_status",
    "offer_verified_at",
    "availability",
)
CREATIVE_BOUND_FIELDS = (
    "version",
    "asset_path",
    "creative_sha256",
    "caption_version",
    "caption_text",
    "caption_sha256",
    "landing_page_sha256",
    "source_policy",
)
FOUNDER_ONLY_ACTIONS = {
    "APPROVE_FOR_CREATIVE",
    "APPROVE_TO_PUBLISH",
    "REQUEST_CANDIDATE_CHANGES",
    "REQUEST_CREATIVE_CHANGES",
    "REJECT_CAMPAIGN",
    "PAUSE_CAMPAIGN",
}
FEEDBACK_ACTIONS = {"REQUEST_CANDIDATE_CHANGES", "REQUEST_CREATIVE_CHANGES"}
FEEDBACK_CATEGORIES = {
    "WRONG_PRODUCT",
    "MISLEADING_VISUAL",
    "COPY_ISSUE",
    "DISCLOSURE_ISSUE",
    "DESIGN_ISSUE",
    "LINK_ISSUE",
    "OTHER",
}


class CampaignError(ValueError):
    """Base campaign governance error."""


class TransitionError(CampaignError):
    """Raised for an illegal state transition."""


class ApprovalError(CampaignError):
    """Raised when an approval is missing, invalid, or unauthorized."""


class RevisionConflict(CampaignError):
    """Raised when a caller tries to update a stale campaign projection."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def identity_hash(campaign: dict[str, Any]) -> str:
    identity = campaign["identity"]
    return canonical_hash({key: identity.get(key) for key in IDENTITY_BOUND_FIELDS})


def publish_bundle_hash(campaign: dict[str, Any]) -> str:
    creative = campaign.get("creative")
    if not creative:
        raise ApprovalError("creative package is missing")
    return canonical_hash(
        {
            "identity_hash": identity_hash(campaign),
            "creative": {key: creative.get(key) for key in CREATIVE_BOUND_FIELDS},
        }
    )


def _actor(actor_id: str, actor_role: str) -> dict[str, str]:
    actor_role = actor_role.upper()
    if actor_role not in {"FOUNDER", "SYSTEM", "MIGRATION"}:
        raise CampaignError(f"unsupported actor role: {actor_role}")
    if not actor_id.strip():
        raise CampaignError("actor id is required")
    return {"id": actor_id.strip(), "role": actor_role}


def _state_machine() -> dict[str, Any]:
    return json.loads(STATE_MACHINE_PATH.read_text(encoding="utf-8"))


def _event(
    campaign: dict[str, Any],
    action: str,
    actor: dict[str, str],
    at: str,
    from_state: str | None,
    to_state: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "campaign_id": campaign["campaign_id"],
        "revision": campaign["revision"],
        "action": action,
        "actor": actor,
        "at": at,
        "from_state": from_state,
        "to_state": to_state,
        "details": details or {},
    }


def new_campaign(
    campaign_id: str,
    identity: dict[str, Any],
    actor_id: str = "rio-system",
    at: str | None = None,
) -> dict[str, Any]:
    """Create a governed campaign from a READY candidate identity snapshot."""
    required = {
        "candidate_id",
        "offer_id",
        "merchant",
        "asin",
        "product_title",
        "variant",
        "canonical_url",
        "affiliate_url",
        "landing_page_url",
        "candidate_score",
        "candidate_status",
        "selected_at",
        "offer_verified_at",
        "availability",
        "evidence_refs",
    }
    missing = sorted(required - set(identity))
    if missing:
        raise CampaignError(f"identity is missing fields: {', '.join(missing)}")
    if identity["candidate_status"] != "READY":
        raise CampaignError("only READY candidates may create a campaign")
    if not campaign_id or not campaign_id.replace("_", "").replace("-", "").replace(":", "").isalnum():
        raise CampaignError("invalid campaign_id")

    timestamp = at or utc_now()
    actor = _actor(actor_id, "SYSTEM")
    campaign: dict[str, Any] = {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "state": "CANDIDATE_REVIEW",
        "revision": 0,
        "identity": copy.deepcopy(identity),
        "creative": None,
        "approvals": {"creative": None, "publish": None},
        "publish": {
            "attempts": 0,
            "idempotency_key": None,
            "precheck": None,
            "media_id": None,
            "permalink": None,
            "error": None,
        },
        "governance": {
            "approval_model": "STEP_2_TWO_STAGE",
            "legacy_import": False,
            "previous_state": None,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "history": [],
    }
    campaign["history"].append(
        _event(campaign, "CAMPAIGN_CREATED", actor, timestamp, None, campaign["state"])
    )
    return campaign


def approval_is_valid(campaign: dict[str, Any], kind: str) -> bool:
    approval = campaign.get("approvals", {}).get(kind)
    if not approval or approval.get("invalidated_at"):
        return False
    expected = identity_hash(campaign) if kind == "creative" else publish_bundle_hash(campaign)
    return approval.get("bound_hash") == expected


def _invalidate(
    campaign: dict[str, Any], kind: str, reason: str, at: str
) -> bool:
    approval = campaign["approvals"].get(kind)
    if not approval or approval.get("invalidated_at"):
        return False
    approval["invalidated_at"] = at
    approval["invalidation_reason"] = reason
    return True


def reconcile_approvals(campaign: dict[str, Any], at: str | None = None) -> list[str]:
    """Invalidate approvals whose exact bound data changed; return invalidated kinds."""
    timestamp = at or utc_now()
    invalidated: list[str] = []
    creative_approval = campaign.get("approvals", {}).get("creative")
    if creative_approval and not creative_approval.get("invalidated_at"):
        if creative_approval.get("bound_hash") != identity_hash(campaign):
            _invalidate(campaign, "creative", "IDENTITY_BUNDLE_CHANGED", timestamp)
            _invalidate(campaign, "publish", "UPSTREAM_CREATIVE_APPROVAL_INVALIDATED", timestamp)
            campaign["state"] = "CANDIDATE_REVIEW"
            invalidated.append("creative")

    publish_approval = campaign.get("approvals", {}).get("publish")
    if publish_approval and not publish_approval.get("invalidated_at"):
        if publish_approval.get("bound_hash") != publish_bundle_hash(campaign):
            _invalidate(campaign, "publish", "PUBLISH_BUNDLE_CHANGED", timestamp)
            if campaign["state"] != "CANDIDATE_REVIEW":
                campaign["state"] = "CREATIVE_REVIEW"
            invalidated.append("publish")
    return invalidated


def update_material_data(
    campaign: dict[str, Any],
    updates: dict[str, dict[str, Any]],
    actor_id: str,
    actor_role: str,
    expected_revision: int,
    at: str | None = None,
) -> dict[str, Any]:
    """Update identity/creative through the governed path and invalidate stale approvals."""
    if campaign["revision"] != expected_revision:
        raise RevisionConflict(
            f"expected revision {expected_revision}, current revision is {campaign['revision']}"
        )
    unknown_sections = set(updates) - {"identity", "creative"}
    if unknown_sections:
        raise CampaignError(f"unsupported material sections: {sorted(unknown_sections)}")

    result = copy.deepcopy(campaign)
    before_state = result["state"]
    for section, values in updates.items():
        if not isinstance(values, dict):
            raise CampaignError(f"{section} update must be an object")
        if section == "creative" and result["creative"] is None:
            raise CampaignError("cannot patch a missing creative package")
        result[section].update(copy.deepcopy(values))

    timestamp = at or utc_now()
    invalidated = reconcile_approvals(result, timestamp)
    result["revision"] += 1
    result["updated_at"] = timestamp
    result["history"].append(
        _event(
            result,
            "MATERIAL_DATA_UPDATED",
            _actor(actor_id, actor_role),
            timestamp,
            before_state,
            result["state"],
            {"sections": sorted(updates), "invalidated_approvals": invalidated},
        )
    )
    return result


def transition_campaign(
    campaign: dict[str, Any],
    action: str,
    actor_id: str,
    actor_role: str,
    expected_revision: int,
    payload: dict[str, Any] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    payload = copy.deepcopy(payload or {})
    if campaign["revision"] != expected_revision:
        raise RevisionConflict(
            f"expected revision {expected_revision}, current revision is {campaign['revision']}"
        )
    if campaign.get("governance", {}).get("legacy_import"):
        raise TransitionError("legacy imported campaigns are immutable")

    result = copy.deepcopy(campaign)
    timestamp = at or utc_now()
    reconcile_approvals(result, timestamp)
    actor = _actor(actor_id, actor_role)
    action = action.upper()
    if action in FOUNDER_ONLY_ACTIONS and actor["role"] != "FOUNDER":
        raise ApprovalError(f"{action} requires FOUNDER role")

    transitions = _state_machine()["transitions"]
    from_state = result["state"]
    target = transitions.get(from_state, {}).get(action)
    if not target:
        raise TransitionError(f"illegal transition: {from_state} + {action}")

    if action in FEEDBACK_ACTIONS:
        category = payload.get("category")
        feedback = str(payload.get("feedback", "")).strip()
        if category not in FEEDBACK_CATEGORIES or not feedback:
            raise CampaignError("change request needs a valid category and feedback")

    if action == "APPROVE_FOR_CREATIVE":
        result["approvals"]["creative"] = {
            "actor": actor,
            "at": timestamp,
            "bound_hash": identity_hash(result),
            "invalidated_at": None,
            "invalidation_reason": None,
        }
        result["approvals"]["publish"] = None

    limit_reason = None
    if action in {"START_CREATIVE_GENERATION", "RETRY_CREATIVE_GENERATION", "START_CREATIVE_CORRECTION"}:
        if not approval_is_valid(result, "creative"):
            raise ApprovalError("valid APPROVED_FOR_CREATIVE is required")
        attempt = int(payload.get("attempt", 1))
        if attempt < 1:
            raise CampaignError("creative generation attempt must be positive")
        if attempt > MAX_CREATIVE_GENERATION_ATTEMPTS:
            limit_reason = "CREATIVE_GENERATION_ATTEMPT_LIMIT"
        if action == "START_CREATIVE_CORRECTION":
            correction_attempt = int(payload.get("correction_attempt", 0))
            if correction_attempt < 1:
                raise CampaignError("creative correction_attempt is required")
            if correction_attempt > 3:
                limit_reason = "CREATIVE_CORRECTION_ATTEMPT_LIMIT"

    if action == "CREATIVE_GENERATION_SUCCEEDED":
        required = {
            "version",
            "asset_path",
            "creative_sha256",
            "caption_version",
            "caption_text",
            "caption_sha256",
            "landing_page_sha256",
            "source_policy",
            "provider",
            "model",
            "request_id",
            "generated_at",
            "attempt",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise CampaignError(f"creative payload is missing fields: {', '.join(missing)}")
        result["creative"] = payload
        _invalidate(result, "publish", "NEW_CREATIVE_VERSION", timestamp)

    if action == "APPROVE_TO_PUBLISH":
        if not approval_is_valid(result, "creative"):
            raise ApprovalError("valid APPROVED_FOR_CREATIVE is required")
        result["approvals"]["publish"] = {
            "actor": actor,
            "at": timestamp,
            "bound_hash": publish_bundle_hash(result),
            "invalidated_at": None,
            "invalidation_reason": None,
        }

    if action == "START_PUBLISH_PRECHECK":
        if not approval_is_valid(result, "creative") or not approval_is_valid(result, "publish"):
            raise ApprovalError("both valid Founder approvals are required")
        key = str(payload.get("idempotency_key", "")).strip()
        if not key:
            raise CampaignError("publish idempotency_key is required")
        existing = result["publish"].get("idempotency_key")
        if existing and existing != key:
            raise CampaignError("idempotency_key cannot change after publish starts")
        result["publish"]["idempotency_key"] = key

    if action in {"PUBLISH_PRECHECK_PASSED", "PUBLISH_PRECHECK_BLOCKED"}:
        result["publish"]["precheck"] = payload

    if action == "PUBLISH_PRECHECK_PASSED":
        if not approval_is_valid(result, "creative") or not approval_is_valid(result, "publish"):
            raise ApprovalError("approvals became invalid during precheck")
        result["publish"]["attempts"] += 1
        if result["publish"]["attempts"] > MAX_PUBLISH_ATTEMPTS:
            raise CampaignError("publish attempt limit exceeded")

    if action in {"PUBLISH_RETRYABLE_FAILED", "PUBLISH_NONRETRYABLE_FAILED"}:
        result["publish"]["error"] = payload
    if action == "PUBLISH_RETRYABLE_FAILED" and result["publish"]["attempts"] >= MAX_PUBLISH_ATTEMPTS:
        limit_reason = "PUBLISH_RETRY_LIMIT"

    if action == "PUBLISH_SUCCEEDED":
        media_id = str(payload.get("media_id", "")).strip()
        if not media_id:
            raise CampaignError("Meta media_id is required")
        result["publish"]["media_id"] = media_id
        result["publish"]["permalink"] = payload.get("permalink")
        result["publish"]["error"] = None

    if action == "REQUEST_CREATIVE_CHANGES":
        _invalidate(result, "publish", "FOUNDER_REQUESTED_CREATIVE_CHANGES", timestamp)

    if action == "PAUSE_CAMPAIGN":
        result["governance"]["previous_state"] = from_state
    if limit_reason:
        result["governance"]["previous_state"] = from_state
        target = "FOUNDER_ACTION_REQUIRED"
        payload["limit_reason"] = limit_reason
    if target == "$PREVIOUS_STATE":
        target = result["governance"].get("previous_state")
        if not target:
            raise TransitionError("campaign has no previous state to restore")
        result["governance"]["previous_state"] = None

    result["state"] = target
    result["revision"] += 1
    result["updated_at"] = timestamp
    safe_details = {
        key: value
        for key, value in payload.items()
        if key not in {"caption_text", "access_token", "token", "secret"}
    }
    result["history"].append(
        _event(result, action, actor, timestamp, from_state, target, safe_details)
    )
    return result


def campaign_path(campaign_id: str) -> Path:
    return CAMPAIGN_DIR / f"{campaign_id}.json"


def load_campaign(campaign_id: str) -> dict[str, Any]:
    return json.loads(campaign_path(campaign_id).read_text(encoding="utf-8"))


def save_campaign(campaign: dict[str, Any]) -> Path:
    """Atomically save one campaign projection."""
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    target = campaign_path(campaign["campaign_id"])
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(CAMPAIGN_DIR))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(campaign, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed RIO campaign transition engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    transition_parser = subparsers.add_parser("transition")
    transition_parser.add_argument("campaign_id")
    transition_parser.add_argument("action")
    transition_parser.add_argument("--actor-id", required=True)
    transition_parser.add_argument("--actor-role", required=True, choices=["FOUNDER", "SYSTEM"])
    transition_parser.add_argument("--expected-revision", required=True, type=int)
    transition_parser.add_argument("--payload-json", default="{}")

    args = parser.parse_args()
    if args.command == "transition":
        current = load_campaign(args.campaign_id)
        updated = transition_campaign(
            current,
            args.action,
            args.actor_id,
            args.actor_role,
            args.expected_revision,
            json.loads(args.payload_json),
        )
        path = save_campaign(updated)
        print(f"{updated['campaign_id']}: {updated['state']} revision={updated['revision']} -> {path}")


if __name__ == "__main__":
    main()
