# Codex review: migration fixes, 2026-08-10

Independent read-only review of the hand-written code changes made during the
cutover session. Codex ran with `--sandbox read-only`, so it could not write
this file itself; findings transcribed verbatim.

## Findings

- **Medium, `www/vercel.json:5-8`**: The workshop redirect exists only in
  generated `www/vercel.json`. The next build regenerates this file and removes
  the rule. Add it to `export/manual-redirects.json`.

- **Medium, `scripts/build_site.py:76-80`**: `\bsrc` also matches `data-src`.
  A valid script with the dead URL in `data-src` can be deleted entirely.
  Require a true `src` attribute boundary.

- **Low, `scripts/build_site.py:304-313`**: Protocol-relative lightbox URLs
  such as `\/\/cdn.example.com\/video.mp4` are incorrectly prefixed with the
  Develop Coaching domain, corrupting the URL.

- **Low, `scripts/build_site.py:304-313`**: URLs containing `&amp;` query
  separators are skipped by `[^&]*?`, leaving them relative and still rejected
  by Elementor.

## Clean

No redirect loops, shadowing, duplicate sources, or catastrophic backtracking
were found. All 77 current lightbox attributes remained valid, and all 366
targeted ActiveCampaign embeds were removed.

## Disposition

All four fixed. See the follow-up commit.

The first finding is the most valuable: it is the same failure mode that lost
the `/trades/` redirect earlier in this migration. `www/vercel.json` is a build
artefact, so any rule added directly to it survives only until the next build.
