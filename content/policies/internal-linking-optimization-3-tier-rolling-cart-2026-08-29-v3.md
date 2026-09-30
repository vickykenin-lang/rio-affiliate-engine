# Internal Linking Optimization Plan — 3-Tier Rolling Cart

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`
**Date:** 2026-08-29T07:15+05:30
**Status:** READY_FOR_FOUNDER_REVIEW
**Offer Key:** `3-tier-rolling-cart`
**Lead AI:** `bedrock-qwen`

## Why
Pillar 1 (website development/conversion/SEO) has 0 *new* completed tasks since last rotation suppression. With 17 ready offers and ₹0 verified revenue, ensuring the conversion path is clean, compliant, and internally linked is the highest-leverage safe task before publishing.

Internal linking:
- Improves SEO signal strength for the offer page
- Reduces bounce by guiding users from high-intent assets to conversion
- Enables cross-selling of verified offers
- Supports the 30-day execution-validation window by proving conversion-path readiness

## Current State
- **Offer Page:** Not yet published
- **High-Intent Assets:**
  - `buying-guide-3tier-cart` — PUBLISHED (2026-08-27)
  - `product-led-blog-3tier-cart` — DRAFT_POLICY (2026-08-29)
  - `instagram-carousel-3tier-cart` — DRAFT_POLICY (2026-08-29)
- **Existing Internal Links:** None yet on offer page

## Proposed Links
| From Asset | Link Text | Destination | Type |
|------------|-----------|-------------|------|
| Buying Guide (Section: Top 3 Options) | "3-Tier Rolling Cart — Verified Offer" | `/offers/3-tier-rolling-cart` | Conversion |
| Product-Led Blog (Conclusion) | "See verified specs & Amazon.in offer" | `/offers/3-tier-rolling-cart` | Conversion |
| Instagram Carousel (CTA Slide) | "Full comparison & verified offer" | `/offers/3-tier-rolling-cart` | Conversion |
| Offer Page (Footer) | "Back to Buying Guide" | `/buying-guides/rolling-cart-buying-guide-2026-08-27` | Navigation |

## Compliance & Tracking
- All links use canonical `/offers/3-tier-rolling-cart` path
- Amazon Associates sub-ID (`rioaffiliate-21`) applied to destination URL
- Disclosure paragraph placed above all links
- No outbound links except Amazon.in (merchant-compliant)

## Sensitivity Forecast (0.5/1/2/3% conversion)
| Rate | Estimated Clicks | Estimated Orders | Approved Commission (INR) |
|------|------------------|------------------|---------------------------|
| 0.5% | 120 | 0.6 | 360 |
| 1% | 120 | 1.2 | 720 |
| 2% | 120 | 2.4 | 1,440 |
| 3% | 120 | 3.6 | 2,160 |

## Resource Envelope
- Approved Tools: Amazon Associates India, GitHub, Markdown editor
- Hosting: Existing GitHub Pages
- API/Model Quotas: DeepSeek + Bedrock quota remaining
- Spend Ceiling: ₹0 additional spend required
- Renewal Dates: Amazon Associates annual renewal: 2027-06-30
- Human-Only Dependencies: Founder approval before publishing

## Next Steps
1. Submit plan for Founder review and approval
2. After approval: commit changes, publish offer page with internal links
3. Rotate to next least-used pillar (Pillar 2: new affiliate networks)