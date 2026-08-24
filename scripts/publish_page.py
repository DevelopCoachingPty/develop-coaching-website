#!/usr/bin/env python3
"""Publish a new page into the static site from a JSON payload.

The site is a frozen export of the old WordPress build, so there is no CMS and
no template engine: a new page is an existing page with its post-specific slots
swapped. Diffing two exported posts shows those slots are the SEO head block,
the JSON-LD graph, the post title, the category term, the post content widget,
and a handful of WordPress leftovers that carry the template's post id.

Reads JSON on stdin (or --json FILE), writes www/<slug>/index.html, and updates
post-sitemap.xml plus search-index.json. Prints a JSON result on stdout.

    {
      "title": "...",
      "slug": "construction-cash-flow",
      "body_html": "<p>...</p>",
      "meta_description": "...",
      "category": "Convert",              # optional, must be an existing term
      "date": "2026-08-11",               # optional, defaults to today
      "template": "construction-sales-funnel",  # optional
      "image_url": "/wp-content/...",     # optional social/schema image
      "overwrite": true                   # optional, needed to replace a page
    }

The slug and the template stay inside www/: a path that escapes it is refused,
and an existing page is only replaced with --overwrite (or "overwrite": true).
"""
import argparse
import datetime
import glob
import html as htmllib
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, "www")
DOMAIN = "https://develop-coaching.com"
DEFAULT_TEMPLATE = "construction-sales-funnel"
LOGO = f"{DOMAIN}/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg"
AUTHOR_ID = f"{DOMAIN}/about-greg-wilkes/#person"

# Per-post WordPress leftovers. They carry the template's post id, so for a page
# that no longer comes from WordPress they are removed rather than rewritten.
STALE_TAGS = [
    re.compile(r'<link rel="alternate" title="JSON"[^>]*/>\s*'),
    re.compile(r'<link rel="EditURI"[^>]*/>\s*'),
    re.compile(r"<link rel='shortlink'[^>]*/>\s*"),
    re.compile(r'<meta name="ti-site-data"[^>]*/>\s*'),
    re.compile(r'<link rel="alternate" type="application/json\+oembed"[^>]*/>\s*'),
    re.compile(r'<link rel="alternate" type="text/xml\+oembed"[^>]*/>\s*'),
]


def safe_site_path(value: str, label: str) -> str:
    """Return a payload-supplied site path, failing if it escapes www/.

    The slug and the template name come straight from the payload, so a value
    like "../../tmp/x" or "/etc/passwd" would otherwise steer a read or a write
    outside the site. Containment is checked on the resolved path, not on the
    raw string, so a symlink inside www/ cannot smuggle the target out either.
    """
    raw = (value or "").strip()
    if os.path.isabs(raw):
        raise SystemExit(f"publish_page: {label} must be site relative, not absolute: {value!r}")
    clean = raw.strip("/")
    if not clean or clean in (os.curdir, os.pardir):
        raise SystemExit(f"publish_page: {label} is empty once normalised: {value!r}")
    root = os.path.realpath(WWW)
    target = os.path.realpath(os.path.join(WWW, clean))
    try:
        contained = target != root and os.path.commonpath([root, target]) == root
    except ValueError:
        contained = False
    if not contained:
        raise SystemExit(f"publish_page: {label} escapes the site directory: {value!r}")
    return clean


def slot(html: str, pattern: str, replacement: str, label: str, count: int = 0) -> str:
    """Substitute a template slot, failing loudly if the slot has moved."""
    new, n = re.subn(pattern, lambda _: replacement, html, count=count, flags=re.S)
    if n == 0:
        raise SystemExit(f"publish_page: slot not found in template: {label}")
    return new


