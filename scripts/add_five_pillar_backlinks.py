#!/usr/bin/env python3
"""Add one visible, contextual Five Pillars backlink to verified support pages."""

import argparse
import re
from pathlib import Path


TARGETS = {
    "construction-business-plan": "plan",
    "profit-and-loss-statement-for-small-construction-company": "plan",
    "construction-profit-margin-uk": "plan",
    "attract-the-right-clients": "attract",
    "construction-lead-generation": "attract",
    "the-architect-attractor": "attract",
    "construction-marketing-ideas-to-scale-your-1m-business-to-5m": "attract",
    "construction-job-pricing": "convert",
    "how-to-stop-wasting-time-on-quotes": "convert",
    "construction-sales-funnel": "convert",
    "construction-project-management": "deliver",
    "software/costtracker-pro": "deliver",
    "streamlined-procurement-system": "deliver",
    "the-hand-off": "deliver",
    "delegation-in-construction": "scale",
    "construction-business-systems": "scale",
    "podcast/hire-a-project-manager": "scale",
    "podcast/the-perfect-week-with-emma-mills": "scale",
}

PILLARS = {
    "plan": {
        "title": "Continue with the Plan pillar",
        "copy": "Connect this topic with clearer goals, financial visibility and the priorities that move a construction business forward.",
    },
    "attract": {
        "title": "Continue with the Attract pillar",
        "copy": "Connect this topic with positioning, proof and a more dependable flow of suitable construction enquiries.",
    },
    "convert": {
        "title": "Continue with the Convert pillar",
        "copy": "Connect this topic with qualification, estimating, proposals and follow-up that protect time and margin.",
    },
    "deliver": {
        "title": "Continue with the Deliver pillar",
        "copy": "Connect this topic with project handover, planning, procurement and the controls used while work is in progress.",
    },
    "scale": {
        "title": "Continue with the Scale pillar",
        "copy": "Connect this topic with clearer roles, delegation and operating rhythms that reduce dependence on the owner.",
    },
}

STYLE = """<style id="dc-pillar-backlink-style">
/* Matches the article design system. Colours are the Elementor kit palette:
   secondary #2C67AC, text #424142, yellow #FDCE36. */
.dc-pillar-backlink{padding:clamp(40px,5vw,64px) 20px;background:#F6F5F2;color:#25262a;font-family:"Source Sans Pro",Arial,sans-serif}
.dc-pillar-backlink__inner{max-width:1120px;margin:0 auto;padding:clamp(26px,4vw,40px);border:1px solid #E4E2DC;border-top:3px solid #FDCE36;background:#fff}
.dc-pillar-backlink__eyebrow{margin:0 0 12px;color:#2C67AC;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
.dc-pillar-backlink h2{margin:0 0 12px;color:#25262a;font-size:clamp(1.6rem,2.8vw,2.25rem);font-weight:700;line-height:1.12;letter-spacing:-.02em}
.dc-pillar-backlink p:not(.dc-pillar-backlink__eyebrow){max-width:64ch;margin:0 0 24px;color:#424142;font-size:1.05rem;line-height:1.7}
.dc-pillar-backlink__link{box-sizing:border-box;display:inline-flex;align-items:center;gap:10px;min-height:50px;padding:13px 22px;border:0;background:#25262a;color:#fff!important;font-weight:700;text-decoration:none;transition:background .18s ease,gap .18s ease}
.dc-pillar-backlink__link:after{content:"\u2192";font-size:17px;line-height:1}
.dc-pillar-backlink__link:hover{background:#2C67AC;gap:14px}
.dc-pillar-backlink__link:focus-visible{background:#2C67AC;outline:3px solid #25262a;outline-offset:3px}
@media(prefers-reduced-motion:reduce){.dc-pillar-backlink__link{transition:none}}
@media(max-width:600px){.dc-pillar-backlink__link{display:flex;width:100%;justify-content:center;text-align:center}}
</style>"""

