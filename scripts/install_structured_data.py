#!/usr/bin/env python3
"""Keep every page's JSON-LD (structured data) correct and in step with the page.

What it enforces, on every HTML page in www/ (the rules the GEO engine's weekly
Schema Sentinel checks, dc-company-os features/geo-engine/lib/jsonld.ts):

1. One Organization for Develop Coaching on every page, built only from facts
   the site itself shows (name, logo, footer social links, footer email, the
   legal name in the footer copyright, and the member-software differentiator
   stated on the homepage, the Mastermind page and the about page). The old
   WordPress (Rank Math) business
   node carried an empty address, a "Place" with no address, unverified opening
   hours and a phone number the site never shows; those are dropped.
2. No Person named with an email address. Those are the old WordPress users
   (staff and the former SEO agency) that Rank Math exported as page authors.
   They are removed and whatever pointed at them now points at the
   Organization, because those landing pages were not written by Greg. The one
   WordPress user that is Greg (/author/gregwilkes/) becomes Greg.
3. One canonical Person for Greg Wilkes (id /about-greg-wilkes/#person), with
   only facts the site states: name, his about page, "Founder" ("Greg Wilkes,
   founder of Develop Coaching") and his photo from that page. /about-greg-wilkes/
   is marked up as his ProfilePage.
4. FAQPage matches the FAQs the page actually shows. Questions and answers are
   read from the visible FAQ section (accordions, question headings, or bold
   question paragraphs). A page with a visible FAQ section gets an FAQPage; a
   page without one loses any stale FAQPage it carried.

Idempotent: a second run changes nothing. publish_page.py and
publish_designed_page.py run it on every page they write, so new and rebuilt
pages cannot bring the old patterns back.

    python3 scripts/install_structured_data.py            # apply to www/
    python3 scripts/install_structured_data.py --check    # report only, exit 1 if anything would change
    python3 scripts/install_structured_data.py --file www/<slug>/index.html [...]

Touches only www/. export/reference/ is the frozen input to build_site.py,
which must not be run, so it is left alone. No Review or AggregateRating is
ever added here.
"""
import copy
import html as htmllib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
SITE = "https://develop-coaching.com"
ORG_ID = f"{SITE}/#organization"
LOGO_ID = f"{SITE}/#logo"
LOGO = f"{SITE}/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg"
GREG_NAME = "Greg Wilkes"
GREG_URL = f"{SITE}/about-greg-wilkes/"
GREG_ID = f"{GREG_URL}#person"
# Older ids the site has used for Greg (set_article_author.py, WordPress).
GREG_ALIASES = {
    GREG_ID,
    f"{SITE}/#/schema/person/greg-wilkes",
    f"{SITE}/author/gregwilkes/",
    f"{SITE}/blog/author/gregwilkes/",
}
# Pages that are about Greg himself and must carry his full Person node.
GREG_PAGES = {GREG_URL}

# The footer links on every page (Facebook, LinkedIn, Instagram, YouTube).
# test_structured_data.py checks each one is really linked from the home page.
SAME_AS = [
    "https://www.facebook.com/developcoach/",
    "https://www.linkedin.com/company/developcoaching/",
    "https://www.instagram.com/greg.wilkes.coach",
    "https://www.youtube.com/@Greg.wilkes",
]

# Greg confirmed this claim. It is the Organization description so answer
# engines read it on every page. Reinstalling structured data keeps it.
ORG_DESCRIPTION = (
    "The only construction business coaching that includes six pieces of "
    "software free for members: CostTracker Pro, FlowBuild, Architect Attractor, "
    "SiteSafe Pro, Muster and Jarvis."
)

