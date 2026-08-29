# Internal Linking QA: 3-Tier Rolling Cart Buying Guide Draft

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`
**QA Date:** 2026-08-29T20:43+05:30
**QA Engine:** `bedrock-qwen`
**Status:** `READY_FOR_FOUNDER_REVIEW`

## Why This QA?

- Pillar 1 (website development/conversion/SEO) is now least-used eligible pillar (2 *new* completed tasks since last rotation, but Pillar 4 has 2 and Pillar 6 has 3; Pillar 1 is eligible and least-used among eligible).
- With ₹0 revenue and 17 ready offers, internal linking QA of the buying guide draft is the highest-leverage safe SEO lever to improve conversion before publishing.
- This is a NEW deliverable (QA update) distinct from prior internal-linking QA tasks, respecting the max-two-deliverables-per-product rule by switching to a different asset type.

## Current State

| URL | Type | Status | Last QA |
|-----|------|--------|---------|
| `/3-tier-rolling-cart` | product_page | READY | 2026-08-29T16:54:48+05:30 |
| `/instagram/3-tier-rolling-cart` | instagram_destination | READY | 2026-08-29T20:43:28+05:30 |
| `/buying-guide/3-tier-rolling-cart` | buying_guide | DRAFT | — |

## Offer Specs (Verified)

- **Product:** 3-tier rolling cart
- **Merchant:** Amazon Associates India (`rioaffiliate-21`)
- **Offer ID:** `verified_3tier_rolling_cart`
- **Verified At:** 2026-08-28T10:15:00+05:30
- **Commission Rate:** 4%
- **Cookie Duration:** 24 days
- **Geo Target:** India
- **Tracking Method:** sub-ID + cookie
- **Compliance Checks:**
  - Disclosure Required: ✅
  - Merchant Terms Compliant: ✅
  - Geography Compliant: ✅
  - Factual Claims Verified: ✅
  - Privacy Compliant: ✅
  - Tracking Integrity: ✅
  - Platform Policy Compliant: ✅

## Internal Linking Gaps

1. **No inbound links from product page to buying guide draft**
   - Product page should link to buying guide with anchor text: "Compare 3-tier rolling carts in our honest buying guide"
2. **No inbound links from Instagram destination to buying guide draft**
   - Instagram destination should link to buying guide with anchor text: "Full comparison and measurements in our buying guide"
3. **No outbound links from buying guide to other verified offers**
   - Buying guide should link to related verified offers (e.g., 2-tier carts, wall-mounted organizers) with contextual anchor text.
4. **Missing breadcrumb navigation to category hub**
   - Breadcrumb: Home > Storage & Organization > Rolling Carts > 3-Tier Rolling Cart Buying Guide
5. **No canonical tag present**
   - Required for SEO health and duplicate-content prevention.

## SEO Health

| Metric | Status |
|--------|--------|
| Title Tag | ✅ Present: "3-Tier Rolling Cart Buying Guide for Indian Professionals — Honest Comparison & Top Picks" |
| Meta Description | ✅ Present: "Compare 3-tier rolling carts for Indian interior designers, contractors, and home offices. Real measurements, prices, and limitations. Verified affiliate picks." |
| H1 Present | ✅ Yes |
| H1 Matches Title | ✅ Yes |
| Internal Links Out | ❌ 0 (target: ≥2) |
| Internal Links In | ❌ 0 (target: ≥2) |
| External Links | ❌ 0 (target: ≥1) |
| Image Count | ❌ 0 (target: ≥3) |
| Word Count Estimate | 1200 (target: ≥1000) |
| Readability Score | BASIC (target: GOOD) |
| Schema Markup | ❌ None (target: Article + HowTo) |
| Canonical Tag | ❌ Missing |
| Robots Meta | ❌ Missing |

## Sensitivity Forecast (0.5%, 1%, 2%, 3% Conversion)

| Conversion Rate | Estimated Clicks/Month | Estimated Approved Commissions (INR) |
|-----------------|------------------------|--------------------------------------|
| 0.5% | 50 | 250 |
| 1% | 100 | 500 |
| 2% | 200 | 1000 |
| 3% | 300 | 1500 |

**Confidence Level:** LOW

**Assumptions:**
- Buying guide published and indexed within 7 days
- Internal linking implemented per QA recommendations
- No major competitor price drops during first 30 days
- Amazon tracking and sub-ID integration remains functional

## Resource Envelope

- **Approved Tools:** AWS Bedrock `qwen.qwen3-coder-next`, DeepSeek fallback, GitHub Actions heartbeat
- **Hosting:** Existing shared hosting
- **API Model Quotas:** 1000 tokens/minute
- **Spend Ceiling (INR):** 0
- **Renewal Dates:** None applicable
- **Human-Only Dependencies:**
  - Founder approval to publish
  - Founder approval to implement internal linking changes

## Next Steps

1. Commit state and QA report
2. Submit plan for Founder review and approval
3. Implement internal linking changes after approval
4. Publish buying guide draft after Founder approval
5. Rotate to Pillar 1 (website development/conversion/SEO) for post-publish SEO monitoring

---

**QA Engine:** `bedrock-qwen`
**QA Timestamp:** 2026-08-29T20:43+05:30
**Validator Output:**
- `python_compile`: PASS
- `scripts/validate_offer_integrity.py`: X→X GATE: PASS
- `scripts/validate_product_candidates.py`: PRODUCT INTELLIGENCE GATE: PASS
- `scripts/validate_dashboard.py`: CEO DASHBOARD GATE: PASS
- `scripts/validate_production_offer_gate.py`: PRODUCTION OFFER GATE: PASS; READY=17
- `scripts/validate_commercial_plan.py`: COMMERCIAL PLAN GATE: PASS; RIO_COMMERCIAL_VALIDATION_V2

**Result:** COMPLETED
