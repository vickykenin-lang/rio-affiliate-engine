# Cuelinks Integration Readiness Plan — 3-tier Rolling Cart

**Policy ID:** `RIO_COMMERCIAL_VALIDATION_V2`  
**Status:** READY_FOR_FOUNDERS_REVIEW  
**Date:** 2026-08-29  
**Offer:** 3-tier rolling cart (Amazon Associates India)  
**Pillar:** 2 — New affiliate networks and product opportunities  
**Lead AI:** bedrock-qwen  

## Why
- Cuelinks is a high-potential Indian-focused affiliate network with strong B2B and home-decor verticals.
- With ₹0 verified revenue and 17 ready offers, expanding to a second network reduces merchant concentration risk and increases conversion-path options.
- This plan prepares for safe, compliant Cuelinks integration *before* publishing, per the Commercial Validation Policy.

## Current State
- Offer verified and live on Amazon Associates India (`rioaffiliate-21`).
- Existing high-intent assets:
  - Product-led blog post (`site/content/blog/3-tier-rolling-cart-for-interior-designers-small-offices-2026-08-29.md`)
  - Instagram carousel content plan (`site/content/policies/instagram-content-plan-3-tier-rolling-cart-2026-08-29.md`)
  - Internal linking optimization plan (`site/content/policies/internal-linking-optimization-3-tier-rolling-cart-2026-08-29-v5.md`)

## Proposed Flow
1. Founder creates Cuelinks account and completes KYC/payment setup.
2. RIO integrates Cuelinks tracking pixel and disclosure logic.
3. RIO publishes Cuelinks version of offer page with:
   - Clear disclosure: "As an Amazon Associates and Cuelinks partner, RIO may earn commission at no extra cost to you."
   - Same verified specs, measurements, and use cases.
   - CTA pointing to Cuelinks destination.
4. Submit for indexing; monitor first 30-day funnel evidence.

## Compliance & Tracking
- **Disclosure:** Hard-coded, non-removable per RIO policy.
- **Geography:** India-only targeting; Cuelinks supports INR and Indian merchants.
- **Factual claims:** All specs pulled from verified Amazon product pages (no AI inference).
- **Privacy:** No tracking before consent; GDPR/DPDP-compliant.
- **Tracking:** Cuelinks sub-ID integration for click→order attribution.
- **Platform policy:** Cuelinks TOS reviewed; no prohibited content.

## Sensitivity Forecast (30-day window)
| Conversion Rate | Monthly Orders | Monthly Approved Commission (INR) |
|----------------|----------------|-----------------------------------|
| 0.5%           | 12             | 960                               |
| 1%             | 24             | 1,920                             |
| 2%             | 48             | 3,840                             |
| 3%             | 72             | 5,760                             |

*Assumes same traffic and intent as Amazon version; conservative baseline.*

## Resource Envelope
- **Approved tools:** Amazon Associates India, Cuelinks (pending Founder setup), DeepSeek, AWS Bedrock.
- **Hosting:** GitHub Pages.
- **API/model quotas:** DeepSeek 50k RPM, Bedrock 10k RPM.
- **Spend ceiling (INR):** 0 (no paid acquisition yet).
- **Renewal dates:** Amazon Associates: annual; Cuelinks: quarterly.
- **Human-only dependencies:** Founder account creation, KYC, legal acceptance.

## Next Steps
1. Submit for Founder review and approval.
2. After approval: create Cuelinks account, complete KYC, integrate tracking.
3. Add 3-tier rolling cart offer to Cuelinks dashboard.
4. Update internal linking and content to include Cuelinks version with disclosure.
5. Submit for indexing and monitor first 30-day funnel evidence.

---
*This plan complies with RIO 3.0 Phase-2 objective and Commercial Validation Policy v2. No revenue is claimed until real approved commissions exist.*
