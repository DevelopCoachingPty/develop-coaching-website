#!/usr/bin/env python3
"""Audit every blog article against the shared blog design system.

Reads the article inventory from three independent sources (post sitemap,
filesystem body classes, search index) and fails closed if they disagree.
Writes docs/blog-rollout-inventory.csv and docs/blog-rollout-inventory.md.
"""

import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
DOCS = ROOT / "docs"
SITEMAP = WWW / "post-sitemap.xml"
SEARCH_INDEX = WWW / "search-index.json"

PILLARS = ["plan", "attract", "convert", "deliver", "scale"]
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(fragment: str) -> str:
    return html.unescape(TAG_RE.sub(" ", fragment)).replace("\xa0", " ").strip()


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugs_from_sitemap() -> set:
    text = SITEMAP.read_text(encoding="utf-8")
    return {
        m.group(1)
        for m in re.finditer(r"<loc>https://develop-coaching\.com/([^<]+?)/</loc>", text)
    }


def slugs_from_filesystem() -> set:
    found = set()
    for page in WWW.glob("*/index.html"):
        text = page.read_text(encoding="utf-8", errors="ignore")
        body = re.search(r"<body[^>]*\bclass=\"([^\"]*)\"", text)
        if body and "single-post" in body.group(1):
            found.add(page.parent.name)
    return found


def slugs_from_search_index() -> set:
    entries = json.loads(SEARCH_INDEX.read_text(encoding="utf-8"))
    return {e["u"].strip("/") for e in entries if e.get("k") == "posts" and e.get("u")}


DIV_RE = re.compile(r"<div\b[^>]*>|</div>", re.I)
NOISE_RE = re.compile(r"<(script|style|noscript)\b[\s\S]*?</\1>", re.I)
WIDGET_RE = re.compile(r'data-widget_type="theme-post-content\.default"[^>]*>')


def article_body(document: str) -> str:
    """The post-content widget only, matched by div depth, scripts stripped."""
    match = WIDGET_RE.search(document)
    if not match:
        return ""
    start = match.end()
    depth = 0
    end = len(document)
    for token in DIV_RE.finditer(document, start):
        if token.group(0).startswith("</"):
            if depth == 0:
                end = token.start()
                break
            depth -= 1
        else:
            depth += 1
    return NOISE_RE.sub(" ", document[start:end])


def first_paragraph(body: str) -> str:
    for match in re.finditer(r"<p[^>]*>([\s\S]*?)</p>", body):
        text = squash(strip_tags(match.group(1)))
        if len(text) > 60:
            return text
    return ""