ORGANIZATION = {
    "@type": "Organization",
    "@id": ORG_ID,
    "name": "Develop Coaching",
    "legalName": "Develop Coaching Pty Ltd",
    "url": f"{SITE}/",
    "email": "hello@develop-coaching.com",
    "logo": {
        "@type": "ImageObject",
        "@id": LOGO_ID,
        "url": LOGO,
        "contentUrl": LOGO,
        "caption": "Develop Coaching",
        "width": "259",
        "height": "82",
        "inLanguage": "en-GB",
    },
    "image": {"@id": LOGO_ID},
    "founder": {"@type": "Person", "@id": GREG_ID, "name": GREG_NAME, "url": GREG_URL},
    "sameAs": SAME_AS,
    "description": ORG_DESCRIPTION,
}

GREG = {
    "@type": "Person",
    "@id": GREG_ID,
    "name": GREG_NAME,
    "url": GREG_URL,
    "jobTitle": "Founder",
    "image": f"{SITE}/wp-content/uploads/2023/01/Greg-Wilkes.jpg",
    "worksFor": {"@id": ORG_ID},
}
# How Greg appears when nested (an author, a founder): enough to stand alone.
GREG_REF = {"@type": "Person", "@id": GREG_ID, "name": GREG_NAME, "url": GREG_URL}
ORG_REF = {"@id": ORG_ID}

JSONLD_RE = re.compile(
    r'(<script\b[^>]*type\s*=\s*["\']?application/ld\+json["\']?[^>]*>)([\s\S]*?)(</script\s*>)',
    re.I,
)
OWNED_ATTR = "data-dc-schema"
OWNED_OPEN = f'<script type="application/ld+json" {OWNED_ATTR}>'
OWNED_RE = re.compile(
    r'[ \t]*<script type="application/ld\+json" ' + OWNED_ATTR + r'>[\s\S]*?</script>\n?'
)


# ---------------------------------------------------------------- helpers

def types_of(node) -> list:
    t = node.get("@type") if isinstance(node, dict) else None
    if isinstance(t, str):
        return [t]
    if isinstance(t, list):
        return [x for x in t if isinstance(x, str)]
    return []


def is_ref(node) -> bool:
    """A bare reference such as {"@id": ...} or {"@id": ..., "name": ...}."""
    return isinstance(node, dict) and "@id" in node and not types_of(node)


def loose(s: str) -> str:
    """Lower-case words only, the same normalising the sentinel uses."""
    s = s.lower().replace("‘", "'").replace("’", "'")
    s = re.sub(r"[^a-z0-9£%.']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def page_url(html: str, path: Path = None):
    m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html, re.I)
    if m and m.group(1).startswith(SITE):
        return m.group(1)
    if path is not None:
        try:
            rel = path.resolve().relative_to(WWW.resolve()).as_posix()
        except ValueError:
            return None
        if rel == "index.html":
            return f"{SITE}/"
        if rel.endswith("/index.html"):
            return f"{SITE}/{rel[: -len('index.html')]}"
        return f"{SITE}/{rel}"
    return None


# ------------------------------------------------------------ people / org

def classify_person(node):
    """Return 'greg', 'wp_author' or None for a Person node."""
    if "Person" not in types_of(node):
        return None
    node_id = str(node.get("@id") or "")
    name = node.get("name")
    name = name.strip() if isinstance(name, str) else ""
    if node_id in GREG_ALIASES or name == GREG_NAME:
        return "greg"
    if "@" in name or "/author/" in node_id or not name:
        return "wp_author"
    return None


def is_our_org(node) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("@id") == ORG_ID and types_of(node):
        return True
    org_like = any("Organization" in t or "Business" in t for t in types_of(node))
    name = str(node.get("name") or "").strip().lower()
    return org_like and "@id" not in node and name in {"develop-coaching.com", "develop coaching"}


def fix_nested(value, redirects):
    """Rewrite nested people, orgs and references in place. Returns new value."""
    if isinstance(value, list):
        return [fix_nested(v, redirects) for v in value]
    if not isinstance(value, dict):
        return value
    if is_ref(value):
        target = redirects.get(value["@id"])
        if target == "greg":
            return dict(GREG_REF)
        if target == "org":
            return dict(ORG_REF)
        return value
    kind = classify_person(value)
    if kind == "greg":
        return dict(GREG_REF)
    if kind == "wp_author":
        return dict(GREG_REF) if str(value.get("@id", "")) in GREG_ALIASES else dict(ORG_REF)
    if is_our_org(value) and value.get("@id") != ORG_ID:
        # A nameless-domain or duplicate inline copy of the business.
        return dict(ORG_REF)
    return {k: fix_nested(v, redirects) for k, v in value.items()}


