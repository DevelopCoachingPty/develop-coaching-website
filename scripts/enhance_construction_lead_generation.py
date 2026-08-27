#!/usr/bin/env python3
"""Add the SEO/GEO lead-quality briefing to the construction lead generation page."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www" / "construction-lead-generation" / "index.html"
MARKER = "dc-lead-quality-briefing"
TITLE = "Construction Lead Generation: Attract Better Enquiries"
DESCRIPTION = (
    "Learn how construction companies can attract better-fit enquiries, reduce "
    "reliance on referrals and track leads through to qualified opportunities."
)

HERO_SUBTITLE = """<p class="dc-lead-hero-subtitle" id="dc-lead-hero-subtitle">A practical guide to building a steadier pipeline of suitable construction enquiries.</p>"""

ARTICLE_INTRO = """<div class="dc-lead-guide-intro" id="dc-lead-guide-intro">
  <p>Construction lead generation is not just about creating more enquiries. The useful measure is whether the right prospects enter a repeatable sales pipeline.</p>
  <img fetchpriority="high" decoding="async" src="/wp-content/uploads/2024/04/construction-lead-generation.webp" alt="Construction lead generation" width="940" height="788" />
  <p>This guide explains how to define your ideal client, use practical marketing systems, respond consistently, reduce reliance on referrals and track each enquiry through to a qualified opportunity.</p>
