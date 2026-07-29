#!/usr/bin/env python3
"""Generate robots.txt and XML sitemaps for the static build.

WordPress served these dynamically via Rank Math, so a static build has to
produce its own. The sub-sitemap filenames deliberately mirror the live ones
(page-sitemap.xml, post-sitemap.xml and so on) because Google already has
those URLs registered; changing them would surface avoidable errors in
Search Console.

Only URLs that actually exist in the build are included, and only content
that was published (no drafts, no noindex pages).
"""
import json
import os
import xml.sax.saxutils as sx

OUT = "www"
DOMAIN = "https://develop-coaching.com"

# live sitemap name  ->  exported post type
GROUPS = {
    "page-sitemap.xml": "pages",
    "post-sitemap.xml": "posts",
    "courses-sitemap.xml": "courses",
    "podcast-sitemap.xml": "podcast",
    "podcast-transcript-sitemap.xml": "podcast-transcript",
}

# ---- which paths genuinely exist in the build? ----
built = set()
for root, dirs, files in os.walk(OUT):
    rel = os.path.relpath(root, OUT)
    if rel.split(os.sep)[0] in ("wp-content", "wp-includes"):
        dirs[:] = []
        continue
    if "index.html" in files:
        p = "/" + os.path.relpath(root, OUT).replace(os.sep, "/")
        built.add("/" if p == "/." else p.rstrip("/") + "/")

# pages that are deliberately kept out of search
NOINDEX_HINTS = ("/test", "-test/", "/sample-page/")


def entries_for(post_type):
    path = f"export/content/{post_type}.json"
    if not os.path.exists(path):
        return []
    out = []
    for item in json.load(open(path)):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "publish":
            continue
        link = item.get("link") or ""
        if not link.startswith(DOMAIN):
            continue
        rel = link[len(DOMAIN):] or "/"
        if not rel.endswith("/"):
            rel += "/"
        if rel not in built:
            continue
        if any(h in rel for h in NOINDEX_HINTS):
            continue
        lastmod = (item.get("modified_gmt") or item.get("modified") or "")[:10]
        out.append((DOMAIN + rel, lastmod))
    return sorted(set(out))


def write_urlset(filename, entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{sx.escape(loc)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    open(os.path.join(OUT, filename), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return len(entries)


total = 0
written = []
for filename, post_type in GROUPS.items():
    entries = entries_for(post_type)
    if not entries:
        continue
    n = write_urlset(filename, entries)
    written.append(filename)
    total += n
    print(f"{filename:34} {n:4} urls")

# ---- sitemap index ----
idx = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for filename in written:
    idx.append("  <sitemap>")
    idx.append(f"    <loc>{DOMAIN}/{filename}</loc>")
    idx.append("  </sitemap>")
idx.append("</sitemapindex>")
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
print(f"{'sitemap.xml':34} index of {len(written)} sitemaps, {total} urls total")

# ---- robots.txt ----
# Mirrors the live file (which only carries a SearchAtlas allowance and no
# Disallow rules), plus the Sitemap directive the live file was missing.
robots = f"""# Allow access to SearchAtlas Bot
User-agent: SearchAtlas Bot
Allow: /

User-agent: *
Allow: /
Disallow: /wp-admin/
Disallow: /wp-includes/

Sitemap: {DOMAIN}/sitemap.xml
"""
open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(robots)
print("robots.txt                         written")
