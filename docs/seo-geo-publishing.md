# SEO and GEO publishing handoff

The production source is this repository's `www/` directory. WordPress at
`wp.develop-coaching.com` is an archive. A WordPress draft is not a live-site
publication or a release-ready handoff.

For every approved content item:
1. Identify the existing URL and relevant Five Pillars category. Check open PRs.
2. Supply the approved copy, source links, intended audience, contextual links
   and any verified client permissions or attribution to the website branch.
3. For managed blog pages, edit `content/blog-system/<slug>.json` and run
   `scripts/blog_design_system.py <slug>`. Preserve both the source and HTML.
4. For other existing pages, make targeted edits to `www/<slug>/index.html`.
   New pages use `scripts/publish_page.py`. Never run the full snapshot rebuild.
5. Check the canonical, robots, sitemap, search entry and visible content.
   Preserve working confirmation URLs, but exclude confirmed utility pages
   from indexing, sitemaps and search. Update generator exclusions as well.
6. Run the relevant tests, inspect the page in a browser, obtain independent
   review of the complete immutable change set, and merge through a PR.
7. Verify the deployed commit and real URLs before recording publication.

Use original explanations and verified examples. Label illustrative numbers.
Do not treat article length, JSON-LD presence or a checklist score as evidence
of AI visibility. Keep the existing 59-query panel and report engine coverage.
Google AI impressions are included in overall Search impressions.

Measurement distinguishes CTA clicks, scheduler starts, confirmed bookings,
qualified enquiries, attendance and sales. The current scheduler-start event
records focus entering the booking iframe. It is not a completed booking.
Do not add a booking event without a verified provider event or CRM receipt.
A full attribution check must reconcile landing page, source and qualification
with the booking and attendance records before claiming enquiry improvement.

Initial September release covers two utility URLs, verified redirecting anchors
and four existing guides. Homepage commercial terms remain pending Greg's
confirmation. Broader archive decisions need page-level performance and campaign
checks. Shared entity schema and legacy metadata remain separate follow-up work.
