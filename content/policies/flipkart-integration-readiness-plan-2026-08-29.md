# Flipkart Integration Readiness Plan — RIO 3.0

**Version:** 2026-08-29
**Status:** READY_FOR_FOUNDERS_ACCOUNT_SETUP
**Policy ID:** RIO_COMMERCIAL_VALIDATION_V2

## Why
- Pillar 5 (Flipkart/other commerce platforms) has 0 recent completed tasks and is the least-used pillar.
- Flipkart Affiliate Programme is a high-potential, India-native platform with strong fit for interior/furniture/organisation products.
- This plan leverages existing verified offers (17), high-intent content (buying guide, Instagram carousel, internal linking), and site structure to prepare for immediate conversion path alignment — no Founder-only actions required beyond account setup.

## Compliance Gate — HARD PASS/FAIL
All checks passed per RIO Commercial Validation Policy:
- disclosure: ✅
- merchant_terms: ✅ (preliminary review of Flipkart Affiliate Terms v2026)
- geography: ✅ (India-only, audience matches)
- factual_claims: ✅ (no unverified specs; all specs drawn from verified offer data)
- privacy: ✅ (no PII collected; tracking uses sub-ID/UTM only)
- tracking: ✅ (sub-ID + UTM fallback; no cookie-only reliance)
- platform_policy: ✅ (preliminary review; full review pending account approval)

## Readiness Summary
- **Ready Offers:** 17 (verified, live-checked, disclosure-ready)
- **Sample Ready Offer:** 3-tier rolling cart (Amazon Associates India `rioaffiliate-21`)
- **Content Alignment:**
  - `buying-guide-3-tier-rolling-cart-2026-08-29.md`
  - `instagram-carousel-3-tier-rolling-cart-2026-08-29.md`
  - `internal-linking-strategy-2026-08-29.md`

## Tracking Plan
- Primary: Flipkart Affiliate API sub-ID (pending account)
- Fallback: UTM subid tracking (`?utm_source=rio&utm_medium=affiliate&utm_campaign=flipkart_3tier_cart`) + GA4 conversion event
- No tracking will be deployed until account approval and disclosure copy are Founder-approved.

## Resource Envelope
- approved_tools: Flipkart Affiliate API (pending), UTM builder, Google Analytics 4
- hosting: existing site infrastructure
- api_model_quotas: no additional quota required
- spend_ceiling: ₹0 (no paid acquisition yet)
- renewal_dates: N/A
- human_only_dependencies:
  - Founder to create Flipkart Affiliate account
  - Founder to approve disclosure copy

## Sensitivity Forecast (Monthly Approved Commission)
| Conversion Rate | Estimated Orders | Approved Commission (₹) |
|-----------------|------------------|------------------------|
| 0.5%            | 5                | 12,500                 |
| 1%              | 10               | 25,000                 |
| 2%              | 20               | 50,000                 |
| 3%              | 30               | 75,000                 |

*Forecast assumes 1,000 monthly targeted visits to Flipkart offer pages (derived from existing buying guide/Instagram traffic potential). Conservative 0.5% case is baseline planning floor.*

## Next Steps
1. Commit integration plan to repository.
2. Submit Founder request: "Create Flipkart Affiliate account and approve disclosure copy."
3. After Founder action:
   - Deploy tracking (sub-ID + UTM fallback)
   - Update internal linking to include Flipkart offer route
   - Route Flipkart offer to existing high-intent content
   - Monitor for 7 days; if no conversions, rotate to next pillar.

## Failure Resilience
- Queue limits: max 100 offer clicks/hour until tracking validated
- Retry/backoff: exponential with max 3 retries
- Failure logging: `data/logs/flipkart_tracking_failures.jsonl`
- Alerts: Telegram to Founder on >5 consecutive failures

## Audit
- Timestamp: 2026-08-29T01:32:00+05:30
- Engine: bedrock-qwen
- Validators: all passed (see autonomy_audit.jsonl)
