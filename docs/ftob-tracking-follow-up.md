# Fill the Order Book tracking follow-up

The GA4 repair sends new workshop visits to the owner's verified stream,
records booking-link activation as `begin_checkout`, and records a thank-you
URL carrying `session_id` as an unverified `checkout_return`. These GA4 return
events contain no revenue or transaction ID. Stripe remains the paid-sales
source of truth. Historical traffic is not recovered by changing the tag.

The existing Meta `Purchase` block is deliberately preserved byte for byte.
It gates on a nonempty URL session ID and uses that ID for `eventID`; it does
not verify payment, distinguish test sessions, or prevent repeated browser
visits. Its existing comments overstate what the URL gate proves. Preserving
the block maintains the current ad signal; it is not a certification of its
accuracy.

Read-only Events Manager inspection on 14 October 2026 showed the workshop
cold and warm campaigns among active ad sets using Purchase for optimization
or targeting. The 17 September–14 October Purchase breakdown showed two
browser events and no server Purchase source. Inspected workshop webhook
handlers did not supply a Meta replacement; other integration chains were
not fully inspected. Do not infer verified paid-event coverage from webhook
HTTP success or from a browser event.

## Separate Meta follow-up, required before replacing the browser signal

- Establish where the exact workshop's successful live Stripe payments are
  verified and forwarded to Meta. Check the payment link/product and workshop
  metadata, and exclude unpaid, failed and test sessions. Define how delayed
  payments and refunds are handled.
- Preserve campaign attribution and use a stable transaction identity for
  idempotency and browser/server deduplication. Keep secret keys server-side.
- Demonstrate a verified paid Purchase arriving in Events Manager with the
  expected GBP value and event ID. Verify retries do not add duplicate sales,
  and unpaid/test/fabricated returns cannot add paid events. An endpoint's
  HTTP success alone is insufficient evidence.
- Confirm which active ad sets depend on Purchase, then review the replacement
  and cutover together before removing or changing the existing browser block.

The local GA4 audit on 14 October around 21:50 UTC produced one received
workshop page view with localhost origin and email e2 parameters. Realtime
subsequently showed one workshop user/view, consistent with that audit.
Exclude this audit traffic from campaign reporting. Checkout and return
payload tests had collection blocked; their receipt in GA4 is not verified.
No test purchase or attendee entitlement verification was performed.

Publication requires a separate approved merge. After publication, verify the
real page, attribution-preserving checkout handoff and GA4 collection; confirm
the existing Meta Purchase signal remains in place. Do not count validation
visits as customer traffic.