def audit_page(slug: str) -> dict:
    page = WWW / slug / "index.html"
    doc = page.read_text(encoding="utf-8", errors="ignore")
    body = article_body(doc)

    h1s = [squash(strip_tags(m)) for m in re.findall(r"<h1[^>]*>([\s\S]*?)</h1>", doc)]
    h2s = [squash(strip_tags(m)) for m in re.findall(r"<h2[^>]*>([\s\S]*?)</h2>", body)]
    title = re.search(r"<title>([\s\S]*?)</title>", doc)
    desc = re.search(r'<meta name="description" content="([^"]*)"', doc)
    canonical = re.search(r'<link rel="canonical" href="([^"]*)"', doc)
    modified = re.search(r'<meta property="article:modified_time" content="([^"]*)"', doc)

    terms = re.search(
        r'<span class="elementor-post-info__terms-list">([\s\S]*?)</span>', doc
    )
    categories = []
    if terms:
        categories = [squash(strip_tags(a)) for a in re.findall(r"<a[^>]*>([\s\S]*?)</a>", terms.group(1))]
    body_classes = re.search(r'<body[^>]*\bclass="([^"]*)"', doc)
    class_pillars = []
    if body_classes:
        class_pillars = [
            p.title()
            for p in PILLARS
            if re.search(rf"\bcategory-{p}\b", body_classes.group(1))
        ]

    words = len(strip_tags(body).split())
    intro = first_paragraph(body)

    schema_headline = ""
    schema_match = re.search(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">([\s\S]*?)</script>',
        doc,
    )
    if schema_match:
        try:
            graph = json.loads(schema_match.group(1)).get("@graph", [])
            for node in graph:
                if node.get("@type") == "BlogPosting":
                    schema_headline = squash(html.unescape(node.get("headline", "")))
        except json.JSONDecodeError:
            schema_headline = "UNPARSEABLE"

    images = re.findall(r"<img\b[^>]*>", body)
    missing_alt = sum(1 for i in images if not re.search(r'\balt="[^"]+"', i))

    pillar_links = re.findall(r'href="/5-pillars-free-trainings/([a-z\-]*)/?"', body)
    category_links = re.findall(r'href="/category/([a-z\-]+)/"', body)

    h1 = h1s[0] if h1s else ""
    title_text = squash(html.unescape(title.group(1))) if title else ""
    desc_text = squash(html.unescape(desc.group(1))) if desc else ""

    # Content-readiness flags
    flags = []
    if len(h1s) != 1:
        flags.append(f"h1-count-{len(h1s)}")
    if not title_text:
        flags.append("no-title")
    elif len(title_text) > 65:
        flags.append(f"title-{len(title_text)}ch")
    if not desc_text:
        flags.append("no-meta-description")
    elif not 110 <= len(desc_text) <= 165:
        flags.append(f"meta-{len(desc_text)}ch")
    if canonical:
        if canonical.group(1).rstrip("/") != f"https://develop-coaching.com/{slug}":
            flags.append("canonical-mismatch")
    else:
        flags.append("no-canonical")
    if re.match(r"^(are you|do you|have you|is your|if you|as a|in the world|in today)", intro.lower()):
        flags.append("fluffy-intro")
    if not intro:
        flags.append("no-intro-paragraph")
    if words < 700:
        flags.append(f"thin-{words}w")
    if len(h2s) < 3:
        flags.append(f"h2-count-{len(h2s)}")
    if re.match(r"^\d+\s", h1) or re.match(r"^(top\s+)?\d+\b", h1.lower()):
        flags.append("listicle-headline")
    if not h1.strip():
        flags.append("empty-h1")
    if schema_headline and h1 and schema_headline.lower() != h1.lower():
        flags.append("schema-headline-drift")
    if missing_alt:
        flags.append(f"alt-missing-{missing_alt}")
    em_dashes = body.count("\u2014")
    if em_dashes:
        flags.append(f"em-dashes-{em_dashes}")
    if not pillar_links:
        flags.append("no-pillar-link")
    if len(categories) != 1:
        flags.append(f"categories-{len(categories) or 0}")

    return {
        "slug": slug,
        "url": f"https://develop-coaching.com/{slug}/",
        "pillar": categories[0] if len(categories) == 1 else "/".join(categories or class_pillars) or "UNSET",
        "all_categories": "; ".join(categories),
        "body_class_pillars": "; ".join(class_pillars),
        "h1": h1,
        "h1_count": len(h1s),
        "title": title_text,
        "title_len": len(title_text),
        "meta_description": desc_text,
        "meta_len": len(desc_text),
        "canonical": canonical.group(1) if canonical else "",
        "words": words,
        "h2_count": len(h2s),
        "first_h2": h2s[0] if h2s else "",
        "intro_first_60": intro[:120],
        "schema_headline": schema_headline,
        "images": len(images),
        "images_missing_alt": missing_alt,
        "em_dashes": em_dashes,
        "pillar_links": "; ".join(sorted(set(p for p in pillar_links if p))),
        "category_links_in_body": "; ".join(sorted(set(category_links))),
        "modified": modified.group(1) if modified else "",
        "already_migrated": "yes" if 'id="dc-article-brief"' in doc or "dc-lead-quality-briefing" in doc else "no",
        "flags": "; ".join(flags),
        "flag_count": len(flags),
    }


BATCH_ONE = [
    "construction-sales-funnel",
    "attract-the-right-clients",
    "construction-job-pricing",
]
REFERENCE = "construction-lead-generation"

AUTO_PREFIXES = (
    "schema-headline-drift",
    "canonical-mismatch",
    "no-pillar-link",
    "categories-",
)


def split_flags(flags: list) -> tuple:
    """Separate what the transformer fixes from what a person must write."""
    auto = [f for f in flags if any(f.startswith(a) for a in AUTO_PREFIXES)]
    manual = [f for f in flags if f not in auto]
    return manual, auto


CONTENT_FLAGS = (
    "listicle-headline",
    "fluffy-intro",
    "no-intro-paragraph",
    "empty-h1",
)


