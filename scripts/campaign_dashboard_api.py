#!/usr/bin/env python3
"""Authenticated RIO campaign review API (stdlib-only WSGI application)."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import date
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import unquote

try:
    from scripts.campaign_state import (
        ApprovalError,
        CampaignError,
        RevisionConflict,
        TransitionError,
        approval_is_valid,
        load_campaign,
        save_campaign,
        transition_campaign,
    )
except ModuleNotFoundError:  # direct `python scripts/campaign_dashboard_api.py`
    from campaign_state import (
        ApprovalError,
        CampaignError,
        RevisionConflict,
        TransitionError,
        approval_is_valid,
        load_campaign,
        save_campaign,
        transition_campaign,
    )

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = ROOT / "data" / "campaigns"
STATE_MACHINE_PATH = ROOT / "data" / "campaign_state_machine.json"
SESSION_COOKIE = "rio_founder_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
MAX_BODY_BYTES = 32 * 1024
OFFER_FRESHNESS_DAYS = int(os.environ.get("RIO_OFFER_FRESHNESS_DAYS", "1"))


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _secret(name: str, minimum: int = 32) -> bytes:
    value = os.environ.get(name, "").encode()
    if len(value) < minimum:
        raise RuntimeError(f"{name} must contain at least {minimum} characters")
    return value


def issue_session(founder_id: str, now: int | None = None) -> tuple[str, str]:
    issued = int(now if now is not None else time.time())
    payload = {"sub": founder_id, "role": "FOUNDER", "iat": issued, "exp": issued + SESSION_TTL_SECONDS,
               "nonce": secrets.token_hex(16)}
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64(hmac.new(_secret("RIO_SESSION_SECRET"), body.encode(), hashlib.sha256).digest())
    token = f"{body}.{signature}"
    csrf = _b64(hmac.new(_secret("RIO_CSRF_SECRET"), token.encode(), hashlib.sha256).digest())
    return token, csrf


def verify_session(token: str, now: int | None = None) -> dict[str, Any]:
    try:
        body, supplied = token.split(".", 1)
        expected = _b64(hmac.new(_secret("RIO_SESSION_SECRET"), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("signature")
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ApiError(401, "INVALID_SESSION", "Session is invalid") from exc
    current = int(now if now is not None else time.time())
    if payload.get("role") != "FOUNDER" or current >= int(payload.get("exp", 0)):
        raise ApiError(401, "EXPIRED_SESSION", "Session has expired")
    return payload


def csrf_for(token: str) -> str:
    return _b64(hmac.new(_secret("RIO_CSRF_SECRET"), token.encode(), hashlib.sha256).digest())


def _json(start_response: Callable, status: int, payload: Any, headers: list[tuple[str, str]] | None = None):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    reason = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
              409: "Conflict", 413: "Payload Too Large", 422: "Unprocessable Entity", 500: "Internal Server Error"}[status]
    base = [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(data))),
            ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")]
    start_response(f"{status} {reason}", base + (headers or []))
    return [data]


def _body(environ: dict[str, Any]) -> dict[str, Any]:
    try:
        size = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError as exc:
        raise ApiError(400, "INVALID_LENGTH", "Invalid content length") from exc
    if size > MAX_BODY_BYTES:
        raise ApiError(413, "BODY_TOO_LARGE", "Request body is too large")
    raw = environ["wsgi.input"].read(size) if size else b"{}"
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ApiError(400, "INVALID_JSON", "Request body must be JSON") from exc
    if not isinstance(value, dict):
        raise ApiError(400, "INVALID_JSON", "Request body must be an object")
    return value


def _cookies(environ: dict[str, Any]) -> SimpleCookie:
    jar = SimpleCookie()
    jar.load(environ.get("HTTP_COOKIE", ""))
    return jar


def _authenticate(environ: dict[str, Any], csrf: bool = False) -> tuple[dict[str, Any], str]:
    morsel = _cookies(environ).get(SESSION_COOKIE)
    if not morsel:
        raise ApiError(401, "AUTH_REQUIRED", "Founder authentication required")
    token = morsel.value
    actor = verify_session(token)
    if csrf:
        supplied = environ.get("HTTP_X_RIO_CSRF", "")
        if not supplied or not hmac.compare_digest(supplied, csrf_for(token)):
            raise ApiError(403, "CSRF_REJECTED", "CSRF validation failed")
    return actor, token


def _campaign_summary(item: dict[str, Any]) -> dict[str, Any]:
    identity = item["identity"]
    transitions = json.loads(STATE_MACHINE_PATH.read_text(encoding="utf-8"))["transitions"]
    return {"campaign_id": item["campaign_id"], "state": item["state"], "revision": item["revision"],
            "candidate_id": identity["candidate_id"], "title": identity["product_title"], "asin": identity["asin"],
            "score": identity.get("candidate_score"), "availability": identity.get("availability"),
            "offer_verified_at": identity.get("offer_verified_at"), "legacy": item["governance"].get("legacy_import", False),
            "creative_approved": approval_is_valid(item, "creative"),
            "publish_approved": bool(item.get("creative")) and approval_is_valid(item, "publish"),
            "allowed_actions": sorted(transitions.get(item["state"], {}))}


def list_campaigns() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(CAMPAIGN_DIR.glob("*.json")):
        rows.append(_campaign_summary(json.loads(path.read_text(encoding="utf-8"))))
    return sorted(rows, key=lambda x: (x["legacy"], -(x["score"] or 0), x["campaign_id"]))


def candidate_catalog(today: date | None = None) -> list[dict[str, Any]]:
    """Return deterministic READY ranking; stale evidence remains visible but ineligible."""
    current = today or date.today()
    existing_asins = {row["asin"] for row in list_campaigns()}
    with (ROOT / "data" / "product_candidates.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = []
    for row in rows:
        if row.get("status") != "READY":
            continue
        observed = date.fromisoformat(row["observed_at"])
        age = (current - observed).days
        blockers = []
        if age > OFFER_FRESHNESS_DAYS:
            blockers.append("FRESH_OFFER_VERIFICATION_REQUIRED")
        if row["merchant_product_id"] in existing_asins:
            blockers.append("CAMPAIGN_ALREADY_EXISTS")
        result.append({
            "candidate_id": row["candidate_id"], "cluster": row["cluster"], "asin": row["merchant_product_id"],
            "title": row["product_title"], "variant": row["variant"], "canonical_url": row["canonical_url"],
            "score": float(row["commercial_score"]), "observed_at": row["observed_at"],
            "verification_age_days": age, "eligible": not blockers, "blockers": blockers,
        })
    return sorted(result, key=lambda x: (-x["score"], x["candidate_id"]))


def application(environ: dict[str, Any], start_response: Callable) -> Iterable[bytes]:
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = unquote(environ.get("PATH_INFO", "/")).rstrip("/") or "/"
    try:
        if method == "POST" and path == "/api/login":
            body = _body(environ)
            supplied = str(body.get("access_token", ""))
            if not hmac.compare_digest(supplied, os.environ.get("RIO_FOUNDER_ACCESS_TOKEN", "")) or not supplied:
                raise ApiError(401, "LOGIN_FAILED", "Invalid Founder access token")
            founder_id = os.environ.get("RIO_FOUNDER_ID", "Vicky Gautam")
            token, csrf = issue_session(founder_id)
            cookie = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age={SESSION_TTL_SECONDS}"
            return _json(start_response, 200, {"actor": founder_id, "csrf_token": csrf}, [("Set-Cookie", cookie)])

        actor, _ = _authenticate(environ, csrf=method not in {"GET", "HEAD"})
        if method == "GET" and path == "/api/session":
            return _json(start_response, 200, {"actor": actor["sub"], "role": actor["role"]})
        if method == "GET" and path == "/api/campaigns":
            return _json(start_response, 200, {"campaigns": list_campaigns()})
        if method == "GET" and path == "/api/candidates":
            return _json(start_response, 200, {"candidates": candidate_catalog(), "selection_limit": 3})
        if method == "GET" and path.startswith("/api/campaigns/") and not path.endswith("/actions"):
            campaign_id = path.split("/")[3]
            return _json(start_response, 200, {"campaign": load_campaign(campaign_id)})
        if method == "POST" and path.startswith("/api/campaigns/") and path.endswith("/actions"):
            campaign_id = path.split("/")[3]
            body = _body(environ)
            if not str(body.get("idempotency_key", "")).strip():
                raise ApiError(400, "IDEMPOTENCY_REQUIRED", "idempotency_key is required")
            current = load_campaign(campaign_id)
            request_key = str(body["idempotency_key"]).strip()
            for event in current.get("history", []):
                recorded = event.get("details", {}).get("request_idempotency_key")
                if recorded == request_key:
                    if event.get("action") != str(body.get("action", "")).upper():
                        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "idempotency_key was used for another action")
                    return _json(start_response, 200, {"campaign": current, "replayed": True})
            payload = body.get("payload") or {}
            if not isinstance(payload, dict):
                raise ApiError(400, "INVALID_PAYLOAD", "payload must be an object")
            payload["request_idempotency_key"] = request_key
            updated = transition_campaign(current, str(body.get("action", "")), actor["sub"], actor["role"],
                                          int(body.get("expected_revision", -1)), payload)
            save_campaign(updated)
            return _json(start_response, 200, {"campaign": updated})
        raise ApiError(404, "NOT_FOUND", "Route not found")
    except FileNotFoundError:
        return _json(start_response, 404, {"error": {"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found"}})
    except RevisionConflict as exc:
        return _json(start_response, 409, {"error": {"code": "REVISION_CONFLICT", "message": str(exc)}})
    except (ApprovalError, TransitionError, CampaignError, ValueError) as exc:
        return _json(start_response, 422, {"error": {"code": "GOVERNANCE_REJECTED", "message": str(exc)}})
    except ApiError as exc:
        return _json(start_response, exc.status, {"error": {"code": exc.code, "message": exc.message}})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    host, port = os.environ.get("RIO_API_HOST", "127.0.0.1"), int(os.environ.get("RIO_API_PORT", "8787"))
    print(f"RIO campaign API listening on http://{host}:{port}")
    make_server(host, port, application).serve_forever()
