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
import subprocess
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
/* Develop Coaching article system.
   Set in Source Sans Pro, the face the site already loads. The weight comes
   from scale, spacing and restraint rather than from ornament. */
.dc-article-hero-subtitle{max-width:640px;margin:14px 0 0!important;color:#fff;font-size:clamp(16px,1.9vw,21px)!important;font-weight:400;line-height:1.5;letter-spacing:.005em;opacity:.94;text-shadow:0 1px 3px rgba(0,0,0,.3)}

/* Article prose.
   The column runs 796px wide and the theme sets 20px text on a 1.4 line, which
   is about 80 characters a line and too tight to read comfortably at length.
   Headings came in at weight 500 with 8px of space above them, so sections did
   not separate, and h3 was smaller than the body text it sat above. This fixes
   the measure, the rhythm and the hierarchy. Images and the design blocks keep
   the full column width. */
.dc-prose > p,.dc-prose > ul,.dc-prose > ol,.dc-prose > h2,.dc-prose > h3,.dc-prose > h4,.dc-prose > blockquote{max-width:66ch}
.dc-prose > p,.dc-prose > ul,.dc-prose > ol{margin-bottom:20px!important;color:#424142;font-size:19px!important;line-height:1.66!important;text-wrap:pretty}
.dc-prose > h2{margin:52px 0 16px!important;color:#25262a!important;font-size:clamp(26px,2.6vw,33px)!important;font-weight:700!important;line-height:1.16!important;letter-spacing:-.022em;text-wrap:balance}
.dc-prose > h3{margin:34px 0 10px!important;color:#25262a!important;font-size:22px!important;font-weight:700!important;line-height:1.28!important;letter-spacing:-.015em;text-wrap:balance}
.dc-prose > h4{margin:26px 0 8px!important;color:#25262a!important;font-size:19px!important;font-weight:700!important}
.dc-prose > ul,.dc-prose > ol{padding-left:24px!important}
.dc-prose > ul > li,.dc-prose > ol > li{margin:0 0 10px!important;padding-left:4px;line-height:1.66}
.dc-prose > ul > li::marker{color:#2C67AC}
.dc-prose > ol > li::marker{color:#2C67AC;font-weight:700}
.dc-prose > figure{margin:30px 0}
.dc-prose > figure img,.dc-prose > p > img{display:block;width:100%%;height:auto}
.dc-prose > h2 + p,.dc-prose > h3 + p{margin-top:0!important}
@media(max-width:600px){
  .dc-prose > p,.dc-prose > ul,.dc-prose > ol{font-size:17.5px!important;line-height:1.62!important}
  .dc-prose > h2{margin:38px 0 12px!important}
  .dc-prose > h3{margin:26px 0 8px!important}
}

/* In-article links. The Hello theme default is a magenta that appears nowhere
   in the brand, so links inside article prose take the kit's secondary blue. */
.elementor-widget-theme-post-content p a:not([class]),.elementor-widget-theme-post-content li a:not([class]){color:#2C67AC;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px}
.elementor-widget-theme-post-content p a:not([class]):hover,.elementor-widget-theme-post-content li a:not([class]):hover{color:#25262a}
.elementor-widget-theme-post-content p a:not([class]):focus-visible,.elementor-widget-theme-post-content li a:not([class]):focus-visible{outline:3px solid #2C67AC;outline-offset:2px}

/* Opening. A standfirst, not a warning callout. */
.dc-article-intro{--ink:#25262a;--quiet:#424142;--signal:#FDCE36;margin:0 0 44px}
.dc-article-intro__answer{position:relative;margin:0 0 30px!important;padding:26px 0 0!important;border:0!important;background:none!important;color:var(--ink)!important;font-size:clamp(20px,2.5vw,26px)!important;font-weight:600!important;line-height:1.38!important;letter-spacing:-.012em}
.dc-article-intro__answer:before{content:"";position:absolute;top:0;left:0;width:56px;height:4px;background:var(--signal)}
.dc-article-intro img{display:block;width:100%%;height:auto;margin:0 0 26px}
.dc-article-intro__roadmap{margin:0!important;color:var(--quiet)!important;font-size:17px!important;font-weight:400!important;line-height:1.72!important;max-width:64ch}

/* Briefing. A site notice: dark head, quiet body, hairline divisions. */
.dc-article-brief{--ink:#25262a;--paper:#F6F5F2;--edge:#E4E2DC;--rule:#D6D3CB;--quiet:#424142;--signal:#FDCE36;--blue:#2C67AC;
  margin:52px 0;background:var(--paper);border:1px solid var(--edge);color:var(--ink);overflow:hidden}
.dc-article-brief *{box-sizing:border-box}
.dc-article-brief__header{padding:26px 30px 24px;background:var(--ink);border-bottom:3px solid var(--signal)}
.dc-article-brief__eyebrow{display:block;margin:0 0 14px!important;color:var(--signal)!important;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px!important;font-weight:700!important;letter-spacing:.2em;line-height:1!important;text-transform:uppercase}
.dc-article-brief h2{margin:0!important;color:#fff!important;font-size:clamp(25px,3.4vw,36px)!important;font-weight:700!important;line-height:1.1!important;letter-spacing:-.022em;max-width:22ch}
.dc-article-brief__stamp{display:inline-block;margin-top:18px;padding:5px 11px;border:1px solid rgba(253,206,54,.55);color:var(--signal);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;font-weight:700;letter-spacing:.18em;line-height:1.4;text-transform:uppercase}
.dc-article-brief__body{padding:30px}
.dc-article-brief__intro{max-width:62ch;margin:0 0 30px!important;color:var(--quiet)!important;font-size:17px!important;font-weight:400!important;line-height:1.72!important}

/* Panels divided by a hairline, not boxed as cards. */
.dc-article-brief__grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0}
.dc-article-brief__panel{padding:0 30px 0 0;background:none;border:0}
.dc-article-brief__panel + .dc-article-brief__panel{padding:0 0 0 30px;border-left:1px solid var(--rule)}
.dc-article-brief__panel h3{position:relative;margin:0 0 14px!important;padding-top:16px;color:var(--ink)!important;font-size:19px!important;font-weight:700!important;line-height:1.28!important;letter-spacing:-.012em}
.dc-article-brief__panel h3:before{content:"";position:absolute;top:0;left:0;width:26px;height:3px;background:var(--blue)}
.dc-article-brief__panel p{margin:0 0 14px!important;color:var(--quiet)!important;font-size:15.5px!important;font-weight:400!important;line-height:1.68!important}
.dc-article-brief__panel p:last-child{margin-bottom:0!important}

/* Steps. Quiet numerals on a fine spine. */
.dc-article-brief__steps{margin:20px 0 0!important;padding:0!important;list-style:none!important;counter-reset:dc-step}
.dc-article-brief__steps li{position:relative;margin:0!important;padding:1px 0 20px 40px;color:var(--quiet);font-size:15.5px;line-height:1.62;counter-increment:dc-step}
.dc-article-brief__steps li:last-child{padding-bottom:0}
.dc-article-brief__steps li:before{content:counter(dc-step);position:absolute;left:0;top:-1px;width:25px;height:25px;display:grid;place-items:center;border:1.5px solid var(--ink);border-radius:50%%;background:var(--paper);color:var(--ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700}
.dc-article-brief__steps li:not(:last-child):after{content:"";position:absolute;left:12px;top:29px;bottom:6px;border-left:1px solid var(--rule)}

/* Closing note and action. */
.dc-article-brief__review{margin:30px 0 0!important;padding:20px 24px!important;background:#EDEBE4;border-left:3px solid var(--signal);color:var(--ink)!important;font-size:15.5px!important;font-weight:400!important;line-height:1.68!important}
.dc-article-brief__review strong{display:block;margin-bottom:6px;color:var(--ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;font-weight:700;letter-spacing:.18em;text-transform:uppercase}
.dc-article-brief__link{display:inline-flex;align-items:center;gap:10px;margin-top:26px;padding:14px 22px;background:var(--ink);border:0;color:#fff!important;font-size:15px;font-weight:700;letter-spacing:.005em;text-decoration:none!important;transition:background .18s ease,gap .18s ease}
.dc-article-brief__link:after{content:"→";font-size:17px;line-height:1}
.dc-article-brief__link:hover{background:var(--blue);gap:14px}
.dc-article-brief__link:focus-visible{background:var(--blue);outline:3px solid var(--ink);outline-offset:3px}
@media(prefers-reduced-motion:reduce){.dc-article-brief__link{transition:none}}

@media(max-width:1100px){
  .dc-article-brief__grid{grid-template-columns:1fr}
  .dc-article-brief__panel{padding:0 0 26px!important}
  .dc-article-brief__panel + .dc-article-brief__panel{padding:26px 0 0!important;border-left:0;border-top:1px solid var(--rule)}
}
@media(max-width:600px){
  .dc-article-hero-subtitle{font-size:16px!important}
  .dc-article-intro{margin-bottom:34px}
  .dc-article-intro__answer{padding-top:22px!important}
  .dc-article-brief{margin:38px 0}
  .dc-article-brief__header{padding:22px 20px 20px}
  .dc-article-brief__body{padding:22px 20px}
  .dc-article-brief__review{padding:18px 20px!important}
}
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
            f'    <p class="dc-article-brief__eyebrow">{esc(brief["eyebrow"])}</p>',
            f'    <h2 id="{title_id}">{esc(brief["title"])}</h2>',
            f'    <p class="dc-article-brief__stamp">{esc(spec["pillar"])} pillar</p>',
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
        # A canonical pointing somewhere else is sometimes deliberate, so this
        # stops by default. Two articles point at URLs that return 404, which
        # tells a search engine the real version of the page does not exist.
        # Correcting one is opted into per article, and the old target is
        # recorded in the content file so the change stays reviewable.
        if not spec.get("fix_canonical"):
            raise ValueError(
                f"canonical mismatch: page says {found.group(1)}, expected {canonical}. "
                "Set fix_canonical in the content file if the current target is wrong."
            )
        document = (
            document[: found.start(1)] + canonical + document[found.end(1) :]
        )

    document = replace_once(
        document, r"<title>.*?</title>", f"<title>{esc(title)}</title>", "title tag"
    )

    # Meta tags vary across the library: some articles were published without
    # og:updated_time or article:modified_time at all. Set the tag where it
    # exists, add it where it does not, rather than failing on a page whose
    # only fault is a missing tag.
    meta_tags = (
        ("name", "description", esc(description)),
        ("property", "og:title", esc(title)),
        ("property", "og:description", esc(description)),
        ("name", "twitter:title", esc(title)),
        ("name", "twitter:description", esc(description)),
        ("property", "article:section", spec["pillar"]),
        ("property", "og:updated_time", modified),
        ("property", "article:modified_time", modified),
    )
    for attribute, name, value in meta_tags:
        pattern = rf'(<meta {attribute}="{re.escape(name)}" content=")[^"]*(")'
        document, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), document, count=1)
        if count == 0:
            tag = f'<meta {attribute}="{name}" content="{value}" />'
            document = document.replace("</head>", tag + "\n</head>", 1)

    # The reference page shipped with a one-off stylesheet before this system
    # existed. Retire it so a page never carries two article stylesheets.
    document = re.sub(
        r'<style id="dc-lead-quality-briefing-styles">.*?</style>\s*',
        "",
        document,
        flags=re.DOTALL,
    )
    existing = re.search(rf'<style id="{STYLE_ID}">.*?</style>', document, re.DOTALL)
    if existing:
        # Spliced by index, not re.sub: the stylesheet contains backslashes and
        # a replacement string would read them as group references.
        document = document[: existing.start()] + STYLES + document[existing.end() :]
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
    for pattern in (
        rf'\s*<p class="dc-article-hero-subtitle" id="{HERO_ID}">.*?</p>',
        r'\s*<p class="dc-lead-hero-subtitle" id="dc-lead-hero-subtitle">.*?</p>',
    ):
        document = re.sub(pattern, "", document, flags=re.DOTALL)
    h1 = re.search(h1_pattern, document, re.DOTALL)
    insert_at = h1.end()
    return document[:insert_at] + "\n" + build_hero(spec) + document[insert_at:]


DIV_RE = re.compile(r"<div\b[^>]*>|</div>", re.I)
NOISE_RE = re.compile(r"<(script|style|noscript)\b[\s\S]*?</\1>", re.I)
WIDGET_RE = re.compile(r'data-widget_type="theme-post-content\.default"[^>]*>')
TAG_RE = re.compile(r"<[^>]+>")


BARE_VIDEO_LINK = re.compile(
    r'<a\b[^>]*href="https://www\.youtube\.com/watch\?v=(?P<id>[\w-]{6,})"[^>]*>'
    r'(?:</p>\s*<p>\s*)?\s*</a>'
)

VIDEO_SCRIPT_MARKER = 'document.querySelectorAll(".lite-youtube")'

VIDEO_SCRIPT = """
<script data-no-optimize="1" data-no-defer data-phast-no-defer  type="text/javascript" >
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".lite-youtube").forEach(function (el) {
      const videoId = el.getAttribute("data-videoid");
      el.addEventListener("click", function () {
        const iframe = document.createElement("iframe");
        iframe.style.position = "absolute";
        iframe.style.top      = 0;
        iframe.style.left     = 0;
        iframe.style.width    = "100%";
        iframe.style.height   = "100%";
        iframe.setAttribute("frameborder", "0");
        iframe.setAttribute("allowfullscreen", "");
        iframe.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture");
        iframe.src = "https://www.youtube.com/embed/" + videoId + "?autoplay=1";
        el.innerHTML = "";
        el.appendChild(iframe);
      });
    });
  });
</script>"""


def video_player(video_id: str, title: str) -> str:
    """The click-to-load player the rest of the articles already use."""
    thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return (
        f'<div class="lite-youtube" style="position:relative;width:100%;padding-bottom:56.25%;'
        f'background:#000;margin-bottom:1rem;" data-videoid="{video_id}">\n'
        f'  <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" rel="noopener" '
        f'aria-label="Play the video: {esc(title)}" '
        f'style="display:block;position:absolute;top:0;left:0;width:100%;height:100%;'
        f"background-size:cover;background-position:center;background-image:url(&#039;{thumb}&#039;);\">\n"
        '    <svg viewBox="0 0 68 48" width="68" height="48" aria-hidden="true" focusable="false" '
        'style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);">\n'
        '      <path d="M66.52 7.02a8.27 8.27 0 00-5.83-5.83C56.18 0 34 0 34 0S11.82 0 7.3 1.19a8.27 '
        '8.27 0 00-5.83 5.83C0 11.54 0 24 0 24s0 12.46 1.47 16.98a8.27 8.27 0 005.83 5.83C11.82 48 34 '
        '48 34 48s22.18 0 26.7-1.19a8.27 8.27 0 005.83-5.83C68 36.46 68 24 68 24s0-12.46-1.48-16.98z" '
        'fill="#f00"></path>\n'
        '      <path d="M45 24L27 14v20l18-10z" fill="#fff"></path>\n'
        "    </svg>\n  </a>\n</div>"
    )


def repair_video_embeds(document: str, spec: dict) -> str:
    """Build a real player where WordPress left a bare YouTube link.

    Two articles carry an anchor closed by a stray </p>, which means it is never
    closed at all: the parser adopts the rest of the article into the link, the
    whole body renders in link colour and every paragraph becomes a tab stop.
    The anchor is also empty, so the video these pages are meant to open with
    simply does not exist. Every other article has a click-to-load player. This
    builds the same player from the link that is already there.
    """
    if "lite-youtube" in document:
        return document

    match = BARE_VIDEO_LINK.search(document)
    if not match:
        return document

    document = (
        document[: match.start()]
        + video_player(match.group("id"), spec.get("h1", "Develop Coaching"))
        + document[match.end() :]
    )
    if VIDEO_SCRIPT_MARKER not in document:
        start, end = body_span(document)
        # Insert before the widget's trailing indentation, so the script does
        # not leave a whitespace-only line behind it.
        insert_at = len(document[:end].rstrip())
        document = document[:insert_at] + VIDEO_SCRIPT + document[insert_at:]
    return document


def mark_prose_container(document: str) -> str:
    """Add the dc-prose class to the post content widget.

    The prose rules are scoped to direct children of this container, so they
    style the article's own copy without reaching into the design blocks, the
    sidebar or any other widget on the page.
    """
    match = WIDGET_RE.search(document)
    if not match:
        raise ValueError("post content widget not found")
    opening_start = document.rfind("<div", 0, match.start())
    opening = document[opening_start : match.end()]
    if "dc-prose" in opening:
        return document
    if re.search(r'\bclass="', opening):
        updated = re.sub(r'(\bclass=")', r"\1dc-prose ", opening, count=1)
    else:
        updated = re.sub(r"^<div\b", '<div class="dc-prose"', opening, count=1)
    if updated == opening:
        raise ValueError("could not tag the post content widget")
    return document[:opening_start] + updated + document[match.end() :]


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

    owned = re.compile(
        rf'<div class="dc-article-intro" id="{INTRO_ID}">.*?</div>'
        r'|<div class="dc-lead-guide-intro" id="dc-lead-guide-intro">.*?</div>',
        re.DOTALL,
    )
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

    spans = prose_paragraphs(body, search_from)
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

    owned = re.compile(
        rf'<section class="dc-article-brief" id="{BRIEF_ID}".*?</section>\s*'
        r'|<section class="dc-lead-brief" id="dc-lead-quality-briefing".*?</section>\s*',
        re.DOTALL,
    )
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


# A prose paragraph never contains an embed, a heading or a nested block. The
# articles carry unclosed <p> tags around video embeds, so a plain
# <p>...</p> match can start before an embed and swallow it. Scan from each
# opening tag to the nearest close instead, and reject anything structural.
FORBIDDEN_INSIDE_PARAGRAPH = re.compile(r"<(script|style|noscript|div|section|h[1-6]|ul|ol|figure)\b", re.I)


def prose_paragraphs(body: str, search_from: int = 0) -> list:
    """Spans of the substantial prose paragraphs in the body, in order."""
    spans = []
    for opening in re.finditer(r"<p\b[^>]*>", body[search_from:]):
        start = opening.start() + search_from
        closing = body.find("</p>", opening.end() + search_from)
        if closing == -1:
            continue
        fragment = body[start : closing + 4]
        if FORBIDDEN_INSIDE_PARAGRAPH.search(fragment):
            continue
        if len(text_of(fragment)) <= 60:
            continue
        if spans and start < spans[-1][1]:
            continue
        spans.append((start, closing + 4))
    return spans


def promote_headings(document: str, spec: dict) -> str:
    """Lift named H3 section headings to H2.

    Several articles mark their real sections as H3 beneath a single H2, which
    leaves one enormous section that cannot be extracted as a passage. Naming
    the headings explicitly keeps the change reviewable rather than sweeping
    every H3 on the page.
    """
    wanted = spec.get("promote_headings") or []
    if not wanted:
        return document
    start, end = body_span(document)
    body = document[start:end]
    for heading in wanted:
        target = None
        for match in re.finditer(r"<h3\b([^>]*)>(.*?)</h3>", body, re.DOTALL):
            if text_of(match.group(0)).casefold() == heading.strip().casefold():
                target = match
                break
        if target is None:
            already = any(
                text_of(m.group(0)).casefold() == heading.strip().casefold()
                for m in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.DOTALL)
            )
            if already:
                continue
            raise ValueError(f"promote_headings: {heading!r} not found as an h3 or an h2")
        replacement = f"<h2{target.group(1)}>{target.group(2)}</h2>"
        body = body[: target.start()] + replacement + body[target.end() :]
    return document[:start] + body + document[end:]


# Three articles embed an image from a generator's temporary storage, signed
# with an access token that expired in September 2024. Every one returns 403,
# so the live pages have rendered a broken image icon for close to two years.
DEAD_IMAGE_HOSTS = ("wsstgprdphotosonic01.blob.core.windows.net",)


def drop_dead_images(document: str) -> str:
    """Remove images whose host is known to no longer serve them.

    A broken image is worse than no image: it renders as a placeholder icon and
    tells a reader the page is neglected. These are removed rather than
    replaced, because inventing a substitute picture is not this script's job.
    """
    start, end = body_span(document)
    body = document[start:end]
    for host in DEAD_IMAGE_HOSTS:
        wrapped = re.compile(
            rf'\s*<(figure|p)\b[^>]*>\s*<img\b[^>]*src="[^"]*{re.escape(host)}[^"]*"[^>]*>\s*</\1>',
            re.IGNORECASE,
        )
        body = wrapped.sub("", body)
        bare = re.compile(
            rf'\s*<img\b[^>]*src="[^"]*{re.escape(host)}[^"]*"[^>]*>', re.IGNORECASE
        )
        body = bare.sub("", body)
    return document[:start] + body + document[end:]


# One article had its markup double escaped somewhere in a WordPress migration,
# so tags arrive as the literal text u003cstrongu003e rather than <strong>.
# Readers see the gibberish on the page, and so does a search engine.
ESCAPED_MARKUP = (("u003c", "<"), ("u003e", ">"), ("u0022", '"'))
SCHEMA_RE = re.compile(
    r'(<script type="application/ld\+json" class="rank-math-schema-pro">)(.*?)(</script>)',
    re.DOTALL,
)


def repair_schema_text(document: str) -> str:
    """Clean literally escaped markup out of the structured data.

    One article's FAQ schema carries its question text as
    u003cbu003eu003cstrongu003e... rather than as markup, so a search engine
    reads the question name as that literal string. The JSON is parsed first
    and the values cleaned inside it: decoding the escapes in the raw text
    would introduce an unescaped quote and break the JSON.

    Schema names are meant to be plain text, so the tags are stripped rather
    than restored.
    """
    match = SCHEMA_RE.search(document)
    if not match or "u003c" not in match.group(2):
        return document
    schema = json.loads(match.group(2))

    def clean(value):
        if isinstance(value, str):
            if "u003c" not in value and "u0022" not in value:
                return value
            for broken, fixed in ESCAPED_MARKUP:
                value = value.replace(broken, fixed)
            return re.sub(r"\s+", " ", TAG_RE.sub("", value)).strip()
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value

    rebuilt = json.dumps(clean(schema), separators=(",", ":"), ensure_ascii=False)
    return document[: match.start()] + match.group(1) + rebuilt + match.group(3) + document[match.end() :]


def repair_escaped_markup(document: str) -> str:
    """Turn literally escaped tags back into markup, inside the article body."""
    start, end = body_span(document)
    body = document[start:end]
    if "u003c" not in body:
        return document
    for broken, fixed in ESCAPED_MARKUP:
        body = body.replace(broken, fixed)
    return document[:start] + body + document[end:]


def deduplicate_sections(document: str, spec: dict) -> str:
    """Remove an earlier copy of a section that appears twice.

    One article carries a whole 325 word block twice, three headings and all,
    because an edited version was pasted in without the original being taken
    out. The reader sees the same three sections run past twice. Naming the
    heading here keeps the removal explicit rather than letting a script guess
    which copy to keep. The last copy is kept, since that is the edited one.
    """
    headings = spec.get("deduplicate_sections") or []
    if not headings:
        return document
    start, end = body_span(document)
    body = document[start:end]

    for wanted in headings:
        while True:
            found = [
                match
                for match in re.finditer(r"<h([23])\b[^>]*>.*?</h\1>", body, re.DOTALL)
                if text_of(match.group(0)).casefold() == wanted.strip().casefold()
            ]
            if len(found) < 2:
                break
            first = found[0]
            level = first.group(1)
            # The block runs to the next heading at the same level or higher.
            following = re.compile(rf"<h[1-{level}]\b[^>]*>", re.IGNORECASE)
            nxt = following.search(body, first.end())
            stop = nxt.start() if nxt else len(body)
            body = body[: first.start()] + body[stop:]
    return document[:start] + body + document[end:]


def insert_headings(document: str, spec: dict) -> str:
    """Introduce H2 sections into articles that were published as flowing prose.

    Twelve articles carry no headings at all, which leaves a reader with an
    unbroken wall of text and gives an answer engine no passage to lift. Each
    heading is declared as {"before": "<opening words of the paragraph>",
    "text": "<the heading>"} so the placement is reviewable as copy rather than
    guessed by a script. Tolerant on re-run: a heading already present is left
    alone.
    """
    headings = spec.get("insert_headings") or []
    if not headings:
        return document
    start, end = body_span(document)
    body = document[start:end]

    for item in headings:
        anchor, text = item["before"].strip(), item["text"].strip()
        if any(
            text_of(m.group(0)).casefold() == text.casefold()
            for m in re.finditer(r"<h2\b[^>]*>.*?</h2>", body, re.DOTALL)
        ):
            continue
        target = None
        for span_start, span_end in prose_paragraphs(body):
            if text_of(body[span_start:span_end]).startswith(anchor):
                target = span_start
                break
        if target is None:
            raise ValueError(
                f"insert_headings: no paragraph starts with {anchor!r}"
            )
        body = body[:target] + f"<h2>{esc(text)}</h2>\n" + body[target:]
    return document[:start] + body + document[end:]


def apply_heading_rewrites(document: str, spec: dict) -> str:
    """Rename body headings, declared as exact old text to new text.

    Tolerant on re-run: if the old heading is gone and the new one is present,
    the rewrite has already been applied. If neither is there, that is a fault
    worth stopping for.
    """
    rewrites = spec.get("heading_rewrites") or {}
    if not rewrites:
        return document
    start, end = body_span(document)
    body = document[start:end]
    for old, new in rewrites.items():
        found = False
        for match in list(re.finditer(r"<h([23])\b([^>]*)>(.*?)</h\1>", body, re.DOTALL)):
            current = text_of(match.group(0))
            if current.casefold() == old.strip().casefold():
                replacement = f"<h{match.group(1)}{match.group(2)}>{esc(new)}</h{match.group(1)}>"
                body = body[: match.start()] + replacement + body[match.end() :]
                found = True
                break
        if not found:
            already = any(
                text_of(m.group(0)).casefold() == new.strip().casefold()
                for m in re.finditer(r"<h[23]\b[^>]*>.*?</h[23]>", body, re.DOTALL)
            )
            if not already:
                raise ValueError(f"heading_rewrites: neither {old!r} nor {new!r} found")
    return document[:start] + body + document[end:]


def apply_text_replacements(document: str, spec: dict) -> str:
    """Targeted copy edits inside the article body, declared find and replace.

    Used to bring published prose in line with house style. Every change is
    visible in the content file rather than buried in a script, so it can be
    read and approved like copy. Tolerant on re-run in the same way as headings.
    """
    replacements = spec.get("text_replacements") or []
    if not replacements:
        return document
    start, end = body_span(document)
    body = document[start:end]
    for item in replacements:
        find, replace = item["find"], item["replace"]
        if find in body:
            body = body.replace(find, replace, 1)
        elif replace not in body:
            raise ValueError(f"text_replacements: neither {find!r} nor {replace!r} found")
    return document[:start] + body + document[end:]


def transform(document: str, spec: dict) -> str:
    document = mark_prose_container(document)
    document = drop_dead_images(document)
    document = repair_escaped_markup(document)
    document = repair_schema_text(document)
    document = repair_video_embeds(document, spec)
    document = update_head(document, spec)
    document = update_schema(document, spec)
    document = update_visible_category(document, spec)
    document = update_h1_and_hero(document, spec)
    document = demote_body_h1s(document, spec)
    document = deduplicate_sections(document, spec)
    document = insert_headings(document, spec)
    document = apply_heading_rewrites(document, spec)
    document = promote_headings(document, spec)
    document = apply_text_replacements(document, spec)
    document = update_intro(document, spec)
    document = update_brief(document, spec)
    return document


# --------------------------------------------------------------------------
# Validation of the content file before anything touches a page
# --------------------------------------------------------------------------

REQUIRED = ("slug", "pillar", "title", "meta_description", "h1", "hero_subtitle",
            "intro", "briefing", "brief_before_heading", "date_modified")


def image_size(source: Path) -> tuple:
    """Real pixel dimensions of an image, or None if they cannot be read."""
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(source)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    values = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.strip().partition(":")
            if key.strip() in ("pixelWidth", "pixelHeight"):
                values[key.strip()] = int(value.strip())
    if len(values) != 2:
        return None
    return values["pixelWidth"], values["pixelHeight"]


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
    image = spec["intro"].get("image")
    if image:
        # A guessed image path produces exactly the broken image this rollout
        # exists to remove, so the file has to be on disk and its dimensions
        # have to match the file rather than the guess.
        source = WWW / image["src"].lstrip("/")
        if not source.exists():
            raise ValueError(f"{path.name}: intro image not found at {image['src']}")
        actual = image_size(source)
        if actual and actual != (int(image["width"]), int(image["height"])):
            raise ValueError(
                f"{path.name}: intro image is {actual[0]}x{actual[1]} on disk, "
                f"the content file says {image['width']}x{image['height']}. "
                "Wrong dimensions make the page jump as the image loads."
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
    for new_heading in (spec.get("heading_rewrites") or {}).values():
        if "\u2014" in new_heading:
            raise ValueError(f"{path.name}: heading rewrite contains an em dash")
    for item in spec.get("text_replacements") or []:
        if "\u2014" in item["replace"]:
            raise ValueError(f"{path.name}: text replacement introduces an em dash")
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
