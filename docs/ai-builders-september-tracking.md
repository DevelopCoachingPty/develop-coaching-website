# September workshop confirmation and attribution

Issue: #58. Dedicated return: `/ai-for-builders-september-2026/thank-you/`.

The checkout still loads automatically. New sessions return to the thank-you page; existing landing-page payment returns forward there before creating checkout. The status API checks the event, price, currency, amount, quantity and paid/complete state. Confirmation contains no buyer details and is never based on URL parameters alone. Payment references are removed from the address bar before optional analytics and retained in session storage for reload verification. Responses are not cached.

## Attribution and campaign links

All five labels are lower-case ASCII letters/digits, hyphens or underscores, maximum 50 characters. Invalid labels are discarded. Never include names, email addresses, phone numbers or other personal details in campaign labels. First touch is retained for this workshop in session storage, including a direct first touch; later campaign links do not overwrite it. With marketing consent it also persists in local storage for return visits. Without consent, cross-session attribution is intentionally unavailable. If storage is blocked the current visit's labels still reach checkout.

Each field is stored as `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` on Stripe Checkout Session and PaymentIntent metadata. `metadata[event]` and event-only `client_reference_id` remain intact. The status API returns only these sanitised labels plus payment status/amount/currency/session ID/livemode. Original attribution is read from Stripe on confirmation, not from confirmation URL UTMs. Attempt IDs retain first-touch attribution for idempotent retries. The v2 attempt storage and Stripe idempotency namespace isolate the new return URL/metadata contract from pre-deployment sessions.

Ready-to-use campaign links (replace creative/audience labels as required):

- Meta: https://develop-coaching.com/ai-for-builders-september-2026/?utm_source=meta&utm_medium=paid_social&utm_campaign=ai-builders-september-2026&utm_content=reel-01&utm_term=uk-builders
- Email: https://develop-coaching.com/ai-for-builders-september-2026/?utm_source=email&utm_medium=email&utm_campaign=ai-builders-september-2026&utm_content=invite-01&utm_term=builders-list
- LinkedIn: https://develop-coaching.com/ai-for-builders-september-2026/?utm_source=linkedin&utm_medium=organic_social&utm_campaign=ai-builders-september-2026&utm_content=launch-post&utm_term=builders

No existing adverts or email campaigns were edited. The older shared-payment-link counter parses `client_reference_id` and needs a separate change to consume these event-specific session metadata fields; its Sheet/Slack reporting is not verified by this PR.

## Conversion behaviour

Explicit consent is required before loading Meta or GA4. A visible bottom banner presents equal Allow and Decline choices; either choice dismisses it. The footer Tracking preferences button reopens it. Global Privacy Control and Do Not Track suppress both providers. Revocation disables Google collection and revokes Meta consent. Preview hosts never load either provider.

GA4 uses the existing Develop Coaching property 391358782, web stream 5655239787, measurement ID `G-PXT2VCVFLW`, verified in live Analytics Admin on 13 September 2026. The older notes' `G-EX5H3P27NP` is not this stream. Basic consent mode loads the tag only after opt-in. Google advertising storage, advertising user data and ad personalisation remain denied. Configuration suppresses the automatic page view, sets a canonical URL without query or fragment, omits the referrer, and supplies sanitised first-touch campaign fields. The confirmation script removes payment references before analytics initialises. See [Google consent guidance](https://developers.google.com/tag-platform/security/guides/consent) and [manual page-view guidance](https://developers.google.com/analytics/devguides/collection/ga4/views).

Meta PageView and landing-page ViewContent correspond to GA4 page_view and view_item, once per page after consent. InitiateCheckout and begin_checkout mean a click on a registration CTA, once per page. The automatically loaded Stripe form creates no intent event. Someone who goes straight to the embedded form without using a CTA can purchase without a begin_checkout event. Do not use Stripe session creation or form loads as unique visitors or checkout intent.

Purchase requires a server-verified live paid session. Its Stripe session ID is the stable Meta eventID and GA4 transaction_id. Purchase campaign fields use the sanitised attribution returned by Stripe. All explicit GA events include workshop_id `ai-for-builders-september-2026`. Group this workshop by event/page even when existing email and ad campaign labels differ. Existing campaign links are preserved.

Stripe paid, completed sessions with matching workshop metadata, currency and amount remain the source of truth for sales. GA4 and Meta report consented, delivered browser events only. Reconcile reporting to Stripe; never divide total Stripe sales by consented GA visits and call that an all-visitor conversion rate. Historical visits cannot be recovered by installing tracking now.

A local/session storage ledger suppresses repeat purchases on reload. Storage failure suppresses Purchase rather than risking duplicates. Meta eventID also supports matching a future server event. This is browser-side deduplication, not a global database ledger: clearing storage or another device can emit again. No CAPI integration is claimed. Delivery cannot be guaranteed if pixels are blocked or the buyer never returns.

## Fulfilment and release

No joining URL, booking email sender, replay delivery automation or September webhook was found in the website API or docs. The page directs buyers to hello@develop-coaching.com, matching existing verified copy, without promising email delivery. Arrange/verify fulfilment separately before promoting sales.

Local safe preview: `node tests/ai-builders-preview.cjs`, then http://127.0.0.1:4296/ai-for-builders-september-2026/ . Mock paid reference `cs_test_paid`; pending `cs_test_pending`; provider failure `cs_test_failure`. These are fixtures, never live purchases. The requested 15-minute Scale Session calendar is embedded below the introduction video, reusing the booking widget from `/schedule-a-call/` and `/contact-2/`. It has a direct-link fallback and no-referrer policy. No appointment was submitted. Local CSP allows this scheduler frame and blocks external scripts and fetches; production host and Stripe livemode gates suppress marketing conversion calls.

This static repository has no package build, lint or TypeScript pipeline for these pages and no database migrations. Use `node --test tests/ai-builders-*.test.cjs`, JS syntax checks, HTML parsing and browser proof. Never run the full frozen-site rebuild. After reviewed merge, verify production assets/return URL and consent-off negative states. A real successful payment and fulfilment remain untested; no card entry or live purchase was performed.
