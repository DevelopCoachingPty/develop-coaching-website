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
| Design only | 31 |
| Recategorise | 6 |
| Rewrite first | 32 |

## Plan (13)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [become-financially-free](https://develop-coaching.com/become-financially-free/) | 42 | 478 | 0 | Rewrite first | Audit | h1-count-4, fluffy-intro, thin-478w, h2-count-0 | schema-headline-drift, no-pillar-link |
| [how-to-get-into-property-development](https://develop-coaching.com/how-to-get-into-property-development/) | 54 | 669 | 0 | Rewrite first | Audit | h1-count-4, thin-669w, h2-count-0 | schema-headline-drift, no-pillar-link |
| [pandemic-affect-construction](https://develop-coaching.com/pandemic-affect-construction/) | 60 | 1248 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [2021-builders-trades](https://develop-coaching.com/2021-builders-trades/) | 61 | 1153 | 0 | Rewrite first | Audit | h2-count-0, listicle-headline | schema-headline-drift, no-pillar-link |
| [how-to-grow-a-construction-business-2](https://develop-coaching.com/how-to-grow-a-construction-business-2/) | 64 | 1490 | 5 | Rewrite first | Audit | fluffy-intro, listicle-headline, em-dashes-1 | no-pillar-link |
| [what-we-can-learn-from-mount-everest](https://develop-coaching.com/what-we-can-learn-from-mount-everest/) | 64 | 858 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [construction-business-profits](https://develop-coaching.com/construction-business-profits/) | 84 | 1191 | 7 | Design only | Audit | none | none |
| [usp-for-construction-company](https://develop-coaching.com/usp-for-construction-company/) | 87 | 1287 | 6 | Design only | Audit | em-dashes-2 | none |
| [construction-business-plan](https://develop-coaching.com/construction-business-plan/) | 96 | 2390 | 6 | Design only | Audit | none | none |
| [construction-business-performance](https://develop-coaching.com/construction-business-performance/) | 100 | 1713 | 7 | Design only | Audit | none | none |
| [construction-project-management](https://develop-coaching.com/construction-project-management/) | 100 | 2347 | 12 | Design only | Audit | none | none |
| [getting-off-the-tools](https://develop-coaching.com/getting-off-the-tools/) | 100 | 1481 | 6 | Design only | Audit | none | none |
| [sell-construction-company](https://develop-coaching.com/sell-construction-company/) | 100 | 1583 | 6 | Design only | Audit | none | none |

## Attract (16)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [good-reviews](https://develop-coaching.com/good-reviews/) | 56 | 737 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [construction-marketing](https://develop-coaching.com/construction-marketing/) | 57 | 2428 | 13 | Rewrite first | Audit | h1-count-2, fluffy-intro, em-dashes-4 | schema-headline-drift, no-pillar-link |
| [social-media-construction-industry](https://develop-coaching.com/social-media-construction-industry/) | 63 | 1392 | 6 | Rewrite first | Audit | no-intro-paragraph, em-dashes-7 | schema-headline-drift, no-pillar-link |
| [how-to-get-good-reviews](https://develop-coaching.com/how-to-get-good-reviews/) | 64 | 1886 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [digital-marketing-construction](https://develop-coaching.com/digital-marketing-construction/) | 69 | 1223 | 5 | Design only | Audit | meta-88ch | schema-headline-drift, no-pillar-link |
| [how-to-use-social-media-for-construction-business](https://develop-coaching.com/how-to-use-social-media-for-construction-business/) | 89 | 1052 | 6 | Design only | Audit | none | none |
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

## Convert (5)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [construction-contracts](https://develop-coaching.com/construction-contracts/) | 96 | 1638 | 8 | Design only | Audit | none | none |
| [construction-tendering](https://develop-coaching.com/construction-tendering/) | 96 | 1708 | 8 | Design only | Audit | none | none |
| [how-to-stop-wasting-time-on-quotes](https://develop-coaching.com/how-to-stop-wasting-time-on-quotes/) | 96 | 1439 | 6 | Design only | Audit | none | none |
| [construction-job-pricing](https://develop-coaching.com/construction-job-pricing/) **[batch 1]** | 100 | 1688 | 7 | Design only | Audit | none | none |
| [construction-sales-funnel](https://develop-coaching.com/construction-sales-funnel/) **[batch 1]** | 100 | 2368 | 10 | Design only | Audit | none | none |

## Deliver (8)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [finding-skilled-tradesmen](https://develop-coaching.com/finding-skilled-tradesmen/) | 48 | 788 | 5 | Rewrite first | Audit | meta-60ch, fluffy-intro | no-pillar-link |
| [accounting-for-construction-companies](https://develop-coaching.com/accounting-for-construction-companies/) | 57 | 1987 | 0 | Rewrite first | Audit | h1-count-10, fluffy-intro, h2-count-0 | schema-headline-drift, no-pillar-link |
| [how-to-find-your-usp](https://develop-coaching.com/how-to-find-your-usp/) | 66 | 1376 | 0 | Rewrite first | Audit | h1-count-6, h2-count-0 | schema-headline-drift, no-pillar-link |
| [perform-at-your-best](https://develop-coaching.com/perform-at-your-best/) | 69 | 1086 | 0 | Rewrite first | Audit | h2-count-0 | schema-headline-drift, no-pillar-link |
| [trade-mastermind-construction](https://develop-coaching.com/trade-mastermind-construction/) | 69 | 1836 | 7 | Rewrite first | Audit | fluffy-intro | no-pillar-link |
| [time-in-construction](https://develop-coaching.com/time-in-construction/) | 70 | 1947 | 3 | Design only | Audit | em-dashes-2 | no-pillar-link |
| [construction-business-goals](https://develop-coaching.com/construction-business-goals/) | 74 | 982 | 6 | Design only | Audit | none | schema-headline-drift, no-pillar-link |
| [construction-site-set-up-plan](https://develop-coaching.com/construction-site-set-up-plan/) | 89 | 2202 | 9 | Design only | Audit | none | no-pillar-link |

## Scale (12)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [mastering-construction-hiring-key-steps-for-building-a-skilled-workforce](https://develop-coaching.com/mastering-construction-hiring-key-steps-for-building-a-skilled-workforce/) | 50 | 2440 | 0 | Rewrite first | Audit | h1-count-8, fluffy-intro, h2-count-0 | schema-headline-drift, no-pillar-link |
| [profit-and-loss-statement-for-small-construction-company](https://develop-coaching.com/profit-and-loss-statement-for-small-construction-company/) | 54 | 1165 | 5 | Rewrite first | Audit | meta-62ch, fluffy-intro, em-dashes-1 | schema-headline-drift, no-pillar-link |
| [why-you-need-to-come-off-the-tools](https://develop-coaching.com/why-you-need-to-come-off-the-tools/) | 57 | 815 | 0 | Rewrite first | Audit | h1-count-3, h2-count-0 | no-pillar-link |
| [how-to-grow-a-construction-business](https://develop-coaching.com/how-to-grow-a-construction-business/) | 65 | 1687 | 5 | Rewrite first | Audit | fluffy-intro, alt-missing-1 | no-pillar-link |
| [delegation-in-construction](https://develop-coaching.com/delegation-in-construction/) | 66 | 1160 | 8 | Design only | Audit | meta-59ch, em-dashes-10 | schema-headline-drift, no-pillar-link |
| [construction-profit-margin-uk](https://develop-coaching.com/construction-profit-margin-uk/) | 69 | 2116 | 5 | Rewrite first | Audit | fluffy-intro, em-dashes-2 | schema-headline-drift, no-pillar-link |
| [how-to-scale-your-construction-business](https://develop-coaching.com/how-to-scale-your-construction-business/) | 70 | 2028 | 5 | Design only | Audit | none | schema-headline-drift, no-pillar-link |
| [construction-cash-flow-management-the-blueprint-to-scaling-past-1m](https://develop-coaching.com/construction-cash-flow-management-the-blueprint-to-scaling-past-1m/) | 74 | 2528 | 7 | Design only | Audit | title-87ch | schema-headline-drift, no-pillar-link |
| [cost-cutting-in-construction](https://develop-coaching.com/cost-cutting-in-construction/) | 74 | 1474 | 5 | Rewrite first | Audit | h1-count-2 | no-pillar-link |
| [mistakes-when-scaling-a-construction-business](https://develop-coaching.com/mistakes-when-scaling-a-construction-business/) | 75 | 1113 | 8 | Design only | Audit | em-dashes-7 | schema-headline-drift, no-pillar-link |
| [federation-of-master-builders](https://develop-coaching.com/federation-of-master-builders/) | 81 | 1357 | 5 | Rewrite first | Audit | h1-count-2 | schema-headline-drift, no-pillar-link |
| [construction-business-systems](https://develop-coaching.com/construction-business-systems/) | 84 | 915 | 5 | Design only | Audit | none | none |

## Attract/Convert (1)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [how-to-get-clients-in-construction](https://develop-coaching.com/how-to-get-clients-in-construction/) | 51 | 1112 | 6 | Rewrite first | Audit | meta-43ch, fluffy-intro, alt-missing-1 | no-pillar-link, categories-2 |

## Plan/Scale (1)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [how-to-recruit-for-your-construction-business](https://develop-coaching.com/how-to-recruit-for-your-construction-business/) | 43 | 2282 | 0 | Rewrite first | Audit | h1-count-7, meta-107ch, fluffy-intro, h2-count-0 | schema-headline-drift, no-pillar-link, categories-2 |

## Uncategorized (14)

| Article | GEO | Words | H2s | Work | Stage | Human content work | Transformer handles |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| [construction-business-marketing](https://develop-coaching.com/construction-business-marketing/) | 46 | 775 | 4 | Rewrite first | Audit | fluffy-intro | schema-headline-drift, no-pillar-link |
| [business-coaching-for-construction](https://develop-coaching.com/business-coaching-for-construction/) | 48 | 1268 | 6 | Rewrite first | Audit | fluffy-intro, em-dashes-1 | schema-headline-drift, no-pillar-link |
| [grow-groundworks-business](https://develop-coaching.com/grow-groundworks-business/) | 55 | 1182 | 6 | Rewrite first | Audit | fluffy-intro, em-dashes-5 | schema-headline-drift, no-pillar-link |
| [how-to-recruit-for-your-construction-business-2](https://develop-coaching.com/how-to-recruit-for-your-construction-business-2/) | 55 | 1057 | 6 | Rewrite first | Audit | fluffy-intro | schema-headline-drift, no-pillar-link |
| [grow-building-company](https://develop-coaching.com/grow-building-company/) | 62 | 1987 | 7 | Recategorise | Audit | meta-53ch, em-dashes-9 | canonical-mismatch, schema-headline-drift, no-pillar-link |
| [grow-plastering-business](https://develop-coaching.com/grow-plastering-business/) | 63 | 1837 | 8 | Rewrite first | Audit | title-68ch, fluffy-intro, em-dashes-10 | schema-headline-drift, no-pillar-link |
| [how-to-expand-electrical-business](https://develop-coaching.com/how-to-expand-electrical-business/) | 67 | 1181 | 6 | Recategorise | Audit | title-82ch, em-dashes-4 | schema-headline-drift, no-pillar-link |
| [how-to-price-construction-work](https://develop-coaching.com/how-to-price-construction-work/) | 67 | 1320 | 3 | Rewrite first | Audit | h1-count-10 | schema-headline-drift, no-pillar-link |
| [grow-painting-business](https://develop-coaching.com/grow-painting-business/) | 70 | 1460 | 8 | Recategorise | Audit | title-66ch, em-dashes-3 | schema-headline-drift, no-pillar-link |
| [what-is-the-work-life-balance](https://develop-coaching.com/what-is-the-work-life-balance/) | 70 | 1715 | 4 | Recategorise | Audit | em-dashes-10 | schema-headline-drift, no-pillar-link |
| [best-social-media-platforms-for-construction-companies](https://develop-coaching.com/best-social-media-platforms-for-construction-companies/) | 74 | 2062 | 6 | Rewrite first | Audit | fluffy-intro | no-pillar-link |
| [construction-networking](https://develop-coaching.com/construction-networking/) | 74 | 1249 | 5 | Recategorise | Audit | em-dashes-1 | schema-headline-drift, no-pillar-link |
| [digital-marketing-for-construction](https://develop-coaching.com/digital-marketing-for-construction/) | 75 | 1547 | 4 | Recategorise | Audit | em-dashes-2 | schema-headline-drift, no-pillar-link |
| [grow-carpentry-business](https://develop-coaching.com/grow-carpentry-business/) | 82 | 1398 | 9 | Rewrite first | Audit | h1-count-2 | schema-headline-drift, no-pillar-link |

