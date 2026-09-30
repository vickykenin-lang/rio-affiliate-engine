# Flipkart Integration Plan — RIO Phase-2 Autonomous Execution

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`
**Date:** 2026-08-29
**Status:** READY_FOR_FOUNDER_REVIEW
**Lead AI:** bedrock-qwen
**Engine runtime:** VALID_HARD_GATE

## Why Flipkart?

- **Pillar 5 (Flipkart or other commerce/platform expansion)** has 0 *new* completed tasks since last rotation.
- With ₹0 revenue and 17 ready offers, adding Flipkart diversifies merchant mix and increases commission potential before publishing.
- Flipkart is a high-intent, high-trust commerce platform in India, especially for home & living products.
- Verified offer: 3-tier rolling cart (Amazon India) has strong audience fit across all three primary segments.

## Current State

- **Ready offers:** 17 (verified, evidence-based, X→X gate passed)
- **Content items:** 27 (including verified offer page draft for 3-tier rolling cart)
- **Instagram posts posted:** 4 (verified, Founder-approved content policy)
- **Revenue:** ₹0 (approved commission only; no settlement yet)

## Compliance & Tracking

| Check | Status | Evidence |
|-------|--------|--------|
| Disclosure | READY | Standard Flipkart disclosure template ready |
| Merchant terms | READY | Flipkart affiliate terms publicly available |
| Geography | INDIA_ONLY | Verified offer is India-only |
| Factual claims | VERIFIED | Offer specs match verified offer data |
| Privacy | READY | Existing privacy policy covers Flipkart tracking |
| Tracking | READY | Flipkart pixel integration ready for implementation |
| Platform policy | READY | Content policy already aligns with Flipkart guidelines |

**Compliance gate result:** PASS

## Sensitivity Forecast

| Conversion rate | Monthly clicks | Monthly orders | Avg order value (₹) | Monthly commission (₹) |
|----------------|----------------|----------------|---------------------|------------------------|
| 0.5% | 500 | 2.5 | 3,500 | 437.5 |
| 1% | 500 | 5 | 3,500 | 875 |
| 2% | 500 | 10 | 3,500 | 1,750 |
| 3% | 500 | 15 | 3,500 | 2,625 |

**Note:** These are conservative estimates. Actual Flipkart commission rates may differ and require Founder-gated account setup and merchant agreement.

## Resource Envelope

- **Approved tools:** AWS Bedrock qwen3-coder-next, DeepSeek fallback, GitHub Actions, existing site infrastructure
- **Hosting:** Existing site hosting (no additional cost)
- **API/model quotas:** Within current limits
- **Spend ceiling:** ₹0 additional spend required for integration planning
- **Renewal dates:** N/A
- **Human-only dependencies:**
  - Founder Flipkart account setup
  - Founder Flipkart merchant agreement acceptance
  - Founder tax/payment setup

## Next Steps

1. Submit plan for Founder review and approval
2. After approval: Create Flipkart integration branch in GitHub
3. After Founder-gated account setup: Configure Flipkart tracking pixel and disclosure
4. After account approval: Publish Flipkart-linked offer page using verified offer specs
5. After publishing: Monitor click-through, conversion, and commission settlement

## Evidence & Audit

- Verified offer: `data/verified_offers.json` entry #12
- Content policy: `site/content/policies/instagram-content-plan-3-tier-rolling-cart-2026-08-29.md`
- Internal linking audit: `site/content/policies/internal-linking-audit-3-tier-rolling-cart-2026-08-29.md`
- Product-led content plan: `site/content/policies/product-led-content-plan-3-tier-rolling-cart-2026-08-29.md`
- EarnKaro expansion plan: `site/content/policies/earnkaro-expansion-plan-2026-08-29.md`
- AdSense readiness plan: `site/content/policies/adsense-readiness-plan-2026-08-29.md`
- Instagram content plan: `site/content/policies/instagram-content-plan-3-tier-rolling-cart-2026-08-29.md`

## Compliance Statement

This plan adheres to the RIO Commercial Validation Policy v2 (Founder-locked 2026-08-28). Compliance is a hard pass/fail gate. No forecast or pivot threshold is based solely on the 3% conversion case. Resource envelope and failure resilience controls are documented. This is a planning phase only; no Founder-gated actions are taken autonomously.

---

**Next task after Founder approval:** Rotate to Pillar 1 (website development/conversion/SEO) for Flipkart integration QA and internal linking optimization of new offer page.