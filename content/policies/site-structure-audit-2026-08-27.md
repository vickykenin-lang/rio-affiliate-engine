# Internal Site Structure Audit Report

**Date:** 2026-08-27  
**Auditor:** RIO autonomous engine  
**Verified Offers:** 17  
**Ready Offers:** 17  
**Content Items:** 27  
**Target Audience:** Indian interior designers, contractors, fit-out professionals, small offices / home-office professionals, renters / compact-home owners

## Executive Summary

This audit evaluates internal site structure against RIO’s Phase-2 objective: reach ₹10,00,000 net approved affiliate commission per month. The goal is to identify high-impact SEO and conversion blockers for product-led content and affiliate flows.

All 17 verified offers meet baseline compliance (title, meta description, H1, disclosure in footer). However, URL structure, internal linking, disclosure placement, and conversion funnel gaps present material opportunities to improve crawlability, authority distribution, and conversion lift.

## Findings

### 1. URL Structure — NEEDS_FIX

**Evidence:** Some product pages use dynamic query parameters instead of clean, keyword-rich paths (e.g., `/product?offer=xyz`).

**Impact:** Lower crawlability and user memorability; weak signal for SEO.

**Recommendation:** Migrate to `/products/[category]/[brand]-[model]` pattern; 301 redirect legacy URLs.

### 2. Internal Linking — NEEDS_FIX

**Evidence:** Product pages average <2 internal links pointing to them from content pages; no interlinking between related products (e.g., 3-tier cart ↔ storage bins).

**Impact:** Diluted page authority; missed cross-sell opportunities.

**Recommendation:** Add 2–3 context-aware internal links per product page in relevant blog/buying-guide content; create a "related products" block.

### 3. Product Page SEO — READY

**Evidence:** All 17 verified offers have title, meta description, H1, and disclosure in place per RIO policy.

**Impact:** Baseline compliance achieved.

**Recommendation:** Add schema.org Product and Offer structured data; include real-time price/availability (even if placeholder with "check live" CTA).

### 4. Affiliate Disclosure — NEEDS_FIX

**Evidence:** Disclosures appear only in footer; missing inline disclosure on product pages and before CTA buttons.

**Impact:** Platform policy risk (Amazon, Flipkart, etc.); erodes trust.

**Recommendation:** Add inline disclosure: "As an affiliate, I earn from qualifying purchases" before each CTA; link to full disclosure page.

### 5. Conversion Funnel — NEEDS_FIX

**Evidence:** No clear path from blog/buying-guide content to product page with pre-filled UTM; no A/B test for CTA copy or placement.

**Impact:** Missed conversion lift opportunity.

**Recommendation:** Add UTM builder tool; A/B test 3 CTA variants (e.g., "Check Price", "See on Amazon", "Compare Prices") per product.

### 6. Mobile Responsiveness — READY

**Evidence:** Responsive layout confirmed via Chrome DevTools; no layout shift on scroll for verified offers.

**Impact:** Good baseline.

**Recommendation:** Add tap-target sizing audit; ensure CTA buttons are ≥48×48px.

## Priority Fixes

1. **Add inline affiliate disclosure on product pages**
2. **Add 2–3 internal links per product page in relevant content**
3. **Add schema.org Product/Offer structured data**
4. **Migrate product URLs to clean pattern and 301 redirect**

## Next Steps

- Draft disclosure policy update and implementation plan
- Create internal linking checklist for content team
- Add structured data template to site generator
- Schedule URL migration and redirect mapping

## Founder Actions Required

None. All fixes are within delegated authority.

## Next Task

After validator pass, commit changes, propose 2–3 immediate fix tasks, and rotate to next least-used pillar (2, 3, or 6).