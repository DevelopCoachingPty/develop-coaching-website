#!/usr/bin/env python3
"""Apply the shared Develop Coaching blog design system to an article.

One transformer, one shared stylesheet, one content file per article. The
design lives here; the words live in content/blog-system/<slug>.json so no two
articles ever carry the same copy.

    python3 scripts/blog_design_system.py construction-sales-funnel
    python3 scripts/blog_design_system.py --all
    python3 scripts/blog_design_system.py --all --check   # no writes

Every transform is idempotent: owned blocks are removed before being inserted,
so running twice produces no drift. Every anchor is fail-closed: a missing
anchor raises rather than writing a half-transformed page.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
CONTENT = ROOT / "content" / "blog-system"
SITE = "https://develop-coaching.com"

PILLARS = ("Plan", "Attract", "Convert", "Deliver", "Scale")

STYLE_ID = "dc-article-system-styles"
HERO_ID = "dc-article-hero-subtitle"
INTRO_ID = "dc-article-intro"
BRIEF_ID = "dc-article-brief"


# --------------------------------------------------------------------------
# The shared stylesheet. Identical on every article. Change it here once.
# --------------------------------------------------------------------------

STYLES = """<style id="%s">
.dc-article-hero-subtitle{max-width:680px;margin:16px 0 0!important;color:#fff;font-size:clamp(17px,2vw,22px)!important;font-weight:600;line-height:1.45;text-shadow:0 2px 4px rgba(0,0,0,.35)}
.dc-article-intro{margin:0 0 38px}
.dc-article-intro__answer{margin:0 0 24px!important;padding:18px 22px;border-left:6px solid #f6c944;background:#f5f3ec;color:#25262a;font-size:20px;font-weight:700;line-height:1.5}
.dc-article-intro img{display:block;width:100%%;height:auto;margin:0 0 24px}
.dc-article-intro__roadmap{margin:0!important;font-size:18px;line-height:1.65}
.dc-article-brief{--ink:#25262a;--paper:#f5f3ec;--signal:#f6c944;--blue:#087f86;margin:56px 0;padding:0;background:var(--paper);border:1px solid #d9d5c9;box-shadow:8px 8px 0 var(--ink);color:var(--ink);overflow:hidden}
.dc-article-brief *{box-sizing:border-box}
.dc-article-brief__header{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:end;padding:32px;background:var(--ink);color:#fff;border-bottom:8px solid var(--signal)}
.dc-article-brief__eyebrow{margin:0 0 10px!important;color:var(--signal);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px!important;font-weight:800;letter-spacing:.15em;text-transform:uppercase}
.dc-article-brief h2{margin:0!important;color:#fff!important;font-size:clamp(30px,4vw,48px)!important;line-height:1.02!important;letter-spacing:-.03em}
.dc-article-brief__stamp{min-width:140px;padding:12px 16px;border:2px solid var(--signal);color:var(--signal);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:800;letter-spacing:.1em;text-align:center;text-transform:uppercase;transform:rotate(2deg)}
.dc-article-brief__body{padding:32px}
.dc-article-brief__intro{max-width:760px;margin:0 0 30px!important;font-size:18px;line-height:1.65}
.dc-article-brief__grid{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:24px}
.dc-article-brief__panel{padding:24px;background:#fff;border-top:5px solid var(--blue)}
.dc-article-brief__panel h3{margin:0 0 12px!important;color:var(--ink)!important;font-size:24px!important;line-height:1.15!important}
.dc-article-brief__panel p{margin:0 0 16px!important}
.dc-article-brief__panel p:last-child{margin-bottom:0!important}
.dc-article-brief__steps{margin:18px 0 0!important;padding:0!important;list-style:none!important;counter-reset:dc-step}
.dc-article-brief__steps li{position:relative;margin:0!important;padding:0 0 18px 42px;counter-increment:dc-step}
.dc-article-brief__steps li:before{content:counter(dc-step);position:absolute;left:0;top:-2px;width:28px;height:28px;display:grid;place-items:center;background:var(--signal);border:2px solid var(--ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:900}
.dc-article-brief__steps li:not(:last-child):after{content:"";position:absolute;left:13px;top:28px;bottom:0;border-left:2px dashed var(--blue)}
.dc-article-brief__review{margin:24px 0 0;padding:20px 24px;background:var(--signal);border-left:8px solid var(--ink)}
.dc-article-brief__review strong{display:block;margin-bottom:4px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase}
.dc-article-brief__link{display:inline-block;margin-top:22px;padding:13px 17px;background:var(--ink);color:#fff!important;font-weight:800;text-decoration:none!important;box-shadow:4px 4px 0 var(--blue)}
.dc-article-brief__link:hover,.dc-article-brief__link:focus-visible{background:var(--blue)}
.dc-article-brief__link:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
@media(max-width:767px){.dc-article-hero-subtitle{font-size:16px!important}.dc-article-intro__answer{padding:16px 18px;font-size:18px}.dc-article-brief{margin:38px 0;box-shadow:5px 5px 0 var(--ink)}.dc-article-brief__header{grid-template-columns:1fr;padding:24px}.dc-article-brief__stamp{justify-self:start;min-width:0}.dc-article-brief__body{padding:20px}.dc-article-brief__grid{grid-template-columns:1fr}.dc-article-brief__panel{padding:20px}}
</style>""" % STYLE_ID


# --------------------------------------------------------------------------
# Block builders
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def build_hero(spec: dict) -> str:
    return (
        f'<p class="dc-article-hero-subtitle" id="{HERO_ID}">'
        f'{esc(spec["hero_subtitle"])}</p>'
    )


def build_intro(spec: dict) -> str:
    intro = spec["intro"]
    parts = [
        f'<div class="dc-article-intro" id="{INTRO_ID}">',
        f'  <p class="dc-article-intro__answer">{esc(intro["answer"])}</p>',
    ]
    image = intro.get("image")
    if image:
        parts.append(
            '  <img fetchpriority="high" decoding="async" '
            f'src="{esc(image["src"])}" alt="{esc(image["alt"])}" '
            f'width="{int(image["width"])}" height="{int(image["height"])}" />'
        )
    parts.append(
        f'  <p class="dc-article-intro__roadmap">{esc(intro["roadmap"])}</p>'
    )
    parts.append("</div>")
    return "\n".join(parts)


def build_brief(spec: dict) -> str:
    brief = spec["briefing"]
    title_id = f"{BRIEF_ID}-title"
    panels = []
    for panel in brief["panels"]:
        block = [
            '      <article class="dc-article-brief__panel">',
            f'        <h3>{esc(panel["heading"])}</h3>',
        ]
        for paragraph in panel.get("paragraphs", []):
            block.append(f"        <p>{esc(paragraph)}</p>")
        if panel.get("steps"):
            block.append('        <ol class="dc-article-brief__steps">')
            for step in panel["steps"]:
                block.append(f"          <li>{esc(step)}</li>")
            block.append("        </ol>")
        block.append("      </article>")
        panels.append("\n".join(block))

    review = brief["review"]
    cta = brief["cta"]
    return "\n".join(
        [
            f'<section class="dc-article-brief" id="{BRIEF_ID}" aria-labelledby="{title_id}">',
            '  <header class="dc-article-brief__header">',
            "    <div>",
            f'      <p class="dc-article-brief__eyebrow">{esc(brief["eyebrow"])}</p>',
            f'      <h2 id="{title_id}">{esc(brief["title"])}</h2>',
            "    </div>",
            f'    <div class="dc-article-brief__stamp">{esc(spec["pillar"])} pillar</div>',
            "  </header>",
            '  <div class="dc-article-brief__body">',
            f'    <p class="dc-article-brief__intro">{esc(brief["intro"])}</p>',
            '    <div class="dc-article-brief__grid">',
            *panels,
            "    </div>",
            f'    <p class="dc-article-brief__review"><strong>{esc(review["label"])}</strong> '
            f'{esc(review["text"])}</p>',
            f'    <a class="dc-article-brief__link" href="{esc(cta["href"])}">{esc(cta["text"])}</a>',
            "  </div>",
            "</section>",
        ]
    )


# --------------------------------------------------------------------------
# Page transforms. Each one is idempotent and fail-closed.
# --------------------------------------------------------------------------


def replace_once(document: str, pattern: str, replacement: str, what: str) -> str:
    document, count = re.subn(pattern, replacement, document, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"{what}: anchor not found")
    return document


def update_head(document: str, spec: dict) -> str:
    title = spec["title"]
    description = spec["meta_description"]
    modified = spec["date_modified"]
    canonical = f"{SITE}/{spec['slug']}/"

    found = re.search(r'<link rel="canonical" href="([^"]*)"', document)
    if not found:
        raise ValueError("canonical link missing")
    if found.group(1).rstrip("/") != canonical.rstrip("/"):
        raise ValueError(
            f"canonical mismatch: page says {found.group(1)}, expected {canonical}"
        )

    pairs = (
        (r"<title>.*?</title>", f"<title>{esc(title)}</title>", "title tag"),
        (
            r'(<meta name="description" content=")[^"]*(")',
            rf"\g<1>{esc(description)}\g<2>",
            "meta description",
        ),
        (
            r'(<meta property="og:title" content=")[^"]*(")',
            rf"\g<1>{esc(title)}\g<2>",
            "og:title",
        ),
        (
            r'(<meta property="og:description" content=")[^"]*(")',
            rf"\g<1>{esc(description)}\g<2>",
            "og:description",
        ),
        (
            r'(<meta name="twitter:title" content=")[^"]*(")',
            rf"\g<1>{esc(title)}\g<2>",
            "twitter:title",
        ),
        (
            r'(<meta name="twitter:description" content=")[^"]*(")',
            rf"\g<1>{esc(description)}\g<2>",
            "twitter:description",
        ),
        (
            r'(<meta property="article:section" content=")[^"]*(")',
            rf"\g<1>{spec['pillar']}\g<2>",
            "article:section",
        ),
        (
            r'(<meta property="og:updated_time" content=")[^"]*(")',
            rf"\g<1>{modified}\g<2>",
            "og:updated_time",
        ),
        (
            r'(<meta property="article:modified_time" content=")[^"]*(")',
            rf"\g<1>{modified}\g<2>",
            "article:modified_time",
        ),
    )
    for pattern, replacement, what in pairs:
        document = replace_once(document, pattern, replacement, what)

    style_pattern = rf'<style id="{STYLE_ID}">.*?</style>'
    if re.search(style_pattern, document, re.DOTALL):
        document = replace_once(document, style_pattern, STYLES, "shared stylesheet")
    else:
        if "</head>" not in document:
            raise ValueError("no </head> to insert the stylesheet into")
        document = document.replace("</head>", STYLES + "\n</head>", 1)
    return document


def update_schema(document: str, spec: dict) -> str:
    pattern = re.compile(
        r'(<script type="application/ld\+json" class="rank-math-schema-pro">)(.*?)(</script>)',
        re.DOTALL,
    )
    match = pattern.search(document)
    if not match:
        raise ValueError("Rank Math schema block not found")
    schema = json.loads(match.group(2))
    graph = schema.get("@graph", [])
    if not graph:
        raise ValueError("schema @graph is empty")

    title = spec["title"]
    description = spec["meta_description"]
    pillar = spec["pillar"]
    modified = spec["date_modified"]
    page_url = f"{SITE}/{spec['slug']}/"

    saw_blogposting = False
    for node in graph:
        node_type = node.get("@type")
        if node_type == "BreadcrumbList":
            items = node.get("itemListElement", [])
            if len(items) >= 3:
                items[1]["item"] = {
                    "@id": f"{SITE}/category/{pillar.lower()}/",
                    "name": pillar,
                }
                items[-1].setdefault("item", {})
                if isinstance(items[-1]["item"], dict):
                    items[-1]["item"]["name"] = title
        elif node_type == "WebPage":
            node["name"] = title
            node["description"] = description
            node["dateModified"] = modified
            node["@id"] = node.get("@id", page_url)
        elif node_type == "BlogPosting":
            saw_blogposting = True
            node["headline"] = title
            node["name"] = title
            node["description"] = description
            node["articleSection"] = pillar
            node["dateModified"] = modified
    if not saw_blogposting:
        raise ValueError("no BlogPosting node in schema")

    schema["@graph"] = graph
    body = json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
    return document[: match.start()] + match.group(1) + body + match.group(3) + document[match.end() :]


def update_visible_category(document: str, spec: dict) -> str:
    pillar = spec["pillar"]
    document = replace_once(
        document,
        r'<span class="elementor-post-info__terms-list">.*?</span>',
        '<span class="elementor-post-info__terms-list">\n'
        f'<a href="/category/{pillar.lower()}/" class="elementor-post-info__terms-list-item">{pillar}</a>\n'
        "</span>",
        "visible category list",
    )
    body_class = re.search(r'(<body[^>]*\bclass=")([^"]*)(")', document)
    if not body_class:
        raise ValueError("body class attribute not found")
    classes = [
        c
        for c in body_class.group(2).split()
        if not c.startswith("category-")
    ]
    classes.append(f"category-{pillar.lower()}")
    return (
        document[: body_class.start()]
        + body_class.group(1)
        + " ".join(classes)
        + body_class.group(3)
        + document[body_class.end() :]
    )


def update_h1_and_hero(document: str, spec: dict) -> str:
    h1_pattern = r'(<h1 class="elementor-heading-title elementor-size-default">).*?(</h1>)'
    document = replace_once(
        document, h1_pattern, rf"\g<1>{esc(spec['h1'])}\g<2>", "post title h1"
    )
    hero_pattern = rf'\s*<p class="dc-article-hero-subtitle" id="{HERO_ID}">.*?</p>'
    document = re.sub(hero_pattern, "", document, flags=re.DOTALL)
    h1 = re.search(h1_pattern, document, re.DOTALL)
    insert_at = h1.end()
    return document[:insert_at] + "\n" + build_hero(spec) + document[insert_at:]


DIV_RE = re.compile(r"<div\b[^>]*>|</div>", re.I)
WIDGET_RE = re.compile(r'data-widget_type="theme-post-content\.default"[^>]*>')
TAG_RE = re.compile(r"<[^>]+>")


BROKEN_ANCHOR = re.compile(r"(<a\b[^>]*>)</p>\s*<p>\s*</a>")


def repair_broken_anchors(document: str) -> str:
    """Close anchors that WordPress left open with a stray </p>.

    An anchor closed by </p> is never closed at all: the parser adopts the rest
    of the article into the link, so the whole body renders in link colour and
    every paragraph becomes a tab stop. Two live articles carry this.
    """
    return BROKEN_ANCHOR.sub(r"\1</a>", document)


def body_span(document: str) -> tuple:
    """(start, end) of the post-content widget, matched by div depth."""
    match = WIDGET_RE.search(document)
    if not match:
        raise ValueError("post content widget not found")
    start = match.end()
    depth = 0
    for token in DIV_RE.finditer(document, start):
        if token.group(0).startswith("</"):
            if depth == 0:
                return start, token.start()
            depth -= 1
        else:
            depth += 1
    raise ValueError("post content widget is not closed")


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", fragment))).strip()


def demote_body_h1s(document: str, spec: dict) -> str:
    """Section headings marked up as h1 break the one-h1 rule. Opt in per article."""
    if not spec.get("demote_body_h1", False):
        return document
    start, end = body_span(document)
    body = document[start:end]
    body = re.sub(r"<h1(\s[^>]*)?>", lambda m: f"<h2{m.group(1) or ''}>", body)
    body = body.replace("</h1>", "</h2>")
    return document[:start] + body + document[end:]


def drop_duplicate_lead_image(body: str, spec: dict) -> str:
    """The intro block owns the lead image. Remove the article's own copy of it."""
    image = spec["intro"].get("image")
    if not image:
        return body
    src = re.escape(image["src"])
    owned = re.compile(rf'<div class="dc-article-intro" id="{INTRO_ID}">.*?</div>', re.DOTALL)
    match = owned.search(body)
    if not match:
        return body
    strays = (
        re.compile(rf'\s*<figure\b[^>]*>(?:(?!</figure>).)*?<img\b[^>]*src="{src}"[^>]*>.*?</figure>',
                   re.IGNORECASE | re.DOTALL),
        re.compile(rf'\s*<p[^>]*>\s*<img\b[^>]*src="{src}"[^>]*>\s*</p>', re.IGNORECASE),
    )
    head, tail = body[: match.end()], body[match.end() :]
    for stray in strays:
        tail = stray.sub("", tail)
    return head + tail


def update_intro(document: str, spec: dict) -> str:
    """Replace the opening paragraphs with the direct-answer intro block."""
    start, end = body_span(document)
    body = document[start:end]
    block = build_intro(spec)

    owned = re.compile(rf'<div class="dc-article-intro" id="{INTRO_ID}">.*?</div>', re.DOTALL)
    if owned.search(body):
        body = owned.sub(block, body, count=1)
        body = drop_duplicate_lead_image(body, spec)
        return document[:start] + body + document[end:]

    count = int(spec.get("intro_replaces_paragraphs", 2))
    if count < 1:
        raise ValueError("intro_replaces_paragraphs must be at least 1")
    search_from = 0
    heading_start = None
    drop_heading = spec.get("intro_removes_heading")
    if drop_heading:
        for match in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.DOTALL):
            if text_of(match.group(0)).casefold() == drop_heading.strip().casefold():
                heading_start, search_from = match.start(), match.end()
                break
        if heading_start is None:
            raise ValueError(f"intro_removes_heading {drop_heading!r} not found")

    spans = [
        (m.start(), m.end())
        for m in re.finditer(r"<p[^>]*>.*?</p>", body[search_from:], re.DOTALL)
        if len(text_of(m.group(0))) > 60
    ]
    spans = [(a + search_from, b + search_from) for a, b in spans]
    if len(spans) < count:
        raise ValueError(
            f"only {len(spans)} substantial opening paragraphs, "
            f"intro_replaces_paragraphs is {count}"
        )
    first = heading_start if heading_start is not None else spans[0][0]
    last = spans[count - 1][1]
    body = body[:first] + block + body[last:]
    body = drop_duplicate_lead_image(body, spec)
    return document[:start] + body + document[end:]


def update_brief(document: str, spec: dict) -> str:
    """Place the practical briefing high in the article, before a named heading."""
    start, end = body_span(document)
    body = document[start:end]

    owned = re.compile(rf'<section class="dc-article-brief" id="{BRIEF_ID}".*?</section>\s*', re.DOTALL)
    body = owned.sub("", body)

    anchor = spec["brief_before_heading"].strip()
    target = None
    for match in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.DOTALL):
        if text_of(match.group(0)).casefold() == anchor.casefold():
            target = match
            break
    if target is None:
        headings = [text_of(m.group(0)) for m in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.DOTALL)]
        raise ValueError(
            f"brief_before_heading {anchor!r} not found. Headings present: {headings}"
        )
    block = build_brief(spec)
    body = body[: target.start()] + block + "\n" + body[target.start() :]
    return document[:start] + body + document[end:]


def transform(document: str, spec: dict) -> str:
    document = repair_broken_anchors(document)
    document = update_head(document, spec)
    document = update_schema(document, spec)
    document = update_visible_category(document, spec)
    document = update_h1_and_hero(document, spec)
    document = demote_body_h1s(document, spec)
    document = update_intro(document, spec)
    document = update_brief(document, spec)
    return document


# --------------------------------------------------------------------------
# Validation of the content file before anything touches a page
# --------------------------------------------------------------------------

REQUIRED = ("slug", "pillar", "title", "meta_description", "h1", "hero_subtitle",
            "intro", "briefing", "brief_before_heading", "date_modified")


def validate(spec: dict, path: Path) -> None:
    missing = [key for key in REQUIRED if key not in spec]
    if missing:
        raise ValueError(f"{path.name}: missing keys {missing}")
    if spec["pillar"] not in PILLARS:
        raise ValueError(f"{path.name}: pillar must be one of {PILLARS}")
    if len(spec["title"]) > 65:
        raise ValueError(f"{path.name}: title is {len(spec['title'])} chars, keep it to 65")
    if not 110 <= len(spec["meta_description"]) <= 165:
        raise ValueError(
            f"{path.name}: meta description is {len(spec['meta_description'])} chars, "
            "keep it between 110 and 165"
        )
    cta = spec["briefing"]["cta"]["href"]
    if not cta.startswith("/5-pillars-free-trainings/"):
        raise ValueError(f"{path.name}: briefing CTA must link to a Five Pillars page")
    if cta.rstrip("/").rsplit("/", 1)[-1] != spec["pillar"].lower():
        raise ValueError(
            f"{path.name}: briefing CTA {cta} does not match pillar {spec['pillar']}"
        )
    for field in ("title", "meta_description", "h1", "hero_subtitle"):
        if "\u2014" in spec[field]:
            raise ValueError(f"{path.name}: {field} contains an em dash")
    panels = spec["briefing"]["panels"]
    if not 1 <= len(panels) <= 2:
        raise ValueError(f"{path.name}: briefing needs one or two panels, got {len(panels)}")


def load(slug: str) -> dict:
    path = CONTENT / f"{slug}.json"
    if not path.exists():
        raise SystemExit(f"No content file at {path.relative_to(ROOT)}")
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec.setdefault("slug", slug)
    if spec["slug"] != slug:
        raise ValueError(f"{path.name}: slug field says {spec['slug']!r}")
    validate(spec, path)
    return spec


def apply(slug: str, check_only: bool) -> bool:
    page = WWW / slug / "index.html"
    if not page.exists():
        raise SystemExit(f"No page at {page.relative_to(ROOT)}")
    spec = load(slug)
    original = page.read_text(encoding="utf-8")
    updated = transform(original, spec)
    twice = transform(updated, spec)
    if twice != updated:
        raise SystemExit(f"{slug}: transform is not idempotent, refusing to write")
    if check_only:
        print(f"{slug}: ok, {'no change' if updated == original else 'would change'}")
        return updated != original
    if updated == original:
        print(f"{slug}: already current")
        return False
    page.write_text(updated, encoding="utf-8")
    print(f"{slug}: updated")
    return True


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slugs", nargs="*", help="article slugs to transform")
    parser.add_argument("--all", action="store_true", help="every article with a content file")
    parser.add_argument("--check", action="store_true", help="validate and transform without writing")
    args = parser.parse_args(argv)

    slugs = args.slugs
    if args.all:
        slugs = sorted(p.stem for p in CONTENT.glob("*.json"))
    if not slugs:
        parser.error("give at least one slug, or --all")

    changed = 0
    for slug in slugs:
        changed += bool(apply(slug, args.check))
    print(f"\n{len(slugs)} article(s) processed, {changed} changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
