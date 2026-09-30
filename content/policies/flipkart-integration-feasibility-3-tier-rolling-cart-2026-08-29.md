# Flipkart Integration Feasibility Plan — 3-Tier Rolling Cart

**Policy ID:** RIO_COMMERCIAL_VALIDATION_V2  
**Date:** 2026-08-29  
**Status:** READY_FOR_FOUNDER_REVIEW  
**Lead Offer:** 3-tier rolling cart (Amazon Associates India verified)  
**Audience Fit:** Indian interior designers, small offices, compact-home owners  

## Why Flipkart?

Flipkart’s Affiliate Sales (AFS) program offers high-intent Indian commerce inventory, especially in home & living, storage, and office furniture — directly aligned with RIO’s Phase-1 audience priority. While Amazon remains the primary verified layer, adding Flipkart diversifies merchant exposure and increases conversion surface area without new product development.

This plan evaluates feasibility for the 3-tier rolling cart offer and prepares for safe, compliant integration under RIO’s commercial validation policy.

## Current State

- **Ready offers (Amazon):** 17  
- **Content items:** 27 (including buying guide, product-led blog, Instagram carousel, internal linking plan)  
- **Verified offer specs:** 3-tier rolling cart (Amazon ASIN verified, disclosure in place, tracking configured)  
- **Compliance status:** Amazon Associates compliant; Flipkart AFS pending account/approval  

## Flipkart AFS Requirements (High-Level)

| Requirement | Status | Owner |
|-------------|--------|-------|
| Flipkart AFS account creation | NOT STARTED | Founder-only |
| Business identity & GST verification | NOT STARTED | Founder-only |
| Payment & KYC setup | NOT STARTED | Founder-only |
| Legal acceptance of Flipkart AFS terms | NOT STARTED | Founder-only |
| Tracking pixel integration | READY TO IMPLEMENT after account approval | RIO |
| Disclosure & FTC-compliant labeling | READY TO IMPLEMENT | RIO |

## Audience Fit & Offer Mapping

The 3-tier rolling cart targets Indian interior designers and small offices — a segment with high Flipkart penetration for home/office furniture and storage. Flipkart’s home & kitchen category includes comparable rolling carts (e.g., metal, plastic, multi-tier) at competitive price points.

**Feasibility signal:** If Flipkart AFS approval is granted, RIO will:
1. Map verified Amazon 3-tier cart specs to Flipkart product URLs (manual verification required).
2. Re-run X-to-X integrity gate for Flipkart offer.
3. Add Flipkart tracking sub-ID and disclosure to existing content assets.

## Compliance & Tracking

- **Disclosures:** Flipkart AFS must include clear affiliate disclosure per Flipkart policy and Indian consumer law.
- **Geography:** India-only targeting (consistent with current assets).
- **Factual claims:** All product specs must be verified live before publication.
- **Tracking:** Use Flipkart sub-ID + UTM parameters to isolate RIO traffic.

## Sensitivity Forecast (Conservative)

Using existing content inventory and 3-tier cart offer:

| Conversion Rate | Monthly Orders (est.) | Approved Commission (est.) |
|-----------------|------------------------|----------------------------|
| 0.5%            | 2–3                    | ₹0–₹5,000                  |
| 1%              | 4–6                    | ₹5,000–₹15,000             |
| 2%              | 8–12                   | ₹15,000–₹30,000            |
| 3%              | 12–18                  | ₹30,000–₹50,000+           |

*Note: Forecast assumes Flipkart AFS approval and same conversion funnel as Amazon. First settlement required before scaling.*

## Resource Envelope

- **Approved tools:** Flipkart AFS sandbox, existing AWS S3/CloudFront hosting, DeepSeek primary + fallback Bedrock.
- **Spend ceiling:** ₹0 (no paid acquisition yet).
- **Renewal dates:** Flipkart AFS account approval (Founder-only).
- **Human-only dependencies:** Account creation/approval, payment/tax KYC, legal acceptance.

## Next Steps

1. Submit this plan for Founder review and approval.
2. Await Flipkart AFS account setup/approval.
3. After approval: draft integration spec, test tracking, prepare content mapping.
4. Rotate to Pillar 1 (website development/conversion/SEO) to implement Flipkart tracking and disclosure in existing assets.

---

*This plan complies with RIO’s commercial validation policy: execution readiness validated, compliance gate pending Founder-only action, sensitivity forecast includes 0.5%/1%/2%/3% rates, and resource envelope documented.*