</div>"""

STYLES = """<style id="dc-lead-quality-briefing-styles">
.dc-lead-hero-subtitle{max-width:680px;margin:16px 0 0!important;color:#fff;font-size:clamp(17px,2vw,22px)!important;font-weight:600;line-height:1.45;text-shadow:0 2px 4px rgba(0,0,0,.35)}
.dc-lead-guide-intro{margin:0 0 38px}
.dc-lead-guide-intro p:first-child{margin:0 0 24px;padding:18px 22px;border-left:6px solid #f6c944;background:#f5f3ec;color:#25262a;font-size:20px;font-weight:700;line-height:1.5}
.dc-lead-guide-intro img{display:block;width:100%;height:auto;margin:0 0 24px}
.dc-lead-guide-intro p:last-child{margin:0;font-size:18px;line-height:1.65}
.dc-lead-brief{--ink:#25262a;--paper:#f5f3ec;--signal:#f6c944;--blue:#087f86;margin:56px 0;padding:0;background:var(--paper);border:1px solid #d9d5c9;box-shadow:8px 8px 0 var(--ink);color:var(--ink);overflow:hidden}
.dc-lead-brief *{box-sizing:border-box}
.dc-lead-brief__header{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:end;padding:32px;background:var(--ink);color:#fff;border-bottom:8px solid var(--signal)}
.dc-lead-brief__eyebrow{margin:0 0 10px!important;color:var(--signal);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px!important;font-weight:800;letter-spacing:.15em;text-transform:uppercase}
.dc-lead-brief h2{margin:0!important;color:#fff!important;font-size:clamp(30px,4vw,48px)!important;line-height:1.02!important;letter-spacing:-.03em}
.dc-lead-brief__stamp{min-width:140px;padding:12px 16px;border:2px solid var(--signal);color:var(--signal);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:800;letter-spacing:.1em;text-align:center;text-transform:uppercase;transform:rotate(2deg)}
.dc-lead-brief__body{padding:32px}
.dc-lead-brief__intro{max-width:760px;margin:0 0 30px!important;font-size:18px;line-height:1.65}
.dc-lead-brief__grid{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:24px}
.dc-lead-brief__panel{padding:24px;background:#fff;border-top:5px solid var(--blue)}
.dc-lead-brief__panel h3{margin:0 0 12px!important;color:var(--ink)!important;font-size:24px!important;line-height:1.15!important}
.dc-lead-brief__panel p{margin:0 0 16px!important}
.dc-lead-brief__panel p:last-child{margin-bottom:0!important}
.dc-lead-brief__steps{margin:18px 0 0!important;padding:0!important;list-style:none!important;counter-reset:lead-step}
.dc-lead-brief__steps li{position:relative;margin:0!important;padding:0 0 18px 42px;counter-increment:lead-step}
.dc-lead-brief__steps li:before{content:counter(lead-step);position:absolute;left:0;top:-2px;width:28px;height:28px;display:grid;place-items:center;background:var(--signal);border:2px solid var(--ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:900}
.dc-lead-brief__steps li:not(:last-child):after{content:"";position:absolute;left:13px;top:28px;bottom:0;border-left:2px dashed var(--blue)}
.dc-lead-brief__review{margin:24px 0 0;padding:20px 24px;background:var(--signal);border-left:8px solid var(--ink)}
.dc-lead-brief__review strong{display:block;margin-bottom:4px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;letter-spacing:.1em;text-transform:uppercase}
.dc-lead-brief__link{display:inline-block;margin-top:22px;padding:13px 17px;background:var(--ink);color:#fff!important;font-weight:800;text-decoration:none!important;box-shadow:4px 4px 0 var(--blue)}
.dc-lead-brief__link:hover,.dc-lead-brief__link:focus-visible{background:var(--blue)}
.dc-lead-brief__link:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
@media(max-width:767px){.dc-lead-hero-subtitle{font-size:16px!important}.dc-lead-guide-intro p:first-child{padding:16px 18px;font-size:18px}.dc-lead-brief{margin:38px 0;box-shadow:5px 5px 0 var(--ink)}.dc-lead-brief__header{grid-template-columns:1fr;padding:24px}.dc-lead-brief__stamp{justify-self:start;min-width:0}.dc-lead-brief__body{padding:20px}.dc-lead-brief__grid{grid-template-columns:1fr}.dc-lead-brief__panel{padding:20px}}
</style>"""

SECTION = """<section class="dc-lead-brief" id="dc-lead-quality-briefing" aria-labelledby="dc-lead-quality-title">
  <header class="dc-lead-brief__header">
    <div>
      <p class="dc-lead-brief__eyebrow">Lead pipeline site briefing</p>
      <h2 id="dc-lead-quality-title">Reduce Reliance on Referrals and Track Better Leads</h2>
    </div>
    <div class="dc-lead-brief__stamp">Attract pillar</div>
  </header>
  <div class="dc-lead-brief__body">
    <p class="dc-lead-brief__intro">Referrals are valuable, but they are difficult to predict. If most new work depends on one relationship or word of mouth alone, your pipeline can slow without warning. The aim is not to stop referrals. It is to support them with a repeatable mix of lead sources that you can control and measure.</p>
    <div class="dc-lead-brief__grid">
      <article class="dc-lead-brief__panel">
        <h3>How can a construction company reduce reliance on referrals?</h3>
        <p>Review where your enquiries came from over the last six to twelve months. Group them by source, such as past clients, professional partners, organic search, paid campaigns, social media and direct outreach.</p>
        <p>If one source supplies most of the pipeline, build one additional channel that reaches your ideal client. Give it a clear owner, a consistent activity and a follow-up process before adding more channels.</p>
      </article>
      <article class="dc-lead-brief__panel">
        <h3>Track the route from enquiry to qualified opportunity</h3>
        <p>A lead becomes a qualified opportunity when the project fits your services, location, likely budget and timing, and you can reach the person involved in the decision.</p>
        <ol class="dc-lead-brief__steps">
          <li>Record the lead source and date received.</li>
          <li>Log the first response and whether contact was made.</li>
          <li>Mark the enquiry as qualified or not qualified, with a reason.</li>
          <li>Track the consultation or site visit, proposal, and final result.</li>
        </ol>
      </article>
    </div>
    <p class="dc-lead-brief__review"><strong>Review weekly</strong> Compare enquiries, qualified opportunities, response time, proposals, wins and lost reasons by source. Lead volume alone does not show which marketing produces suitable work.</p>
    <a class="dc-lead-brief__link" href="/5-pillars-free-trainings/attract/">Explore the Attract pillar resources</a>
  </div>
</section>"""

def update_schema(document: str) -> str:
    pattern = re.compile(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">(.*?)</script>',
        re.DOTALL,
    )
    match = pattern.search(document)
    if not match:
        raise ValueError("Rank Math schema not found")
    schema = json.loads(match.group(1))
    graph = schema.get("@graph", [])
    graph = [
        node
        for node in graph
        if node.get("@id")
        != "https://develop-coaching.com/construction-lead-generation/#lead-quality-faq"
    ]
    for node in graph:
        node_type = node.get("@type")
        if node_type == "BreadcrumbList":
            items = node.get("itemListElement", [])
            if len(items) >= 3:
                items[1]["item"] = {
                    "@id": "https://develop-coaching.com/category/attract/",
                    "name": "Attract",
                }
                items[2]["item"]["name"] = TITLE
        if node_type == "WebPage":
            node["name"] = TITLE
            node["description"] = DESCRIPTION
            node["dateModified"] = "2026-08-28T00:00:00+10:00"
        if node_type == "BlogPosting":
            node["headline"] = TITLE
            node["name"] = TITLE
            node["description"] = DESCRIPTION
            node["articleSection"] = "Attract"
            node["dateModified"] = "2026-08-28T00:00:00+10:00"
    schema["@graph"] = graph
    replacement = (
        '<script type="application/ld+json" class="rank-math-schema-pro">'
        + json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
        + "</script>"
    )
    return document[: match.start()] + replacement + document[match.end() :]


def update_page_signals(document: str) -> str:
    replacements = (
        (r"<title>.*?</title>", f"<title>{TITLE}</title>"),
        (
            r'(<meta name="description" content=")[^"]*("\s*/>)',
            rf"\g<1>{DESCRIPTION}\g<2>",
        ),
        (
            r'(<meta property="og:title" content=")[^"]*("\s*/>)',
            rf"\g<1>{TITLE}\g<2>",
        ),
        (
            r'(<meta property="og:description" content=")[^"]*("\s*/>)',
            rf"\g<1>{DESCRIPTION}\g<2>",
        ),
        (
            r'(<meta name="twitter:title" content=")[^"]*("\s*/>)',
            rf"\g<1>{TITLE}\g<2>",
        ),
        (
            r'(<meta name="twitter:description" content=")[^"]*("\s*/>)',
            rf"\g<1>{DESCRIPTION}\g<2>",
        ),
        (
            r'(<meta property="article:section" content=")[^"]*("\s*/>)',
            r"\g<1>Attract\g<2>",
        ),
        (
            r'(<meta property="og:updated_time" content=")[^"]*("\s*/>)',
            r"\g<1>2026-08-28T00:00:00+10:00\g<2>",
        ),
        (
            r'(<meta property="article:modified_time" content=")[^"]*("\s*/>)',
            r"\g<1>2026-08-28T00:00:00+10:00\g<2>",
        ),
        (
            r'<h1 class="elementor-heading-title elementor-size-default">.*?</h1>',
            f'<h1 class="elementor-heading-title elementor-size-default">{TITLE}</h1>',
        ),
    )
    for pattern, replacement in replacements:
        document, count = re.subn(pattern, replacement, document, count=1)
        if count != 1:
            raise ValueError(f"Page signal not found: {pattern}")

    category_pattern = re.compile(
        r'<span class="elementor-post-info__terms-list">[\s\S]*?</span>'
    )
    document, count = category_pattern.subn(
        '<span class="elementor-post-info__terms-list">\n'
        '<a href="/category/attract/" class="elementor-post-info__terms-list-item">Attract</a>'
        "\t\t\t\t</span>",
        document,
        count=1,
    )
    if count != 1:
        raise ValueError("Visible category list not found")
    document = document.replace(
        "category-convert category-scale tag-most-read",
        "category-attract tag-most-read",
        1,
    )
    document = document.replace(
        "12%20Secrets%20for%20Effective%20Construction%20Lead%20Generation",
        "Construction%20Lead%20Generation%3A%20Attract%20Better%20Enquiries",
    )
    return document


def update_hero(document: str) -> str:
    subtitle_pattern = re.compile(
        r'<p class="dc-lead-hero-subtitle" id="dc-lead-hero-subtitle">[\s\S]*?</p>'
    )
    if subtitle_pattern.search(document):
        return subtitle_pattern.sub(HERO_SUBTITLE, document, count=1)
    h1 = f'<h1 class="elementor-heading-title elementor-size-default">{TITLE}</h1>'
    if h1 not in document:
        raise ValueError("Hero title not found")
    return document.replace(h1, h1 + "\n" + HERO_SUBTITLE, 1)


def update_intro(document: str) -> str:
    owned_pattern = re.compile(
        r'<div class="dc-lead-guide-intro" id="dc-lead-guide-intro">[\s\S]*?</div>'
    )
    if owned_pattern.search(document):
        return owned_pattern.sub(ARTICLE_INTRO, document, count=1)
    legacy_pattern = re.compile(
        r"<p>Are you looking to supercharge your construction business\?[\s\S]*?</p>"
    )
    document, count = legacy_pattern.subn(ARTICLE_INTRO, document, count=1)
    if count != 1:
        raise ValueError("Legacy article introduction not found")
    return document


def transform(document: str) -> str:
    document = update_page_signals(document)
    document = update_hero(document)
    document = update_intro(document)
    section_pattern = re.compile(
        rf'<section class="dc-lead-brief" id="{MARKER}"[\s\S]*?</section>(?:\r?\n)*'
    )
    document = section_pattern.sub("", document)
    first_guide_heading = '<h2 dir="ltr">Identify and Target Your Ideal Client</h2>'
    if first_guide_heading not in document:
        raise ValueError("First guide heading not found")
    document = re.sub(
        r"\s*" + re.escape(first_guide_heading),
        "\n" + SECTION + "\n" + first_guide_heading,
        document,
        count=1,
    )
    style_pattern = re.compile(
        r'<style id="dc-lead-quality-briefing-styles">[\s\S]*?</style>'
    )
    if style_pattern.search(document):
        document = style_pattern.sub(STYLES, document, count=1)
    else:
        if "</head>" not in document:
            raise ValueError("Head insertion point not found")
        document = document.replace("</head>", STYLES + "\n</head>", 1)
    return update_schema(document)


def main() -> None:
    original = PAGE.read_text(encoding="utf-8")
    updated = transform(original)
    PAGE.write_text(updated, encoding="utf-8")
    print(f"Enhanced {PAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
