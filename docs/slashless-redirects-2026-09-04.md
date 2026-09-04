# Slashless About redirects

Scope: only `/my-story` and `/case-study`, including query preservation.
Keep the global `trailingSlash: true` behaviour and every existing rule.

## Evidence and cause

At 2026-09-04 03:42:39 UTC, production commit
`8eecc6b98cf7fb25724e7d25cdb032a6db22347c` returned:

- `/my-story` -> 308 `/my-story/` -> 308 `/about-greg-wilkes/` -> 200.
- `/case-study` -> 308 `/case-study/` -> 308 `/about-greg-wilkes/` -> 200.
- Query parameters were preserved by the old two-hop behaviour.

Vercel's `getTransformedRoutes` applies trailing-slash rules before redirects:
https://github.com/vercel/vercel/blob/main/packages/routing-utils/src/index.ts
The locally installed CLI 50.1.6 confirms the same order.
Reordering the existing redirect array cannot fix this.

## Correction

The deployment-scoped `www/priority-redirects.json` contains exactly two rules.
Bulk redirects run before deployment routes, including slash normalisation:
https://vercel.com/docs/routing/redirects/bulk-redirects
The current field names and query/case defaults are documented at:
https://vercel.com/docs/project-configuration/vercel-json#bulkredirectspath
Use explicit case-sensitive matching and preserve query parameters.
The Develop Coaching team is verified Pro. No plan/capacity change is authorised.

Existing destinations in `export/manual-redirects.json` and `www/vercel.json`
remain unchanged and are checked against the priority entries by tests.
If a future full rebuild is explicitly authorised, preserve the priority file
and `bulkRedirectsPath` configuration. Do not run the frozen-site rebuild here.

## Verification and release

`python3 scripts/check_about_redirects.py` is an actual HTTP regression.
Before the fix it failed four slashless cases, while all slash cases passed.
The new config test also failed before adding the priority configuration.
Run the full Python suite, inspect the diff, and require an independent review.
Use the Git PR preview as the canary before production publication.
Bulk redirects are not supported by `vercel dev`, so local tests are not proof.
After publication run the HTTP regression, plus unchanged-path smoke checks.
Ahrefs reporting is separate and must await its next crawl.

Rollback: revert only this change, restoring the old two-hop behaviour.
Pre-change backup: `/tmp/dc-before-slashless.bundle` (origin/main).
No runtime dashboard redirects, permissions, or site content are changed.