def balanced_div(html: str, start: int) -> tuple[int, int]:
    """Return (inner_start, inner_end) of the div opening at `start`."""
    depth = 0
    i = start
    token = re.compile(r"<div\b[^>]*>|</div>")
    inner_start = None
    while True:
        m = token.search(html, i)
        if not m:
            raise SystemExit("publish_page: unbalanced divs around post content")
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return inner_start, m.start()
        else:
            depth += 1
            if depth == 1:
                inner_start = m.end()
        i = m.end()


def replace_post_content(html: str, body_html: str) -> str:
    marker = html.find("elementor-widget-theme-post-content")
    if marker == -1:
        raise SystemExit("publish_page: post content widget not found in template")
    widget_open = html.rfind("<div", 0, marker)
    inner_start, inner_end = balanced_div(html, widget_open)
    return html[:inner_start] + "\n" + body_html.strip() + "\n\t\t\t\t" + html[inner_end:]


def rewrite_jsonld(html: str, *, title, description, url, date, image) -> str:
    m = re.search(r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', html, re.S)
    if not m:
        raise SystemExit("publish_page: JSON-LD block not found in template")
    try:
        graph = json.loads(m.group(2))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"publish_page: template JSON-LD is not valid JSON: {exc}")

    nodes = graph.get("@graph", [])
    for node in nodes:
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if {"BlogPosting", "Article", "NewsArticle"} & set(types):
            node["@id"] = f"{url}#richSnippet"
            node["headline"] = title
            node["name"] = title
            node["description"] = description
            node["author"] = {"@id": AUTHOR_ID}
            node["datePublished"] = date
            node["dateModified"] = date
            node["url"] = url
            node["mainEntityOfPage"] = {"@id": url}
            if image:
                node["image"] = {"@type": "ImageObject", "url": image}
            else:
                node.pop("image", None)
        elif "WebPage" in types:
            node["@id"] = url
            node["url"] = url
            node["name"] = title
            node["description"] = description
            node["datePublished"] = date
            node["dateModified"] = date
            node.pop("primaryImageOfPage", None)
            if "breadcrumb" in node:
                node.pop("breadcrumb")
        elif "BreadcrumbList" in types:
            node["itemListElement"] = [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN},
                {"@type": "ListItem", "position": 2, "name": title},
            ]
            node["@id"] = f"{url}#breadcrumb"

    def is_template_leftover(node: dict) -> bool:
        node_id = node.get("@id", "")
        # The template's own featured image, its author (the old SEO agency's
        # WordPress user) and that author's gravatar.
        if node.get("@type") == "ImageObject" and node_id.startswith(f"{DOMAIN}/wp-content"):
            return True
        if node.get("@type") == "ImageObject" and "gravatar.com" in node_id:
            return True
        if node.get("@type") == "Person" and "/author/" in node_id:
            return True
        return False

    nodes = [n for n in nodes if not is_template_leftover(n)]
    nodes.append(
        {
            "@type": "Person",
            "@id": AUTHOR_ID,
            "name": "Greg Wilkes",
            "url": f"{DOMAIN}/about-greg-wilkes/",
            "worksFor": {"@id": f"{DOMAIN}/#organization"},
        }
    )
    graph["@graph"] = nodes
    return html[: m.start()] + m.group(1) + json.dumps(graph, separators=(",", ":")) + m.group(3) + html[m.end():]


