#!/usr/bin/env python3
"""Link a published article from the blog, its category hub, and related posts.

publish_page.py writes the article, the sitemap and the search index, then
stops. /blog/ and the category hubs are frozen Elementor lists, so a new
article is an orphan until something links to it. This module adds those
links without rewriting the article body or touching funnel pages:

  * a "Latest articles" list on www/blog/index.html
  * a "Latest {Category} articles" list on the matching category hub,
    placed before the Elementor archive widget
  * a "Related articles" aside on 3 or 4 existing posts

Links are root-relative (/slug/ only). Running the linker again is a no-op.

    python3 scripts/link_published_article.py          # JSON plan, writes nothing
    python3 scripts/link_published_article.py --apply  # link the 18 Nov 2026 orphans
"""
import argparse
import html as htmllib
import json
import re
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUM_RE = re.compile(r"^\d+[a-z]?$")
FUNNEL = frozenset({
    "free-trainings",
    "sell-your-construction-company",
    "fill-the-order-book",
    "double-your-profits-workshop",
    "5-profit-leaks-workshop",
    "webinar",
    "win-big-clients",
    "win-big-clients-webinar",
    "free-book-download",
    "book-download",
    "download-book-form",
    "uk-cost-guide",
    "uk-cost-guide-download",
    "aus-cost-guide-download",
    "the-schedule-page",
    "the-schedule-page-subscribers",
    "event-booking",
    "fire-figure",
    "greg-testimonial",
    "greg-wilkes-media",
})
# Audited orphans from the 18 Nov 2026 crawl. Applied oldest published date first.
ORPHAN_SLUGS = (
    "markup-vs-margin",
    "retention-in-construction",
    "construction-kpis",
    "construction-cash-flow-forecast",
    "construction-job-costing",
    "construction-cost-estimating",
    "construction-programme",
    "construction-company-structure",
    "construction-risk-management",
    "construction-marketing-plan",
    "managing-subcontractors-on-site",
    "snagging-list",
    "design-and-build-contractor",
)
# "system"/"systems" and "plan" stay significant. "time" is handled separately.
IGNORE = frozenset("""
a an the and or of to for in on with your how from vs uk past over into that
this what when which who why its it you our their them than then not just more
most very can will are is be as at by per without within across about off out
up down do does did done doing get got getting make made making use using used
need needs keep already let lets stop real good best key steps weekly yearly
take taking run running manage management pay paying win winning work losing
month blueprint protect control practical complete guide scale scaling grow
growing growth numbers number way ways area areas tips tip proven expert advice
basics small big large construction company companies business builder builders
building build firms firm list
""".split())
TOPIC = {
    "markup": {"margin", "profit", "pricing", "price", "costing", "estimating", "quote", "quotes"},
    "margin": {"markup", "profit", "pricing", "price", "profits"},
    "retention": {"cash", "payment", "profit", "flow", "accounting"},
    "kpis": {"performance", "goals", "scorecard", "track"},
    "kpi": {"performance", "goals", "scorecard", "track"},
    "cash": {"flow", "forecast", "profit", "accounting", "retention", "payment"},
    "forecast": {"cash", "flow", "accounting", "profit"},
    "costing": {"pricing", "price", "estimating", "job", "margin", "quotes"},
    "estimating": {"pricing", "price", "tendering", "tender", "costing", "quotes", "job"},
    "programme": {"project", "projects", "time", "site", "schedule", "scheduling"},
    "structure": {"delegation", "hiring", "recruit", "roles", "organise", "team", "systems"},
    "risk": {"contracts", "contract", "site", "snagging", "project", "margin", "handover"},
    "marketing": {"lead", "leads", "clients", "brand", "branding", "social", "strategy"},
    "subcontractors": {"subcontractor", "site", "project", "contracts", "tradesmen", "delegation"},
    "snagging": {"handover", "site", "project", "defects", "risk"},
    "design": {"contracts", "tendering", "contractor", "risk"},
    "contractor": {"contracts", "tendering", "design", "contract"},
    "job": {"pricing", "costing", "price", "quotes", "estimating"},
    "pricing": {"price", "margin", "markup", "costing", "estimating", "quotes"},
    "price": {"pricing", "margin", "markup", "quotes"},
    "hiring": {"recruit", "recruitment", "workforce", "delegation"},
    "recruit": {"hiring", "recruitment", "workforce"},
}
SOURCE_CAP = 5
STYLE = """<style id="dc-published-links-style">
.dc-published-index,.dc-published-related{box-sizing:border-box;margin:0;padding:28px 20px;background:#F6F5F2;color:#25262a;font-family:"Source Sans Pro",Arial,sans-serif}
.dc-published-index ul,.dc-published-related ul{max-width:1120px;margin:0 auto;padding:0;list-style:none}
.dc-published-index h2,.dc-published-related h2{max-width:1120px;margin:0 auto 14px;color:#2C67AC;font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.dc-published-index a,.dc-published-related a{color:#25262a;font-weight:700;text-decoration:none}
.dc-published-index a:hover,.dc-published-related a:hover{color:#2C67AC}
.dc-published-index li,.dc-published-related li{margin:0;padding:10px 0;border-top:1px solid #E4E2DC}
.dc-published-index li:first-child,.dc-published-related li:first-child{border-top:0}
</style>"""

