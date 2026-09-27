#!/usr/bin/env python3
"""RIO shared OpenAI-compatible AI client for legacy callers.

Bedrock Qwen is the required primary provider. DeepSeek is optional and disabled
unless RIO_ALLOW_DEEPSEEK_FALLBACK=1. Legacy module name is preserved to avoid
breaking existing imports while provider routing is migrated safely.
"""
import json, os, urllib.error, urllib.request

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
ALLOW_DEEPSEEK = os.environ.get("RIO_ALLOW_DEEPSEEK_FALLBACK", "0").strip().lower() in {"1","true","yes"}
BEDROCK_KEY = os.environ.get("AWS_BEDROCK_API_KEY", "").strip()
BEDROCK_REGION = os.environ.get("AWS_BEDROCK_REGION", "us-east-1").strip() or "us-east-1"
BEDROCK_URL = f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1/chat/completions"
BEDROCK_MODEL = os.environ.get("RIO_BEDROCK_CONTENT_MODEL", "qwen.qwen3-coder-next")
LAST_PROVIDER = None


def available():
    return bool(BEDROCK_KEY or (ALLOW_DEEPSEEK and DEEPSEEK_KEY))


def _call(url, key, model, prompt, timeout):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 700,
    }).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    if not text.strip():
        raise RuntimeError("empty provider content")
    return text


def ask(prompt, timeout=45):
    global LAST_PROVIDER
    errors = []

    if BEDROCK_KEY:
        try:
            text = _call(BEDROCK_URL, BEDROCK_KEY, BEDROCK_MODEL, prompt, timeout)
            LAST_PROVIDER = "bedrock-qwen"
            return text
        except urllib.error.HTTPError as e:
            try: detail = e.read().decode(errors="replace")[:300]
            except Exception: detail = "(could not read error body)"
            errors.append(f"bedrock HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            errors.append(f"bedrock network: {e}")
        except Exception as e:
            errors.append(f"bedrock: {e}")
    else:
        errors.append("bedrock credential missing")

    if ALLOW_DEEPSEEK and DEEPSEEK_KEY:
        try:
            text = _call(f"{DEEPSEEK_BASE}/chat/completions", DEEPSEEK_KEY, DEEPSEEK_MODEL, prompt, timeout)
            LAST_PROVIDER = "deepseek-optional-fallback"
            return text
        except urllib.error.HTTPError as e:
            try: detail = e.read().decode(errors="replace")[:300]
            except Exception: detail = "(could not read error body)"
            errors.append(f"deepseek HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            errors.append(f"deepseek network: {e}")
        except Exception as e:
            errors.append(f"deepseek: {e}")

    LAST_PROVIDER = None
    raise RuntimeError("AI providers unavailable: " + " | ".join(errors))


def ask_json(prompt, timeout=45):
    txt = ask(prompt, timeout).strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:]
    txt = txt.strip()
    try:
        return json.loads(txt, strict=False)
    except json.JSONDecodeError:
        start, end = txt.find("{"), txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(txt[start:end + 1], strict=False)
        raise