HEAD_CLOSE_RE = re.compile(r"</head>", re.I)
STYLE_RE = re.compile(
    r'<style id="dc-pillar-backlink-style">.*?</style>', re.S | re.I
)
CALLOUT_RE = re.compile(
    r'<aside\b[^>]*\bdata-dc-pillar-backlink="[^"]+"[^>]*>.*?</aside>',
    re.S | re.I,
)
MAIN_CLOSE_RE = re.compile(r"</main>", re.I)
BOOK_AWARD_RE = re.compile(r'<section\b[^>]*class="[^"]*\bdc-book-award\b', re.I)
FOOTER_RE = re.compile(r"<footer\b", re.I)
BODY_CLOSE_RE = re.compile(r"</body>", re.I)


def callout(pillar: str) -> str:
    data = PILLARS[pillar]
    return f"""<aside class="dc-pillar-backlink" data-dc-pillar-backlink="{pillar}" aria-labelledby="dc-pillar-backlink-title">
  <div class="dc-pillar-backlink__inner">
    <p class="dc-pillar-backlink__eyebrow">Free Five Pillars training</p>
    <h2 id="dc-pillar-backlink-title">{data['title']}</h2>
    <p>{data['copy']}</p>
    <a class="dc-pillar-backlink__link" href="/5-pillars-free-trainings/{pillar}/">Explore the {pillar.title()} pillar</a>
  </div>
</aside>"""


def add_backlink(html: str, pillar: str) -> str:
    marker = f'data-dc-pillar-backlink="{pillar}"'
    target_href = f'href="/5-pillars-free-trainings/{pillar}/"'
    if marker in html:
        callouts = CALLOUT_RE.findall(html)
        # The article design system also places a contextual pillar link inside
        # the article body, so the page can legitimately carry more than one
        # link to the pillar. Only the link inside this callout is ours to own.
        links_in_callout = sum(block.count(target_href) for block in callouts)
        if (
            html.count(marker) != 1
            or links_in_callout != 1
            or len(STYLE_RE.findall(html)) != 1
            or len(callouts) != 1
        ):
            raise ValueError(f"Invalid existing {pillar} backlink state")
        html = STYLE_RE.sub(lambda _match: STYLE, html, count=1)
        return CALLOUT_RE.sub(lambda _match: callout(pillar), html, count=1)
    if "data-dc-pillar-backlink=" in html or target_href in html:
        raise ValueError(f"Unexpected existing pillar backlink for {pillar}")

    if 'id="dc-pillar-backlink-style"' not in html:
        if not HEAD_CLOSE_RE.search(html):
            raise ValueError("Closing head tag not found")
        html = HEAD_CLOSE_RE.sub(
            lambda match: f"{STYLE}\n{match.group(0)}", html, count=1
        )

    markup = callout(pillar)
    if MAIN_CLOSE_RE.search(html):
        return MAIN_CLOSE_RE.sub(
            lambda match: f"{markup}\n{match.group(0)}", html, count=1
        )
    if BOOK_AWARD_RE.search(html):
        return BOOK_AWARD_RE.sub(
            lambda match: f"{markup}\n{match.group(0)}", html, count=1
        )
    if FOOTER_RE.search(html):
        return FOOTER_RE.sub(
            lambda match: f"{markup}\n{match.group(0)}", html, count=1
        )
    if BODY_CLOSE_RE.search(html):
        return BODY_CLOSE_RE.sub(
            lambda match: f"{markup}\n{match.group(0)}", html, count=1
        )
    raise ValueError("No safe backlink insertion point found")


def apply_targets(root: Path, check: bool = False) -> int:
    changed = 0
    for relative_path, pillar in TARGETS.items():
        path = root / relative_path / "index.html"
        if not path.is_file():
            raise FileNotFoundError(path)
        original = path.read_text(encoding="utf-8")
        updated = add_backlink(original, pillar)
        if updated != original:
            if check:
                raise ValueError(f"Backlink update required: {relative_path}")
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("www"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = apply_targets(args.root, check=args.check)
    print(f"Added contextual Five Pillars backlinks to {changed} pages")


if __name__ == "__main__":
    main()
