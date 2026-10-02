import importlib.util
import json
import os
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rio_flyer_transport.py"
spec = importlib.util.spec_from_file_location("rio_flyer_transport", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def run_in_tmp(env):
    with tempfile.TemporaryDirectory() as td:
        old = os.getcwd()
        old_env = os.environ.copy()
        try:
            os.chdir(td)
            os.environ.clear()
            os.environ.update(old_env)
            os.environ.update(env)
            mod.RESULT_DIR = Path("integration/results/flyer_tasks")
            mod.ASSET_DIR = Path("creatives/generated")
            mod.USAGE_PATH = Path("data/image_generation_usage.json")
            return mod.run(), Path(td)
        finally:
            os.chdir(old)
            os.environ.clear()
            os.environ.update(old_env)


def test_requires_exact_product_reference():
    result, _ = run_in_tmp({"RIO_FLYER_TASK_ID": "t1", "RIO_FLYER_PAYLOAD": "{}"})
    assert result["status"] == "SAFE_STOP"
    assert result["error_code"] == "PRODUCT_REFERENCE_REQUIRED"


def test_requires_verified_https_product_image():
    result, _ = run_in_tmp({
        "RIO_FLYER_TASK_ID": "t2",
        "RIO_PRODUCT_REFERENCE": "B0ABC123",
        "RIO_FLYER_PAYLOAD": json.dumps({"product_image_url": "http://example.com/x.jpg"}),
    })
    assert result["error_code"] == "VERIFIED_PRODUCT_IMAGE_URL_REQUIRED"
    assert result["live_request_verified"] is False


def test_missing_cloudflare_credentials_safe_stops_before_provider_call():
    result, _ = run_in_tmp({
        "RIO_FLYER_TASK_ID": "t3",
        "RIO_PRODUCT_REFERENCE": "B0ABC123",
        "RIO_FLYER_PAYLOAD": json.dumps({"product_image_url": "https://example.com/x.jpg"}),
        "CLOUDFLARE_ACCOUNT_ID": "",
        "CLOUDFLARE_API_TOKEN": "",
    })
    assert result["error_code"] == "CLOUDFLARE_CREDENTIALS_NOT_CONFIGURED"
    assert result["credential_available"] is False


def test_monthly_provider_limit_blocks_before_download(monkeypatch=None):
    with tempfile.TemporaryDirectory() as td:
        old = os.getcwd()
        old_env = os.environ.copy()
        try:
            os.chdir(td)
            os.environ.update({
                "RIO_FLYER_TASK_ID": "t4",
                "RIO_PRODUCT_REFERENCE": "B0ABC123",
                "RIO_FLYER_PAYLOAD": json.dumps({"product_image_url": "https://example.com/x.jpg"}),
                "CLOUDFLARE_ACCOUNT_ID": "acct",
                "CLOUDFLARE_API_TOKEN": "token",
                "RIO_IMAGE_MONTHLY_PROVIDER_CALL_LIMIT": "1",
            })
            mod.RESULT_DIR = Path("integration/results/flyer_tasks")
            mod.ASSET_DIR = Path("creatives/generated")
            mod.USAGE_PATH = Path("data/image_generation_usage.json")
            month = mod.month_key()
            mod.save_json(mod.USAGE_PATH, {
                "version": "RIO_IMAGE_USAGE_V1",
                "months": {month: {"provider_calls": 1, "generated_assets": 0, "qa_approved_assets": 0}},
            })
            result = mod.run()
            assert result["error_code"] == "MONTHLY_IMAGE_PROVIDER_CALL_LIMIT_REACHED"
            assert result["provider_calls_this_month"] == 1
        finally:
            os.chdir(old)
            os.environ.clear()
            os.environ.update(old_env)


def test_preflight_verifies_transport_without_provider_call():
    result, _ = run_in_tmp({
        "RIO_FLYER_TASK_ID": "preflight-1",
        "RIO_PRODUCT_REFERENCE": "PRE-FLIGHT-FIXTURE",
        "RIO_FLYER_PAYLOAD": json.dumps({"product_image_url": "https://example.invalid/reference.jpg"}),
        "RIO_FLYER_PREFLIGHT_ONLY": "true",
        "CLOUDFLARE_ACCOUNT_ID": "acct",
        "CLOUDFLARE_API_TOKEN": "token",
    })
    assert result["status"] == "PREFLIGHT_READY"
    assert result["execution_status"] == "COMPLETED"
    assert result["credential_available"] is True
    assert result["endpoint_config_present"] is True
    assert result["provider_call_counted"] is False
    assert result["provider_call_attempted"] is False
    assert result["live_request_verified"] is False
    assert result["real_output_verified"] is False


def test_prompt_forbids_model_generated_marketing_text():
    prompt = mod.build_prompt({"title": "Socket Cover", "category": "Child Safety"})
    assert "exact factual product reference" in prompt
    assert "Do not render prices" in prompt
    assert "Do not replace it with a similar product" in prompt
