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

from simplify_navigation import simplify_main_navigation
from modernise_footer import modernise_footer

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
NEWSLETTER_EMBED_RE = re.compile(
    r'<iframe\b(?=[^>]*\bsrc=["\']https://link\.flow-build\.com/widget/form/'
    r'LrwamDnwkXRzgaIuSFn2["\'])[^>]*>.*?</iframe>\s*'
    r'<script\b(?=[^>]*\bsrc=["\']https://link\.flow-build\.com/js/'
    r'form_embed\.js["\'])[^>]*>.*?</script>',
    re.S | re.I,
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


# The ActiveCampaign account has been closed for years: every
# developcoaching.activehosted.com/f/embed.php request answers 402 and the
# account URL redirects to ActiveCampaign's win-back page. So none of these
# embeds have rendered anything in a long time, and 361 of the 366 sit inside
# widgets hidden at every breakpoint anyway. Each one still costs a blocking
# request to a dead third-party host on page load, so drop the script and the
# container it would have populated.
# \bsrc would also match data-src, so a lazily-loaded script that merely
# mentions the URL could be deleted wholesale. Require real whitespace before
# the attribute so only a genuine src= matches.
DEAD_AC_EMBED_RE = re.compile(
    r'(?:<div class="_form_\d+"\s*></div>\s*)?'
    r'<script\b[^>]*\ssrc=["\']https://developcoaching\.activehosted\.com/'
    r'f/embed\.php\?id=\d+["\'][^>]*>\s*</script>',
    re.S | re.I,
)


def strip_dead_activecampaign(html: str) -> str:
    return DEAD_AC_EMBED_RE.sub("", html)


def dedupe_newsletter_embed(html: str) -> str:
    """Keep one newsletter form in the shared Elementor popup."""
    seen = False

    def keep_first(match):
        nonlocal seen
        if seen:
            return ""
        seen = True
        return match.group(0)

    return NEWSLETTER_EMBED_RE.sub(keep_first, html)


# Injected into every page. On preview hosts (*.vercel.app) it switches off
# the analytics and pixels so that reviewing the copy does not pollute the
# real GA4 property, Meta Pixel and Clarity with fake traffic. On the
# production domain the condition is false and nothing changes.
PREVIEW_GUARD = """<script data-preview-guard>
(function(){
  if (!location.hostname.endsWith('.vercel.app')) return;
  var params = new URLSearchParams(location.search);
  if (params.has('gtm_debug') || params.has('gtm_preview') || params.has('gtm_auth')) {
    console.info('[preview] analytics enabled for Tag Assistant');
    return;
  }
  window['ga-disable-G-PXT2VCVFLW'] = true;      // official GA4 opt-out flag
  window.fbq = window.fbq || function(){};        // swallow Meta Pixel calls
  window.clarity = window.clarity || function(){};
  console.info('[preview] analytics disabled on this host');
})();
</script>"""

# The WordPress snapshot has the GTM noscript fallback but no GTM loader. It
# also loads GA4 directly, which means the container's click/conversion tags
# never run. Replace the standalone GA4 bootstrap with the real GTM container.
# On Vercel preview hosts GTM only loads when Tag Assistant supplies its normal
# preview parameters, so ordinary QA traffic still cannot pollute analytics.
GTM_LOADER = """<script data-gtm-loader>
(function(w,d,s,l,i){
  var previewHost = location.hostname.endsWith('.vercel.app');
  var params = new URLSearchParams(location.search);
  var tagAssistant = params.has('gtm_debug') || params.has('gtm_preview') || params.has('gtm_auth');
  if (previewHost && !tagAssistant) {
    console.info('[preview] GTM disabled unless Tag Assistant is connected');
    return;
  }
  w[l]=w[l]||[];
  w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
  var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';
  j.async=true;
  j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;
  f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-T4HBRD3');
</script>"""

STANDALONE_GA4_LOADER_RE = re.compile(
    r'<script[^>]*src="https://www\.googletagmanager\.com/gtag/js\?id=G-PXT2VCVFLW"[^>]*></script>',
    re.I,
)
STANDALONE_GA4_CONFIG_RE = re.compile(
    r"<script[^>]*>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];"
    r"\s*function gtag\(\)\{dataLayer\.push\(arguments\);\}"
    r"\s*gtag\('js',\s*new Date\(\)\);"
    r"\s*gtag\('config',\s*'G-PXT2VCVFLW'\);\s*</script>",
    re.S | re.I,
)

INTERNAL_LINK_FIXES = {
    "/7-mistakes-when-scaling-a-construction-business-past-1m": "/mistakes-when-scaling-a-construction-business/",
    "/build-a-self-running-team": "/delegation-in-construction/",
    "/free-trainings/construction-recruitment-blueprint": "/how-to-recruit-for-your-construction-business-2/",
    "/from-trades-to-transformation-practical-growth-for-sme-construction-firms": "/construction-business-systems/",
    "/get-client-to-leave-a-review": "/customer-reviews-for-construction-company/",
    "/how-to-implement-effective-construction-business-systems": "/construction-business-systems/",
    "/mastermind-course": "/courses/mastermind-course/",
    "/podcast/digital-transformation-construction": "/podcast/systemise-your-business-with-james-brown/",
    "/podcast/systems-implementation-case-study": "/podcast/from-firefighting-to-fueling-a-1m-electrical-company-the-journey-of-dan-james/",
    "/scale": "/5-pillars-free-trainings/scale/",
    "/scale/business-transformation": "/5-pillars-free-trainings/scale/",
    "/scale/financial-growth": "/construction-cash-flow-management-the-blueprint-to-scaling-past-1m/",
    "/scale/systems-processes": "/systems-and-processes-subcategory-page/",
    "/scale/team-development": "/delegation-in-construction/",
    "/show-up-like-a-boss-in-2024": "/the-big-growth-plan/",
    "/strategic-planning-for-2024": "/5-pillars-free-trainings/plan/",
}

HEAD_RE = re.compile(r"<head[^>]*>", re.I)
HEAD_CLOSE_RE = re.compile(r"</head>", re.I)

# Injected last in <head> so it wins the cascade over Elementor's stylesheets.
# Kept deliberately small: this is a targeted fix, not a place to accumulate
# style overrides. Anything larger belongs in a proper stylesheet.
CUSTOM_CSS = """<style data-dc-custom>
/* Desktop header nav wrapped "Contact" onto a second line: the menu row needs
   993px inside a 991px container, so it broke by 2px. Trimming the horizontal
   padding recovers roughly 70px and keeps all nine items on one line without
   touching font size, colours or spacing anywhere else. Scoped to >=1025px so
   the mobile burger menu is completely unaffected. The live WordPress site has
   the same wrap, so this is a fix rather than a migration regression.

   Elementor sets this padding from a widget-scoped rule
   (.elementor-4222 .elementor-element-b81d386 ... .elementor-item) whose
   specificity beats any sane selector here, so !important is used rather than
   duplicating those generated ids, which change whenever the header template
   is re-saved. */
@media (min-width: 1025px) {
  .elementor-nav-menu--main .elementor-nav-menu {
    flex-wrap: nowrap;
  }
  .elementor-nav-menu--main .elementor-nav-menu > li > a.elementor-item {
    padding-left: 13px !important;
    padding-right: 13px !important;
  }
}
</style>"""

# WordPress emits discovery <link> tags pointing at endpoints that do not exist
# on a static build. Crawlers and embed tools follow them and collect 404s.
# Removed deliberately narrowly: each pattern is pinned to the WordPress-only
# rel/type, so canonical, hreflang, favicons, Open Graph, Twitter cards and
# JSON-LD are untouched. The podcast feed is NOT affected: it is served from
# /feed/podcast via a rewrite and has no discovery <link> tag here.
#
# All four already point at dead or irrelevant endpoints on the live site:
#   /feed/ 410, /comments/feed/ 410, /xmlrpc.php 405, /wp-json/ not migrated.
LEGACY_DISCOVERY_PATTERNS = [
    ("RSS and comments feed links",
     re.compile(r'\s*<link[^>]+type="application/rss\+xml"[^>]*/?>', re.I)),
    ("WordPress REST API discovery",
     re.compile(r'\s*<link[^>]+rel="https://api\.w\.org/"[^>]*/?>', re.I)),
    # Per-post REST link: <link rel="alternate" type="application/json"
    # href=".../wp-json/wp/v2/pages/4808" />. Pinned to a wp-json href so no
    # other rel="alternate" link (hreflang, RSS handled above) can match.
    ("WordPress REST per-page link",
     re.compile(r'\s*<link[^>]+rel="alternate"[^>]*href="[^"]*/wp-json/wp/v2/[^"]*"[^>]*/?>', re.I)),
    ("oEmbed discovery links",
     re.compile(r'\s*<link[^>]+type="(?:application/json|text/xml)\+oembed"[^>]*/?>', re.I)),
    ("EditURI / RSD (XML-RPC)",
     re.compile(r'\s*<link[^>]+rel="EditURI"[^>]*/?>', re.I)),
]

discovery_removed = {}


def strip_legacy_discovery(html: str) -> str:
    for label, pat in LEGACY_DISCOVERY_PATTERNS:
        html, n = pat.subn("", html)
        if n:
            discovery_removed[label] = discovery_removed.get(label, 0) + n
    return html


def rewrite(html: str, relative_path: str = "") -> str:
    html = unblock_scripts(html)
    html = simplify_main_navigation(html)
    html = modernise_footer(html, relative_path)
    html = strip_dead_activecampaign(html)
    html = dedupe_newsletter_embed(html)
    html = strip_legacy_discovery(html)
    html = STANDALONE_GA4_LOADER_RE.sub("", html)
    html = STANDALONE_GA4_CONFIG_RE.sub("", html)
    html = HEAD_RE.sub(
        lambda m: m.group(0) + PREVIEW_GUARD + GTM_LOADER,
        html,
        count=1,
    )
    html = HEAD_CLOSE_RE.sub(lambda m: CUSTOM_CSS + m.group(0), html, count=1)
    preserved = {}

    def stash(m):
        key = f"\x00PRESERVE{len(preserved)}\x00"
        preserved[key] = m.group(0)
        return key

    for pat in PRESERVE_PATTERNS:
        html = pat.sub(stash, html)

    # The www. form has to be handled explicitly: a large number of internal
    # links (including the "Schedule a Call" CTA on nearly every page) were
    # authored as https://www.develop-coaching.com/... These would still
    # resolve after cutover, but only via an extra www-to-apex redirect hop on
    # the primary conversion path, and on the preview they send visitors to
    # the live WordPress site instead of the copy being reviewed.
    html = html.replace("https://www.develop-coaching.com/", "/")
    html = html.replace("https://www.develop-coaching.com", "/")
    html = html.replace("http://www.develop-coaching.com/", "/")
    html = html.replace("//www.develop-coaching.com/", "/")
    html = html.replace("https:\\/\\/www.develop-coaching.com\\/", "\\/")
    html = html.replace("https%3A%2F%2Fwww.develop-coaching.com%2F", "%2F")

    html = html.replace(DOMAIN + "/", "/").replace(DOMAIN, "/")
    html = html.replace("http://develop-coaching.com/", "/")
    # protocol-relative
    html = html.replace("//develop-coaching.com/", "/")
    # JSON-escaped form used inside Elementor data-settings attributes
    html = html.replace("https:\\/\\/develop-coaching.com\\/", "\\/")
    # URL-encoded form (share links, oembed params)
    html = html.replace("https%3A%2F%2Fdevelop-coaching.com%2F", "%2F")

    for old_path, new_path in INTERNAL_LINK_FIXES.items():
        html = html.replace(f'href="{old_path}"', f'href="{new_path}"')
        html = html.replace(f'href="{old_path}/"', f'href="{new_path}"')

    for key, val in preserved.items():
        html = html.replace(key, val)

    html = absolutise_lightbox_urls(html)
    return html


# Elementor 4.2.0 added a guard to Lightbox.showModal:
#
#     showModal(e){ if (e.url && !e.url.startsWith("http")) return; ... }
#
# so a lightbox whose url is site-relative now silently does nothing when
# clicked. The URL rewriting above makes every internal URL relative, which
# is right everywhere else but breaks every click-to-play video. Put the
# absolute form back inside data-elementor-lightbox attributes only.
# Only a genuine site-relative URL should be absolutised: (?!\\/) skips the
# protocol-relative \/\/host\/path form, which is already absolute and would be
# corrupted by prefixing the domain. Matching up to &quot; rather than
# excluding every & lets URLs carrying &amp; query separators through too.
LIGHTBOX_URL_RE = re.compile(
    r'(data-elementor-lightbox="[^"]*?&quot;url&quot;:&quot;)'
    r'(\\/(?!\\/)(?:(?!&quot;).)*?)'
    r'(&quot;)'
)


def absolutise_lightbox_urls(html: str) -> str:
    def fix(m):
        return m.group(1) + "https:\\/\\/develop-coaching.com" + m.group(2) + m.group(3)

    return LIGHTBOX_URL_RE.sub(fix, html)


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
                rel_file = os.path.relpath(os.path.join(root, f), OUT)
                # /search/ is a hand-built static tool, not a WordPress export.
                # Preserve it when regenerating the snapshot-owned pages.
                if rel_file == os.path.join("search", "index.html"):
                    continue
                if f == "index.html" or f == "vercel.json":
                    os.remove(os.path.join(root, f))
    os.makedirs(OUT, exist_ok=True)

    count = 0
    for fname in sorted(os.listdir(REF)):
        if not fname.endswith(".html"):
            continue
        html = open(os.path.join(REF, fname), encoding="utf-8", errors="ignore").read()
        dest = out_path(fname)
        relative_path = os.path.relpath(dest, OUT).replace(os.sep, "/")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(rewrite(html, relative_path))
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
            "source": "/wp-content/uploads/:path(.*\\.(?:mp3|mp4|mov))",
            "destination": f"{BLOB_BASE}/wp-content/uploads/:path",
            "permanent": False,
        })
    with open(os.path.join(OUT, "vercel.json"), "w") as f:
        json.dump(vercel, f, indent=1)

    print(f"{count} pages written to {OUT}/, {len(redirects)} redirects in vercel.json")
    if discovery_removed:
        print("\nlegacy WordPress discovery tags removed:")
        for label, n in sorted(discovery_removed.items()):
            print(f"   {label:34} {n}")


if __name__ == "__main__":
    main()