PAGE_CONTENT_RE = re.compile(
    r'<div\b(?=[^>]*\bclass="[^"]*\bpage-content\b)[^>]*>',
    re.I,
)
ARCHIVE_RE = re.compile(
    r'<div\b(?=[^>]*\bclass="[^"]*\belementor-widget-archive-posts\b)[^>]*>',
    re.I,
)
BOOK_RE = re.compile(r'<section\b[^>]*\bclass="[^"]*\bdc-book-award\b', re.I)
FOOTER_RE = re.compile(r"<footer\b", re.I)
BODY_END_RE = re.compile(r"</body>", re.I)
HEAD_END_RE = re.compile(r"</head>", re.I)
TITLE_SUFFIX_RE = re.compile(r"\s+[|\-]\s+Develop Coaching\s*$")


def refuse_slug(slug: str) -> None:
    """Reject path tricks, the other domain, and pages that must never be edited."""
    text = (slug or "").strip()
    lowered = text.lower()
    if "com.au" in lowered or "developcoaching" in lowered:
        raise SystemExit(f"link_published_article: refused {slug!r}")
    if not SLUG_RE.fullmatch(text) or text in FUNNEL:
        raise SystemExit(f"link_published_article: refused {slug!r}")


def category_hub(category: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (category or "").strip().lower()).strip("-")


def category_label(category: str) -> str:
    text = (category or "").strip()
    if not text:
        return ""
    if text == text.lower() or text == text.upper():
        return " ".join(part.capitalize() for part in text.split())
    return text


def normal_date(value) -> str:
    if not value:
        return ""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", str(value).strip())
    return match.group(1) if match else ""


def raw_tokens(text: str) -> frozenset:
    return frozenset(re.findall(r"[a-z0-9]+", (text or "").lower()))


def significant(text: str) -> frozenset:
    return frozenset(
        token for token in raw_tokens(text)
        if token not in IGNORE and not NUM_RE.match(token)
    )


def expand_slug(tokens: frozenset) -> frozenset:
    expanded = set(tokens)
    for token in tokens:
        expanded |= TOPIC.get(token, set())
    return frozenset(expanded)


def counted_overlap(left: frozenset, right: frozenset, candidate_slug_tokens: frozenset) -> frozenset:
    """Slug overlap. 'time' counts only for a candidate whose only real slug token is time."""
    overlap = set(left & right)
    if "time" in overlap and candidate_slug_tokens != frozenset({"time"}):
        overlap.discard("time")
    return frozenset(overlap)


