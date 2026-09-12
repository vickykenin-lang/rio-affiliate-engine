# RIO Step 4 — GitHub-native campaign dashboard

GitHub is the only operational source of truth. The dashboard is a static GitHub Pages projection; it never receives an Amazon, Instagram, GitHub PAT, or custom Founder token.

## Authentication and writes

- Founder authentication is the existing GitHub login.
- State changes run only through the repository's **Campaign founder action** GitHub Actions workflow.
- The workflow allows only repository owner `vickykenin-lang`, requires the current campaign revision, validates the transition server-side, and commits the campaign plus audit projection to GitHub.
- GitHub supplies a unique workflow run ID as the request idempotency key.
- Concurrent actions are serialized and stale revisions fail closed.
- Secrets remain in GitHub Actions secrets and never enter Pages HTML or JavaScript.

## Founder flow

Open `/campaign-dashboard/` on GitHub Pages, inspect the bundle, and choose a legal action. GitHub opens the authenticated workflow page. Enter the campaign ID, action, and revision shown by the dashboard. Correction actions also require category and feedback. The workflow validates, commits, regenerates the projection, and Pages refreshes from GitHub.

No campaign is approved merely by selecting it on the public dashboard. The authenticated workflow run is the approval ceremony and its commit is the durable audit evidence.
