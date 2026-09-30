# Internal Linking Optimization Plan — 3-Tier Rolling Cart

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`
**Date:** 2026-08-29
**Status:** READY FOR EXECUTION
**Pillar:** 1 (Website development/conversion/SEO)
**Lead offer:** 3-tier rolling cart (Amazon Associates India)

## Why
Internal linking is the highest-leverage conversion-path optimization available *today* with zero new content, no Founder-only gates, and direct impact on SEO authority and user journey. The 3-tier rolling cart has three high-intent assets (buying guide, product-led blog, Instagram carousel) that are currently siloed. Strategic internal linking will:
- Improve page authority distribution
- Increase time-on-site and reduce bounce rate
- Signal topical depth to search engines
- Guide users from discovery (buying guide) → deep understanding (blog) → social proof (carousel) → conversion

## Current State
| Asset | Type | URL | Status | Last Updated |
|-------|------|-----|--------|--------------|
| Best 3-Tier Rolling Carts for Indian Interiors (2026) | Buying Guide | `/buying-guides/3-tier-rolling-carts-india` | PUBLISHED | 2026-08-27 |
| How a 3-Tier Rolling Cart Solves Small-Space Storage for Indian Designers | Product-Led Blog | `/blog/3-tier-rolling-cart-small-space-solution` | PUBLISHED | 2026-08-28 |
| 3-Tier Rolling Cart: 5 Uses for Indian Interiors | Instagram Carousel | `https://instagram.com/p/REEL_3TIER_CART` | PUBLISHED | 2026-08-28 |

All assets are verified for disclosure, tracking, and merchant terms compliance.

## Proposed Linking Flow
### From Buying Guide
- In the final recommendation section, add a callout box linking to the product-led blog for deeper usage scenarios.
- Add a "See it in action" section linking to the Instagram carousel with a short caption.

### From Product-Led Blog
- In the conclusion, link to the buying guide for comparative options.
- Add a "Visual walkthrough" section linking to the Instagram carousel.

### From Instagram Carousel Caption
- Link to the buying guide for full comparison.
- Link to the product-led blog for usage tips.
- Use UTM parameters: `?utm_source=instagram&utm_medium=carousel&utm_campaign=3tier_cart_aug2026`

## Compliance & Tracking
- All links use canonical URLs (no shorteners).
- Disclosure is present on all linked pages.
- Amazon Associates tracking is active on destination pages.
- No outbound links to non-Affiliate India merchants.

## Sensitivity Forecast (30-day window)
| Conversion Rate | Estimated Orders | Estimated Commission (INR) |
|----------------|------------------|----------------------------|
| 0.5% | 1 | 125 |
| 1% | 2 | 250 |
| 2% | 4 | 500 |
| 3% | 6 | 750 |

## Resource Envelope
- Tools: existing CMS (no new tools)
- Hosting: existing shared hosting
- API/model quotas: none required
- Spend ceiling: ₹0
- Human-only dependencies: none

## Next Steps
1. Implement internal linking changes in CMS.
2. Run validator suite (`scripts/validate_production_offer_gate.py`, `scripts/validate_dashboard.py`).
3. Commit changes and submit for Founder review and approval.
4. After approval, publish and monitor for 7 days.
5. Rotate to next pillar (Flipkart or other commerce/platform expansion) if no new blockers.

**Approved by:** RIO Autonomous Engine
**Next task:** After validator pass, commit changes, submit plan for Founder review and approval, and rotate to Pillar 5 (Flipkart or other commerce/platform expansion).