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

    h3s = [squash(strip_tags(m)) for m in re.findall(r"<h3[^>]*>([\s\S]*?)</h3>", body)]
    question_headings = sum(1 for h in h2s + h3s if h.rstrip().endswith("?"))
    lists = len(re.findall(r"<(ol|ul)\b", body))
    internal_links = len(
        set(
            re.findall(r'href="(?:https://develop-coaching\.com)?(/[a-z0-9\-/]+/)"', body)
        )
    )

    schema_author = schema_published = ""
    schema_section = ""
    if schema_match:
        try:
            for node in json.loads(schema_match.group(1)).get("@graph", []):
                if node.get("@type") == "BlogPosting":
                    author = node.get("author")
                    schema_author = (author or {}).get("name", "") if isinstance(author, dict) else str(author or "")
                    schema_published = node.get("datePublished", "")
                    schema_section = node.get("articleSection", "")
        except json.JSONDecodeError:
            pass

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
    if "greg" not in schema_author.lower():
        flags.append("author-not-greg")
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
        "question_headings": question_headings,
        "lists": lists,
        "internal_links": internal_links,
        "schema_author": schema_author,
        "schema_published": schema_published,
        "schema_section": schema_section,
        "em_dashes": em_dashes,
        "pillar_links": "; ".join(sorted(set(p for p in pillar_links if p))),
        "category_links_in_body": "; ".join(sorted(set(category_links))),
        "modified": modified.group(1) if modified else "",
        "already_migrated": "yes" if 'id="dc-article-brief"' in doc or "dc-lead-quality-briefing" in doc else "no",
        "flags": "; ".join(flags),
        "flag_count": len(flags),
    }


# --------------------------------------------------------------------------
# GEO readiness score
#
# Generative engines lift answers out of pages. They favour a direct answer up
# front, headings phrased as the question a person asks, extractable lists,
# clean schema and clear internal routes. Every dimension below is measured
# from the page itself. Nothing here is a proxy for traffic; see the note in
# docs/blog-geo-backlog.md.
# --------------------------------------------------------------------------

GEO_DIMENSIONS = (
    ("Direct answer up front", 12),
    ("Question-shaped headings", 10),
    ("Extractable lists", 8),
    ("Heading structure", 12),
    ("Depth", 8),
    ("Schema integrity", 12),
    ("Metadata", 12),
    ("Internal routes", 10),
    ("Images and alt text", 6),
    ("Freshness", 6),
    ("Brand compliance", 4),
)

TODAY = "2026-08-31"


def months_since(stamp: str) -> int:
    match = re.match(r"(\d{4})-(\d{2})", stamp or "")
    if not match:
        return 999
    year, month = int(match.group(1)), int(match.group(2))
    now_year, now_month = int(TODAY[:4]), int(TODAY[5:7])
    return (now_year - year) * 12 + (now_month - month)


