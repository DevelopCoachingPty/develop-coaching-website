# Blog rollout inventory

70 articles. Inventory reconciled across three independent sources (post sitemap, filesystem body classes, search index); the audit fails closed if they disagree. Regenerate with `python3 scripts/audit_blog_library.py`.

## Status key

| Column | Meaning |
| --- | --- |
| GEO | Readiness score out of 100 across eleven measured dimensions. See docs/blog-geo-backlog.md for the model. Lowest first, because that is the work queue. |
| Human content work | Needs a person to write or restructure: headline, intro, section headings, length, title and meta wording, image alt text. |
| Transformer handles | Fixed automatically when the shared design is applied: schema headline sync, canonical, contextual pillar link, single-pillar category. |
| Work | `Rewrite first` needs headline, intro or structure fixed before the shared design goes on. `Recategorise` needs a pillar decision. `Design only` is ready for the transformer. |
| Stage | Audit / Content review / Redesign / Approved / Deployed. Update by hand as each article moves. |

## Batches

- **Batch 1 (approval batch):** construction-sales-funnel, attract-the-right-clients, construction-job-pricing
- **Batches 2 onwards:** grouped by pillar in the order Plan, Attract, Convert, Deliver, Scale. No article is excluded.

## Totals

| Work needed | Articles |
| --- | --- |
| Reference | 1 |
| Design only | 54 |
| Recategorise | 1 |
| Rewrite first | 14 |

