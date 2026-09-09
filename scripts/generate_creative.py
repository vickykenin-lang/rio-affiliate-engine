#!/usr/bin/env python3
"""
generate_creative.py

Automates the first draft of an Instagram post creative for offers that
have already cleared the identity/affiliate verification gate
(data/offer_identity_registry.csv: identity_status=VERIFIED,
availability_status=IN_STOCK, affiliate_status=ACTIVE,
publish_status=READY).

What this script does NOT do, on purpose:
  - It does not fetch or fabricate a product photo. As of this writing,
    SiteStripe's Image/Text+Image links were discontinued Dec 2023, the
    old Product Advertising API was retired Jan 2025, and its replacement
    (Amazon Creators API) requires qualifying sales this account does not
    yet have. A generic illustration standing in for one specific real
    product would risk violating the X-to-X integrity policy's "images
    describe the intended product" rule. So every generated creative
    ships with a clearly labelled photo placeholder that a human fills in
    (e.g. via a SiteStripe-generated text link + a manually sourced,
    compliant photo) before it can be approved.
  - It does not touch offer_identity_registry.csv. That file is the
    verification gate and this script only ever reads it.
  - It does not publish anything. It only adds/updates an entry in
    data/creative_approval_queue.json with status "pending" (or
    "redevelop_pending" -> regenerated -> "pending" again). Publishing
    happens only after a human approves via the dashboard.

Env:
  DEEPSEEK_API_KEY   required. Used only to draft headline/subheadline/
                      feature copy, grounded strictly in the verified
                      product_name / creative_variant fields -- the
                      prompt forbids inventing specs, prices, or claims
                      not present in the registry row.

Reads:
  data/offer_identity_registry.csv
  data/creative_approval_queue.json   (created if missing)

Writes:
  site/creatives/<offer_id>_v<version>.html
  data/creative_approval_queue.json
"""

import csv
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "offer_identity_registry.csv"
QUEUE_PATH = ROOT / "data" / "creative_approval_queue.json"
CREATIVE_DIR = ROOT / "site" / "creatives"

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# offer_identity_registry.csv has NO dedicated tracking_id column -- it is
# only ever mentioned inside the free-text "notes" field. Every verified
# row currently references the same Associates tracking ID
# ("tracking_id rioaffiliate-21"), so it's set here explicitly rather than
# regex-scraped out of notes text, which would be fragile. If a second
# tracking ID is ever introduced per-campaign, this needs to become a real
# registry column instead.
TRACKING_ID = "rioaffiliate-21"

READY_STATES = {
    "identity_status": "VERIFIED",
    "availability_status": "IN_STOCK",
    "affiliate_status": "ACTIVE",
    "publish_status": "READY",
}


def load_registry():
    if not REGISTRY_PATH.exists():
        sys.exit(f"registry not found at {REGISTRY_PATH}")
    with open(REGISTRY_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def is_release_ready(row):
    return all(row.get(k, "").strip() == v for k, v in READY_STATES.items())


def load_queue():
    if not QUEUE_PATH.exists():
        return {}
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue):
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")


def needs_generation(entry):
    if entry is None:
        return True
    return entry.get("status") == "redevelop_pending"


