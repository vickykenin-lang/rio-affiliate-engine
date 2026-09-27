#!/usr/bin/env python3
"""Governed creative-generation entrypoint.

Reuses the existing rendering/queue logic from generate_creative.py but replaces
its legacy direct-DeepSeek copy function with the shared Bedrock-first client.
DeepSeek fallback remains disabled unless RIO_ALLOW_DEEPSEEK_FALLBACK is
explicitly enabled; production workflow does not enable it.
"""
import json
import generate_creative as legacy
from deepseek_client import ask_json


def bedrock_draft_copy(row, feedback=None):
    grounding = {
        "product_name": row.get("creative_product_name") or row.get("product_name"),
        "variant": row.get("creative_variant") or row.get("variant"),
    }
    prompt = (
        "You write short Instagram affiliate creative copy for RIO. "
        "Use only the verified product data below. Do not invent specs, dimensions, "
        "prices, ratings, claims, benefits, certifications, or availability. "
        "Return strict JSON only with keys headline, subheadline, features. "
        "headline max 40 chars; subheadline max 110 chars; features must be exactly "
        "3 short strings, each max 24 chars.\nVerified product data: "
        + json.dumps(grounding, ensure_ascii=False)
    )
    if feedback:
        prompt += "\nPrevious governed feedback: " + str(feedback)[:800]
    copy = ask_json(prompt, timeout=45)
    for key in ("headline", "subheadline", "features"):
        if key not in copy:
            raise ValueError(f"Bedrock response missing '{key}'")
    if not isinstance(copy["features"], list) or len(copy["features"]) != 3:
        raise ValueError("Bedrock response must include exactly 3 features")
    return copy


legacy.draft_copy = bedrock_draft_copy
legacy.main()
