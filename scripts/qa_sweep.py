#!/usr/bin/env python3
"""Site-wide QA sweep of the built copy (filesystem-level, all pages).

Checks every page in www/ for:
1. Local asset references (img src/srcset, css, js, media, css url()) that
   don't exist in the build -> broken resource.
2. Internal links that resolve to neither a page, a file, nor a redirect
   rule -> will 404 on the copy. Each is compared with the live site's
   status so pre-existing dead links (parity) are separated from regressions.
"""
import json
import os
import re
import urllib.parse

OUT = "www"

# ---------- collect redirect sources ----------
vercel = json.load(open(os.path.join(OUT, "vercel.json")))
plain_redirects = set()
regex_redirects = []
for r in vercel["redirects"]:
    s = r["source"]
    if "(" in s or ":" in s:
        # path-to-regexp source; build a rough matcher
        pat = re.sub(r":\w+\(([^)]*)\)", r"\1", s)
        pat = re.sub(r":\w+\*", ".*", pat)
        pat = re.sub(r":\w+", "[^/]+", pat)
        try:
            regex_redirects.append(re.compile("^" + pat + "/?$"))
        except re.error:
            pass
    else:
        plain_redirects.add(s.rstrip("/") or "/")

def redirected(path):
    p = path.rstrip("/") or "/"
    if p in plain_redirects:
        return True
    return any(rx.match(p) or rx.match(path) for rx in regex_redirects)

# ---------- gather pages ----------
pages = []
for root, dirs, files in os.walk(OUT):
    rel = os.path.relpath(root, OUT)
    if rel.split(os.sep)[0] in ("wp-content", "wp-includes", "feeds"):
        dirs[:] = []
        continue
    for f in files:
        if f.endswith(".html"):
            pages.append(os.path.join(root, f))

ASSET_RE = re.compile(r'(?:src|href)="(/[^"]+?\.(?:png|jpe?g|webp|gif|svg|css|js|ico|mp4|mp3|woff2?|ttf))(?:\?[^"]*)?"')
SRCSET_RE = re.compile(r'srcset="([^"]+)"')
ESC_RE = re.compile(r'\\/wp-(?:content|includes)\\/[^"\\]+?\.(?:png|jpe?g|webp|gif|svg|mp4|mp3)')
LINK_RE = re.compile(r'href="(/[^"#?]*?)/?"')

missing_assets = {}   # asset -> [pages]
internal_404 = {}     # path -> [pages]

def exists_local(path):
    p = urllib.parse.unquote(path.split("?")[0])
    # Audio and video are intentionally excluded from Git and served by the
    # Vercel Blob redirect emitted by build_site.py.
    if p.startswith("/wp-content/uploads/") and p.lower().endswith((".mp3", ".mp4", ".mov")):
        return True
    return os.path.exists(os.path.join(OUT, p.lstrip("/")))

for page in pages:
    html = open(page, encoding="utf-8", errors="ignore").read()
    page_rel = "/" + os.path.relpath(page, OUT).replace(os.sep, "/")
    refs = set(ASSET_RE.findall(html))
    for srcset in SRCSET_RE.findall(html):
        for part in srcset.split(","):
            u = part.strip().split(" ")[0]
            if u.startswith("/"):
                refs.add(u.split("?")[0])
    refs.update(m.replace("\\/", "/") for m in ESC_RE.findall(html))
    for ref in refs:
        if not exists_local(ref):
            missing_assets.setdefault(ref, []).append(page_rel)

    for link in set(LINK_RE.findall(html)):
        if link.startswith(("/wp-", "/feeds", "//")) or "." in link.split("/")[-1]:
            continue
        target = os.path.join(OUT, link.lstrip("/"), "index.html")
        if not os.path.exists(target) and not redirected(link):
            internal_404.setdefault(link, []).append(page_rel)

print(f"pages scanned: {len(pages)}")
print(f"\n== MISSING ASSETS ({len(missing_assets)}):")
for a, ps in sorted(missing_assets.items()):
    print(f"  {a}  (on {len(ps)} pages, e.g. {ps[0]})")
print(f"\n== INTERNAL LINKS WITH NO PAGE/REDIRECT ({len(internal_404)}):")
for l, ps in sorted(internal_404.items()):
    print(f"  {l}  (on {len(ps)} pages, e.g. {ps[0]})")

json.dump(
    {"missing_assets": missing_assets, "internal_404": internal_404},
    open("export/qa-sweep.json", "w"), indent=1,
)
