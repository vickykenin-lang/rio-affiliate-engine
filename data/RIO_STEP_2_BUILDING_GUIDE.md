# RIO Step 2 — Governed Creative-to-Publish Building Guide

**Document status:** FOUNDER LOCKED — STEP 2 IMPLEMENTATION CONTRACT  
**Locked by:** Founder Vicky Gautam, explicit instruction on 2026-09-12  
**Prepared:** 2026-09-12  
**Scope:** Candidate selection through Instagram publication  
**Not in this phase:** Instagram SEO/optimization, new product discovery, revenue forecasting

## 1. Product decision

RIO will be a low-intervention affiliate operations dashboard with two mandatory Founder approvals:

1. Founder selects an eligible candidate and grants `APPROVED_FOR_CREATIVE`.
2. RIO creates a compliant creative package and presents it for review.
3. Founder either requests corrections or grants `APPROVED_TO_PUBLISH`.
4. RIO performs fresh deterministic checks and publishes to Instagram.

Automation may prepare, validate, retry, and recommend. It may never grant either Founder approval to itself.

`READY` in the existing product pipeline means **eligible for selection**, not approved for creative generation and not approved for publication.

## 2. Customer path

Instagram feed media is not treated as a clickable destination.

`Instagram post/Reel -> profile link or Story link sticker -> RIO landing page -> exact verified Amazon Special Link`

On the RIO landing page, the approved product image and CTA may link directly to the matching Amazon product page. Every destination must include the configured affiliate tag and pass X-to-X identity validation.

Required disclosure surfaces:

- Instagram: paid-partnership label where Meta requires it, plus a clear affiliate disclosure in the caption.
- RIO landing page: link-level affiliate disclosure and the Amazon Associate account statement.
- No URL cloaking, artificial clicks, false urgency, fabricated price/rating/review, or implied Amazon endorsement.

## 3. One canonical campaign record

Each selected candidate creates one immutable-identity campaign record. Proposed source of truth: `data/campaigns/<campaign_id>.json`.

Required identity fields:

- `campaign_id`, `candidate_id`, `offer_id`, `merchant`, `asin`
- exact `product_title`, `variant`, `canonical_url`, `affiliate_url`
- `candidate_score`, `candidate_status`, `selected_at`
- `offer_verified_at`, `availability`, and evidence references

Required creative fields:

- `creative_version`, `creative_asset_path`, `creative_sha256`
- `caption_version`, `caption_text`, `caption_sha256`
- `landing_page_url`, `landing_page_sha256`
- generation provider/model, request ID, timestamp, attempt number, estimated/actual cost when available
- source policy used: `ORIGINAL_CONTEXTUAL` or `PERMITTED_EXACT_ASSET`
- validation results and correction history

Required approval fields:

- approval state, actor, timestamp, approved version/hash bundle
- rejection category, Founder feedback, correction attempt
- complete append-only event history

Required publish fields:

- precheck timestamp/results, idempotency key, Meta container/media ID, permalink
- publish attempts, error class, next retry time, terminal status

Secrets and access tokens must never appear in campaign records, logs, dashboard HTML, or generated assets.

## 4. Canonical state machine

The candidate pipeline remains separate from the campaign workflow.

### 4.1 Existing candidate eligibility pipeline

`DISCOVERY_REQUIRED -> DISCOVERED -> IDENTITY_REVIEW -> SPEC_REVIEW -> SCORED -> OFFER_MAPPING -> READY`

Existing `QUARANTINED` and `REJECTED` behavior remains. Only `READY` candidates may enter a campaign.

### 4.2 New campaign workflow

`CANDIDATE_REVIEW`

- Founder actions: `APPROVE_FOR_CREATIVE`, `REQUEST_CANDIDATE_CHANGES`, `REJECT_CAMPAIGN`.
- Approval moves to `APPROVED_FOR_CREATIVE`.
- A change request moves to `CANDIDATE_CHANGES_REQUESTED`; RIO corrects/revalidates and returns it to `CANDIDATE_REVIEW`.

`APPROVED_FOR_CREATIVE -> CREATIVE_GENERATING -> CREATIVE_REVIEW`

- Generation failure moves to `CREATIVE_GENERATION_FAILED`, never to approval.
- Founder actions in review: `APPROVE_TO_PUBLISH`, `REQUEST_CREATIVE_CHANGES`, `REJECT_CAMPAIGN`.
- A change request moves to `CREATIVE_CHANGES_REQUESTED`; RIO creates a new version and returns it to `CREATIVE_REVIEW`.

`APPROVED_TO_PUBLISH -> PUBLISH_PRECHECK -> POST_PENDING -> INSTAGRAM_POSTED`

- A precheck failure moves to `PUBLISH_BLOCKED`.
- A retryable Meta/API failure moves to `PUBLISH_RETRY_WAIT` and then back to `PUBLISH_PRECHECK`.
- A non-retryable failure moves to `PUBLISH_FAILED`.
- `INSTAGRAM_POSTED` is terminal for that creative version.

