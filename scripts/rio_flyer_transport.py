#!/usr/bin/env python3
import base64
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

MODEL = "@cf/black-forest-labs/flux-2-klein-9b"
MONTHLY_PROVIDER_CALL_LIMIT_DEFAULT = 30
MAX_ATTEMPTS_PER_PRODUCT_DEFAULT = 2
RESULT_DIR = Path("integration/results/flyer_tasks")
ASSET_DIR = Path("creatives/generated")
USAGE_PATH = Path("data/image_generation_usage.json")


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clean(value, max_len=500):
    return str(value or "").strip()[:max_len]


def safe_task_id(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", clean(value, 160)).strip("-")
    return value[:120] or "unknown-task"


def month_key():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def usage_state():
    state = load_json(USAGE_PATH, {"version": "RIO_IMAGE_USAGE_V1", "months": {}})
    state.setdefault("version", "RIO_IMAGE_USAGE_V1")
    state.setdefault("months", {})
    month = month_key()
    current = state["months"].setdefault(month, {
        "provider_calls": 0,
        "generated_assets": 0,
        "qa_approved_assets": 0,
        "last_updated_at": None,
    })
    return state, current


def provider_limit():
    try:
        return max(1, int(os.getenv("RIO_IMAGE_MONTHLY_PROVIDER_CALL_LIMIT", str(MONTHLY_PROVIDER_CALL_LIMIT_DEFAULT))))
    except Exception:
        return MONTHLY_PROVIDER_CALL_LIMIT_DEFAULT


def max_attempts():
    try:
        return max(1, int(os.getenv("RIO_IMAGE_MAX_ATTEMPTS", str(MAX_ATTEMPTS_PER_PRODUCT_DEFAULT))))
    except Exception:
        return MAX_ATTEMPTS_PER_PRODUCT_DEFAULT


def build_result(task_id, product_reference, status, execution_status, error_code=None, **extra):
    result = {
        "task_id": task_id,
        "task_type": "PRODUCT_FLYER_GENERATE",
        "sender": "rio",
        "recipient": "hermes",
        "message_type": "TASK_RESULT",
        "product_reference": product_reference,
        "status": status,
        "execution_status": execution_status,
        "error_code": error_code,
        "provider": "cloudflare-workers-ai",
        "model": MODEL,
        "public_action_performed": False,
        "credential_transfer_performed": False,
        "objective_changed": False,
        "live_request_verified": False,
        "real_output_verified": False,
        "qa_approved": False,
        "business_outcome_verified": False,
        "created_at": now_iso(),
    }
    result.update(extra)
    return result


def parse_payload():
    raw = os.getenv("RIO_FLYER_PAYLOAD", "{}")
    try:
        payload = json.loads(raw)
    except Exception:
        return None, "PAYLOAD_INVALID_JSON"
    if not isinstance(payload, dict):
        return None, "PAYLOAD_MUST_BE_OBJECT"
    return payload, None


def download_reference_image(url):
    response = requests.get(url, timeout=25, headers={"User-Agent": "RIO-Flyer-Transport/1.0"})
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "image/jpeg").split(";")[0]
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    image.thumbnail((511, 511), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue(), "image/jpeg", image.size, content_type


def build_prompt(payload):
    title = clean(payload.get("title"), 180)
    category = clean(payload.get("category"), 80)
    angle = clean(payload.get("creative_angle") or "clean premium product promotion", 180)
    audience = clean(payload.get("target_audience"), 120)
    prompt = (
        "Use input image 0 as the exact factual product reference. Preserve the product's identity, "
        "shape, proportions, colors, visible branding and physical features. Do not replace it with a similar product. "
        f"Create a polished commercial lifestyle promotional visual for {title or 'this product'}"
        f"{f' in the {category} category' if category else ''}. Creative direction: {angle}. "
        f"{f'Target audience: {audience}. ' if audience else ''}"
        "Use a clean premium advertising composition, realistic lighting, clear focal hierarchy and generous negative space "
        "for later text overlay. Do not render prices, logos, QR codes, badges, claims, captions or other typography."
    )
    return prompt


def call_cloudflare(account_id, token, prompt, image_bytes, image_mime):
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    files = {
        "input_image_0": ("product-reference.jpg", image_bytes, image_mime),
    }
    data = {
        "prompt": prompt,
        "width": "1024",
        "height": "1024",
    }
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files,
        timeout=120,
    )
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:1000]}
    return response, body


def extract_image_base64(body):
    if isinstance(body, dict):
        if isinstance(body.get("image"), str):
            return body["image"]
        result = body.get("result")
        if isinstance(result, dict) and isinstance(result.get("image"), str):
            return result["image"]
    return None


def validate_generated_image(raw):
    if len(raw) < 10_000:
        return False, "GENERATED_IMAGE_TOO_SMALL", None
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        width, height = image.size
        if width < 512 or height < 512:
            return False, "GENERATED_IMAGE_DIMENSIONS_TOO_SMALL", [width, height]
        return True, None, [width, height]
    except Exception:
        return False, "GENERATED_IMAGE_INVALID", None


