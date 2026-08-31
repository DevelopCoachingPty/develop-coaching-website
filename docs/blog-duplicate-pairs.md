# Near-duplicate article pairs: keep, merge, redirect

Twelve articles are competing with a sibling for the same search term. Neither
page in a pair can win outright, and internal link equity is split between them.
No amount of redesign fixes two pages arguing over one query.

**Nothing here is merged or redirected without Greg approving that pair.** They
go to him one at a time, in the order below.

## What the recommendation is based on

Depth, internal inbound links from elsewhere on the site, publish date, slug
quality and GEO readiness. All of it measured from the site itself.

**What it is not based on:** actual rankings, impressions or clicks. There is no
Search Console access on this machine. Pairs 3 and 5 are close enough that real
search data could flip them, and both are marked accordingly. Worth getting that
access before those two are final.

## Recommendations

### Pair 1. USP for construction company

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `usp-for-construction-company` | `usp-for-construction-company-2` |
| Words | 1,127 | 902 |
| Inbound internal links | 1 | 0 |
| Published | Sep 2022 | Nov 2021 |
| GEO | 70 | 51 |

**Recommendation:** keep `usp-for-construction-company`. It is longer, newer,
scores 19 points higher, holds the only inbound link and owns the clean slug.
Move anything distinctive from the older piece into it, then 301 the `-2`.

**Confidence:** high. Every signal points the same way.

### Pair 2. How to grow a construction business

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `how-to-grow-a-construction-business` | `how-to-grow-a-construction-business-2` |
| Words | 1,687 | 1,490 |
| Inbound internal links | 1 | 0 |
| Published | Jan 2023 | Apr 2020 |
| GEO | 62 | 61 |

**Recommendation:** keep `how-to-grow-a-construction-business`. Nearly three
years newer, longer, holds the inbound link, clean slug. The two are also filed
under different pillars, Scale and Plan, which is a symptom of the duplication
rather than a reason to keep both.

**Confidence:** high.

### Pair 3. How to recruit for your construction business

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `how-to-recruit-for-your-construction-business` | `how-to-recruit-for-your-construction-business-2` |
| Words | 2,282 | 1,057 |
| Inbound internal links | 4 | 2 |
| Published | Apr 2023 | Apr 2022 |
| GEO | 40 | 52 |
| H2 sections | 0 | 6 |

**Recommendation:** keep `how-to-recruit-for-your-construction-business`, but
rebuild it using the other article's section structure. The keeper has twice the
substance, twice the inbound links and the clean slug, and it is the newer piece.
It scores lower only because it has no H2 sections at all, which is a formatting
fault rather than a content one, and it is exactly what the rewrite pass fixes.
Take the `-2` article's headings as the skeleton, fold its content in, then 301 it.

**Confidence:** medium. This is the pair where the better content and the better
structure sit on different URLs. The call rests on inbound links and depth, and
search data could change it.

### Pair 4. Getting good reviews

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `how-to-get-good-reviews` | `good-reviews` |
| Words | 1,886 | 737 |
| Inbound internal links | 1 | 0 |
| Published | Jun 2019 | Oct 2021 |
| GEO | 61 | 53 |

**Recommendation:** keep `how-to-get-good-reviews`. Two and a half times the
length, holds the inbound link, and the slug matches the phrase a person types.
`good-reviews` is newer but thin, and its title is a bare question with the brand
name bolted on.

**Worth raising with Greg at the same time:** reviews are covered across four
articles. `how-to-get-good-reviews`, `good-reviews`,
`how-to-deal-with-negative-reviews` and `customer-reviews-for-construction-company`.
The other two are distinct enough to keep, but the cluster is worth a look as a
whole rather than one merge in isolation.

**Confidence:** high on the merge. The wider cluster needs a separate decision.

### Pair 5. Digital marketing for construction

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `digital-marketing-for-construction` | `digital-marketing-construction` |
| Words | 1,547 | 1,223 |
| Inbound internal links | 0 | 0 |
| Published | Aug 2019 | Sep 2021 |
| GEO | 72 | 66 |

**Recommendation:** keep `digital-marketing-for-construction`. It is longer,
scores higher, already has a question-shaped heading, and its slug reads as the
natural phrase. Against it: it is the older piece and it currently sits
uncategorised, so it needs a pillar either way.

**Confidence:** low to medium. Neither article has a single inbound internal
link, so the usual tiebreaker is absent, and the newer piece has the fresher
date. This is the pair most likely to flip with Search Console data. Recommend
holding this one until that access exists.

### Pair 6. Construction marketing

| | Keep | Merge and redirect |
| --- | --- | --- |
| Article | `construction-marketing` | `construction-business-marketing` |
| Words | 2,428 | 775 |
| Inbound internal links | 4 | 1 |
| Published | Oct 2023 | Jan 2023 |
| GEO | 54 | 43 |
| H2 sections | 13 | 4 |

**Recommendation:** keep `construction-marketing`. Three times the length, four
times the inbound links, newer, and the broader term. `construction-business-marketing`
is a 775 word piece with no clear job of its own.

**Confidence:** high.

## If a merge is approved

1. Move anything the losing article says that the keeper does not into the keeper.
2. Add the redirect to **both** `export/manual-redirects.json` and `www/vercel.json`,
   with the bare path and the trailing slash version, as the repo guide requires.
3. Update any internal links that pointed at the retired URL.
4. Rerun `python3 scripts/audit_blog_library.py`. The article count drops and the
   three inventory sources must still agree.
5. Verify the redirect on the live URL after deploy, not just the build.
