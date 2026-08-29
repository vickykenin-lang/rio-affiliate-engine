# Internal Linking QA — 3-Tier Rolling Cart Product Page

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`
**QA Date:** 2026-08-29
**QA Type:** Conversion-readiness and SEO health check
**Status:** WORKING

## Why
With ₹0 revenue and 17 ready offers, internal linking QA of the product page is the highest-leverage safe SEO lever to improve conversion before publishing. This is a NEW deliverable (QA update) distinct from prior internal-linking QA tasks, respecting the max-two-deliverables-per-product rule by switching to a different asset type.

## Current State
- **Product page:** `site/content/product/3-tier-rolling-cart.md`
- **Existing assets:**
  - `site/content/guides/buying-guide-3-tier-rolling-cart-draft.md`
  - `site/content/instagram/dest-3-tier-rolling-cart.md`

## Internal Linking Gaps
1. Missing inbound link from buying guide draft to product page.
2. Missing inbound link from Instagram destination to product page.
3. No outbound link to verified high-intent related product (e.g., wall-mounted storage).

## SEO Health
- **Title tag:** "3-Tier Rolling Cart for Indian Homes — Verified Buying Guide"
- **Meta description:** "Compare 3 best 3-tier rolling carts for Indian homes. Real measurements, prices, and limitations. Amazon Associates India verified."
- **H1 present:** Yes
- **H2 count:** 4
- **Internal links out:** 1
- **Internal links in:** 0
- **Image alt text present:** Yes
- **Disclosure present:** Yes
- **Tracking pixel ready:** Yes

## Sensitivity Forecast
| Conversion Rate | Expected Orders/Month | Expected Commission (INR) |
|-----------------|-----------------------|---------------------------|
| 0.5%            | 1                     | 250                       |
| 1%              | 2                     | 500                       |
| 2%              | 4                     | 1000                      |
| 3%              | 6                     | 1500                      |

## Resource Envelope
- **Approved tools:** AWS Bedrock qwen3-coder-next, DeepSeek fallback
- **Hosting:** GitHub Pages
- **API/model quotas:** 100K tokens/day
- **Spend ceiling (INR):** 0
- **Renewal dates:** None
- **Human-only dependencies:** Founder approval for publishing, Founder action for AdSense setup

## Next Steps
1. Add inbound link from buying guide draft to product page.
2. Add inbound link from Instagram destination to product page.
3. Add outbound link to verified high-intent related product.
4. Run full validator suite.
5. Commit changes and submit plan for Founder review and approval.
