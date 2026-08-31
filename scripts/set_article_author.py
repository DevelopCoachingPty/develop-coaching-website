#!/usr/bin/env python3
"""Credit Greg Wilkes as the author of every blog article.

Greg confirmed on 31 August 2026 that every article is credited to him.

Before this ran, 41 articles credited seo@digital-progress.co.uk, five credited
jessica@digital-progress.co.uk, seven credited nobody and four credited
"gregwilkes". Search engines and answer engines weigh the author entity when
judging whether a page carries real expertise, and the articles carry weight
because of Greg's experience.

The four that already credited him pointed at
https://develop-coaching.com/author/gregwilkes/, which returns 404 on the live
site. This script points every article at the about page instead, which exists.

    python3 scripts/set_article_author.py --check   # report, write nothing
    python3 scripts/set_article_author.py           # apply

Idempotent and fail-closed: a page with no BlogPosting node raises rather than
being written half-changed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
SITEMAP = WWW / "post-sitemap.xml"
SITE = "https://develop-coaching.com"

AUTHOR_ID = f"{SITE}/#/schema/person/greg-wilkes"
AUTHOR_NAME = "Greg Wilkes"
AUTHOR_URL = f"{SITE}/about-greg-wilkes/"
ORGANISATION_ID = f"{SITE}/#organization"

AUTHOR_PERSON = {
    "@type": "Person",
    "@id": AUTHOR_ID,
    "name": AUTHOR_NAME,
    "url": AUTHOR_URL,
    "worksFor": {"@id": ORGANISATION_ID},
}

AUTHOR_REFERENCE = {"@id": AUTHOR_ID, "name": AUTHOR_NAME}

SCHEMA_RE = re.compile(
    r'(<script type="application/ld\+json" class="rank-math-schema-pro">)(.*?)(</script>)',
    re.DOTALL,
)


def article_slugs() -> list:
    text = SITEMAP.read_text(encoding="utf-8")
    return sorted(
        m.group(1)
        for m in re.finditer(rf"<loc>{re.escape(SITE)}/([^<]+?)/</loc>", text)
    )


def set_author(document: str) -> tuple:
    """Return (document, previous author name). Raises if the schema is unusable."""
    match = SCHEMA_RE.search(document)
    if not match:
        raise ValueError("Rank Math schema block not found")
    schema = json.loads(match.group(2))
    graph = schema.get("@graph")
    if not graph:
        raise ValueError("schema @graph is empty")

    posting = next((n for n in graph if n.get("@type") == "BlogPosting"), None)
    if posting is None:
        raise ValueError("no BlogPosting node in schema")

    existing = posting.get("author") or {}
    previous = existing.get("name", "") if isinstance(existing, dict) else str(existing)
    previous_id = existing.get("@id") if isinstance(existing, dict) else None

    # Drop the Person node this article used as its author, keeping any other
    # Person node the page might legitimately describe.
    graph = [
        node
        for node in graph
        if not (
            node.get("@type") == "Person"
            and node.get("@id") in {previous_id, AUTHOR_ID}
        )
    ]

    # Put the author Person back where the old one sat, before the BlogPosting.
    insert_at = next(
        (i for i, n in enumerate(graph) if n.get("@type") == "BlogPosting"), len(graph)
    )
    graph.insert(insert_at, dict(AUTHOR_PERSON))

    for node in graph:
        if node.get("@type") == "BlogPosting":
            node["author"] = dict(AUTHOR_REFERENCE)

    schema["@graph"] = graph
    body = json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
    updated = (
        document[: match.start()]
        + match.group(1)
        + body
        + match.group(3)
        + document[match.end() :]
    )
    return updated, previous


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report without writing")
    args = parser.parse_args(argv)

    changed = []
    unchanged = []
    for slug in article_slugs():
        page = WWW / slug / "index.html"
        original = page.read_text(encoding="utf-8")
        updated, previous = set_author(original)
        twice, _ = set_author(updated)
        if twice != updated:
            raise SystemExit(f"{slug}: not idempotent, refusing to write")
        if updated == original:
            unchanged.append(slug)
            continue
        changed.append((slug, previous or "nobody"))
        if not args.check:
            page.write_text(updated, encoding="utf-8")

    verb = "would change" if args.check else "changed"
    print(f"{len(changed)} {verb}, {len(unchanged)} already correct")
    tally = {}
    for _, previous in changed:
        tally[previous] = tally.get(previous, 0) + 1
    for previous, count in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {count:3}  was {previous}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
