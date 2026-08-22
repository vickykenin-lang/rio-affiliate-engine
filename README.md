# RIO Affiliate Engine — Production Readiness

India-focused affiliate content engine for compact-home and Home/Kitchen buying guides.

## Locked objective

RIO's Day-0 objective is affiliate commissions only: build an automated, scalable affiliate business toward ₹10 lakh/month net profit, with a long-term ₹50 lakh+/month goal. Infrastructure, dashboards and content counts enable that objective; they are not business results.

## Evidence-backed status

The repository currently contains:

- 27 content items
- 32 product candidates: 17 READY, 13 DISCOVERY_REQUIRED, 2 REJECTED
- 17 Amazon.in offers marked READY with tracking ID `rioaffiliate-21`
- A heartbeat with real production reachability plus four local commercial validators
- Daily content QA and product-discovery suggestions
- Instagram publishing with public-image preflight and deduplication

Do not call the system live, production-ready or earning from local validators alone. Current truth is stored in:

- `data/status.json` — heartbeat and validator state
- `data/production_status.json` — real HTTP checks for homepage, sitemap and social-card asset
- `data/dashboard_snapshot.json` — pipeline counts
- `data/content_review_report.json` — content trust assessment
- `data/ig_published.json` — confirmed Instagram media IDs/permalinks only

During the 2026-08-22 audit, both the default GitHub Pages URL and `rio.designinfra.in` returned HTTP 404. Public availability therefore remains unverified until the production gate passes. A private source repository requires a GitHub plan/configuration that supports Pages, or a separate public deployment target.

## Validate locally

```bash
python3 scripts/validate.py
python3 scripts/validate_offer_integrity.py
python3 scripts/validate_product_candidates.py
python3 scripts/validate_dashboard.py
python3 scripts/validate_production_offer_gate.py
```

## Verify production

```bash
python3 scripts/check_production.py
```

Set `RIO_PUBLIC_SITE_BASE` when a different public deployment URL is selected.

## Security and compliance

- Never commit passwords, API keys, tokens, payment data, government IDs or private customer/order data.
- Amazon links must carry the approved tracking ID.
- Customer review text and star ratings must not be published without an approved Amazon Product Advertising API source and its license requirements.
- Revenue remains ₹0 until a real Associates report proves approved commission.
- Paid promotion requires explicit Founder budget approval.
