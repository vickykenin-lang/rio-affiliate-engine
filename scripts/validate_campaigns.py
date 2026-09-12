#!/usr/bin/env python3
"""Fail-closed structural and governance validation for RIO campaigns."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = ROOT / "data" / "campaigns"
STATE_MACHINE = json.loads(
    (ROOT / "data" / "campaign_state_machine.json").read_text(encoding="utf-8")
)
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def validate_campaign(campaign: dict, path: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "campaign_id",
        "state",
        "revision",
        "identity",
        "creative",
        "approvals",
        "publish",
        "governance",
        "created_at",
        "updated_at",
        "history",
    }
    missing = sorted(required - set(campaign))
    if missing:
        return [f"{path}: missing {', '.join(missing)}"]
    if campaign["state"] not in STATE_MACHINE["transitions"]:
        errors.append(f"{path}: unknown state {campaign['state']}")
    if path.stem != campaign["campaign_id"]:
        errors.append(f"{path}: filename/campaign_id mismatch")
    if campaign["governance"].get("legacy_import"):
        if campaign["governance"].get("approval_model") != "PRE_STEP_2_LEGACY":
            errors.append(f"{path}: legacy import has wrong approval model")
        if campaign["state"] != "INSTAGRAM_POSTED" or not campaign["publish"].get("media_id"):
            errors.append(f"{path}: legacy record must preserve a confirmed posted media ID")
        if any(campaign["approvals"].values()):
            errors.append(f"{path}: legacy migration must not fabricate approvals")
    else:
        if campaign["governance"].get("approval_model") != "STEP_2_TWO_STAGE":
            errors.append(f"{path}: governed campaign has wrong approval model")
        for kind, approval in campaign["approvals"].items():
            if approval and not SHA256.fullmatch(approval.get("bound_hash", "")):
                errors.append(f"{path}: invalid {kind} approval hash")
    history = campaign.get("history", [])
    if not history:
        errors.append(f"{path}: history is empty")
    for event in history:
        if event.get("campaign_id") != campaign["campaign_id"]:
            errors.append(f"{path}: event campaign_id mismatch")
    return errors


def main() -> None:
    errors: list[str] = []
    paths = sorted(CAMPAIGN_DIR.glob("*.json")) if CAMPAIGN_DIR.exists() else []
    for path in paths:
        try:
            campaign = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: unreadable JSON: {exc}")
            continue
        errors.extend(validate_campaign(campaign, path))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"campaign validation PASS: {len(paths)} record(s)")


if __name__ == "__main__":
    main()