def build_page(payload: dict) -> str:
    template = safe_site_path(payload.get("template") or DEFAULT_TEMPLATE, "template")
    template_path = os.path.join(WWW, template, "index.html")
    if not os.path.exists(template_path):
        raise SystemExit(f"publish_page: template page not found: {template_path}")
    html = open(template_path, encoding="utf-8").read()

    title = payload["title"].strip()
    slug = safe_site_path(payload["slug"], "slug")
    description = (payload.get("meta_description") or "").strip()
    date = payload.get("date") or datetime.date.today().isoformat()
    image = payload.get("image_url") or ""
    if image.startswith("/"):
        image = DOMAIN + image
    url = f"{DOMAIN}/{slug}/"

    esc = lambda s: htmllib.escape(s, quote=True)

    html = slot(html, r"<title>.*?</title>", f"<title>{esc(title)}</title>", "<title>", 1)
    html = slot(
        html,
        r'<meta name="description" content=".*?"/>',
        f'<meta name="description" content="{esc(description)}"/>',
        "meta description",
        1,
    )
    html = slot(
        html,
        r'<link rel="canonical" href=".*?" />',
        f'<link rel="canonical" href="{url}" />',
        "canonical",
        1,
    )
    for prop, value in [
        ("og:title", title),
        ("og:description", description),
        ("og:url", url),
        ("og:image", image or LOGO),
    ]:
        html = slot(
            html,
            rf'<meta property="{prop}" content=".*?" />',
            f'<meta property="{prop}" content="{esc(value)}" />',
            prop,
            1,
        )
    for name, value in [
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:image", image or LOGO),
    ]:
        html = re.sub(
            rf'<meta name="{name}" content=".*?" />',
            lambda _: f'<meta name="{name}" content="{esc(value)}" />',
            html,
            count=1,
            flags=re.S,
        )
    html = re.sub(
        r'(<meta name="twitter:label1" content="Written by" />\s*<meta name="twitter:data1" content=")[^"]*(")',
        lambda m: m.group(1) + "Greg Wilkes" + m.group(2),
        html,
        count=1,
        flags=re.S,
    )

    # Article timestamps only exist on post templates.
    for prop, value in [
        ("article:published_time", f"{date}T00:00:00+00:00"),
        ("article:modified_time", f"{date}T00:00:00+00:00"),
    ]:
        html = re.sub(
            rf'<meta property="{prop}" content=".*?" />',
            lambda _: f'<meta property="{prop}" content="{value}" />',
            html,
            count=1,
            flags=re.S,
        )

    html = rewrite_jsonld(
        html, title=title, description=description, url=url, date=date, image=image
    )

    for pattern in STALE_TAGS:
        html = pattern.sub("", html)

    # Post title widget
    html = slot(
        html,
        r'(<h1 class="elementor-heading-title elementor-size-default">).*?(</h1>)',
        f'<h1 class="elementor-heading-title elementor-size-default">{esc(title)}</h1>',
        "post title h1",
        1,
    )

    # Category term shown under the title
    category = payload.get("category")
    if category:
        cat_slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
        html = re.sub(
            r'<a href="/category/[^"]*" class="elementor-post-info__terms-list-item">.*?</a>',
            lambda _: f'<a href="/category/{cat_slug}/" class="elementor-post-info__terms-list-item">{esc(category)}</a>',
            html,
            count=1,
            flags=re.S,
        )

    # The template's post id stays in body classes and in the Elementor CSS
    # filenames (/wp-content/uploads/elementor/css/post-<id>.css). That file
    # holds the layout styling this page reuses, so rewriting the id would
    # point the page at a stylesheet that does not exist and strip its design.
    html = re.sub(r'"page_id":\d+', '"page_id":0', html)
    html = re.sub(r"&quot;page_id&quot;:\d+", "&quot;page_id&quot;:0", html)

    # Elementor's frontend config repeats the template's post id and title.
    html = re.sub(
        r'"post":\{"id":\d+,"title":"[^"]*","excerpt":"[^"]*","featuredImage":(?:"[^"]*"|false)\}',
        lambda _: '"post":{"id":0,"title":"%s","excerpt":"","featuredImage":false}'
        % urllib.parse.quote(title, safe=""),
        html,
        count=1,
    )

    # A stale page-cache stamp from the old host.
    html = re.sub(r"\s*<!-- Page cached by LiteSpeed Cache[^>]*-->\s*$", "\n", html)

    # The title container's inline background is the post's hero image. Left
    # alone, a new page would wear the template post's photo.
    if payload.get("image_url"):
        hero = payload["image_url"]
        html, n = re.subn(
            r'(elementor-element-cec9484 > \.elementor-motion-effects-container > \.elementor-motion-effects-layer\{background-image:url\(")[^"]*(")',
            lambda m: m.group(1) + hero + m.group(2),
            html,
            count=1,
        )
        if n == 0:
            print("publish_page: warning, hero image slot not found", file=sys.stderr)

    html = replace_post_content(html, payload["body_html"])
    return html


