# Blog GEO audit: ranked action backlog

70 articles audited. Median GEO readiness 96 out of 100. Lowest 42, highest 100. Regenerate with `python3 scripts/audit_blog_library.py`.

## How the score is built

Eleven dimensions, all measured from the page itself, totalling 100. Generative engines lift answers out of pages, so the model rewards a direct answer up front, headings phrased as the question a person actually asks, extractable lists, clean structured data and clear internal routes.

| Dimension | Points | What earns them |
| --- | ---: | --- |
| Direct answer up front | 12 | The opening answers the question instead of winding up to it |
| Question-shaped headings | 10 | Two or more headings phrased as a question |
| Extractable lists | 8 | Three or more ordered or unordered lists in the body |
| Heading structure | 12 | Exactly one H1, and at least four H2 sections |
| Depth | 8 | 1,200 words or more |
| Schema integrity | 12 | BlogPosting present, headline matches the H1, articleSection is a pillar, author is Greg |
| Metadata | 12 | Title 65 characters or fewer, meta description 110 to 165, canonical matches the slug |
| Internal routes | 10 | A contextual Five Pillars link in the body, and three or more internal links |
| Images and alt text | 6 | At least one body image, every image with real alt text |
| Freshness | 6 | Modified within 24 months |
| Brand compliance | 4 | No em dashes |

## What this score is not

It is a measure of whether a page is built to be quoted, not a measure of whether it earns traffic. There is no Google Analytics or Search Console access on this machine, so nothing here is weighted by sessions, impressions or rank. Two of the six duplicate decisions could flip with that data. Getting Search Console access is worth doing before the merge decisions are final.

## Top 10 actions, ranked

### 1. Credit Greg as the author in every article schema

**Articles affected:** 0

41 articles are attributed to seo@digital-progress.co.uk and five to jessica@digital-progress.co.uk. Seven name nobody. Four name Greg. Generative engines and Google both lean on the author entity when deciding whether a page carries real expertise, and the whole proposition here is Greg's experience. This is one field per page and the transformer can set it, but it is Greg's call whether he is named on all 71.

*Effort:* One transformer field. Needs Greg's yes, then it is mechanical.

### 2. Add a contextual Five Pillars link inside every article body

**Articles affected:** 16 &nbsp;&nbsp; **Score recoverable:** 224 points

The pillar links that exist sit in page furniture, which crawlers and answer engines discount. A link from inside the article body, in context, is what routes a reader from a question to the pillar that answers it. It is also the single largest pool of recoverable score in the audit.

*Effort:* Ships automatically with each article's briefing block.

### 3. Give every article at least two question-shaped headings

**Articles affected:** 26 &nbsp;&nbsp; **Score recoverable:** 195 points

51 articles contain no heading phrased as a question. Answer engines lift question-and-answer pairs; a heading that matches what someone typed is the cheapest way to become the passage that gets quoted. The briefing block supplies one, so most articles need one more in the body.

*Effort:* One heading rewrite per article, inside the rewrite pass.

### 4. Resolve the six near-duplicate pairs

**Articles affected:** 12

Twelve articles are competing with a sibling for the same term, so neither can win outright and internal link equity is split. No amount of redesign fixes two pages arguing over one query. Recommendations per pair are in docs/blog-duplicate-pairs.md; nothing gets merged or redirected without Greg's approval, one pair at a time.

*Effort:* One decision per pair, then a merge plus redirects in two files.

### 5. Fix the second unclosed anchor, on best-social-media-platforms-for-construction-companies

**Articles affected:** 1

An anchor closed by a stray </p> is never closed at all, so the parser pulls the rest of the article into the link. The whole body renders in link colour and every paragraph becomes a keyboard tab stop. This is live now. The same fault on construction-sales-funnel is already fixed.

*Effort:* The transformer repairs it automatically when that article is done.

### 6. Replace preamble openings with a direct answer

**Articles affected:** 8 &nbsp;&nbsp; **Score recoverable:** 96 points

27 articles open with a wind-up rather than an answer. Both a reader deciding whether to stay and a model deciding what to quote read the first block. If the answer is in paragraph five, neither finds it.

