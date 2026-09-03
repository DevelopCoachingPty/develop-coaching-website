# Orphan page audit, 3 September 2026

Ahrefs reported 105 orphan pages during a crawl that was still running. The saved
audit evidence contains 50 visible URL rows, not the full export. A repository
crawl independently reproduced 76 sitemap URLs with no href link from another
local HTML page. The two sets overlap but are not identical because the Ahrefs
snapshot also flags podcast pages that local archive pagination links to.

The missing 55 Ahrefs rows cannot be reconstructed exactly without a full export.
They are not guessed here. This report therefore records the complete, repeatable
76-URL repository baseline and keeps the audit discrepancy explicit.

## Links added now

- `/blog/`, linked from the home page footer
- `/trades-pipeline-diagnostic/`, linked from the home page footer
- `/terms-conditions/`, linked from the home page legal footer
- `/groundwork-business-coach/`, linked from the matching groundworks guide
- `/decorating-business-coach/`, linked from the matching painting guide
- `/carpentry-business-coach/`, linked from the matching carpentry guide
- `/electrical-business-coach/`, linked from the matching electrical guide
- `/plastering-business-coach/`, linked from the matching plastering guide
- `/landscaping-business-coach/`, linked from the matching landscaping guide

The blog was visible in the saved Ahrefs rows but not in the 76-URL local baseline,
because the local search page already links to it. The new home page link gives it
a direct route from the site's primary entry page.

## Deferred groups

Standalone testimonials should be reconciled with the current `/client-wins/`
proof hub before links or redirects are chosen. Test, duplicate, archive and old
campaign pages are removal or redirect candidates, not pages to promote. Lead
capture, booking and thank-you URLs are funnel steps and should not receive public
navigation links without confirming the active campaigns and intended sequence.
Podcast rows from the saved Ahrefs evidence need a separate podcast archive check,
because the repository currently links them from paginated archive pages.

Every URL in the baseline has one action classification:

- `linked now`: the eight locally reproducible URLs in the link list above
  (the ninth link, `/blog/`, comes from the saved Ahrefs rows)
- `proof consolidation`: the 20 named client testimonial URLs, pending
  reconciliation with `/client-wins/`
- `obsolete candidate`: `/10795-2/`, the three `5-steps-to-5-million` event URLs,
  `/blog_2/`, `/build-your-future-event-page/`, `/contact-2/`, `/fire-figure/`,
  the five URLs beginning with `/test`, `/upgradelondonvip/`, and
  `/usp-for-construction-company-2/`
- `decision needed`: `/courses/`, `/greg-wilkes-media/`, `/how-we-work/`, and
  `/locations.kml/`
- `funnel or campaign stage`: the remaining 29 baseline URLs, including lead
  capture, booking, event, webinar, download and thank-you steps

## Reproducible 76-URL baseline

```text
/10795-2/
/5-profit-leaks-bonus/
/5-profit-leaks-workshop/
/5-steps-to-5-million-2/
/5-steps-to-5-million-edinburgh-registration-2/
/5-steps-to-5-million-in-2024-vip/
/annual-growth-calculator/
/aus-cost-guide-download/
/before-your-scale-session-2/
/blog_2/
/book-download/
/brad-testimonial/
/bradley-testimonial/
/build-your-future-event-page/
/carpentry-business-coach/
/contact-2/
/courses/
/dale-testimonial/
/dan-testimonial/
/dave-testimonial/
/decorating-business-coach/
/dominic-testimonial/
/double-your-profits-workshop/
/download-book-form/
/electrical-business-coach/
/event-booking/
/fire-figure/
/free-book-download/
/geoff-testimonial/
/george-testimonial/
/greg-testimonial/
/greg-wilkes-media/
/groundwork-business-coach/
/how-we-work/
/james-overton-testimonial/
/james-wilcock-testimonial/
/landscaping-business-coach/
/locations.kml/
/lukas-testimonial/
/mike-and-nick-testimonial/
/plastering-business-coach/
/richard-abrahams-testimonial/
/richard-jenkinson-testimonial/
/sam-and-nathan-testimonial/
/schedule-a-call-book/
/schedule-a-call-subscribe/
/sell-your-construction-company/
/sophie-and-neil-testimonial/
/stephen-and-ashley-testimonial-2/
/stephen-and-salina-testimonial/
/terms-conditions/
/test-landing-page/
/test-page/
/test/
/testimonial/
/testing-sop/
/thank-you-5m-builder-gameplan/
/thank-you-build-scale-summit/
/thank-you-built-to-cash-out/
/thank-you-subscribe-2/
/thank-you/
/thankyou/
/the-5m-builder-game-plan-workshop/
/the-build-and-scale-summit-2025/
/the-perfect-project/
/the-schedule-page-subscribers/
/the-schedule-page/
/trades-pipeline-diagnostic/
/uk-cost-guide-download/
/uk-cost-guide/
/upgradelondonvip/
/usp-for-construction-company-2/
/valy-testimonial/
/webinar/
/win-big-clients-webinar/
/win-big-clients/
```

## Method

The baseline normalises the 371 URLs in `export/all-sitemap-urls.txt`, parses all
local `www/**/*.html` anchors, ignores self-links and external domains, and reports
sitemap paths with no href source page. Live HTTP checks confirmed the priority
targets return 200. Redirect, sitemap, robots, image and head metadata changes are
deliberately outside this pull request.
