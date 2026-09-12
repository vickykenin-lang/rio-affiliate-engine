# RIO Step 4 — Authenticated Campaign Dashboard

This increment replaces display-only approval controls with a server-side campaign review API and an interactive Founder control surface.

## Security contract

- `RIO_FOUNDER_ACCESS_TOKEN`, `RIO_SESSION_SECRET`, and `RIO_CSRF_SECRET` are deployment secrets and must never be placed in HTML, JavaScript, Git, logs, or campaign records.
- Login creates an eight-hour, signed `HttpOnly; Secure; SameSite=Strict` Founder session.
- Every state-changing request requires the session, a derived CSRF token, an optimistic `expected_revision`, and a unique `idempotency_key`.
- The API delegates every action to `scripts/campaign_state.py`; the browser cannot manufacture an approval or bypass a transition.
- Duplicate action requests replay safely. Reusing an idempotency key for a different action returns a conflict.
- Candidate ranking is deterministic. Offers older than `RIO_OFFER_FRESHNESS_DAYS` remain visible but cannot be treated as eligible.

## Local verification

Set the three secrets to values of at least 32 characters, then run:

```text
python scripts/campaign_dashboard_api.py
```

The production deployment must terminate TLS and provide persistent, single-writer access to the repository campaign store. GitHub Pages remains display-only and must not receive any state-changing credential.

## Deployment boundary

This commit implements and tests the API/UI contract. Provisioning the authenticated runtime, secret injection, TLS hostname, and durable repository write adapter is a separate deployment operation because it changes cloud infrastructure and requires Founder-controlled credentials.