*Effort:* Part of the rewrite pass, then the intro block carries it.

### 7. Repair heading structure: single H1, at least four H2 sections

**Articles affected:** 9 &nbsp;&nbsp; **Score recoverable:** 72 points

13 articles use H1 for section headings, so the page has no single subject. 18 have fewer than four H2 sections, which leaves long unbroken runs of prose that cannot be extracted as a passage. The transformer can demote stray H1s; adding real sections is writing.

*Effort:* Demotion is automatic. New sections are part of the rewrite.

### 8. Assign one pillar to every article and make schema agree

**Articles affected:** 4

16 articles carry no pillar or the wrong one in their structured data, and some carry two at once. The pillar is how the site explains its own shape, in the visible tag, the body class, the meta tag and the schema together.

*Effort:* One field in the content file. The transformer syncs all four places.

### 9. Remove em dashes from article body copy

**Articles affected:** 4 &nbsp;&nbsp; **Score recoverable:** 16 points

22 articles carry em dashes, 121 in total, against the house style rule. Low search impact, but it is a visible inconsistency on pages being reviewed for exactly that.

*Effort:* Sentence by sentence inside the rewrite pass. Not a find and replace.

### 10. Add a lead image with real alt text where one is missing

**Articles affected:** 10 &nbsp;&nbsp; **Score recoverable:** 30 points

21 articles have no image in the body at all. Others carry alt text that repeats the file name. The design puts a full width image directly under the answer, so an article without one cannot meet the standard.

*Effort:* Sourcing or generating an image per article. The slowest item here.

## The ten lowest scoring articles

| Article | GEO | Words | Weakest dimensions |
| --- | ---: | ---: | --- |
| [become-financially-free](https://develop-coaching.com/become-financially-free/) | 42 | 478 | Direct answer up front; Question-shaped headings; Extractable lists; Heading structure; Depth; Schema integrity; Internal routes; Images and alt text |
| [how-to-recruit-for-your-construction-business](https://develop-coaching.com/how-to-recruit-for-your-construction-business/) | 43 | 2282 | Direct answer up front; Question-shaped headings; Extractable lists; Heading structure; Schema integrity; Metadata; Internal routes; Images and alt text |
| [construction-business-marketing](https://develop-coaching.com/construction-business-marketing/) | 46 | 775 | Direct answer up front; Question-shaped headings; Extractable lists; Depth; Schema integrity; Internal routes |
| [how-to-get-into-property-development](https://develop-coaching.com/how-to-get-into-property-development/) | 54 | 669 | Question-shaped headings; Extractable lists; Heading structure; Depth; Schema integrity; Internal routes; Images and alt text |
| [how-to-recruit-for-your-construction-business-2](https://develop-coaching.com/how-to-recruit-for-your-construction-business-2/) | 55 | 1057 | Direct answer up front; Question-shaped headings; Extractable lists; Depth; Schema integrity; Internal routes |
| [good-reviews](https://develop-coaching.com/good-reviews/) | 56 | 737 | Question-shaped headings; Extractable lists; Heading structure; Depth; Schema integrity; Internal routes; Images and alt text |
| [construction-marketing](https://develop-coaching.com/construction-marketing/) | 57 | 2428 | Direct answer up front; Question-shaped headings; Heading structure; Schema integrity; Internal routes; Images and alt text; Brand compliance |
| [pandemic-affect-construction](https://develop-coaching.com/pandemic-affect-construction/) | 60 | 1248 | Question-shaped headings; Extractable lists; Heading structure; Schema integrity; Internal routes; Images and alt text |
| [2021-builders-trades](https://develop-coaching.com/2021-builders-trades/) | 61 | 1153 | Question-shaped headings; Extractable lists; Heading structure; Depth; Schema integrity; Internal routes; Images and alt text |
| [social-media-construction-industry](https://develop-coaching.com/social-media-construction-industry/) | 63 | 1392 | Direct answer up front; Extractable lists; Schema integrity; Internal routes; Brand compliance |
