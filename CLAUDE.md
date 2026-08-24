# develop-coaching.com

The live Develop Coaching website. Read this before changing anything.

## What this site is

A **frozen static copy** of the old WordPress site, hosted on Vercel. There is no
CMS, no database and no template engine. Every page is a finished HTML file in
`www/`. What you see in the repo is exactly what visitors get.

WordPress still exists at `wp.develop-coaching.com`, but it is an archive. It is
set to noindex and **nothing published there reaches the live site**. Never point
anyone at it as a way to change the website.

## The one thing that matters most

**Pushing to `main` publishes to the live site within about a minute.** There is no
staging gate. Treat every push as going straight in front of customers.

Work on a branch and open a pull request unless you have been told otherwise:

    git checkout -b content/<short-name>
    # make the change
    git add <specific files>
    git commit -m "..."
    git push -u origin content/<short-name>
    gh pr create --fill

Never `git add -A`. Other people and other agent sessions work in this repo, and
you will sweep up their unfinished work.

## Publishing a new page

Use the publisher. Do not hand-write a page from scratch: pages carry SEO tags,
JSON-LD, tracking and navigation that must match the rest of the site.

    echo '{
      "title": "How to price commercial work",
      "slug": "how-to-price-commercial-work",
      "body_html": "<p>...</p>",
      "meta_description": "...",
      "category": "Convert"
    }' | python3 scripts/publish_page.py

It writes `www/<slug>/index.html` and updates the sitemap and search index. It
refuses to replace an existing page unless you pass `--overwrite`, which is
deliberate.

## Editing an existing page

Edit the HTML in `www/<slug>/index.html` directly. Change only the words you mean
to change. The surrounding markup is Elementor output: it looks alarming, but
leave it alone and the page keeps working.

## Never run the full rebuild

`scripts/build_site.py` regenerates the whole site from snapshots captured in July
2026. Several live pages were restored by hand afterwards and do not exist in
those snapshots, including `/software/` and its four product pages,
`/5-profit-leaks-workshop/` and `/5-profit-leaks-workshop-thank-you/`. A full
rebuild would delete them. If you genuinely need it, check with Greg first.

## Redirects

Two files, and they must stay in step:

- `export/manual-redirects.json` is the source of truth for future builds
- `www/vercel.json` is what is actually deployed

Add to **both**, and add both the bare path and the trailing-slash version:

    {"source": "/old-page", "destination": "/new-page/", "permanent": true}
    {"source": "/old-page/", "destination": "/new-page/", "permanent": true}

The site runs `trailingSlash: true`, so `/foo` redirects to `/foo/`. A `.html`
URL does **not** redirect to its folder automatically; it needs its own rule.

## Images and video

Images live in `www/wp-content/uploads/`. Anything over about 50MB will not fit in
git and belongs in Vercel Blob instead, served through the redirect rule already
in `vercel.json`. Ask before adding large media.

## Always verify on the live site

A green deploy is not proof. After pushing, check the real URL:

    curl -sI https://develop-coaching.com/<slug>/     # expect 200
    curl -sIL https://develop-coaching.com/<old-url>  # redirects end in 200

Then look at the page in a browser. Several faults this month passed every
automated check and were only visible to a human eye.

## Things that have bitten people here

- Pages that exist only as hand-placed files, invisible to sitemaps and crawls.
  Three were found in three days, each because a person noticed something broken.
- Verifying your own work against your own list. If you built the list, it is not
  a check. Compare against an independent source.
- Claiming something is fixed before the deploy has finished. Wait for the change
  to appear on the live URL, then verify.
