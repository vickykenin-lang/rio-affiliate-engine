#!/usr/bin/env python3
"""RIO shared OpenAI-compatible AI client for legacy DeepSeek callers.

DeepSeek remains the preferred provider for these legacy content/discovery paths,
but a bad/missing DeepSeek credential must not take the business pipeline down.
When DeepSeek is unavailable or returns an auth/network failure, the client falls
back to the already-governed Bedrock Qwen endpoint when AWS_BEDROCK_API_KEY is
available. Callers still receive plain text / JSON and do not fabricate success.
"""
import json, os, urllib.error, urllib.request

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
BEDROCK_KEY = os.environ.get("AWS_BEDROCK_API_KEY", "").strip()
BEDROCK_REGION = os.environ.get("AWS_BEDROCK_REGION", "us-east-1").strip() or "us-east-1"
BEDROCK_URL = f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1/chat/completions"
BEDROCK_MODEL = os.environ.get("RIO_BEDROCK_CONTENT_MODEL", "qwen.qwen3-coder-next")
LAST_PROVIDER = None


def available():
    return bool(DEEPSEEK_KEY or BEDROCK_KEY)


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
    if DEEPSEEK_KEY:
        try:
            text = _call(f"{DEEPSEEK_BASE}/chat/completions", DEEPSEEK_KEY, DEEPSEEK_MODEL, prompt, timeout)
            LAST_PROVIDER = "deepseek"
            return text
        except urllib.error.HTTPError as e:
            try: detail = e.read().decode(errors="replace")[:300]
            except Exception: detail = "(could not read error body)"
            errors.append(f"deepseek HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            errors.append(f"deepseek network: {e}")
        except Exception as e:
            errors.append(f"deepseek: {e}")
    else:
        errors.append("deepseek credential missing")

    if BEDROCK_KEY:
        try:
            text = _call(BEDROCK_URL, BEDROCK_KEY, BEDROCK_MODEL, prompt, timeout)
            LAST_PROVIDER = "bedrock-qwen-fallback"
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

    LAST_PROVIDER = None
    raise RuntimeError("AI providers unavailable: " + " | ".join(errors))


def ask_json(prompt, timeout=45):
    """Call governed provider chain, strip markdown fences, and parse JSON."""
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
