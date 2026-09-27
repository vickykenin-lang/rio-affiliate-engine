# RIO Affiliate Engine — Version 3.0

India-focused affiliate content and authority engine.

## Locked objective (RIO 3.0)

Build an automated, scalable affiliate business toward **₹10 lakh/month net approved commission**, with a long-term ₹50 lakh+/month goal.

**Primary positioning**:
Help Indian interior designers, contractors, and small offices use AI tools and practical digital products to design faster, present better, and manage projects more efficiently.

**Supporting layer** (already live):
Compact-home storage, kitchen/bathroom/wardrobe/balcony organisers, and baby-proofing/home-safety products for Indian rented homes.

Core discipline remains unchanged: **Discovery → Live-verify → Score → Publish**. Nothing goes live without real verification.

Full definition: `data/RIO_3.0_DEFINITION.md`

## Evidence-backed status

Current repository/runtime truth:

- 27 content items
- 56 product candidates
- 17 Amazon.in offers marked READY with tracking ID `rioaffiliate-21`
- AWS Bedrock Qwen is the required primary AI runtime; active configured fallback is Bedrock GLM
- DeepSeek is not enabled in production workflow execution
- Heartbeat cadence is 15 minutes with production reachability, validators and SOUL hard gate
- Instagram publishing has 12 confirmed posted media records
- Instagram token is live-verified and media/insights telemetry is `LIVE_OR_PARTIAL`
- Website affiliate-click telemetry is live through the Cloudflare `rio-click-telemetry` collector
- Affiliate clicks/orders/commission remain source-evidence governed; missing merchant reports are UNKNOWN, never assumed zero
- Settled affiliate revenue remains ₹0 until a real affiliate-network report proves approved commission

Canonical truth sources:

- `data/status.json` — heartbeat and validator state
- `data/provider_health.json` — live AI provider health
- `data/runtime_health.json` — combined runtime health
- `data/production_status.json` — real HTTP checks
- `data/dashboard_snapshot.json` — pipeline counts
- `data/telemetry_state.json` — Instagram and website telemetry
- `data/affiliate_attribution_state.json` — clicks/orders/commission source-evidence state
- `data/ig_published.json` — confirmed Instagram media IDs only
- `data/instagram_approval.json` — per-offer publishing state
- `data/instagram_run_status.json` — latest real publish outcome or blocker
- `data/RIO_3.0_DEFINITION.md` — Version 3.0 objective and governance definition

## Validate locally

```bash
python3 scripts/validate.py
python3 scripts/validate_offer_integrity.py
python3 scripts/validate_product_candidates.py
python3 scripts/validate_dashboard.py
python3 scripts/validate_production_offer_gate.py
```

## Verify production

```bash
python3 scripts/check_production.py
```

Set `RIO_PUBLIC_SITE_BASE` when a different public deployment URL is selected.

## Runtime and control-plane security

- AWS Bedrock is the production AI path.
- GitHub issue control commands are accepted only from the repository owner/Founder identity.
- Untrusted public issues must not activate kill-switch, resume, or persistent RIO-message commands.
- No raw secrets are committed or logged.
- Production actions remain subject to validators, evidence receipts, post-action verification, legal/compliance controls and cost controls.

## Security and compliance

- Never commit passwords, API keys, tokens, payment data, government IDs or private customer/order data.
- Amazon links must carry the approved tracking ID.
- Customer review text and star ratings must not be published without an approved Amazon Product Advertising/Creators source and applicable licence compliance.
- Revenue remains ₹0 until a real affiliate report proves approved commission.
- No Founder name or professional claim goes public without applicable governance review.