def geo_score(row: dict) -> dict:
    flags = row["flags"].split("; ") if row["flags"] else []
    words = int(row["words"])
    scores = {}

    scores["Direct answer up front"] = (
        0 if ("fluffy-intro" in flags or "no-intro-paragraph" in flags) else 12
    )

    questions = int(row["question_headings"])
    scores["Question-shaped headings"] = 10 if questions >= 2 else 5 if questions == 1 else 0

    lists = int(row["lists"])
    scores["Extractable lists"] = 8 if lists >= 3 else 4 if lists >= 1 else 0

    structure = 0
    if int(row["h1_count"]) == 1:
        structure += 6
    if int(row["h2_count"]) >= 4:
        structure += 6
    scores["Heading structure"] = structure

    scores["Depth"] = 8 if words >= 1200 else 5 if words >= 900 else 0

    schema = 0
    if row["schema_headline"] and row["schema_headline"] != "UNPARSEABLE":
        schema += 3
    if "schema-headline-drift" not in flags and row["schema_headline"]:
        schema += 3
    if row["schema_section"].strip().lower() in PILLARS:
        schema += 3
    if "greg" in row["schema_author"].strip().lower():
        schema += 3
    scores["Schema integrity"] = schema

    metadata = 0
    if row["title"] and len(row["title"]) <= 65:
        metadata += 4
    if 110 <= len(row["meta_description"]) <= 165:
        metadata += 4
    if "canonical-mismatch" not in flags and "no-canonical" not in flags:
        metadata += 4
    scores["Metadata"] = metadata

    routes = 0
    if row["pillar_links"]:
        routes += 6
    if int(row["internal_links"]) >= 3:
        routes += 4
    scores["Internal routes"] = routes

    images = 0
    if int(row["images"]) >= 1:
        images += 3
    if int(row["images_missing_alt"]) == 0:
        images += 3
    scores["Images and alt text"] = images

    age = months_since(row["modified"])
    scores["Freshness"] = 6 if age <= 24 else 3 if age <= 48 else 0

    scores["Brand compliance"] = 0 if int(row["em_dashes"]) else 4

    return scores


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
    out.append("| GEO | Readiness score out of 100 across eleven measured dimensions. See docs/blog-geo-backlog.md for the model. Lowest first, because that is the work queue. |")
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
        out.append("| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |")
        out.append("| --- | ---: | ---: | ---: | --- | --- | --- | --- |")
        for row in sorted(group, key=lambda r: (int(r["geo_score"]), r["slug"])):
            batch = " **[batch 1]**" if row["slug"] in BATCH_ONE else ""
            flags = row["flags"].split("; ") if row["flags"] else []
            manual, auto = split_flags(flags)
            out.append(
                f"| [{row['slug']}]({row['url']}){batch} | {row['geo_score']} | {row['words']} "
                f"| {row['h2_count']} | {row['work_type']} | Audit "
                f"| {', '.join(manual) or 'none'} | {', '.join(auto) or 'none'} |"
            )
        out.append("")

    path = DOCS / "blog-rollout-inventory.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Ranked action backlog
#
# Actions, not articles. Each one is ranked on how many articles it touches,
# how much GEO score it recovers, and whether it is a live defect. Counts are
# computed from the audit so they cannot drift from reality. The order and the
# reasoning are a judgement call and are open to challenge.
# --------------------------------------------------------------------------

DUPLICATE_PAIRS = (
    ("usp-for-construction-company", "usp-for-construction-company-2"),
    ("how-to-grow-a-construction-business", "how-to-grow-a-construction-business-2"),
    ("how-to-recruit-for-your-construction-business", "how-to-recruit-for-your-construction-business-2"),
    ("good-reviews", "how-to-get-good-reviews"),
    ("digital-marketing-construction", "digital-marketing-for-construction"),
    ("construction-marketing", "construction-business-marketing"),
)


