# Affiliate Network Expansion Plan — EarnKaro & Flipkart

**Policy ID:** RIO_COMMERCIAL_VALIDATION_V2  
**Date:** 2026-08-29  
**Status:** READY_FOR_FOUNDER_REVIEW  
**Lead Offer:** 3-tier rolling cart (Amazon Associates India, verified)

## Why
- Pillar 2 (new affiliate networks and product opportunities) has 0 *new* completed tasks since last rotation.
- With ₹0 revenue and 17 ready offers, preparing platform expansion is the highest-leverage safe task to increase merchant diversity, reduce concentration risk, and expand commission potential before publishing.
- EarnKaro and Flipkart are high-priority for Indian professionals: EarnKaro offers higher-ticket AI/SaaS/design tools; Flipkart offers strong home & living inventory with local fulfillment.

## Current State
- Amazon Associates India (`rioaffiliate-21`) is live and verified.
- EarnKaro and Flipkart require Founder-only account setup, approval, and tax/payment onboarding.
- No integration, data models, or validation logic exist yet for EarnKaro or Flipkart.

## Compliance & Tracking
- All offers must pass X-to-X integrity gate before promotion.
- Disclosure visibility, geography, factual claims, privacy, tracking, and platform policy must pass before integration.
- EarnKaro and Flipkart must be evaluated against RIO’s commercial validation policy: compliance is a hard pass/fail gate.

## Platform Evaluation Criteria
1. **Audience fit** — Indian interior designers, contractors, fit-out professionals, small offices/home-office professionals.
2. **Economics** — commission rate, average order value, payment terms.
3. **Trust** — merchant reputation, product quality, return policy.
4. **Execution feasibility** — API access, data model compatibility, validation logic.

## EarnKaro
- **Focus:** AI/SaaS/design tools, higher-ticket offers.
- **Audience fit:** High — Indian professionals seeking productivity tools.
- **Commission:** Up to 30% on SaaS; variable on physical goods.
- **Blockers:** Founder-only account setup, KYC, tax onboarding.
- **Next step after approval:** Prepare integration specs, data models, and validation logic.

## Flipkart
- **Focus:** Home & living, storage, organization, furniture.
- **Audience fit:** High — Indian renters, compact-home owners, interior designers.
- **Commission:** Up to 10% on home & living; varies by category.
- **Blockers:** Founder-only Flipkart Business account, approval, tax onboarding.
- **Next step after approval:** Prepare integration specs, data models, and validation logic.

## Sensitivity Forecast (3-tier rolling cart baseline)
- **0.5% conversion:** ₹6,250/month approved commission @ 12.5 orders
- **1% conversion:** ₹12,500/month approved commission @ 25 orders
- **2% conversion:** ₹25,000/month approved commission @ 50 orders
- **3% conversion:** ₹37,500/month approved commission @ 75 orders

## Resource Envelope
- **Approved tools:** Amazon Associates India, EarnKaro (pending), Cuelinks (pending), Flipkart (pending)
- **Hosting:** existing
- **API/model quotas:** bedrock-qwen + fallbacks
- **Spend ceiling:** ₹0 autonomous spend
- **Renewal dates:** Amazon Associates: annual
- **Human-only dependencies:** EarnKaro account setup, Flipkart Business account approval, payment/tax onboarding

## Next Steps
1. Submit plan for Founder review and approval.
2. After approval: prepare integration specs, data models, and validation logic for Flipkart and EarnKaro.
3. Rotate to Pillar 3 (AdSense readiness) for parallel progress.

## Compliance Gates
- disclosure, merchant_terms, geography, factual_claims, privacy, tracking, platform_policy

## Failure Resilience
- queue_limits, retry_backoff, failure_logging, alerts

## Failed Pilot Limit
- 2 consecutive failed niche pilots before mandatory Dr. Victor strategy review
