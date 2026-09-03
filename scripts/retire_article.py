#!/usr/bin/env python3
"""Retire an article and redirect it to its replacement.

Consolidating duplicates means removing a live URL, which is the one operation
in this rollout that a reader can notice going wrong. Doing it by hand seven
times invites a missed step, so every step happens here or not at all:

  1. redirect added to export/manual-redirects.json and www/vercel.json,
     both the bare path and the trailing slash form
  2. removed from www/post-sitemap.xml
  3. removed from www/search-index.json
  4. post cards for the retired article removed from listing pages
  5. remaining contextual links across the site repointed at the destination
  6. the generated article directory deleted
  7. the managed article source files deleted

    python3 scripts/retire_article.py <slug> <destination-path> [--check]

The destination must already exist, and the audit's three inventory sources
must agree afterwards, so a half-finished retirement fails loudly.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
SITE = "https://develop-coaching.com"
MANUAL_REDIRECTS = ROOT / "export" / "manual-redirects.json"
VERCEL = WWW / "vercel.json"
SITEMAP = WWW / "post-sitemap.xml"
SEARCH_INDEX = WWW / "search-index.json"
BLOG_SYSTEM = ROOT / "content" / "blog-system"


def add_redirects(slug: str, destination: str, check: bool) -> int:
    rules = [
        {"source": f"/{slug}", "destination": destination, "permanent": True},
        {"source": f"/{slug}/", "destination": destination, "permanent": True},
    ]
    added = 0
    for path, key in ((MANUAL_REDIRECTS, None), (VERCEL, "redirects")):
        data = json.loads(path.read_text(encoding="utf-8"))
        target = data if key is None else data[key]
        existing = {r["source"] for r in target}
        new = [r for r in rules if r["source"] not in existing]
        added += len(new)
        if new and not check:
            target[:0] = new
            path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return added


def validate_destination_not_redirected(destination: str) -> None:
    destination_key = destination.rstrip("/")
    for path, key in ((MANUAL_REDIRECTS, None), (VERCEL, "redirects")):
        data = json.loads(path.read_text(encoding="utf-8"))
        redirects = data if key is None else data[key]
        redirected_sources = {item["source"].rstrip("/") for item in redirects}
        if destination_key in redirected_sources:
            raise SystemExit(
                f"destination is already redirected in {path.relative_to(ROOT)}: {destination}"
            )


def validate_no_inbound_redirects(slug: str) -> None:
    retired_key = f"/{slug}".rstrip("/")
    for path, key in ((MANUAL_REDIRECTS, None), (VERCEL, "redirects")):
        data = json.loads(path.read_text(encoding="utf-8"))
        redirects = data if key is None else data[key]
        inbound = [
            item["source"]
            for item in redirects
            if item["destination"].rstrip("/") == retired_key
        ]
        if inbound:
            raise SystemExit(
                f"existing redirects point to /{slug}/ in {path.relative_to(ROOT)}: "
                + ", ".join(inbound)
            )


def drop_from_sitemap(slug: str, check: bool) -> int:
    text = SITEMAP.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"\s*<url>(?:(?!</url>).)*?/{re.escape(slug)}/</loc>.*?</url>", re.DOTALL
    )
    updated, count = pattern.subn("", text)
    if count and not check:
        SITEMAP.write_text(updated, encoding="utf-8")
    return count


def drop_from_search_index(slug: str, check: bool) -> int:
    entries = json.loads(SEARCH_INDEX.read_text(encoding="utf-8"))
    kept = [e for e in entries if (e.get("u") or "").strip("/") != slug]
    removed = len(entries) - len(kept)
    if removed and not check:
        SEARCH_INDEX.write_text(
            json.dumps(kept, separators=(",", ":"), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return removed


def retire_sources(slug: str, check: bool) -> int:
    sources = [
        path
        for path in (BLOG_SYSTEM / f"{slug}.json", BLOG_SYSTEM / f"{slug}.body.html")
        if path.exists()
    ]
    if sources and not check:
        subprocess.run(
            ["git", "rm", "-q", "--", *(str(path) for path in sources)],
            cwd=ROOT,
            check=True,
        )
    return len(sources)


def _balanced_element_end(document: str, start: int, tag: str) -> int:
    depth = 0
    token_re = re.compile(rf"</?{tag}\b[^>]*>", re.IGNORECASE)
    for token in token_re.finditer(document, start):
        if token.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return token.end()
        elif not token.group(0).rstrip().endswith("/>"):
            depth += 1
    raise ValueError(f"unclosed {tag} listing card")


def drop_listing_cards(post_id: str, check: bool) -> int:
    """Remove archive and loop cards while leaving contextual links to repoint."""
    card_re = re.compile(
        rf'<(?P<tag>article|div)\b(?=[^>]*\bpost-{re.escape(post_id)}\b)'
        r'(?=[^>]*(?:data-elementor-type="loop-item"|class="[^"]*elementor-post\b))[^>]*>',
        re.IGNORECASE,
    )
    dynamic_style_re = re.compile(
        rf'<style\b[^>]*>(?:(?!</style>).)*?\.e-loop-item-{re.escape(post_id)}\b'
        r'(?:(?!</style>).)*?</style>\s*$',
        re.IGNORECASE | re.DOTALL,
    )
    removed = 0
    for page in WWW.rglob("index.html"):
        html = page.read_text(encoding="utf-8", errors="ignore")
        spans = []
        for match in card_re.finditer(html):
            start = match.start()
            style = dynamic_style_re.search(html[:start])
            if style:
                start = style.start()
            spans.append((start, _balanced_element_end(html, match.start(), match.group("tag"))))
        if not spans:
            continue
        removed += len(spans)
        if not check:
            for start, end in reversed(spans):
                html = html[:start] + html[end:]
            page.write_text(html, encoding="utf-8")
    return removed


def repoint_links(slug: str, destination: str, check: bool) -> int:
    pattern = re.compile(rf'(?:{re.escape(SITE)})?/{re.escape(slug)}/')
    changed = 0
    for page in WWW.rglob("index.html"):
        if page.parent.name == slug:
            continue
        html = page.read_text(encoding="utf-8", errors="ignore")
        if f"/{slug}/" not in html:
            continue
        updated, count = pattern.subn(lambda _match: destination, html)
        if count:
            changed += count
            if not check:
                page.write_text(updated, encoding="utf-8")
    return changed


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("destination", help="path to redirect to, e.g. /keeper/")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    slug, destination = args.slug, args.destination
    if not destination.startswith("/") or not destination.endswith("/"):
        raise SystemExit("destination must look like /keeper/")
    if not (WWW / destination.strip("/") / "index.html").exists():
        raise SystemExit(f"destination does not exist: {destination}")
    validate_destination_not_redirected(destination)
    validate_no_inbound_redirects(slug)
    article = WWW / slug / "index.html"
    if not article.exists():
        raise SystemExit(f"nothing to retire at /{slug}/")
    post_id_match = re.search(r"\bpostid-(\d+)\b", article.read_text(encoding="utf-8"))
    if not post_id_match:
        raise SystemExit(f"could not find WordPress post id for /{slug}/")

    redirects = add_redirects(slug, destination, args.check)
    sitemap = drop_from_sitemap(slug, args.check)
    index = drop_from_search_index(slug, args.check)
    cards = drop_listing_cards(post_id_match.group(1), args.check)
    links = repoint_links(slug, destination, args.check)
    sources = retire_sources(slug, args.check)
    if not args.check:
        subprocess.run(["git", "rm", "-r", "-q", str(WWW / slug)], cwd=ROOT, check=True)

    verb = "would" if args.check else ""
    print(
        f"{slug} -> {destination}: {verb} redirects {redirects}, sitemap {sitemap}, "
        f"index {index}, cards {cards}, links repointed {links}, sources {sources}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
