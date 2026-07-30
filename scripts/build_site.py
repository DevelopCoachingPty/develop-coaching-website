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

# Public base of the dc-website-media Vercel Blob store (team develop-coaching,
# region lhr1, store_GgdzvmzaZ1n7EO4I). The 93 podcast mp3s and testimonial mp4s
# live here rather than in the deploy: ~2.4GB, and four of them are over
# GitHub's 100MB per-file limit. Paths are mirrored 1:1, so
# /wp-content/uploads/x is served from BLOB_BASE/wp-content/uploads/x and the
# page markup needs no rewriting. Not a secret: this is a public store, and the
# host is visible in every page that plays media.
BLOB_BASE = "https://ggdzvmzaz1n7eo4i.public.blob.vercel-storage.com"

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


# Injected into every page. On preview hosts (*.vercel.app) it switches off
# the analytics and pixels so that reviewing the copy does not pollute the
# real GA4 property, Meta Pixel and Clarity with fake traffic. On the
# production domain the condition is false and nothing changes.
PREVIEW_GUARD = """<script data-preview-guard>
(function(){
  if (!location.hostname.endsWith('.vercel.app')) return;
  window['ga-disable-G-PXT2VCVFLW'] = true;      // official GA4 opt-out flag
  window.fbq = window.fbq || function(){};        // swallow Meta Pixel calls
  window.clarity = window.clarity || function(){};
  console.info('[preview] analytics disabled on this host');
})();
</script>"""

HEAD_RE = re.compile(r"<head[^>]*>", re.I)


def rewrite(html: str) -> str:
    html = unblock_scripts(html)
    html = HEAD_RE.sub(lambda m: m.group(0) + PREVIEW_GUARD, html, count=1)
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
    # Patterns ending in a wildcard (:path*) already match with or without a
    # trailing slash. Everything else, including capture-group patterns like
    # /blog/page/:n(\d+), needs an explicit slashed twin or it will not fire
    # on the trailing-slash URLs WordPress has always used.
    slashed = [
        {**r, "source": r["source"] + "/"}
        for r in redirects
        if not r["source"].endswith("/") and not r["source"].endswith("*")
    ]
    redirects.extend(slashed)
    vercel = {
        "trailingSlash": True,
        "redirects": redirects,
        "rewrites": [
            {"source": "/feed/podcast", "destination": "/feeds/podcast.xml"},
            {"source": "/feed/podcast/", "destination": "/feeds/podcast.xml"}
        ],
        # Large A/V is excluded from the deploy (see .gitignore) and served
        # from Vercel Blob instead. This no longer depends on the live
        # WordPress host, so it survives cutover as-is.
        "_av_redirects": True,
    }
    vercel["headers"] = [
        # noindex any *.vercel.app host so the copy is never indexed; the real
        # domain does not match this pattern so production SEO is unaffected
        {
            "source": "/(.*)",
            "has": [{"type": "host", "value": "(?<sub>.*)\\.vercel\\.app"}],
            "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}],
        },
        # Security headers, applied to every response.
        # Deliberately NOT setting a Content-Security-Policy: the pages load
        # scripts from GTM, Meta, Clarity, Mouseflow, ActiveCampaign,
        # GoHighLevel, Trustindex and YouTube, so a CSP would need careful
        # per-domain work and could silently break tracking or bookings.
        # HSTS matches what the live site already sends. "preload" is left
        # off on purpose: submitting to the preload list is very hard to undo.
        {
            "source": "/(.*)",
            "headers": [
                {"key": "Strict-Transport-Security",
                 "value": "max-age=31536000; includeSubDomains"},
                {"key": "X-Content-Type-Options", "value": "nosniff"},
                {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
                {"key": "Permissions-Policy",
                 "value": "geolocation=(), microphone=(), payment=()"},
            ],
        },
    ]
    if vercel.pop("_av_redirects", False):
        vercel["redirects"].append({
            "source": "/wp-content/uploads/:path(.*\\.(?:mp3|mp4))",
            "destination": f"{BLOB_BASE}/wp-content/uploads/:path",
            "permanent": False,
        })
    with open(os.path.join(OUT, "vercel.json"), "w") as f:
        json.dump(vercel, f, indent=1)

    print(f"{count} pages written to {OUT}/, {len(redirects)} redirects in vercel.json")


if __name__ == "__main__":
    main()