## Plan (15)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [become-financially-free](https://develop-coaching.com/become-financially-free/) | 42 | 478 | 0 | Rewrite first | Audit | h1-count-4, fluffy-intro, thin-478w, h2-count-0 | schema-headline-drift, no-pillar-link |
| [how-to-get-into-property-development](https://develop-coaching.com/how-to-get-into-property-development/) | 54 | 669 | 0 | Rewrite first | Audit | h1-count-4, thin-669w, h2-count-0 | schema-headline-drift, no-pillar-link |
| [pandemic-affect-construction](https://develop-coaching.com/pandemic-affect-construction/) | 60 | 1248 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [2021-builders-trades](https://develop-coaching.com/2021-builders-trades/) | 61 | 1153 | 0 | Rewrite first | Audit | h2-count-0, listicle-headline | schema-headline-drift, no-pillar-link |
| [how-to-grow-a-construction-business-2](https://develop-coaching.com/how-to-grow-a-construction-business-2/) | 64 | 1490 | 5 | Rewrite first | Audit | fluffy-intro, listicle-headline, em-dashes-1 | no-pillar-link |
| [what-we-can-learn-from-mount-everest](https://develop-coaching.com/what-we-can-learn-from-mount-everest/) | 64 | 858 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [construction-business-profits](https://develop-coaching.com/construction-business-profits/) | 84 | 1191 | 7 | Design only | Audit | none | none |
| [usp-for-construction-company](https://develop-coaching.com/usp-for-construction-company/) | 91 | 1289 | 6 | Design only | Audit | none | none |
| [business-coaching-for-construction](https://develop-coaching.com/business-coaching-for-construction/) | 92 | 1417 | 7 | Design only | Audit | none | none |
| [construction-business-goals](https://develop-coaching.com/construction-business-goals/) | 93 | 1173 | 7 | Design only | Audit | none | none |
| [construction-business-plan](https://develop-coaching.com/construction-business-plan/) | 96 | 2390 | 6 | Design only | Audit | none | none |
| [construction-business-performance](https://develop-coaching.com/construction-business-performance/) | 100 | 1713 | 7 | Design only | Audit | none | none |
| [construction-project-management](https://develop-coaching.com/construction-project-management/) | 100 | 2347 | 12 | Design only | Audit | none | none |
| [getting-off-the-tools](https://develop-coaching.com/getting-off-the-tools/) | 100 | 1481 | 6 | Design only | Audit | none | none |
| [sell-construction-company](https://develop-coaching.com/sell-construction-company/) | 100 | 1583 | 6 | Design only | Audit | none | none |

## Attract (18)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [good-reviews](https://develop-coaching.com/good-reviews/) | 56 | 737 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [construction-marketing](https://develop-coaching.com/construction-marketing/) | 57 | 2428 | 13 | Rewrite first | Audit | h1-count-2, fluffy-intro, em-dashes-4 | schema-headline-drift, no-pillar-link |
| [social-media-construction-industry](https://develop-coaching.com/social-media-construction-industry/) | 63 | 1392 | 6 | Rewrite first | Audit | no-intro-paragraph, em-dashes-7 | schema-headline-drift, no-pillar-link |
| [how-to-get-good-reviews](https://develop-coaching.com/how-to-get-good-reviews/) | 64 | 1886 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [digital-marketing-construction](https://develop-coaching.com/digital-marketing-construction/) | 69 | 1223 | 5 | Design only | Audit | meta-88ch | schema-headline-drift, no-pillar-link |
| [how-to-use-social-media-for-construction-business](https://develop-coaching.com/how-to-use-social-media-for-construction-business/) | 89 | 1052 | 6 | Design only | Audit | none | none |
| [how-to-get-clients-in-construction](https://develop-coaching.com/how-to-get-clients-in-construction/) | 91 | 1244 | 7 | Design only | Audit | none | none |
| [construction-brand](https://develop-coaching.com/construction-brand/) | 92 | 1918 | 5 | Design only | Audit | none | none |
| [how-to-deal-with-negative-reviews](https://develop-coaching.com/how-to-deal-with-negative-reviews/) | 93 | 1165 | 4 | Design only | Audit | none | none |
| [construction-marketing-ideas-to-scale-your-1m-business-to-5m](https://develop-coaching.com/construction-marketing-ideas-to-scale-your-1m-business-to-5m/) | 95 | 2233 | 6 | Design only | Audit | none | none |
| [grow-landscaping-business](https://develop-coaching.com/grow-landscaping-business/) | 95 | 1435 | 10 | Design only | Audit | none | none |
| [the-construction-company-marketing-strategy-to-scale-past-1m](https://develop-coaching.com/the-construction-company-marketing-strategy-to-scale-past-1m/) | 95 | 2238 | 8 | Design only | Audit | none | none |
| [construction-lead-generation](https://develop-coaching.com/construction-lead-generation/) | 96 | 1962 | 7 | Reference | Audit | none | none |
| [customer-reviews-for-construction-company](https://develop-coaching.com/customer-reviews-for-construction-company/) | 96 | 1905 | 6 | Design only | Audit | none | none |
| [how-to-find-good-tradesmen](https://develop-coaching.com/how-to-find-good-tradesmen/) | 96 | 1598 | 7 | Design only | Audit | none | none |
| [marketing-for-construction-companies-the-blueprint-to-scale](https://develop-coaching.com/marketing-for-construction-companies-the-blueprint-to-scale/) | 96 | 1859 | 7 | Design only | Audit | none | none |
| [attract-the-right-clients](https://develop-coaching.com/attract-the-right-clients/) **[batch 1]** | 100 | 1966 | 7 | Design only | Audit | none | none |
| [best-social-media-platforms-for-construction-companies](https://develop-coaching.com/best-social-media-platforms-for-construction-companies/) | 100 | 2288 | 7 | Design only | Audit | none | none |

## Convert (6)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [construction-contracts](https://develop-coaching.com/construction-contracts/) | 96 | 1638 | 8 | Design only | Audit | none | none |
| [construction-tendering](https://develop-coaching.com/construction-tendering/) | 96 | 1708 | 8 | Design only | Audit | none | none |
| [how-to-stop-wasting-time-on-quotes](https://develop-coaching.com/how-to-stop-wasting-time-on-quotes/) | 96 | 1439 | 6 | Design only | Audit | none | none |
| [construction-job-pricing](https://develop-coaching.com/construction-job-pricing/) **[batch 1]** | 100 | 1688 | 7 | Design only | Audit | none | none |
| [construction-sales-funnel](https://develop-coaching.com/construction-sales-funnel/) **[batch 1]** | 100 | 2368 | 10 | Design only | Audit | none | none |
| [how-to-price-construction-work](https://develop-coaching.com/how-to-price-construction-work/) | 100 | 1514 | 13 | Design only | Audit | none | none |

## Deliver (7)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [finding-skilled-tradesmen](https://develop-coaching.com/finding-skilled-tradesmen/) | 89 | 958 | 6 | Design only | Audit | none | none |
| [what-is-the-work-life-balance](https://develop-coaching.com/what-is-the-work-life-balance/) | 91 | 1847 | 5 | Design only | Audit | none | none |
| [time-in-construction](https://develop-coaching.com/time-in-construction/) | 96 | 2112 | 4 | Design only | Audit | none | none |
| [accounting-for-construction-companies](https://develop-coaching.com/accounting-for-construction-companies/) | 100 | 2126 | 14 | Design only | Audit | none | none |
| [construction-site-set-up-plan](https://develop-coaching.com/construction-site-set-up-plan/) | 100 | 2422 | 10 | Design only | Audit | none | none |
| [how-to-find-your-usp](https://develop-coaching.com/how-to-find-your-usp/) | 100 | 1709 | 10 | Design only | Audit | none | none |
| [perform-at-your-best](https://develop-coaching.com/perform-at-your-best/) | 100 | 1339 | 4 | Design only | Audit | none | none |

## Scale (20)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [how-to-grow-a-construction-business](https://develop-coaching.com/how-to-grow-a-construction-business/) | 65 | 1687 | 5 | Rewrite first | Audit | fluffy-intro, alt-missing-1 | no-pillar-link |
| [construction-business-systems](https://develop-coaching.com/construction-business-systems/) | 84 | 915 | 5 | Design only | Audit | none | none |
| [how-to-scale-your-construction-business](https://develop-coaching.com/how-to-scale-your-construction-business/) | 91 | 2141 | 5 | Design only | Audit | none | none |
| [grow-groundworks-business](https://develop-coaching.com/grow-groundworks-business/) | 95 | 1391 | 7 | Design only | Audit | none | none |
| [grow-painting-business](https://develop-coaching.com/grow-painting-business/) | 95 | 1642 | 9 | Design only | Audit | none | none |
| [delegation-in-construction](https://develop-coaching.com/delegation-in-construction/) | 96 | 1337 | 9 | Design only | Audit | none | none |
| [federation-of-master-builders](https://develop-coaching.com/federation-of-master-builders/) | 96 | 1529 | 7 | Design only | Audit | none | none |
| [mastering-construction-hiring-key-steps-for-building-a-skilled-workforce](https://develop-coaching.com/mastering-construction-hiring-key-steps-for-building-a-skilled-workforce/) | 96 | 2672 | 13 | Design only | Audit | none | none |
| [mistakes-when-scaling-a-construction-business](https://develop-coaching.com/mistakes-when-scaling-a-construction-business/) | 96 | 1251 | 9 | Design only | Audit | none | none |
| [profit-and-loss-statement-for-small-construction-company](https://develop-coaching.com/profit-and-loss-statement-for-small-construction-company/) | 96 | 1304 | 6 | Design only | Audit | none | none |
| [why-you-need-to-come-off-the-tools](https://develop-coaching.com/why-you-need-to-come-off-the-tools/) | 97 | 1019 | 6 | Design only | Audit | none | none |
| [construction-cash-flow-management-the-blueprint-to-scaling-past-1m](https://develop-coaching.com/construction-cash-flow-management-the-blueprint-to-scaling-past-1m/) | 100 | 2776 | 8 | Design only | Audit | none | none |
| [construction-networking](https://develop-coaching.com/construction-networking/) | 100 | 1426 | 6 | Design only | Audit | none | none |
| [construction-profit-margin-uk](https://develop-coaching.com/construction-profit-margin-uk/) | 100 | 2334 | 6 | Design only | Audit | none | none |
| [cost-cutting-in-construction](https://develop-coaching.com/cost-cutting-in-construction/) | 100 | 1561 | 7 | Design only | Audit | none | none |
| [grow-building-company](https://develop-coaching.com/grow-building-company/) | 100 | 1885 | 7 | Design only | Audit | none | none |
| [grow-carpentry-business](https://develop-coaching.com/grow-carpentry-business/) | 100 | 1555 | 11 | Design only | Audit | none | none |
| [grow-plastering-business](https://develop-coaching.com/grow-plastering-business/) | 100 | 1975 | 10 | Design only | Audit | none | none |
| [how-to-expand-electrical-business](https://develop-coaching.com/how-to-expand-electrical-business/) | 100 | 1328 | 7 | Design only | Audit | none | none |
| [trade-mastermind-construction](https://develop-coaching.com/trade-mastermind-construction/) | 100 | 2008 | 8 | Design only | Audit | none | none |

## Plan/Scale (1)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [how-to-recruit-for-your-construction-business](https://develop-coaching.com/how-to-recruit-for-your-construction-business/) | 43 | 2282 | 0 | Rewrite first | Audit | h1-count-7, meta-107ch, fluffy-intro, h2-count-0 | schema-headline-drift, no-pillar-link, categories-2 |

## Uncategorized (3)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [construction-business-marketing](https://develop-coaching.com/construction-business-marketing/) | 46 | 775 | 4 | Rewrite first | Audit | fluffy-intro | schema-headline-drift, no-pillar-link |
| [how-to-recruit-for-your-construction-business-2](https://develop-coaching.com/how-to-recruit-for-your-construction-business-2/) | 55 | 1057 | 6 | Rewrite first | Audit | fluffy-intro | schema-headline-drift, no-pillar-link |
| [digital-marketing-for-construction](https://develop-coaching.com/digital-marketing-for-construction/) | 75 | 1547 | 4 | Recategorise | Audit | em-dashes-2 | schema-headline-drift, no-pillar-link |