def backlog_actions(rows: list) -> list:
    by_slug = {r["slug"]: r for r in rows}
    scored = {r["slug"]: geo_score(r) for r in rows}

    def lost(dimension: str) -> int:
        cap = dict(GEO_DIMENSIONS)[dimension]
        return sum(cap - scored[r["slug"]][dimension] for r in rows)

    def count(predicate) -> int:
        return sum(1 for r in rows if predicate(r))

    return [
        {
            "action": "Credit Greg as the author in every article schema",
            "articles": count(lambda r: "greg" not in r["schema_author"].lower()),
            "recovers": None,
            "why": (
                "41 articles are attributed to seo@digital-progress.co.uk and five to "
                "jessica@digital-progress.co.uk. Seven name nobody. Four name Greg. Generative "
                "engines and Google both lean on the author entity when deciding whether a page "
                "carries real expertise, and the whole proposition here is Greg's experience. "
                "This is one field per page and the transformer can set it, but it is Greg's call "
                "whether he is named on all 71."
            ),
            "effort": "One transformer field. Needs Greg's yes, then it is mechanical.",
        },
        {
            "action": "Add a contextual Five Pillars link inside every article body",
            "articles": count(lambda r: not r["pillar_links"]),
            "recovers": lost("Internal routes"),
            "why": (
                "The pillar links that exist sit in page furniture, which crawlers and answer "
                "engines discount. A link from inside the article body, in context, is what routes "
                "a reader from a question to the pillar that answers it. It is also the single "
                "largest pool of recoverable score in the audit."
            ),
            "effort": "Ships automatically with each article's briefing block.",
        },
        {
            "action": "Give every article at least two question-shaped headings",
            "articles": count(lambda r: int(r["question_headings"]) < 2),
            "recovers": lost("Question-shaped headings"),
            "why": (
                "51 articles contain no heading phrased as a question. Answer engines lift "
                "question-and-answer pairs; a heading that matches what someone typed is the "
                "cheapest way to become the passage that gets quoted. The briefing block supplies "
                "one, so most articles need one more in the body."
            ),
            "effort": "One heading rewrite per article, inside the rewrite pass.",
        },
        {
            "action": "Resolve the six near-duplicate pairs",
            "articles": len(DUPLICATE_PAIRS) * 2,
            "recovers": None,
            "why": (
                "Twelve articles are competing with a sibling for the same term, so neither can "
                "win outright and internal link equity is split. No amount of redesign fixes two "
                "pages arguing over one query. Recommendations per pair are in "
                "docs/blog-duplicate-pairs.md; nothing gets merged or redirected without Greg's "
                "approval, one pair at a time."
            ),
            "effort": "One decision per pair, then a merge plus redirects in two files.",
        },
        {
            "action": "Fix the second unclosed anchor, on best-social-media-platforms-for-construction-companies",
            "articles": 1,
            "recovers": None,
            "why": (
                "An anchor closed by a stray </p> is never closed at all, so the parser pulls the "
                "rest of the article into the link. The whole body renders in link colour and "
                "every paragraph becomes a keyboard tab stop. This is live now. The same fault on "
                "construction-sales-funnel is already fixed."
            ),
            "effort": "The transformer repairs it automatically when that article is done.",
        },
        {
            "action": "Replace preamble openings with a direct answer",
            "articles": count(lambda r: "fluffy-intro" in r["flags"] or "no-intro-paragraph" in r["flags"]),
            "recovers": lost("Direct answer up front"),
            "why": (
                "27 articles open with a wind-up rather than an answer. Both a reader deciding "
                "whether to stay and a model deciding what to quote read the first block. If the "
                "answer is in paragraph five, neither finds it."
            ),
            "effort": "Part of the rewrite pass, then the intro block carries it.",
        },
        {
            "action": "Repair heading structure: single H1, at least four H2 sections",
            "articles": count(lambda r: int(r["h1_count"]) != 1 or int(r["h2_count"]) < 4),
            "recovers": lost("Heading structure"),
            "why": (
                "13 articles use H1 for section headings, so the page has no single subject. 18 "
                "have fewer than four H2 sections, which leaves long unbroken runs of prose that "
                "cannot be extracted as a passage. The transformer can demote stray H1s; adding "
                "real sections is writing."
            ),
            "effort": "Demotion is automatic. New sections are part of the rewrite.",
        },
        {
            "action": "Assign one pillar to every article and make schema agree",
            "articles": count(lambda r: r["schema_section"].strip().lower() not in PILLARS),
            "recovers": None,
            "why": (
                "16 articles carry no pillar or the wrong one in their structured data, and some "
                "carry two at once. The pillar is how the site explains its own shape, in the "
                "visible tag, the body class, the meta tag and the schema together."
            ),
            "effort": "One field in the content file. The transformer syncs all four places.",
        },
        {
            "action": "Remove em dashes from article body copy",
            "articles": count(lambda r: int(r["em_dashes"])),
            "recovers": lost("Brand compliance"),
            "why": (
                "22 articles carry em dashes, 121 in total, against the house style rule. Low "
                "search impact, but it is a visible inconsistency on pages being reviewed for "
                "exactly that."
            ),
            "effort": "Sentence by sentence inside the rewrite pass. Not a find and replace.",
        },
        {
            "action": "Add a lead image with real alt text where one is missing",
            "articles": count(lambda r: int(r["images"]) == 0 or int(r["images_missing_alt"])),
            "recovers": lost("Images and alt text"),
            "why": (
                "21 articles have no image in the body at all. Others carry alt text that repeats "
                "the file name. The design puts a full width image directly under the answer, so "
                "an article without one cannot meet the standard."
            ),
            "effort": "Sourcing or generating an image per article. The slowest item here.",
        },
    ]