def fix_graph(graph: list, url) -> list:
    """Canonicalise the top-level nodes of one @graph."""
    redirects = {}
    for node in graph:
        if not isinstance(node, dict):
            continue
        kind = classify_person(node)
        node_id = node.get("@id")
        if kind == "wp_author" and node_id:
            redirects[node_id] = "greg" if node_id in GREG_ALIASES else "org"
        elif kind == "greg" and node_id and node_id != GREG_ID:
            redirects[node_id] = "greg"

    out = []
    have_greg = False
    for node in graph:
        if not isinstance(node, dict):
            out.append(node)
            continue
        node_id = node.get("@id", "")
        kind = classify_person(node)
        if kind == "wp_author" and node_id not in GREG_ALIASES:
            continue
        if kind in {"greg", "wp_author"}:
            if not have_greg:
                out.append(copy.deepcopy(GREG))
                have_greg = True
            continue
        if node_id == ORG_ID and types_of(node):
            continue  # re-added once, canonical, below
        if "Place" in types_of(node) and node_id == f"{SITE}/#place":
            continue  # an address-less Place from the old WordPress config
        if "ImageObject" in types_of(node) and "gravatar.com" in str(node_id):
            continue  # the removed WordPress users' avatars
        out.append(fix_nested(node, redirects))

    if url in GREG_PAGES and not have_greg:
        out.append(copy.deepcopy(GREG))
    if url in GREG_PAGES:
        for node in out:
            if isinstance(node, dict) and node.get("@id") in {url, f"{url}#webpage"} and any(
                t.endswith("Page") for t in types_of(node)
            ):
                node["@type"] = "ProfilePage"
                node["mainEntity"] = {"@id": GREG_ID}
    return out


# ---------------------------------------------------------- visible FAQs

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style", "noscript", "template", "svg"}
HEADING = re.compile(r"^h([1-6])$")
FAQ_HEADING = re.compile(r"\bfaqs?\b|frequently asked questions", re.I)
FAQ_CLASS = re.compile(r"(?<![a-z])faq", re.I)
SCREEN_READER_ONLY = {"elementor-screen-only", "screen-reader-text", "sr-only", "visually-hidden",
                      "screen-only"}
