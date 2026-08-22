#!/usr/bin/env python3
"""RIO public-content compliance and truthfulness gate."""
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
errors = []
warnings = []

snapshot = json.loads((ROOT / "data" / "dashboard_snapshot.json").read_text(encoding="utf-8"))
review = json.loads((ROOT / "data" / "content_review_report.json").read_text(encoding="utf-8"))

for path in SITE.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(SITE)

    if "pagead2.googlesyndication.com" in text:
        errors.append(f"{rel}: AdSense code conflicts with affiliate-only Day-0 objective")

    canonical = re.search(r'<link rel="canonical" href="([^"]+)">', text)
    if not canonical:
        errors.append(f"{rel}: missing canonical")
    elif urlparse(canonical.group(1)).scheme not in ("http", "https"):
        errors.append(f"{rel}: canonical must be absolute")

    prohibited = [
        r"Rated \d(?:\.\d)?/5",
        r"\b\d[\d,]* ratings\b",
        r"% five-star",
        r"Amazon(?:'s)? (?:own )?review summary",
        r"one reviewer",
        r"buyers report",
    ]
    if any(re.search(pattern, text, re.I) for pattern in prohibited):
        errors.append(f"{rel}: customer rating/review evidence needs approved PA-API provenance")

    for href in re.findall(r'href="(https://www\.amazon\.in/[^"]+)"', text):
        if "tag=rioaffiliate-21" not in href:
            errors.append(f"{rel}: Amazon link missing rioaffiliate-21 tag")

    hotlinks = len(re.findall(r'm\.media-amazon\.com', text))
    if hotlinks:
        warnings.append(f"{rel}: {hotlinks} Amazon image hotlink(s); confirm SiteStripe/PA-API license provenance")

articles = review.get("articles", review)
for article_path, result in articles.items():
    if float(result.get("score", 0)) < 6:
        public_path = SITE / article_path
        if public_path.exists() and 'content="noindex,follow"' not in public_path.read_text(encoding="utf-8"):
            errors.append(f"{article_path}: score below 6 must remain noindex until re-reviewed")

sitemap = ET.fromstring((SITE / "sitemap.xml").read_bytes())
locs = [node.text.strip() for node in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc") if node.text]
if not locs or any(urlparse(loc).scheme not in ("http", "https") or not urlparse(loc).netloc for loc in locs):
    errors.append("sitemap.xml: every loc must be an absolute URL")

home = (SITE / "index.html").read_text(encoding="utf-8")
for value, label in [
    (snapshot["content_items"], "Content items"),
    (snapshot["ready_offers"], "Verified offers"),
]:
    expected = f"<strong>{value}</strong><span>{label}</span>"
    if expected not in home:
        errors.append(f"index.html: audited {label.lower()} count is stale")

for warning in warnings:
    print("WARNING:", warning)
if errors:
    print("PUBLIC CONTENT GATE: FAIL")
    for error in errors:
        print("ERROR:", error)
    sys.exit(1)
print(f"PUBLIC CONTENT GATE: PASS ({len(warnings)} provenance warning(s))")
