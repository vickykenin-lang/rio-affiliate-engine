#!/usr/bin/env python3
"""SOUL runtime integrity layer — mandatory fail-closed gate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOUL = ROOT / "data" / "SOUL.md"
OBJECTIVE = ROOT / "data" / "RIO_3.0_DEFINITION.md"
MEMORY = ROOT / "data" / "rio_work_status.json"
STATUS = ROOT / "data" / "status.json"
OUT = ROOT / "data" / "soul_runtime_status.json"

REQUIRED_MARKERS = (
    "# SOUL — Portable Autonomous Runtime Contract",
    "## Precedence",
    "## Seven Laws",
    "## Runtime Contract",
    "## AI Binding",
    "## Liveness Semantics",
)


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_json(path):
    try:
        value = json.loads(read(path))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def inspect_runtime():
    soul = read(SOUL)
    objective = read(OBJECTIVE)
    memory = load_json(MEMORY)
    status = load_json(STATUS)
    checks = {
        "soul_present": bool(soul.strip()),
        "soul_contract_markers": bool(soul.strip()) and all(m in soul for m in REQUIRED_MARKERS),
        "objective_present": bool(objective.strip()),
        "memory_present": MEMORY.exists() and bool(memory),
        "heartbeat_status_present": STATUS.exists() and bool(status),
        "lead_ai_declared": bool(status.get("runtime_primary_ai")),
        "validators_declared": "all_validators_pass" in status,
        "validators_healthy": status.get("all_validators_pass") is True,
    }
    valid = all(checks.values())
    result = {
        "mode": "hard_fail_closed",
        "hard_fail_closed": True,
        "project_binding": "RIO",
        "valid": valid,
        "checks": checks,
        "soul_sha256": hashlib.sha256(soul.encode("utf-8")).hexdigest() if soul else None,
        "objective_path": "data/RIO_3.0_DEFINITION.md",
        "memory_path": "data/rio_work_status.json",
        "lead_ai": status.get("runtime_primary_ai"),
        "fallbacks": status.get("runtime_fallbacks") or [],
        "validators_currently_healthy": status.get("all_validators_pass"),
        "execution_effect": "ALLOWED" if valid else "AUTONOMOUS_EXECUTION_BLOCKED",
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(inspect_runtime())