def update_sitemap(slug: str, date: str) -> bool:
    """Record the page in the sitemaps.

    The site splits its sitemap by post type (posts, pages, courses and so on),
    so a URL that already lives in one of them gets its lastmod refreshed
    there. Appending it to post-sitemap.xml instead would list the same URL in
    two sitemaps.
    """
    loc = f"{DOMAIN}/{slug}/"
    pattern = re.compile(
        r"(<url>\s*<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)[^<]*(</lastmod>)"
    )
    for path in sorted(glob.glob(os.path.join(WWW, "*sitemap*.xml"))):
        xml = open(path, encoding="utf-8").read()
        if pattern.search(xml):
            open(path, "w", encoding="utf-8").write(pattern.sub(rf"\g<1>{date}\g<2>", xml))
            return True
        if loc in xml:
            return False  # already listed, just without a lastmod

    path = os.path.join(WWW, "post-sitemap.xml")
    if not os.path.exists(path):
        return False
    xml = open(path, encoding="utf-8").read()
    entry = f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{date}</lastmod>\n  </url>\n"
    open(path, "w", encoding="utf-8").write(xml.replace("</urlset>", entry + "</urlset>"))
    return True


def update_search_index(title: str, slug: str, body_html: str, kind: str = "posts") -> bool:
    path = os.path.join(WWW, "search-index.json")
    if not os.path.exists(path):
        return False
    index = json.load(open(path, encoding="utf-8"))
    url = f"/{slug}/"
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", body_html))
    summary = re.sub(r"\s+", " ", text).strip()[:210]
    entry = {"t": title, "u": url, "s": summary, "k": kind}
    for i, row in enumerate(index):
        if row.get("u") == url:
            index[i] = entry
            break
    else:
        index.append(entry)
    json.dump(index, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="payload file (default: stdin)")
    ap.add_argument("--dry-run", action="store_true", help="build but do not write")
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing page (refused by default)",
    )
    args = ap.parse_args()

    raw = open(args.json, encoding="utf-8").read() if args.json else sys.stdin.read()
    payload = json.loads(raw)
    for field in ("title", "slug", "body_html"):
        if not payload.get(field):
            raise SystemExit(f"publish_page: missing required field: {field}")

    slug = safe_site_path(payload["slug"], "slug")
    date = payload.get("date") or datetime.date.today().isoformat()
    html = build_page(payload)

    out_dir = os.path.join(WWW, slug)
    out_file = os.path.join(out_dir, "index.html")
    existed = os.path.exists(out_file)
    overwrite = bool(args.overwrite or payload.get("overwrite"))

    # Replacing a live page is destructive and irreversible here, so it needs
    # saying out loud rather than happening as a side effect of a reused slug.
    if existed and not overwrite:
        if args.dry_run:
            print(
                f"publish_page: warning, page already exists: {out_file}",
                file=sys.stderr,
            )
        else:
            raise SystemExit(
                f"publish_page: page already exists: {out_file}. "
                'Pass --overwrite (or "overwrite": true in the payload) to replace it.'
            )

    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        open(out_file, "w", encoding="utf-8").write(html)
        update_sitemap(slug, date)
        update_search_index(payload["title"], slug, payload["body_html"])

    print(
        json.dumps(
            {
                "path": os.path.relpath(out_file, ROOT),
                "url": f"{DOMAIN}/{slug}/",
                "created": not existed,
                "bytes": len(html),
                "dry_run": bool(args.dry_run),
            }
        )
    )


if __name__ == "__main__":
    main()
