# Review: dead-link redirects + page publisher

Date: 2026-08-13
Reviewer: Codex (`codex exec --sandbox read-only`), claims then verified live by Claude.
Scope: the 23 new redirect rules, and `scripts/publish_page.py` from PRs #9 and #13.

Codex could not write its own findings file (read-only sandbox), so its verdict is
reproduced here verbatim, with the result of checking each claim.

## Codex verdict: BLOCKING

### HIGH: "16 of 23 new redirect pairs point directly to known 404 routes"

**Not upheld.** All 23 were requested against the live site after deploy and every
one returns HTTP 200 at the end of its chain. Codex had no network access and
reasoned from the repo alone: the `/blog/YYYY/MM/DD/...` destinations have no
matching directory in `www/`, so it inferred a 404. In fact those paths are
already served or redirected by rules that existed before this change.

A repo-only reviewer cannot settle this question. The live check can, and did.

### HIGH: "Stored script injection via JSON-LD, body_html, date, slug, image_url"

**Partly by design, low risk in practice.** `body_html` is inserted raw at
`publish_page.py:116` because it *is* the page body: a publisher that escaped it
would produce pages of visible tags. Other payload fields are escaped through
`htmllib.escape(..., quote=True)` at line 205.

The residual risk is real but bounded: the payload comes from whoever is
publishing (Greg, Chloe, or Claude acting for them), not from the public. This is
worth knowing before the publisher is ever fed input from an untrusted source,
and worth revisiting then.

### MEDIUM: "Nested slugs plus overwrite can replace arbitrary pages; writes are non-atomic"

**Overwrite and traversal are mitigated and tested.** `publish_page.py:57-77`
resolves the path and refuses anything escaping `www/`, and overwriting an
existing page requires explicit opt-in. `scripts/test_publish_page.py` covers
exactly this, and all 13 checks pass:

    traversal slug refused / absolute slug refused / empty slug refused
    traversal template refused / traversal slug wrote nothing
    second publish refused / refused publish left the page alone
    overwrite flag replaces the page / overwrite payload field replaces the page

**Non-atomic writes stand.** Page, sitemap and search index are written
separately, so a crash mid-publish leaves them inconsistent. Impact is low and
the fix is to re-run the publisher, so this is noted rather than actioned.

## Found and fixed outside the Codex review

Four of the 23 redirects pointed at a destination that was itself redirected,
giving visitors three hops. Resolved each to its terminal page (commit `aba49ce`)
and confirmed live: all four now take one redirect and land on 200. Codex
explicitly reported "no chains", so this was missed by the review and caught by a
direct check of the rules against each other.

## Standing note

Two of the three findings here were weakened or overturned by checking the live
site rather than the repo. A static review of a diff cannot tell you what a
production URL returns. Treat "this route 404s" from any repo-only reviewer,
human or model, as a hypothesis to test.
