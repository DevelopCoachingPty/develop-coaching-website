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

Explicit consent is required before loading Meta. Global Privacy Control and Do Not Track suppress marketing events. Choices remain available in the page footer. Meta PageView and landing-page ViewContent fire after consent; InitiateCheckout fires after the embedded form mounts (also if consent is granted later). Purchase requires a server-verified live paid session. Its Stripe session ID is the stable Meta eventID and, when an existing gtag is available, GA transaction_id. No new GA property is installed.

A local/session storage ledger suppresses repeat purchases on reload. Storage failure suppresses Purchase rather than risking duplicates. Meta eventID also supports matching a future server event. This is browser-side deduplication, not a global database ledger: clearing storage or another device can emit again. No CAPI integration is claimed. Delivery cannot be guaranteed if pixels are blocked or the buyer never returns.

## Fulfilment and release

No joining URL, booking email sender, replay delivery automation or September webhook was found in the website API or docs. The page directs buyers to hello@develop-coaching.com, matching existing verified copy, without promising email delivery. Arrange/verify fulfilment separately before promoting sales.

Local safe preview: `node tests/ai-builders-preview.cjs`, then http://127.0.0.1:4296/ai-for-builders-september-2026/ . Mock paid reference `cs_test_paid`; pending `cs_test_pending`; provider failure `cs_test_failure`. These are fixtures, never live purchases. The requested 15-minute Scale Session calendar is embedded below the introduction video, reusing the booking widget from `/schedule-a-call/` and `/contact-2/`. It has a direct-link fallback and no-referrer policy. No appointment was submitted. Local CSP allows this scheduler frame and blocks external scripts and fetches; production host and Stripe livemode gates suppress marketing conversion calls.

This static repository has no package build, lint or TypeScript pipeline for these pages and no database migrations. Use `node --test tests/ai-builders-*.test.cjs`, JS syntax checks, HTML parsing and browser proof. Never run the full frozen-site rebuild. After human merge, verify production assets/return URL and consent-off negative states. A real successful payment and fulfilment remain untested; no card entry or live purchase was performed.
