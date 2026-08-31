# Develop Coaching blog design system

One design, one transformer, one content file per article. The design lives in
`scripts/blog_design_system.py`. The words live in `content/blog-system/<slug>.json`.
No two articles ever carry the same copy.

Reference implementation: [construction-lead-generation](https://develop-coaching.com/construction-lead-generation/)

## Running it

```bash
python3 scripts/blog_design_system.py construction-sales-funnel   # one article
python3 scripts/blog_design_system.py --all                       # every content file
python3 scripts/blog_design_system.py --all --check               # validate, write nothing
python3 -m unittest discover -s scripts -p 'test_*.py'            # tests
python3 scripts/audit_blog_library.py                             # refresh the inventory
```

Every run is idempotent. The transformer removes the blocks it owns before it
inserts them, and refuses to write if a second pass would produce different
output. Every anchor is fail-closed: a missing heading, a mismatched canonical
or a missing schema block raises rather than writing a half-transformed page.

## The seven parts of the standard

| Part | What it is | Where it comes from |
| --- | --- | --- |
| Outcome-led hero | H1 naming the outcome, plus a one-line audience promise underneath | `h1`, `hero_subtitle` |
| Direct-answer introduction | The answer in the first block a reader or an AI summariser sees, before any preamble | `intro.answer` |
| Article image treatment | Full-width lead image directly under the answer, with real alt text | `intro.image` |
| Practical briefing | A dark-header block placed high in the article, carrying the strongest practical guidance and a question a reader would actually type | `briefing` |
| Contextual Five Pillars link | A link to the matching pillar page from inside the article body, not just in the page furniture | `briefing.cta` |
| Consistent mobile and keyboard behaviour | Two-column briefing collapses to one under 768px, 28px H1 on phones, a 3px focus ring on the CTA | shared stylesheet |
| Page-specific metadata | Title, meta description, Open Graph, Twitter, canonical and article schema all carrying the same words | `title`, `meta_description`, `pillar` |

Two optional fields carry copy changes to the existing article body, so every
wording edit is reviewable in the content file rather than buried in a script:

| Field | What it does |
| --- | --- |
| `heading_rewrites` | Renames body headings, exact old text to new text. Used to make a heading match the question a reader types. |
| `text_replacements` | Targeted find and replace inside the body, for house style fixes and contextual internal links. |

Both are tolerant on re-run: if the old text is gone and the new text is present,
the change has already been applied. If neither is found, the run stops.

## What the transformer enforces

Validation runs before anything touches a page. A content file is rejected if:

- the title is longer than 65 characters
- the meta description is outside 110 to 165 characters
- the pillar is not one of Plan, Attract, Convert, Deliver, Scale
- the briefing CTA does not point at the matching pillar page
- any headline field contains an em dash
- the briefing has more than two panels

And the page is rejected if its canonical URL does not match its own slug.

## Checklist for a new article

Every new brief uses this from the start. Nothing here is optional.

**Before writing**

- [ ] Pillar chosen: Plan, Attract, Convert, Deliver or Scale. One only.
- [ ] Search intent named in one sentence. What does the reader type, and what do they want back?
- [ ] Confirmed no existing article already targets that term. Check `docs/blog-rollout-inventory.csv`.

**Writing**

- [ ] Headline is outcome-led, not a number. "Win Contracts at Better Margins", not "10 Tips For".
- [ ] Exactly one H1. Section headings are H2. Sub-points are H3.
- [ ] The opening answers the question directly. No "Are you looking to", no scene setting.
- [ ] At least four H2 sections, at least 900 words.
- [ ] At least two headings phrased as a question a reader would actually type.
- [ ] At least three lists or step sequences, so an answer engine has something to lift.
- [ ] At least three internal links from inside the body.
- [ ] The briefing carries the single most useful thing in the article, and sits near the top.
- [ ] One briefing panel is phrased as a question a reader would type.
- [ ] Every figure is either from Greg or from the article's own research. Nothing invented.
- [ ] No em dashes. No swearing. "PC" written out as "practical completion".
- [ ] Examples are specific to this article. Nothing pasted from another one.

**Metadata**

- [ ] Title 65 characters or fewer, carrying the primary term.
- [ ] Meta description 110 to 165 characters.
- [ ] Lead image has descriptive alt text, not the file name.
- [ ] Canonical URL matches the slug and does not change.
- [ ] Author in the schema is Greg, not an agency address.

**Before merge**

- [ ] `python3 scripts/blog_design_system.py <slug> --check` passes.
- [ ] `python3 scripts/audit_blog_library.py` shows the article scoring 90 or better.
- [ ] `python3 -m unittest discover -s scripts -p 'test_*.py'` passes.
- [ ] Desktop preview checked. One H1, two-column briefing, no horizontal scroll.
- [ ] 390px phone preview checked. One-column briefing, 28px H1, no horizontal scroll.
- [ ] Pull request opened. A person reviews and merges, not an agent.

**After deploy**

- [ ] `curl -sI https://develop-coaching.com/<slug>/` returns 200.
- [ ] The live page looked at in a browser, not just checked by script.
- [ ] Stage updated in `docs/blog-rollout-inventory.md`.

## Preview gotcha

`python3 -m http.server --directory www` serves the site well enough to check
layout, but confirm any colour or typography fault against the live URL before
calling it a bug. The reverse also applies: two faults found this way were real
and live, not preview artefacts.

## Known repairs the transformer performs

- **Unclosed anchors.** WordPress left anchors closed by a stray `</p>` on two
  articles. An anchor closed that way is never closed at all, so the parser
  adopts the rest of the article into the link: the whole body renders in link
  colour and every paragraph becomes a tab stop. The transformer closes them.
- **Duplicate lead image.** The intro block owns the lead image, so the
  article's own copy of the same file is removed rather than shown twice.
- **Multiple category tags.** Articles carrying two pillars are reduced to the
  one named in the content file, in the visible tag, the body class, the meta
  tag and the schema together.