At any non-terminal stage the Founder may use `PAUSE_CAMPAIGN` or `REJECT_CAMPAIGN`. Kill switch overrides every state.

## 5. Approval invariants

### `APPROVED_FOR_CREATIVE`

Approval is bound to this identity bundle:

- candidate ID, offer ID, merchant, ASIN, exact variant, landing page, affiliate destination
- the offer verification snapshot shown to the Founder

Changing any bound field automatically invalidates the approval and returns the campaign to `CANDIDATE_REVIEW`.

### `APPROVED_TO_PUBLISH`

Approval is bound to:

- the exact creative bytes/hash
- the exact caption bytes/hash
- the exact landing-page version/hash
- the identity bundle approved above

Any creative, caption, disclosure, CTA, landing page, offer, ASIN, variant, or destination change invalidates publish approval and returns the campaign to the appropriate review state. Cropping, text correction, and regenerated output count as creative changes.

The current `AUTONOMOUS_POLICY_VALIDATED` setting must not bypass these approvals. `instagram_auto_publish=true` only permits the scheduler to publish a campaign that already has a valid, unexpired `APPROVED_TO_PUBLISH` record.

## 6. Rejection and correction loops

Every change request requires:

- one category: `WRONG_PRODUCT`, `MISLEADING_VISUAL`, `COPY_ISSUE`, `DISCLOSURE_ISSUE`, `DESIGN_ISSUE`, `LINK_ISSUE`, or `OTHER`
- Founder feedback text
- an append-only event containing old version/hash and timestamp
- a new version; approved assets are never overwritten

Limits:

- Maximum 3 automated creative correction attempts per campaign.
- Maximum 2 automatic retries for a transient generation request.
- Maximum 3 Meta publish retries with exponential backoff and jitter.
- Validation, permission, identity, stale-offer, or billing/access failures are not blindly retried.
- At a limit, the campaign becomes `FOUNDER_ACTION_REQUIRED` with the exact blocker.

## 7. Automated creative policy

Because the Founder does not want a manual photography/licensing workflow, the default is `ORIGINAL_CONTEXTUAL`:

- Generate an original category/problem-solution scene; do not create a pixel-level or confusing replica of the Amazon listing image.
- Do not send an Amazon-hosted product image to image-to-image generation unless program terms and machine-readable provenance explicitly permit that transformation.
- Do not add Amazon logos, marketplace badges, seller watermarks, review stars, unverified performance claims, or fake packaging.
- If the scene is illustrative rather than the exact product, the creative/caption must not claim that the depicted object is the exact listed item.
- Product facts in copy must come only from the verified offer record.
- The RIO landing page remains the exact-product truth surface and carries the matching Amazon destination.

`PERMITTED_EXACT_ASSET` is allowed only when the registry records a current permission/licence and permitted transformations. The asset must remain unaltered except for operations the applicable terms expressly allow. Absence of evidence means no image-to-image transformation.

This design reduces manual intervention but does not claim that AI output is automatically copyright-free. Every output still passes automated similarity, trademark, text, disclosure, and claim checks before Founder review.

## 8. Nova Canvas integration contract

Provider ID: `amazon.nova-canvas-v1:0` in `us-east-1` through Amazon Bedrock.

The console test on 2026-09-12 returned `ValidationException: Operation not allowed`; therefore Nova is `BLOCKED_ACCESS` until a successful minimal invocation proves model/IAM/account access. A failed invocation must not be recorded as a generated creative.

Before production generation:

- Run one minimal access probe and store request/result metadata, never credentials.
- Require an explicit configured campaign budget and per-image cost ceiling.
- Enforce `max_images_per_request`, maximum attempts, monthly ceiling, and kill switch.
- Record the actual provider/model; never label a fallback output as Nova.
- A provider fallback may prepare a draft only if enabled in configuration. It cannot bypass the same validations or approvals.
- No paid request runs after the budget is exhausted or while access/cost information is unknown.

The previously approved paid scope is limited to the first three pilot campaigns. It does not authorize open-ended paid generation.

## 9. Automatic candidate sorting

The dashboard default recommendation order is deterministic:

1. Hard-gate `READY` only.
2. Exclude stale/unreachable offers, missing affiliate mapping, prior publication duplicates, and policy-blocked categories.
3. Sort by commercial score descending.
4. Tie-break by fresher live verification, then candidate ID ascending.
5. Display why each candidate ranked where it did; allow Founder selection rather than automatic approval.

With the current snapshot, the first three score-ranked READY candidates are:

1. `CAND_CO_001` — airtight containers — score 95 — ASIN `B0753ZQDR7`
2. `CAND_UB_001` — under-bed storage — score 94 — ASIN `B07B8K3RQK`
3. `CAND_SC_001` — baby socket covers — score 92 — ASIN `B0829RL6Z5`

