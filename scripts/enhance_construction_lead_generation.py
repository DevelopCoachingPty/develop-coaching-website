#!/usr/bin/env python3
"""Add the SEO/GEO lead-quality briefing to the construction lead generation page."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www" / "construction-lead-generation" / "index.html"
MARKER = "dc-lead-quality-briefing"

STYLES = """<style id="dc-lead-quality-briefing-styles">
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
.dc-lead-brief__link:hover,.dc-lead-brief__link:focus-visible{background:var(--blue);outline:3px solid var(--signal);outline-offset:3px}
@media(max-width:767px){.dc-lead-brief{margin:38px 0;box-shadow:5px 5px 0 var(--ink)}.dc-lead-brief__header{grid-template-columns:1fr;padding:24px}.dc-lead-brief__stamp{justify-self:start;min-width:0}.dc-lead-brief__body{padding:20px}.dc-lead-brief__grid{grid-template-columns:1fr}.dc-lead-brief__panel{padding:20px}}
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
    <p class="dc-lead-brief__review"><strong>Review weekly</strong>Compare enquiries, qualified opportunities, response time, proposals, wins and lost reasons by source. Lead volume alone does not show which marketing produces suitable work.</p>
    <a class="dc-lead-brief__link" href="/5-pillars-free-trainings/attract/">Explore the Attract pillar resources</a>
  </div>
</section>"""

FAQS = (
    (
        "How can a construction company reduce reliance on referrals?",
        "Review where enquiries came from, then build one additional channel that reaches your ideal client. Give it a clear owner, consistent activity and a follow-up process, while continuing to nurture referrals.",
    ),
    (
        "What should a construction company track from an enquiry?",
        "Track the source, date received, first response, contact outcome, qualification decision and reason, consultation or site visit, proposal, and whether the opportunity was won or lost.",
    ),
)


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
    faq_id = "https://develop-coaching.com/construction-lead-generation/#lead-quality-faq"
    graph = [node for node in graph if node.get("@id") != faq_id]
    graph.append(
        {
            "@type": "FAQPage",
            "@id": faq_id,
            "isPartOf": {
                "@id": "https://develop-coaching.com/construction-lead-generation/#webpage"
            },
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                }
                for question, answer in FAQS
            ],
        }
    )
    for node in graph:
        if node.get("@type") == "WebPage" or node.get("@type") == "BlogPosting":
            node["dateModified"] = "2026-08-27T00:00:00+10:00"
    schema["@graph"] = graph
    replacement = (
        '<script type="application/ld+json" class="rank-math-schema-pro">'
        + json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
        + "</script>"
    )
    return document[: match.start()] + replacement + document[match.end() :]


def transform(document: str) -> str:
    if f'id="{MARKER}"' not in document:
        conclusion = "<h2>Conclusion</h2>"
        if conclusion not in document:
            raise ValueError("Conclusion insertion point not found")
        document = document.replace(conclusion, SECTION + "\n" + conclusion, 1)
    if 'id="dc-lead-quality-briefing-styles"' not in document:
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