CONTAINERS = {"section", "div", "details", "dl", "article", "aside"}
P_CLOSERS = {"p", "div", "section", "article", "aside", "details", "summary", "ul", "ol",
             "dl", "table", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "footer",
             "nav", "figure", "blockquote", "pre", "hr", "dt", "dd"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.children, self.parent = tag, attrs, [], parent


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        if tag == "p" or (tag in P_CLOSERS and self._open("p")):
            if self._open("p") and tag in P_CLOSERS:
                self._close("p")
        node = Node(tag, dict(attrs), self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, dict(attrs), self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        self._close(tag)

    def handle_data(self, data):
        self.cur.children.append(data)

    def _open(self, tag):
        n = self.cur
        while n is not None and n.tag != "#root":
            if n.tag == tag:
                return True
            n = n.parent
        return False

    def _close(self, tag):
        n = self.cur
        while n is not None and n.tag != "#root":
            if n.tag == tag:
                self.cur = n.parent
                return
            n = n.parent
        # Stray end tag: ignore.


def hidden(node: Node, region) -> bool:
    a = node.attrs
    if "hidden" in a or a.get("aria-hidden") == "true":
        return True
    if re.search(r"display\s*:\s*none", a.get("style") or "", re.I):
        return True
    classes = (a.get("class") or "").split()
    # Screen-reader-only labels ("Answer") are not part of the visible text.
    if any(c in SCREEN_READER_ONLY for c in classes):
        return True
    if region:
        for c in classes:
            m = re.fullmatch(r"only-([a-z]{2})", c)
            if m and m.group(1) != region:
                return True
    # A call-to-action button is not part of an answer.
    if node.tag == "a" and any("button" in c or c.startswith("cta") for c in classes):
        return True
    return False


def text_of(node, region, skip=()) -> str:
    parts = []

    def walk(n):
        if isinstance(n, str):
            parts.append(n)
            return
        if n.tag in SKIP_TEXT or n in skip or hidden(n, region):
            return
        if n.tag == "br" or n.tag in P_CLOSERS or n.tag == "li":
            parts.append(" ")
        for c in n.children:
            walk(c)
        if n.tag in P_CLOSERS or n.tag == "li":
            parts.append(" ")

    walk(node)
    return re.sub(r"\s+", " ", htmllib.unescape("".join(parts))).strip()


def iter_nodes(node):
    for c in node.children:
        if isinstance(c, Node):
            yield c
            yield from iter_nodes(c)


def heading_level(node):
    m = HEADING.match(node.tag) if isinstance(node, Node) else None
    return int(m.group(1)) if m else None


def faq_starts(root, region):
    """Visible FAQ headings and FAQ containers, in page order (the sentinel's test)."""
    for n in iter_nodes(root):
        lvl = heading_level(n)
        if lvl and lvl <= 4 and FAQ_HEADING.search(text_of(n, region)):
            yield n, "heading"
        elif n.tag in CONTAINERS:
            ident = f"{n.attrs.get('id') or ''} {n.attrs.get('class') or ''}"
            if FAQ_CLASS.search(ident):
                yield n, "container"


def scope_after_heading(root, heading):
    """Document-order nodes after `heading` up to the next heading of its level or higher."""
    lvl = heading_level(heading)
    seen = False
    out = []
    for n in iter_nodes(root):
        if n is heading:
            seen = True
            continue
        if not seen or _inside(n, heading):
            continue
        nl = heading_level(n)
        if nl and nl <= lvl:
            break
        out.append(n)
    return out


def _inside(node, ancestor):
    p = node.parent
    while p is not None:
        if p is ancestor:
            return True
        p = p.parent
    return False


def is_question(s: str) -> bool:
    return s.endswith("?") and len(s) > 8


def extract_faqs(html: str):
    """Visible FAQs as [(question, answer)], [] if a section shows but none could
    be read, or None when the page shows no FAQ section at all."""
    body = re.search(r"<body\b[^>]*>", html, re.I)
    m = re.search(r'<body\b[^>]*\bdata-region=["\']([a-z]{2})["\']', html, re.I)
    region = m.group(1).lower() if m else None
    tree = Tree()
    tree.feed(html[body.start():] if body else html)
    root = tree.root
    found = None
    for start, kind in faq_starts(root, region):
        if hidden(start, region) or any(hidden(a, region) for a in _ancestors(start)):
            continue
        scope = list(iter_nodes(start)) if kind == "container" else scope_after_heading(root, start)
        faqs = _read_faqs(scope, region)
        if faqs:
            return faqs
        found = []
    return found


def _ancestors(node):
    p = node.parent
    while p is not None and p.tag != "#root":
        yield p
        p = p.parent


def _read_faqs(scope, region):
    scope_set = set(scope)
    faqs = []

    # A. Accordions: <details><summary>Question</summary>answer</details>
    for n in scope:
        if n.tag != "details" or hidden(n, region):
            continue
        summary = next((c for c in n.children if isinstance(c, Node) and c.tag == "summary"), None)
        if summary is None:
            continue
        q = text_of(summary, region)
        a = text_of(n, region, skip=(summary,))
        if q and a:
            faqs.append((q, a))
    if faqs:
        return faqs

    # B. A question heading followed by its answer.
    for n in scope:
        lvl = heading_level(n)
        if not lvl or hidden(n, region):
            continue
        q = text_of(n, region)
        if not is_question(q):
            continue
        parts = []
        for s in _siblings_after(n):
            if isinstance(s, Node):
                if heading_level(s) or s.tag not in {"p", "ul", "ol", "span", "strong", "em", "a", "b", "i"}:
                    break
                if s not in scope_set:
                    break
                parts.append(text_of(s, region))
            else:
                parts.append(s)
        a = re.sub(r"\s+", " ", htmllib.unescape(" ".join(parts))).strip()
        if a:
            faqs.append((q, a))
    if faqs:
        return faqs

    # C. <p><strong>Question?</strong><br>Answer</p>
    for n in scope:
        if n.tag != "p" or hidden(n, region):
            continue
        kids = [c for c in n.children if not (isinstance(c, str) and not c.strip())]
        if not kids or not isinstance(kids[0], Node) or kids[0].tag not in {"strong", "b"}:
            continue
        q = text_of(kids[0], region)
        if not is_question(q):
            continue
        a = text_of(n, region, skip=(kids[0],))
        if a:
            faqs.append((q, a))
    return faqs


def _siblings_after(node):
    kids = node.parent.children
    i = next(i for i, c in enumerate(kids) if c is node)
    return kids[i + 1:]


def faq_questions(faqs):
    return [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in faqs
    ]


def questions_match(main_entity, faqs) -> bool:
    if not isinstance(main_entity, list) or len(main_entity) != len(faqs):
        return False
    for node, (q, a) in zip(main_entity, faqs):
        if not isinstance(node, dict) or "Question" not in types_of(node):
            return False
        ans = node.get("acceptedAnswer") or {}
        ans_text = re.sub(r"<[^>]+>", " ", htmllib.unescape(str(ans.get("text") or "")))
        if loose(str(node.get("name") or "")) != loose(q):
            return False
        # An existing answer may leave out a trailing pointer such as "See the
        # Mastermind investment" link line; it must still be the visible answer.
        have, shown = loose(ans_text), loose(a)
        if not have or have not in shown or len(have) < 0.6 * len(shown):
            return False
    return True


_DROP = object()


def sync_faq(graph: list, faqs, url) -> list:
    """Make the graph's FAQPage match `faqs` (None = the page shows no FAQs).

    The first FAQPage found, top level or nested (Rank Math nests some under an
    Article's subjectOf), is kept where it is and brought in step; any other
    FAQPage is dropped. A page showing FAQs with no FAQPage gets one."""
    if faqs == []:
        return graph  # a section shows but could not be read: leave it alone
    placed = []

    def handle(node):
        if faqs is None or placed:
            others = [t for t in types_of(node) if t != "FAQPage"]
            if not others:
                return _DROP  # FAQs the page does not show, or a duplicate
            node = dict(node)
            node["@type"] = others[0] if len(others) == 1 else others
            entity = node.get("mainEntity")
            if isinstance(entity, list) and all(
                "Question" in types_of(q) for q in entity if isinstance(q, dict)
            ):
                node.pop("mainEntity")
            return node
        placed.append(True)
        if questions_match(node.get("mainEntity"), faqs):
            return node
        node = dict(node)
        node["mainEntity"] = faq_questions(faqs)
        return node

    def walk(value):
        if isinstance(value, list):
            kept = [walk(v) for v in value]
            return [v for v in kept if v is not _DROP]
        if isinstance(value, dict):
            if "FAQPage" in types_of(value):
                return handle(value)
            if "Question" in types_of(value):
                return value
            out = {}
            for k, v in value.items():
                r = walk(v)
                if r is _DROP or (isinstance(v, list) and v and r == []):
                    continue
                out[k] = r
            return out
        return value

    out = walk(graph)
    if faqs and not placed and url:
        out.append({"@type": "FAQPage", "@id": f"{url}#faq", "url": url,
                    "mainEntity": faq_questions(faqs)})
    return out


# ------------------------------------------------------------------ install

def is_page(html: str) -> bool:
    return bool(re.search(r"<head\b", html, re.I) and re.search(r"</head>", html, re.I)
                and re.search(r"<body\b", html, re.I))


def install(html: str, url=None, path: Path = None) -> str:
    if not is_page(html):
        return html
    url = url or page_url(html, path)
    html = OWNED_RE.sub("", html)
    faqs = extract_faqs(html)

    blocks = []  # (match, data)
    for m in JSONLD_RE.finditer(html):
        raw = m.group(2).strip()
        try:
            blocks.append((m, json.loads(raw) if raw else None))
        except json.JSONDecodeError:
            blocks.append((m, None))

    main = next((i for i, (_, d) in enumerate(blocks)
                 if isinstance(d, dict) and isinstance(d.get("@graph"), list)), None)
    new_blocks = {}
    for i, (m, data) in enumerate(blocks):
        if data is None:
            continue
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            graph = fix_graph(data["@graph"], url)
        elif isinstance(data, dict):
            context = data.get("@context")
            node = {k: v for k, v in data.items() if k != "@context"}
            graph = fix_graph([node], url)
            if len(graph) == 1 and graph[0] == node:
                # Untouched stand-alone block: keep its exact form.
                graph = None
            elif graph:
                data = {"@context": context or "https://schema.org", "@graph": graph}
                graph = None
            else:
                data = None
        else:
            continue
        if graph is not None:
            if i == main:
                graph = [n for n in graph if not (isinstance(n, dict) and n.get("@id") == ORG_ID)]
                graph.insert(_org_slot(graph), copy.deepcopy(ORGANIZATION))
                graph = sync_faq(graph, faqs, url)
            data = dict(data)
            data["@graph"] = graph
        new_blocks[i] = data

    # Stand-alone FAQPage blocks follow the same rule as graph nodes.
    for i, data in list(new_blocks.items()):
        if i != main and isinstance(data, dict) and "FAQPage" in types_of(data):
            synced = sync_faq([data], faqs, url)
            new_blocks[i] = synced[0] if synced else None

    out = []
    last = 0
    for i, (m, data) in enumerate(blocks):
        if i not in new_blocks:
            continue
        out.append(html[last:m.start()])
        if new_blocks[i] is not None:
            original = json.loads(m.group(2)) if m.group(2).strip() else None
            if new_blocks[i] == original:
                out.append(m.group(0))
            else:
                out.append(m.group(1) + dumps(new_blocks[i], m.group(2)) + m.group(3))
        last = m.end()
    out.append(html[last:])
    html = "".join(out)

    if main is None:
        graph = [copy.deepcopy(ORGANIZATION)]
        if url in GREG_PAGES:
            graph.append(copy.deepcopy(GREG))
        graph = sync_faq(graph, faqs, url)
        owned = OWNED_OPEN + json.dumps({"@context": "https://schema.org", "@graph": graph},
                                        ensure_ascii=False, separators=(",", ":")) + "</script>\n"
        head_end = re.search(r"</head>", html, re.I)
        html = html[:head_end.start()] + owned + html[head_end.start():]
    return html


def _org_slot(graph):
    """Index just before the WebSite node, where Rank Math put the business."""
    for i, n in enumerate(graph):
        if isinstance(n, dict) and "WebSite" in types_of(n):
            return i
    return 0


def dumps(data, original_raw: str) -> str:
    pretty = "\n" in original_raw.strip()
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def target_files(argv):
    if "--file" in argv:
        files = [Path(a) for a in argv[argv.index("--file") + 1:] if not a.startswith("--")]
        return [f if f.is_absolute() else (Path.cwd() / f) for f in files]
    return [p for p in sorted(WWW.rglob("*.html")) if "wp-content" not in p.relative_to(WWW).parts]


def main(argv):
    check = "--check" in argv
    changed = []
    for path in target_files(argv):
        old = path.read_bytes().decode("utf-8")
        new = install(old, path=path)
        if new != old:
            if not check:
                path.write_bytes(new.encode("utf-8"))
            changed.append(str(path))
    verb = "Would update" if check else "Updated"
    print(f"{verb} structured data on {len(changed)} page(s).")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
