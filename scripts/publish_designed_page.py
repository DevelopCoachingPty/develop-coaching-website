#!/usr/bin/env python3
"""Publish a custom-designed page into the static site.

publish_page.py reuses an exported page wholesale, which is right for blog
posts but leaves the body locked to the Elementor blog layout. Landing pages
need their own design, so this keeps only the chrome from an exported page (the
<head>, the site header and the footer, which carry the nav, fonts, tracking
and brand styling) and replaces everything between the header and footer with
hand-written markup and CSS.

That split is safe because the region between </header> and <footer> is
div-balanced in the export, so dropping it whole leaves valid HTML.

    python3 scripts/publish_designed_page.py --json page.json

    {
      "title": "...",
      "slug": "courses/mastermind-course",
      "meta_description": "...",
      "content_file": "content/mastermind.html",   # body markup + its <style>
      "shell": "courses/mastermind-course",        # page to borrow chrome from
      "date": "2026-08-11",
      "image_url": "/wp-content/..."
    }
"""
import argparse
import datetime
import html as htmllib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_page as pp  # noqa: E402

DEFAULT_SHELL = "courses/mastermind-course"


def safe_repo_file(value: str, label: str) -> str:
    """Resolve a payload file inside the repository and refuse escapes."""
    raw = (value or "").strip()
    if not raw:
        raise SystemExit(f"publish_designed_page: missing {label}")
    root = os.path.realpath(pp.ROOT)
    target = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(root, raw))
    try:
        contained = target != root and os.path.commonpath([root, target]) == root
    except ValueError:
        contained = False
    if not contained:
        raise SystemExit(f"publish_designed_page: {label} escapes the repository: {value!r}")
    if not os.path.isfile(target):
        raise SystemExit(f"publish_designed_page: {label} not found: {value!r}")
    return target


def split_chrome(html: str) -> tuple[str, str]:
    """Return (everything up to and including </header>, everything from <footer>)."""
    marker = html.find("</header>")
    footer = html.find("<footer")
    if marker == -1 or footer == -1 or footer < marker:
        raise SystemExit("publish_designed_page: could not find header/footer in the shell page")
    return html[: marker + len("</header>")], html[footer:]


def build_page(payload: dict) -> str:
    shell_slug = pp.safe_site_path(payload.get("shell") or DEFAULT_SHELL, "shell")
    shell_path = os.path.join(pp.WWW, shell_slug, "index.html")
    if not os.path.exists(shell_path):
        raise SystemExit(f"publish_designed_page: shell page not found: {shell_path}")

    content_path = safe_repo_file(payload["content_file"], "content file")

    html = open(shell_path, encoding="utf-8").read()
    content = open(content_path, encoding="utf-8").read()

    title = payload["title"].strip()
    slug = pp.safe_site_path(payload["slug"], "slug")
    description = (payload.get("meta_description") or "").strip()
    date = payload.get("date") or datetime.date.today().isoformat()
    image = payload.get("image_url") or ""
    if image.startswith("/"):
        image = pp.DOMAIN + image
    url = f"{pp.DOMAIN}/{slug}/"
    esc = lambda s: htmllib.escape(s, quote=True)

    head, footer = split_chrome(html)

    # Same SEO slots as the blog publisher, applied to the chrome's <head>.
    head = pp.slot(head, r"<title>.*?</title>", f"<title>{esc(title)}</title>", "<title>", 1)
    head = re.sub(
        r'<meta name="description" content=".*?"/>',
        lambda _: f'<meta name="description" content="{esc(description)}"/>',
        head,
        count=1,
        flags=re.S,
    )
    head = re.sub(
        r'<link rel="canonical" href=".*?" />',
        lambda _: f'<link rel="canonical" href="{url}" />',
        head,
        count=1,
        flags=re.S,
    )
    for prop, value in [
        ("og:title", title),
        ("og:description", description),
        ("og:url", url),
        ("og:image", image or pp.LOGO),
    ]:
        head = re.sub(
            rf'<meta property="{prop}" content=".*?" />',
            lambda _: f'<meta property="{prop}" content="{esc(value)}" />',
            head,
            count=1,
            flags=re.S,
        )
    for name, value in [("twitter:title", title), ("twitter:description", description)]:
        head = re.sub(
            rf'<meta name="{name}" content=".*?" />',
            lambda _: f'<meta name="{name}" content="{esc(value)}" />',
            head,
            count=1,
            flags=re.S,
        )

    head = pp.rewrite_jsonld(
        head, title=title, description=description, url=url, date=date, image=image
    )
    for pattern in pp.STALE_TAGS:
        head = pattern.sub("", head)
    head = re.sub(
        r'(<meta name="twitter:label1" content="Written by" />\s*<meta name="twitter:data1" content=")[^"]*(")',
        lambda m: m.group(1) + "Greg Wilkes" + m.group(2),
        head,
        count=1,
        flags=re.S,
    )

    footer = re.sub(r"\s*<!-- Page cached by LiteSpeed Cache[^>]*-->\s*$", "\n", footer)

    # Shared CSS is inlined rather than linked so a page is one self-contained
    # file, matching how the rest of the export works.
    css_parts = []
    for css_file in payload.get("css_files", ["content/_design-system.css"]):
        css_path = safe_repo_file(css_file, "CSS file")
        css_parts.append(open(css_path, encoding="utf-8").read())

    fonts = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Source+Sans+Pro:ital,wght@0,400;0,700;1,400;1,700&display=swap">'
    )
    style = "<style>\n" + "\n".join(css_parts) + "\n</style>"

    return (
        f"{head}\n{fonts}\n{style}\n"
        f'<div class="dc-page">\n{content.strip()}\n</div>\n{footer}'
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing page (refused by default)",
    )
    args = ap.parse_args()

    payload = json.load(open(args.json, encoding="utf-8"))
    for field in ("title", "slug", "content_file"):
        if not payload.get(field):
            raise SystemExit(f"publish_designed_page: missing required field: {field}")

    slug = pp.safe_site_path(payload["slug"], "slug")
    date = payload.get("date") or datetime.date.today().isoformat()
    html = build_page(payload)

    out_file = os.path.join(pp.WWW, slug, "index.html")
    existed = os.path.exists(out_file)
    overwrite = bool(args.overwrite or payload.get("overwrite"))
    if existed and not overwrite and not args.dry_run:
        raise SystemExit(
            f"publish_designed_page: page already exists: {out_file}. "
            'Pass --overwrite (or "overwrite": true in the payload) to replace it.'
        )
    if not args.dry_run:
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        open(out_file, "w", encoding="utf-8").write(html)
        pp.update_sitemap(slug, date)
        search_kind = payload.get("search_kind") or (
            "courses" if slug.startswith("courses/") else "pages"
        )
        pp.update_search_index(
            payload["title"],
            slug,
            payload.get("meta_description") or "",
            kind=search_kind,
        )

    print(
        json.dumps(
            {
                "path": os.path.relpath(out_file, pp.ROOT),
                "url": f"{pp.DOMAIN}/{slug}/",
                "created": not existed,
                "bytes": len(html),
                "dry_run": bool(args.dry_run),
            }
        )
    )


if __name__ == "__main__":
    main()