def draft_copy(row, feedback=None):
    """Ask DeepSeek for headline/subheadline/3 features, grounded only in
    the verified registry row. Raises on any API/parsing failure -- callers
    should skip the offer rather than fall back to invented copy."""

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    grounding = {
        "product_name": row.get("creative_product_name") or row.get("product_name"),
        "variant": row.get("creative_variant") or row.get("variant"),
    }

    system_prompt = (
        "You write short Instagram ad copy for a home-storage affiliate brand called RIO. "
        "You are given ONLY a verified product name and variant. "
        "Do not invent specs, dimensions, prices, ratings, or claims that are not "
        "obviously implied by the product name/variant itself. "
        "If the product name doesn't tell you something, leave it out rather than guessing. "
        "Reply with strict JSON only, no prose, no markdown fences, matching this shape: "
        '{"headline": str (max 40 chars, 2-3 short line-breakable phrases), '
        '"subheadline": str (max 110 chars), '
        '"features": [str, str, str] (each max 24 chars)}'
    )

    user_prompt = f"Verified product data: {json.dumps(grounding, ensure_ascii=False)}"
    if feedback:
        user_prompt += (
            f"\n\nThe previous draft was rejected with this feedback -- address it: {feedback}"
        )

    payload = json.dumps(
        {
            "model": "deepseek-chat",
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"].strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    copy = json.loads(content)

    for key in ("headline", "subheadline", "features"):
        if key not in copy:
            raise ValueError(f"DeepSeek response missing '{key}'")
    if not isinstance(copy["features"], list) or len(copy["features"]) != 3:
        raise ValueError("DeepSeek response must include exactly 3 features")

    return copy


def render_html(offer_id, row, copy, version):
    headline_html = copy["headline"].replace(" | ", "<br>")
    features_html = "\n".join(
        f'<div class="frow"><div class="fic"></div><div class="flabel">{f}</div></div>'
        for f in copy["features"]
    )
    canonical_url = row.get("canonical_url", "").strip()
    cta_href = f"{canonical_url}?tag={TRACKING_ID}" if canonical_url else "#"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>RIO creative — {offer_id} v{version}</title>
<style>
  :root{{--ink:#1A1A17;--muted:#6B6558;--paper:#FAF6EC;--line:#E7E0CE;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:#0E1110;font-family:sans-serif;padding:32px 16px 64px;}}
  .wrap{{max-width:1080px;margin:0 auto;}}
  .card{{width:100%;aspect-ratio:1080/1350;background:var(--paper);border-radius:18px;overflow:hidden;position:relative;color:var(--ink);display:flex;flex-direction:column;}}
  .badge{{position:absolute;top:44px;left:44px;width:64px;height:64px;border-radius:50%;background:var(--ink);color:var(--paper);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;z-index:3;}}
  .top{{flex:1;position:relative;display:flex;}}
  .textcol{{width:68%;padding:120px 0 0 40px;position:relative;z-index:2;}}
  h1{{font-weight:800;font-size:38px;line-height:1.15;letter-spacing:-0.01em;}}
  .sub{{font-size:14px;color:var(--muted);line-height:1.55;margin-top:16px;max-width:30ch;}}
  .features{{margin-top:26px;display:flex;flex-direction:column;gap:14px;}}
  .frow{{display:flex;align-items:center;gap:12px;}}
  .fic{{width:34px;height:34px;border-radius:50%;border:1.5px solid var(--ink);flex-shrink:0;}}
  .flabel{{font-size:14px;font-weight:500;}}
  .cta{{margin-top:28px;display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:var(--paper);font-weight:600;font-size:14px;padding:14px 22px;border-radius:100px;width:fit-content;text-decoration:none;}}
  .photoslot{{position:absolute;right:0;top:0;width:40%;height:100%;background:repeating-linear-gradient(45deg,#EFE7D0,#EFE7D0 10px,#E3D6AE 10px,#E3D6AE 20px);display:flex;align-items:center;justify-content:center;text-align:center;padding:20px;}}
  .photoslot span{{font-size:13px;color:#6B6558;font-weight:600;}}
  .bottom{{border-top:1px solid var(--line);padding:20px 44px;display:flex;justify-content:space-between;align-items:flex-start;background:var(--paper);}}
  .pname{{font-size:13px;line-height:1.4;max-width:60%;}}
  .disc{{font-size:10px;color:var(--muted);margin-top:8px;}}
  .brandcol{{text-align:right;}}
  .brandmark{{font-weight:700;font-size:16px;}}
  .pricenote{{font-size:10px;color:var(--muted);margin-top:6px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="badge">Rio</div>
    <div class="top">
      <div class="textcol">
        <h1>{headline_html}</h1>
        <p class="sub">{copy['subheadline']}</p>
        <div class="features">
{features_html}
        </div>
        <a class="cta" href="{cta_href}" target="_blank" rel="noopener sponsored">Check current price</a>
      </div>
      <div class="photoslot"><span>PRODUCT PHOTO NEEDED<br>(SiteStripe-sourced, manual)</span></div>
    </div>
    <div class="bottom">
      <div>
        <p class="pname"><b>{row.get('creative_product_name') or row.get('product_name')}</b><br>{row.get('creative_variant') or row.get('variant')}</p>
        <p class="disc">If you buy via our link, we may earn a commission.</p>
      </div>
      <div class="brandcol">
        <div class="brandmark">Rio</div>
        <p class="pricenote">*Price may change</p>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""


def main():
    registry = load_registry()
    queue = load_queue()
    now = datetime.now(timezone.utc).isoformat()
    generated = []

    for row in registry:
        offer_id = row.get("offer_id", "").strip()
        if not offer_id or not is_release_ready(row):
            continue

        existing = queue.get(offer_id)
        if not needs_generation(existing):
            continue

        feedback = existing.get("feedback") if existing else None
        version = (existing.get("version", 1) if existing else 1)

        try:
            copy = draft_copy(row, feedback=feedback)
        except Exception as exc:
            print(f"[skip] {offer_id}: copy generation failed: {exc}", file=sys.stderr)
            continue

        html = render_html(offer_id, row, copy, version)
        CREATIVE_DIR.mkdir(parents=True, exist_ok=True)
        html_path = CREATIVE_DIR / f"{offer_id}_v{version}.html"
        html_path.write_text(html, encoding="utf-8")

        history = (existing or {}).get("history", [])
        history.append({"status": "generated", "at": now, "version": version})

        queue[offer_id] = {
            "offer_id": offer_id,
            "version": version,
            "status": "pending",
            "html_path": str(html_path.relative_to(ROOT)),
            "product_name": row.get("creative_product_name") or row.get("product_name"),
            "tracking_id": TRACKING_ID,
            "canonical_url": row.get("canonical_url", "").strip(),
            "needs_photo": True,
            "generated_at": now,
            "history": history,
        }
        generated.append(offer_id)
        print(f"[generated] {offer_id} v{version} -> {html_path.relative_to(ROOT)}")

    if generated:
        save_queue(queue)
        print(f"queue updated: {len(generated)} offer(s) generated")
    else:
        print("nothing to generate")


if __name__ == "__main__":
    main()