def escape(text: str) -> str:
    return htmllib.escape(text or "", quote=True)


def sort_records(records):
    """Newest date first. Same date, alphabetical by slug."""
    rows = sorted(records, key=lambda row: row[0])
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows


def section_html(index_id: str, heading: str, records) -> str:
    heading_id = f"dc-published-{index_id}-title"
    lines = [
        f'<section class="dc-published-index" data-dc-published-index="{index_id}" aria-labelledby="{heading_id}">',
        f'<h2 id="{heading_id}">{escape(heading)}</h2>',
        "<ul>",
    ]
    for slug, date, title in sort_records(records):
        lines.append(
            f'<li data-dc-published-slug="{slug}" data-dc-published-date="{date}">'
            f'<a href="/{slug}/">{escape(title)}</a></li>'
        )
    lines.extend(["</ul>", "</section>"])
    return "\n".join(lines)


def aside_html(records) -> str:
    lines = [
        '<aside class="dc-published-related" data-dc-published-related aria-labelledby="dc-published-related-title">',
        '<h2 id="dc-published-related-title">Related articles</h2>',
        "<ul>",
    ]
    for slug, date, title in sort_records(records):
        lines.append(
            f'<li data-dc-related-slug="{slug}" data-dc-related-date="{date}">'
            f'<a href="/{slug}/">{escape(title)}</a></li>'
        )
    lines.extend(["</ul>", "</aside>"])
    return "\n".join(lines)


def ensure_style(html: str) -> str:
    if 'id="dc-published-links-style"' in html:
        return html
    match = HEAD_END_RE.search(html)
    if not match:
        raise SystemExit("link_published_article: closing head tag not found")
    return html[:match.start()] + STYLE + "\n" + html[match.start():]


def replace_section(html: str, index_id: str, section: str):
    pattern = re.compile(
        rf'<section\b[^>]*\bdata-dc-published-index="{re.escape(index_id)}"[^>]*>.*?</section>',
        re.S | re.I,
    )
    if pattern.search(html):
        return pattern.sub(lambda _match: section, html, count=1), True
    return html, False


def parse_section_items(html: str, index_id: str):
    pattern = re.compile(
        rf'<section\b[^>]*\bdata-dc-published-index="{re.escape(index_id)}"[^>]*>(.*?)</section>',
        re.S | re.I,
    )
    match = pattern.search(html)
    if not match:
        return None, {}
    body = match.group(1)
    heading_match = re.search(r"<h2\b[^>]*>(.*?)</h2>", body, re.S | re.I)
    heading = htmllib.unescape(re.sub(r"\s+", " ", heading_match.group(1))).strip() if heading_match else ""
    items = {}
    for item in re.finditer(r"<li\b[^>]*>", body, re.I):
        tag = item.group(0)
        slug_match = re.search(r'data-dc-published-slug="([^"]+)"', tag)
        date_match = re.search(r'data-dc-published-date="([^"]+)"', tag)
        if slug_match:
            items[slug_match.group(1)] = date_match.group(1) if date_match else ""
    return heading, items


def parse_related(html: str) -> dict:
    items = {}
    for item in re.finditer(r"<li\b[^>]*\bdata-dc-related-slug=\"([^\"]+)\"[^>]*>", html, re.I):
        tag = item.group(0)
        date_match = re.search(r'data-dc-related-date="([^"]+)"', tag)
        items[item.group(1)] = date_match.group(1) if date_match else ""
    return items


class Page:
    def __init__(self, slug, title, date, hub, label):
        self.slug = slug
        self.title = title
        self.date = date
        self.hub = hub
        self.label = label
        self.slug_tokens = significant(slug)
        self.raw_slug_tokens = raw_tokens(slug)
        self.expanded = expand_slug(self.slug_tokens)
        self.title_tokens = significant(title)