def work_type(row: dict) -> str:
    """How much work an article needs before the shared design can be applied."""
    flags = row["flags"].split("; ") if row["flags"] else []
    if row["slug"] == REFERENCE:
        return "Reference"
    content = [f for f in flags if f in CONTENT_FLAGS]
    if any(f.startswith("h1-count") for f in flags):
        content.append("multiple h1")
    if any(f.startswith("h2-count") for f in flags):
        content.append("too few sections")
    if int(row["words"]) < 900:
        content.append("thin")
    if content:
        return "Rewrite first"
    if row["pillar"] in ("Uncategorized", "UNSET") or "/" in row["pillar"]:
        return "Recategorise"
    return "Design only"


def write_markdown(rows: list) -> Path:
    by_pillar = {}
    for row in rows:
        row["work_type"] = work_type(row)
        by_pillar.setdefault(row["pillar"], []).append(row)

    order = ["Plan", "Attract", "Convert", "Deliver", "Scale"]
    order += [p for p in sorted(by_pillar) if p not in order]

    out = []
    out.append("# Blog rollout inventory")
    out.append("")
    out.append(
        f"{len(rows)} articles. Inventory reconciled across three independent sources "
        "(post sitemap, filesystem body classes, search index); the audit fails closed "
        "if they disagree. Regenerate with `python3 scripts/audit_blog_library.py`."
    )
    out.append("")
    out.append("## Status key")
    out.append("")
    out.append("| Column | Meaning |")
    out.append("| --- | --- |")
    out.append("| Human content work | Needs a person to write or restructure: headline, intro, section headings, length, title and meta wording, image alt text. |")
    out.append("| Transformer handles | Fixed automatically when the shared design is applied: schema headline sync, canonical, contextual pillar link, single-pillar category. |")
    out.append("| Work | `Rewrite first` needs headline, intro or structure fixed before the shared design goes on. `Recategorise` needs a pillar decision. `Design only` is ready for the transformer. |")
    out.append("| Stage | Audit / Content review / Redesign / Approved / Deployed. Update by hand as each article moves. |")
    out.append("")
    out.append("## Batches")
    out.append("")
    out.append(f"- **Batch 1 (approval batch):** {', '.join(BATCH_ONE)}")
    out.append("- **Batches 2 onwards:** grouped by pillar in the order Plan, Attract, Convert, Deliver, Scale. No article is excluded.")
    out.append("")

    counts = {}
    for row in rows:
        counts[row["work_type"]] = counts.get(row["work_type"], 0) + 1
    out.append("## Totals")
    out.append("")
    out.append("| Work needed | Articles |")
    out.append("| --- | --- |")
    for key in ("Reference", "Design only", "Recategorise", "Rewrite first"):
        if key in counts:
            out.append(f"| {key} | {counts[key]} |")
    out.append("")

    for pillar in order:
        group = by_pillar.get(pillar)
        if not group:
            continue
        out.append(f"## {pillar} ({len(group)})")
        out.append("")
        out.append("| Article | Words | H2s | Work | Stage | Human content work | Transformer handles |")
        out.append("| --- | ---: | ---: | --- | --- | --- | --- |")
        for row in sorted(group, key=lambda r: (r["work_type"], r["slug"])):
            batch = " **[batch 1]**" if row["slug"] in BATCH_ONE else ""
            flags = row["flags"].split("; ") if row["flags"] else []
            manual, auto = split_flags(flags)
            out.append(
                f"| [{row['slug']}]({row['url']}){batch} | {row['words']} | {row['h2_count']} "
                f"| {row['work_type']} | Audit | {', '.join(manual) or 'none'} "
                f"| {', '.join(auto) or 'none'} |"
            )
        out.append("")

    path = DOCS / "blog-rollout-inventory.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def main() -> None:
    sitemap = slugs_from_sitemap()
    filesystem = slugs_from_filesystem()
    search = slugs_from_search_index()
    if not (sitemap == filesystem == search):
        raise SystemExit(
            "Inventory sources disagree.\n"
            f"  sitemap only: {sorted(sitemap - filesystem - search)}\n"
            f"  filesystem only: {sorted(filesystem - sitemap - search)}\n"
            f"  search index only: {sorted(search - sitemap - filesystem)}"
        )

    rows = [audit_page(slug) for slug in sorted(sitemap)]
    DOCS.mkdir(exist_ok=True)

    csv_path = DOCS / "blog-rollout-inventory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    md_path = write_markdown(rows)
    print(f"{len(rows)} articles audited, three sources agree")
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")
    return rows


if __name__ == "__main__":
    main()
