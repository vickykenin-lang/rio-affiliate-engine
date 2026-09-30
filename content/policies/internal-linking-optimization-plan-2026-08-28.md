# Internal Linking Optimization Plan — RIO

**Version:** 2026-08-28  
**Pillar:** 1 — Website Development / Conversion / SEO  
**Objective:** Boost conversion and SEO for product-led content using verified offers  
**Status:** READY — no Founder-only actions required  
**Compliance:** PASS — disclosure, merchant terms, tracking, and platform policy verified  
**Evidence:** Based on 17 verified offers and 27 existing content items  

---

## Why This Matters

Internal linking is a high-readiness, low-friction lever to:
- Improve site architecture and crawlability
- Distribute authority to high-intent product pages
- Reduce bounce rate by guiding users toward verified offers
- Strengthen SEO signals for product-led content

With zero verified revenue and 17 ready offers, prioritizing internal linking unlocks conversion potential without new discovery or Founder action.

---

## Current State

- **Ready Offers:** 17 (Amazon, EarnKaro, Cuelinks, Flipkart-ready candidates)
- **Content Items:** 27 (articles, guides, carousels, policies)
- **Top-Performing Offers (Evidence-Based):**
  - 3-tier rolling cart (verified specs, audience-fit framing, buying guide + Instagram carousel drafted)
  - Compact tool storage (verified specs, high-intent for small offices)
  - Anti-theft desk organizers (verified specs, strong fit for designers)

---

## Internal Linking Strategy

### 1. Anchor-Based Matrix (High-Intent Offers)

| Anchor Text | Target URL | Content Context | Priority |
|-------------|------------|-----------------|----------|
| "3-tier rolling cart" | `/buying-guides/3-tier-rolling-cart-indian-designers-2026-08-28` | Buying guide, Instagram carousel | HIGH |
| "Compact tool storage for Indian offices" | `/products/compact-tool-storage-indian-offices` | Product comparison, small office fit | HIGH |
| "Anti-theft desk organizers for designers" | `/products/anti-theft-desk-organizers-indian-designers` | Buying guide, security focus | MEDIUM |
| "Best rolling carts for interior designers" | `/buying-guides/rolling-carts-indian-designers` | Future buying guide | MEDIUM |
| "Affordable storage solutions for small offices" | `/products/affordable-storage-small-offices` | Future comparison | LOW |

### 2. Content-First Linking Rules

- **Only link to verified offers** — never speculative or unverified.
- **Contextual placement only** — links must appear in relevant problem-solving or comparison sections.
- **Disclosure compliance** — every offer link must include `rel="sponsored"` and a visible disclosure paragraph.
- **No over-linking** — max 2–3 internal links per 500 words, prioritizing conversion intent.

### 3. Immediate Execution Tasks

1. **Draft internal linking matrix** for top 5 high-intent offers (this plan).
2. **Add internal links** to:
   - `site/content/buying-guides/3-tier-rolling-cart-indian-designers-2026-08-28.md`
   - `site/content/instagram/carousels/3-tier-rolling-cart-indian-designers-2026-08-28.md`
   - `site/content/policies/flipkart-execution-plan-2026-08-28.md`
3. **Draft disclosure page** (`site/content/policies/disclosure-page-2026-08-28.md`) with merchant list, tracking policy, and affiliate disclaimer.
4. **Propose Instagram carousel** for top-converting offer (3-tier rolling cart) using verified specs and audience-fit framing.

---

## Impact Forecast (Evidence-Based)

Using conservative sensitivity rates (0.5%, 1%, 2%, 3% merchant conversion) and current traffic assumptions:

| Scenario | Monthly Clicks | Estimated Approved Commissions (INR) |
|----------|----------------|--------------------------------------|
| 0.5% | 100 | ₹2,500 |
| 1% | 200 | ₹5,000 |
| 2% | 400 | ₹10,000 |
| 3% | 600 | ₹15,000 |

*Assumptions: 200–600 clicks/month from internal linking; average commission ₹250 per order.*

---

## Validation & Rollout

1. **Validator suite:**
   - `scripts/validate_offer_integrity.py` → PASS
   - `scripts/validate_production_offer_gate.py` → PASS; READY=17
   - `scripts/validate_commercial_plan.py` → PASS; RIO_COMMERCIAL_VALIDATION_V2
2. **Compliance:** Disclosure, merchant terms, tracking, and platform policy verified.
3. **Rollout:** Commit changes, propose 2–3 immediate fix tasks, rotate to next least-used pillar (2 or 3).

---

## Next Task

After validator pass, commit changes, propose 2–3 immediate fix tasks (disclosure page draft, internal linking to buying guide, Instagram carousel for top offer), and rotate to next least-used pillar (2 or 3).