def read_title(html: str, slug: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if not match:
        return slug.replace("-", " ")
    title = htmllib.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
    return TITLE_SUFFIX_RE.sub("", title).strip() or slug.replace("-", " ")


def read_published_date(html: str) -> str:
    match = re.search(r'<meta property="article:published_time" content="([^"]+)"', html)
    return normal_date(match.group(1) if match else "")


def read_category(html: str):
    """Prefer the visible category chip. article:section is stale on several posts."""
    match = re.search(
        r'href="/category/([^"/]+)/" class="elementor-post-info__terms-list-item">([^<]*)</a>',
        html,
    )
    if match:
        return match.group(1).strip().lower(), htmllib.unescape(match.group(2)).strip()
    match = re.search(r'<meta property="article:section" content="([^"]*)"', html)
    if not match:
        return "", ""
    label = htmllib.unescape(match.group(1)).strip()
    return category_hub(label), category_label(label)


class Library:
    def __init__(self, www):
        self.www = Path(www)
        self.html = {}
        self.dirty = set()
        self.pages = {}
        self.sitemap_dates = {}
        self.blog_items = {}
        self.hub_items = {}
        self.hub_headings = {}
        self.related = {}
        self._load()

    def read(self, path: Path) -> str:
        key = str(path)
        if key not in self.html:
            self.html[key] = path.read_text(encoding="utf-8")
        return self.html[key]

    def remember(self, path: Path, html: str) -> None:
        self.html[str(path)] = html
        self.dirty.add(path)

    def _load(self) -> None:
        sitemap = self.www / "post-sitemap.xml"
        slugs = []
        if sitemap.is_file():
            text = sitemap.read_text(encoding="utf-8")
            for loc, lastmod in re.findall(
                r"<loc>https://develop-coaching.com/([^/<]+)/</loc>(?:\s*<lastmod>([^<]*)</lastmod>)?",
                text,
            ):
                slugs.append(loc)
                if lastmod:
                    self.sitemap_dates[loc] = normal_date(lastmod)
        for slug in slugs:
            if slug in FUNNEL:
                continue
            path = self.www / slug / "index.html"
            if not path.is_file():
                continue
            self.pages[slug] = self._page(slug, self.read(path))
            related = parse_related(self.read(path))
            if related:
                self.related[slug] = dict(related)
        blog = self.www / "blog" / "index.html"
        self.has_blog = blog.is_file()
        if self.has_blog:
            _heading, items = parse_section_items(self.read(blog), "blog")
            self.blog_items = dict(items)
        if (self.www / "category").is_dir():
            for path in (self.www / "category").glob("*/index.html"):
                hub = path.parent.name
                if not SLUG_RE.fullmatch(hub):
                    continue
                heading, items = parse_section_items(self.read(path), f"category-{hub}")
                self.hub_items[hub] = dict(items)
                if heading:
                    self.hub_headings[hub] = heading

    def _page(self, slug: str, html: str) -> Page:
        hub, label = read_category(html)
        date = read_published_date(html) or self.sitemap_dates.get(slug, "")
        return Page(slug, read_title(html, slug), date, hub, label)

    def ensure_page(self, slug: str) -> Page:
        if slug not in self.pages:
            path = self.www / slug / "index.html"
            if not path.is_file():
                raise SystemExit(f"link_published_article: page not found: {slug}")
            self.pages[slug] = self._page(slug, self.read(path))
        return self.pages[slug]

    def source_allowed(self, slug: str) -> bool:
        if slug not in self.pages or slug in FUNNEL:
            return False
        match = re.fullmatch(r"(.+)-2", slug)
        return not (match and match.group(1) in self.pages)

    def title_of(self, slug: str) -> str:
        page = self.pages.get(slug)
        if page:
            return page.title
        path = self.www / slug / "index.html"
        if path.is_file():
            return read_title(self.read(path), slug)
        return slug.replace("-", " ")

    def date_of(self, slug: str, explicit=None) -> str:
        if explicit:
            return normal_date(explicit)
        page = self.pages.get(slug)
        if page and page.date:
            return page.date
        return self.sitemap_dates.get(slug, "")

    def records(self, items: dict):
        return [(slug, items[slug], self.title_of(slug)) for slug in items]

    def update_blog(self, slug: str, date: str) -> bool:
        path = self.www / "blog" / "index.html"
        if not path.is_file():
            return False
        html = self.read(path)
        self.blog_items[slug] = date or self.blog_items.get(slug, "")
        section = section_html("blog", "Latest articles", self.records(self.blog_items))
        html, replaced = replace_section(html, "blog", section)
        if not replaced:
            match = PAGE_CONTENT_RE.search(html)
            if not match:
                return False
            html = html[:match.end()] + "\n" + section + html[match.end():]
        self.remember(path, ensure_style(html))
        return True

    def update_hub(self, slug: str, date: str, hub: str, label: str):
        if not hub or not SLUG_RE.fullmatch(hub):
            return None
        path = self.www / "category" / hub / "index.html"
        if not path.is_file():
            return None
        html = self.read(path)
        index_id = f"category-{hub}"
        items = self.hub_items.setdefault(hub, {})
        items[slug] = date or items.get(slug, "")
        heading = self.hub_headings.get(hub) or f"Latest {label or hub.capitalize()} articles"
        self.hub_headings[hub] = heading
        section = section_html(index_id, heading, self.records(items))
        html, replaced = replace_section(html, index_id, section)
        if not replaced:
            match = ARCHIVE_RE.search(html)
            if not match:
                return None
            html = html[:match.start()] + section + "\n" + html[match.start():]
        self.remember(path, ensure_style(html))
        return hub

    def place_aside(self, html: str, aside: str) -> str:
        pattern = re.compile(
            r'<aside\b[^>]*\bdata-dc-published-related\b[^>]*>.*?</aside>',
            re.S | re.I,
        )
        if pattern.search(html):
            return pattern.sub(lambda _match: aside, html, count=1)
        for finder in (BOOK_RE, FOOTER_RE, BODY_END_RE):
            match = finder.search(html)
            if match:
                return html[:match.start()] + aside + "\n" + html[match.start():]
        raise SystemExit("link_published_article: no insertion point for related articles")

    def apply_related(self, source: str) -> None:
        if source in FUNNEL:
            raise SystemExit(f"link_published_article: refused {source!r}")
        path = self.www / source / "index.html"
        if not path.is_file():
            raise SystemExit(f"link_published_article: related source not found: {source}")
        items = self.related.get(source, {})
        aside = aside_html((slug, items[slug], self.title_of(slug)) for slug in items)
        html = ensure_style(self.place_aside(self.read(path), aside))
        self.remember(path, html)

    def incoming(self, slug: str):
        return sorted(source for source, items in self.related.items() if slug in items and source != slug)

    def room_for(self, source: str, target: str) -> bool:
        items = self.related.get(source, {})
        return target in items or len(items) < SOURCE_CAP

    def established(self, candidate: Page, target: Page) -> bool:
        if not candidate.date or not target.date:
            return True
        if candidate.date < target.date:
            return True
        return candidate.date == target.date and candidate.slug < target.slug

    def choose_sources(self, target: Page):
        existing = self.incoming(target.slug)
        if len(existing) >= 3:
            return existing
        selected = list(existing)
        candidates = [
            page for page in self.pages.values()
            if page.slug != target.slug and self.source_allowed(page.slug)
        ]

        def take(ranked, limit):
            for page in ranked:
                if len(selected) >= limit:
                    return
                if page.slug in selected or not self.room_for(page.slug, target.slug):
                    continue
                selected.append(page.slug)

        strong = []
        strong_slugs = set()
        for page in candidates:
            overlap = counted_overlap(target.expanded, page.expanded, page.slug_tokens)
            if not overlap:
                continue
            direct = counted_overlap(target.slug_tokens, page.slug_tokens, page.slug_tokens)
            strong.append((-len(overlap), -len(direct), page.date, page.slug, page))
            strong_slugs.add(page.slug)
        strong.sort()
        take([row[-1] for row in strong], 4)
        if len(selected) >= 3:
            return selected

        titled = []
        for page in candidates:
            if page.slug in strong_slugs:
                continue
            # Title tokens only. Expanded slug tokens stay in the strong pass.
            title_hit = counted_overlap(
                target.title_tokens, page.title_tokens | page.slug_tokens, page.slug_tokens
            ) | counted_overlap(target.slug_tokens, page.title_tokens, page.slug_tokens)
            if not title_hit:
                continue
            titled.append((-len(title_hit), page.date, page.slug, page))
        titled.sort()
        take([row[-1] for row in titled], 3)
        if len(selected) >= 3:
            return selected

        take(self.category_fillers(target, selected, established_only=True), 3)
        if len(selected) < 3:
            take(self.category_fillers(target, selected, established_only=False), 3)
        return selected

    def category_fillers(self, target: Page, selected, established_only: bool):
        """Same-category pages used only to reach 3 links.

        A page whose slug carries the hub name comes first. That is how
        construction-kpis, which has only two topical matches, is linked from
        construction-business-plan.
        """
        if not target.hub:
            return []
        ranked = []
        for page in self.pages.values():
            if page.slug == target.slug or page.slug in selected or page.hub != target.hub:
                continue
            if not self.source_allowed(page.slug):
                continue
            if established_only and not self.established(page, target):
                continue
            namesake = 0 if target.hub in page.raw_slug_tokens else 1
            ranked.append((namesake, page.date, page.slug, page))
        ranked.sort()
        return [row[-1] for row in ranked]

    def link(self, slug: str, title=None, category=None, date=None, write=True):
        refuse_slug(slug)
        page = self.ensure_page(slug)
        if title and str(title).strip():
            page.title = TITLE_SUFFIX_RE.sub("", str(title).strip()).strip()
        if category and str(category).strip():
            page.label = category_label(str(category))
            page.hub = category_hub(str(category))
        resolved_date = self.date_of(slug, date)
        if resolved_date:
            page.date = resolved_date
        blog = self.update_blog(slug, page.date)
        hub = self.update_hub(slug, page.date, page.hub, page.label or page.hub.capitalize())
        sources = self.choose_sources(page)
        for source in sources:
            self.related.setdefault(source, {})[slug] = page.date
            self.apply_related(source)
        if write:
            self.flush()
        return {"blog": blog, "hub": hub, "sources": sources}

    def flush(self) -> int:
        written = 0
        for path in list(self.dirty):
            text = self.html[str(path)]
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != text:
                path.write_text(text, encoding="utf-8")
                written += 1
        self.dirty.clear()
        return written

    def orphan_order(self, slugs):
        def key(slug):
            page = self.ensure_page(slug)
            return (page.date or "9999-99-99", slug)
        return sorted(slugs, key=key)


def link_published_article(www, slug, title=None, category=None, date=None):
    """Plan and write blog, category-hub, and related-post links for one article.

    If www/blog/index.html is missing, leave it missing and do not raise. A
    second call with the same articles writes nothing.
    """
    return Library(www).link(slug, title=title, category=category, date=date, write=True)


def plan_articles(www, slugs, write: bool):
    library = Library(www)
    articles = []
    for slug in library.orphan_order(slugs):
        result = library.link(slug, write=write)
        articles.append({"slug": slug, "hub": result["hub"], "sources": result["sources"]})
    return articles


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write links for the audited orphan articles")
    args = parser.parse_args(argv)
    www = Path(__file__).resolve().parents[1] / "www"
    articles = plan_articles(www, ORPHAN_SLUGS, write=bool(args.apply))
    print(json.dumps({"apply": bool(args.apply), "articles": articles}, indent=2))


if __name__ == "__main__":
    main()