These are pilot candidates, not current approvals. Each needs fresh offer verification before being shown for `APPROVED_FOR_CREATIVE`.

## 10. Dashboard requirements

The static report becomes an authenticated control surface backed by server-side actions. No state-changing secrets or credentials are exposed to client JavaScript.

Minimum screens:

- **Candidates:** filters, deterministic rank, verification age, score explanation, offer/link status, multi-select (pilot capped at 3).
- **Candidate Review:** exact product identity, evidence, destination preview, disclosure, approve/request changes/reject.
- **Creative Review:** image preview, caption, link journey, validation results, version history, cost, approve/request changes/reject.
- **Publish Queue:** approval freshness, scheduled time, precheck status, retry/blocker, Meta result.
- **Audit:** immutable event timeline with actor, timestamps, hashes, and reasons.

Every state-changing request requires authentication, authorization, CSRF protection, optimistic locking/version check, idempotency key, server-side transition validation, and audit logging.

Buttons are enabled only when the requested transition is legal. The API rejects stale UI versions rather than overwriting newer decisions.

## 11. Publish precheck — all must pass

- kill switch off; campaign not paused/rejected
- valid `APPROVED_FOR_CREATIVE` and `APPROVED_TO_PUBLISH` hashes
- exact candidate/offer/ASIN/variant mapping unchanged
- fresh live destination and availability check within configured TTL
- affiliate tag present; no redirect/cloaking mismatch
- landing page reachable and exact-product mapping valid
- creative and caption files match approved hashes
- required affiliate and branded-content disclosures present
- creative policy validator pass
- Meta credentials/account permissions healthy
- idempotency key not already published
- budget and rate limits pass
- global validators known-passing

Failure blocks publication and reports one precise remediation. It never silently substitutes a product, image, caption, or link.

## 12. Audit, security, and recovery

- Append-only events are the authoritative approval history.
- Dashboard projections may be rebuilt from campaign records/events.
- Credentials remain in the platform secret store and use least privilege.
- Logs redact tokens, signed URLs where necessary, and personal data.
- Every external request records a correlation ID and safe response metadata.
- Generate and publish operations are idempotent.
- A partial failure cannot advance the state.
- Existing published records remain immutable; corrections create a new campaign/version and do not erase history.

## 13. Pilot acceptance criteria

Step 2 is considered implemented only when all of these pass for the three pilot candidates:

1. Ranking selects the three candidates listed in section 9 after fresh validation, or visibly explains any exclusion/reordering.
2. Neither creative generation nor publishing is possible without the matching Founder approval.
3. Candidate rejection/correction returns to review with preserved history.
4. Creative rejection/correction produces a new version and invalidates the old publish approval.
5. Changing ASIN, destination, caption, creative, disclosure, or landing page invalidates the applicable approval.
6. Nova access probe succeeds before paid generation; otherwise the UI shows `BLOCKED_ACCESS` and no false output.
7. Generation respects attempt and cost ceilings.
8. All compliance and X-to-X validators pass.
9. A dry-run publish proves the exact approved asset/caption/link bundle without calling Meta.
10. One explicitly approved live test produces a single Instagram media ID and cannot duplicate on rerun.
11. Dashboard, campaign record, Meta result, and audit event agree on final status.
12. Existing tests continue to pass and new transition/approval/idempotency tests are added.

## 14. Implementation order after Founder lock

1. Add campaign schema, event schema, transition engine, and approval invalidation rules.
2. Add unit tests and migration from current Instagram approval data without changing historical posted records.
3. Add authenticated dashboard API and interactive review screens.
4. Add creative provider interface, validators, cost ledger, and Nova access probe.
5. Add governed generation worker and correction loop.
6. Refactor Instagram publisher to require valid hash-bound publish approval and idempotency.
7. Run the three-candidate dry-run pilot, then one separately approved live publish test.

## 15. Explicit changes to existing behavior

- Replace the current simple `APPROVED` publish meaning with the two-stage campaign approval model.
- Remove autonomous approval bypass from `scripts/publish_instagram.py`.
- Treat `instagram_auto_publish` as scheduling permission only.
- Replace mutable single approval status as the source of truth with campaign records plus append-only events.
- Replace HTML-only dashboard controls with authenticated server actions.
- Replace exact Amazon image use in Instagram publishing with the creative policy in section 7; preserve exact unmodified product use on RIO surfaces only when permitted and validated.
- Keep historical `INSTAGRAM_POSTED` records intact during migration.

## Founder lock statement

When the Founder approves this document, it becomes the Step 2 implementation contract. Code, dashboard behavior, workers, and validators must conform to it. Any later change to approval authority, product-image policy, destination path, or paid-spend boundary requires a versioned Founder-approved amendment.
