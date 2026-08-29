# RIO Affiliate Report Inbox

This folder is the evidence inbox for affiliate outcome reports.

Accepted input file: `latest.json`

Required fields:
- `source`: one of `amazon_associates_report`, `earnkaro_report`, `cuelinks_report`, `other_verified_affiliate_report`
- `observed_at_utc`: ISO timestamp
- `clicks`: integer or null
- `orders`: integer or null
- `commission_inr`: number or null
- `settled_revenue_inr`: number or null
- `source_reference`: non-secret report/account reference

Rules:
- Missing values remain UNKNOWN; never coerce to zero.
- RIO must not infer purchase, commission or revenue from clicks/content/activity.
- Raw credentials/tokens are prohibited in this folder.
- Only an evidence-backed report may update `data/affiliate_attribution_state.json`.
