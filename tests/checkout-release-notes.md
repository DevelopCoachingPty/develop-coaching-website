# AI for Builders payment return

Closes #54; follow-up to approved page PR #52. Preserves the page design and adds replay to the format details.

The page creates an embedded session only after the buyer clicks the ticket button. Stripe idempotency keys make browser retries reuse that attempt. Server code validates an active, one-time 4500 GBP price on the existing Live Workshop product. A return URL triggers a separate server-side lookup checking event metadata, exact configured price, quantity, total, currency, completed session and paid status. It never starts another session. Customer details are not exposed.

Validation: `node --test tests/ai-builders-checkout.test.cjs` (6 passing), `node --check` on both handlers, `git diff --check`. Local Chrome fixture on port 4198 confirmed zero create-session calls before intent and on paid return, customer-friendly unavailable/retry, and confirmation rendering. Screenshot `/tmp/checkout-confirmation-proof.png`. No package build/lint/typecheck or migrations in this static website slice; Docker migration checks are not applicable. Browser fixture uses mocked payment status, not live Stripe proof.

Release dependencies: configure Stripe credentials, independently verify actual live form/product/one-time £45 GBP, and establish the September registration/fulfilment route before promotion. The legacy fallback URL pointed to an older workshop and is removed from the customer flow. Confirmation currently supplies support email for joining details; it does not claim automated registration or email fulfilment. No payment was submitted.

Independent adversarial code review: no critical/high code defects. Prices read and Checkout Sessions read/write permissions are required. Draft remains blocked on live configuration and registration/fulfilment verification; it is not yet payment-release ready.