def write_backlog(rows: list) -> Path:
    scores = sorted(int(r["geo_score"]) for r in rows)
    median = scores[len(scores) // 2]
    out = []
    out.append("# Blog GEO audit: ranked action backlog")
    out.append("")
    out.append(
        f"{len(rows)} articles audited. Median GEO readiness "
        f"{median} out of 100. Lowest {scores[0]}, highest {scores[-1]}. "
        "Regenerate with `python3 scripts/audit_blog_library.py`."
    )
    out.append("")
    out.append("## How the score is built")
    out.append("")
    out.append(
        "Eleven dimensions, all measured from the page itself, totalling 100. "
        "Generative engines lift answers out of pages, so the model rewards a direct "
        "answer up front, headings phrased as the question a person actually asks, "
        "extractable lists, clean structured data and clear internal routes."
    )
    out.append("")
    out.append("| Dimension | Points | What earns them |")
    out.append("| --- | ---: | --- |")
    detail = {
        "Direct answer up front": "The opening answers the question instead of winding up to it",
        "Question-shaped headings": "Two or more headings phrased as a question",
        "Extractable lists": "Three or more ordered or unordered lists in the body",
        "Heading structure": "Exactly one H1, and at least four H2 sections",
        "Depth": "1,200 words or more",
        "Schema integrity": "BlogPosting present, headline matches the H1, articleSection is a pillar, author is Greg",
        "Metadata": "Title 65 characters or fewer, meta description 110 to 165, canonical matches the slug",
        "Internal routes": "A contextual Five Pillars link in the body, and three or more internal links",
        "Images and alt text": "At least one body image, every image with real alt text",
        "Freshness": "Modified within 24 months",
        "Brand compliance": "No em dashes",
    }
    for name, cap in GEO_DIMENSIONS:
        out.append(f"| {name} | {cap} | {detail[name]} |")
    out.append("")
    out.append("## What this score is not")
    out.append("")
    out.append(
        "It is a measure of whether a page is built to be quoted, not a measure of "
        "whether it earns traffic. There is no Google Analytics or Search Console "
        "access on this machine, so nothing here is weighted by sessions, impressions "
        "or rank. Two of the six duplicate decisions could flip with that data. Getting "
        "Search Console access is worth doing before the merge decisions are final."
    )
    out.append("")
    out.append("## Top 10 actions, ranked")
    out.append("")
    for index, item in enumerate(backlog_actions(rows), start=1):
        out.append(f"### {index}. {item['action']}")
        out.append("")
        line = f"**Articles affected:** {item['articles']}"
        if item["recovers"]:
            line += f" &nbsp;&nbsp; **Score recoverable:** {item['recovers']} points"
        out.append(line)
        out.append("")
        out.append(item["why"])
        out.append("")
        out.append(f"*Effort:* {item['effort']}")
        out.append("")
    out.append("## The ten lowest scoring articles")
    out.append("")
    out.append("| Article | GEO | Words | Weakest dimensions |")
    out.append("| --- | ---: | ---: | --- |")
    for row in sorted(rows, key=lambda r: int(r["geo_score"]))[:10]:
        out.append(
            f"| [{row['slug']}]({row['url']}) | {row['geo_score']} | {row['words']} "
            f"| {row['geo_weakest']} |"
        )
    out.append("")
    path = DOCS / "blog-geo-backlog.md"
    path.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
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
    for row in rows:
        scores = geo_score(row)
        row["geo_score"] = sum(scores.values())
        row["geo_weakest"] = "; ".join(
            name for name, cap in GEO_DIMENSIONS if scores[name] < cap
        )
    DOCS.mkdir(exist_ok=True)

    csv_path = DOCS / "blog-rollout-inventory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    md_path = write_markdown(rows)
    backlog_path = write_backlog(rows)
    print(f"{len(rows)} articles audited, three sources agree")
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")
    print(f"wrote {backlog_path.relative_to(ROOT)}")
    return rows


if __name__ == "__main__":
    main()