def run():
    task_id = safe_task_id(os.getenv("RIO_FLYER_TASK_ID"))
    product_reference = clean(os.getenv("RIO_PRODUCT_REFERENCE"), 300)
    result_path = RESULT_DIR / f"{task_id}.json"

    if not product_reference:
        result = build_result(task_id, product_reference, "SAFE_STOP", "BLOCKED", "PRODUCT_REFERENCE_REQUIRED")
        save_json(result_path, result)
        return result

    payload, payload_error = parse_payload()
    if payload_error:
        result = build_result(task_id, product_reference, "SAFE_STOP", "BLOCKED", payload_error)
        save_json(result_path, result)
        return result

    image_url = clean(payload.get("product_image_url"), 1500)
    if not image_url.startswith("https://"):
        result = build_result(task_id, product_reference, "SAFE_STOP", "BLOCKED", "VERIFIED_PRODUCT_IMAGE_URL_REQUIRED")
        save_json(result_path, result)
        return result

    account_id = clean(os.getenv("CLOUDFLARE_ACCOUNT_ID"), 100)
    token = clean(os.getenv("CLOUDFLARE_API_TOKEN"), 1000)
    if not account_id or not token:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "BLOCKED", "CLOUDFLARE_CREDENTIALS_NOT_CONFIGURED",
            credential_available=False,
        )
        save_json(result_path, result)
        return result

    state, current = usage_state()
    limit = provider_limit()
    if int(current.get("provider_calls", 0)) >= limit:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "BLOCKED", "MONTHLY_IMAGE_PROVIDER_CALL_LIMIT_REACHED",
            monthly_provider_call_limit=limit,
            provider_calls_this_month=int(current.get("provider_calls", 0)),
        )
        save_json(result_path, result)
        return result

    try:
        image_bytes, image_mime, reference_dimensions, source_content_type = download_reference_image(image_url)
    except Exception as exc:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "BLOCKED", "PRODUCT_IMAGE_FETCH_FAILED",
            detail=clean(exc, 300),
        )
        save_json(result_path, result)
        return result

    # Count before provider invocation so failed/billable calls remain bounded and auditable.
    current["provider_calls"] = int(current.get("provider_calls", 0)) + 1
    current["last_updated_at"] = now_iso()
    save_json(USAGE_PATH, state)

    prompt = build_prompt(payload)
    try:
        response, body = call_cloudflare(account_id, token, prompt, image_bytes, image_mime)
    except Exception as exc:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "FAILED", "CLOUDFLARE_REQUEST_FAILED",
            provider_call_counted=True,
            detail=clean(exc, 300),
            reference_dimensions=list(reference_dimensions),
        )
        save_json(result_path, result)
        return result

    if not response.ok:
        errors = body.get("errors") if isinstance(body, dict) else None
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "FAILED", "CLOUDFLARE_HTTP_ERROR",
            provider_call_counted=True,
            provider_http_status=response.status_code,
            provider_errors=errors,
            reference_dimensions=list(reference_dimensions),
        )
        save_json(result_path, result)
        return result

    image_b64 = extract_image_base64(body)
    if not image_b64:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "FAILED", "CLOUDFLARE_IMAGE_MISSING",
            provider_call_counted=True,
            provider_http_status=response.status_code,
        )
        save_json(result_path, result)
        return result

    try:
        generated = base64.b64decode(image_b64, validate=True)
    except Exception:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "FAILED", "CLOUDFLARE_IMAGE_BASE64_INVALID",
            provider_call_counted=True,
        )
        save_json(result_path, result)
        return result

    valid, image_error, generated_dimensions = validate_generated_image(generated)
    if not valid:
        result = build_result(
            task_id, product_reference, "SAFE_STOP", "FAILED", image_error,
            provider_call_counted=True,
            generated_dimensions=generated_dimensions,
        )
        save_json(result_path, result)
        return result

    asset_path = ASSET_DIR / f"{task_id}.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(generated)

    current["generated_assets"] = int(current.get("generated_assets", 0)) + 1
    current["last_updated_at"] = now_iso()
    save_json(USAGE_PATH, state)

    # This runtime verifies provider response + valid image bytes, not product-identity QA.
    result = build_result(
        task_id,
        product_reference,
        "GENERATED_PENDING_QA",
        "COMPLETED",
        None,
        credential_available=True,
        endpoint_config_present=True,
        source_implemented=True,
        live_request_verified=True,
        real_output_verified=True,
        qa_approved=False,
        asset_path=str(asset_path),
        provider_http_status=response.status_code,
        provider_call_counted=True,
        monthly_provider_call_limit=limit,
        provider_calls_this_month=int(current.get("provider_calls", 0)),
        generated_assets_this_month=int(current.get("generated_assets", 0)),
        reference_dimensions=list(reference_dimensions),
        generated_dimensions=generated_dimensions,
        source_content_type=source_content_type,
        prompt_version="RIO_FLYER_PROMPT_V1",
        max_attempts_per_product=max_attempts(),
    )
    save_json(result_path, result)
    return result


if __name__ == "__main__":
    output = run()
    print(json.dumps(output, sort_keys=True))
    # Always return zero after persisting a truthful task result; the orchestrator reads the result contract.
    sys.exit(0)
