#!/usr/bin/env python3
"""Generate RIO's verified product storefront and exact-offer landing pages."""
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
REGISTRY = ROOT / "data" / "offer_identity_registry.csv"
IMAGE_REGISTRY = ROOT / "data" / "product_image_registry.json"
BASE = "https://vickykenin-lang.github.io/rio-affiliate-engine"


def esc(value):
    return html.escape(value or "", quote=True)


def page_shell(title, description, body, canonical):
    return f'''<!doctype html>
<html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{('../' if '/products/' in canonical else '')}styles.css">
</head><body><header class="site-header"><div class="wrap nav"><a class="brand" href="{('../' if '/products/' in canonical else './')}">RIO</a><nav><a href="{('../' if '/products/' in canonical else '')}compare.html">Compare</a><a href="{('../' if '/products/' in canonical else '')}guides/">Guides</a><a href="{('../' if '/products/' in canonical else '')}legal/affiliate-disclosure.html">Disclosure</a></nav></div></header>
{body}
<footer class="site-footer"><div class="wrap"><p class="foot-disclosure"><strong>Affiliate disclosure:</strong> RIO may earn from qualifying purchases made through eligible links, at no extra cost to you. Merchant pages remain the source for current price and availability.</p></div></footer></body></html>'''


def card(offer, image):
    name = esc(offer["creative_product_name"])
    link = esc(image["affiliate_url"])
    img = esc(image["image_url"])
    oid = esc(offer["offer_id"])
    return f'''<article class="deal-card" data-offer-id="{oid}">
<div class="thumb-wrap"><a class="product-image-link" href="{link}" target="_blank" rel="nofollow sponsored noopener" aria-label="View {name}"><img src="{img}" alt="{name}" loading="lazy"></a><span class="verified-pill">Verified product</span></div>
<div class="body"><h3>{name}</h3><p class="product-meta">Exact product identity and destination matched by RIO.</p><a class="go product-cta" href="{link}" target="_blank" rel="nofollow sponsored noopener">View product</a><a class="details-link" href="products/{oid}.html">Product details</a></div></article>'''


def main():
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        offers = {row["offer_id"]: row for row in csv.DictReader(handle) if row["publish_status"] == "READY" and row["affiliate_status"] == "ACTIVE" and row["identity_status"] == "VERIFIED" and row["availability_status"] == "IN_STOCK"}
    images = json.loads(IMAGE_REGISTRY.read_text(encoding="utf-8"))["images"]
    by_asin = {item["asin"]: item for item in images}
    ready = []
    for offer in offers.values():
        image = by_asin.get(offer["merchant_product_id"])
        if not image or f"/dp/{offer['merchant_product_id']}" not in image.get("affiliate_url", "") or "tag=rioaffiliate-21" not in image.get("affiliate_url", ""):
            raise SystemExit(f"STORE FRONT GATE: missing exact validated image/link mapping for {offer['offer_id']}")
        ready.append((offer, image))

    snapshot_path = ROOT / "data" / "dashboard_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else {}
    content_items = int(snapshot.get("content_items", 0))

    cards = "\n".join(card(offer, image) for offer, image in ready)
    home_body = f'''<section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><div class="hero-badges"><span>Exact product links</span><span>India focused</span><span>Affiliate disclosure</span></div><h1>Verified products. One clear click.</h1><p>Every product image and the button directly below it open the same verified product destination.</p></div></div></section><main class="wrap"><div class="stats-strip"><div><strong>{content_items}</strong><span>Content items</span></div><div><strong>{len(ready)}</strong><span>Verified offers</span></div><div><strong>1:1</strong><span>Image-to-link match</span></div><div><strong>Active</strong><span>Direct links</span></div></div><section class="section-head"><div><div class="eyebrow">RIO verified storefront</div><h2>Choose a product</h2></div></section><div class="deals-grid">{cards}</div><div class="notice"><strong>Disclosure:</strong> RIO may earn a commission from qualifying purchases. Confirm current price, availability and variant on the merchant page.</div></main>'''
    (SITE / "index.html").write_text(page_shell("RIO — Verified Products", "Verified products with exact direct affiliate links.", home_body, f"{BASE}/"), encoding="utf-8")

    product_dir = SITE / "products"
    product_dir.mkdir(exist_ok=True)
    for offer, image in ready:
        name = esc(offer["creative_product_name"])
        link = esc(image["affiliate_url"])
        body = f'''<main class="wrap product-page"><p><a href="../">← All verified products</a></p><article class="product-detail"><a class="product-image-link" href="{link}" target="_blank" rel="nofollow sponsored noopener"><img class="product-hero-image" src="{esc(image['image_url'])}" alt="{name}"></a><div class="product-copy"><span class="verified-label">Exact product verified</span><h1>{name}</h1><p>RIO matched this image, product identity and destination to ASIN {esc(offer['merchant_product_id'])}.</p><a class="btn product-cta" href="{link}" target="_blank" rel="nofollow sponsored noopener">View product</a><p class="muted">Price and availability can change. Please confirm them on the merchant page.</p></div></article><div class="disclosure"><strong>Affiliate disclosure:</strong> RIO may earn a commission from qualifying purchases made through this link, at no extra cost to you.</div></main>'''
        target = product_dir / f"{offer['offer_id']}.html"
        target.write_text(page_shell(name, f"Verified product destination for {name}.", body, f"{BASE}/products/{offer['offer_id']}.html"), encoding="utf-8")
    print(f"STOREFRONT: generated {len(ready)} verified direct-link product cards and landing pages")


if __name__ == "__main__":
    main()
