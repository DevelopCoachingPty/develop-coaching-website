#!/usr/bin/env python3
"""Build the deployable static site in www/ from the reference snapshots.

- export/reference/<a__b>.html  ->  www/a/b/index.html
- Rewrites absolute develop-coaching.com URLs to root-relative so the site
  works on any preview domain, EXCEPT canonical links, og:/twitter: meta and
  JSON-LD structured data (those should keep the real domain for SEO).
- Emits vercel.json with the legacy redirects recorded from the live site.
"""
import json
import os
import re
import shutil

REF = "export/reference"
OUT = "www"
DOMAIN = "https://develop-coaching.com"

# Regions of the HTML where absolute self-URLs must be preserved
PRESERVE_PATTERNS = [
    re.compile(r'<link[^>]+rel="canonical"[^>]*>'),
    re.compile(r'<link[^>]+rel="(?:next|prev|alternate)"[^>]*>'),
    re.compile(r'<meta[^>]+(?:property="og:|name="twitter:)[^>]*>'),
    re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>', re.S),
]


WPMETEOR_BOOTSTRAP_RE = re.compile(
    r'<script[^>]*(?:>var _wpmeteor=|data-wpmeteor-nooptimize[^>]*>).*?</script>', re.S
)
PHAST_INLINE_RE = re.compile(
    r'<script[^>]*data-phast-params[^>]*>.*?</script>', re.S
)


def unblock_scripts(html: str) -> str:
    """Undo WP Meteor's script deferral so pages work without its runtime."""
    html = WPMETEOR_BOOTSTRAP_RE.sub("", html)
    html = PHAST_INLINE_RE.sub("", html)

    def restore(m):
        tag = m.group(0)
        tag = tag.replace('type="javascript/blocked"', "")
        tag = re.sub(r'data-wpmeteor-type="([^"]*)"', r'type="\1"', tag)
        tag = re.sub(r'data-wpmeteor-src="([^"]*)"', r'src="\1"', tag)
        tag = tag.replace(" data-wpmeteor-after", "")
        return tag

    html = re.sub(r"<script[^>]*>", restore, html)
    return html


def rewrite(html: str) -> str:
    html = unblock_scripts(html)
    preserved = {}

    def stash(m):
        key = f"\x00PRESERVE{len(preserved)}\x00"
        preserved[key] = m.group(0)
        return key

    for pat in PRESERVE_PATTERNS:
        html = pat.sub(stash, html)

    html = html.replace(DOMAIN + "/", "/").replace(DOMAIN, "/")
    html = html.replace("http://develop-coaching.com/", "/")
    # protocol-relative
    html = html.replace("//develop-coaching.com/", "/")
    # JSON-escaped form used inside Elementor data-settings attributes
    html = html.replace("https:\\/\\/develop-coaching.com\\/", "\\/")
    # URL-encoded form (share links, oembed params)
    html = html.replace("https%3A%2F%2Fdevelop-coaching.com%2F", "%2F")

    for key, val in preserved.items():
        html = html.replace(key, val)
    return html


def out_path(fname: str) -> str:
    stem = fname[:-5]  # drop .html
    if stem == "__home":
        return os.path.join(OUT, "index.html")
    parts = stem.split("__")
    return os.path.join(OUT, *parts, "index.html")


def main():
    # Remove only generated HTML pages; keep mirrored assets (wp-content etc.)
    if os.path.exists(OUT):
        for root, dirs, files in os.walk(OUT):
            rel = os.path.relpath(root, OUT)
            if rel.split(os.sep)[0] in ("wp-content", "wp-includes", "feeds"):
                dirs[:] = []
                continue
            for f in files:
                if f == "index.html" or f == "vercel.json":
                    os.remove(os.path.join(root, f))
    os.makedirs(OUT, exist_ok=True)

    count = 0
    for fname in sorted(os.listdir(REF)):
        if not fname.endswith(".html"):
            continue
        html = open(os.path.join(REF, fname), encoding="utf-8", errors="ignore").read()
        dest = out_path(fname)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(rewrite(html))
        count += 1

    # vercel.json: trailing slashes like WordPress, plus legacy redirects
    redirects = []
    if os.path.exists("export/extra-results.txt"):
        for line in open("export/extra-results.txt"):
            if not line.startswith("REDIRECT "):
                continue
            src, dest = line[len("REDIRECT "):].strip().split(" -> ")
            src_path = src.replace(DOMAIN, "").rstrip("/") or "/"
            dest_path = dest.replace(DOMAIN, "")
            if src_path and dest_path and src_path != dest_path.rstrip("/"):
                redirects.append(
                    {"source": src_path, "destination": dest_path, "permanent": True}
                )
    if os.path.exists("export/manual-redirects.json"):
        manual = json.load(open("export/manual-redirects.json"))
        existing = {r["source"] for r in redirects}
        redirects.extend(r for r in manual if r["source"] not in existing)
    # WordPress URLs carry a trailing slash; match both forms of every rule
    slashed = [
        {**r, "source": r["source"] + "/"}
        for r in redirects
        if not r["source"].endswith("/") and "(" not in r["source"]
    ]
    redirects.extend(slashed)
    vercel = {
        "trailingSlash": True,
        "redirects": redirects,
        "rewrites": [
            {"source": "/feed/podcast", "destination": "/feeds/podcast.xml"},
            {"source": "/feed/podcast/", "destination": "/feeds/podcast.xml"}
        ],
        # PREVIEW PHASE ONLY: large A/V is excluded from the deploy and
        # served from the live WordPress host. Before cutover these files
        # must move to real storage and this block must be removed.
        "_preview_av_redirects": True,
    }
    # noindex any *.vercel.app host so the copy is never indexed; the real
    # domain does not match this pattern so production SEO is unaffected
    vercel["headers"] = [{
        "source": "/(.*)",
        "has": [{"type": "host", "value": "(?<sub>.*)\\.vercel\\.app"}],
        "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}],
    }]
    if vercel.pop("_preview_av_redirects", False):
        vercel["redirects"].append({
            "source": "/wp-content/uploads/:path(.*\\.(?:mp3|mp4))",
            "destination": "https://develop-coaching.com/wp-content/uploads/:path",
            "permanent": False,
        })
    with open(os.path.join(OUT, "vercel.json"), "w") as f:
        json.dump(vercel, f, indent=1)

    print(f"{count} pages written to {OUT}/, {len(redirects)} redirects in vercel.json")


if __name__ == "__main__":
    main()
