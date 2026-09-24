# Beyond the Tender 2026 RSVP

This integration replaces the page's `mailto:` handoff with:

`members page → Apps Script → Google Sheet → Flow Build / GoHighLevel → confirmation email`

The Apps Script deliberately does not send email. GoHighLevel is the single
confirmation sender and owns all later reminders.

## Google Sheet

Use the native Google Sheet **Beyond the Tender 2026 — RSVPs**. Its columns must
match `HEADERS` in `Code.gs` exactly.

## Apps Script setup

1. Create an Apps Script project named **Beyond the Tender 2026 RSVP**.
2. Paste `Code.gs` into the project.
3. Add these Script Properties in Project Settings:
   - `SHEET_ID`: the ID of the RSVP Sheet.
   - `GHL_WEBHOOK_URL`: the inbound-webhook URL from the GHL workflow.
4. Deploy as a web app, executing as the project owner, with access for anyone.
5. Put the `/exec` deployment URL in `APPS_SCRIPT_URL` in
   `www/beyond-the-tender/index.html`.

Never commit the GHL webhook URL.

## GoHighLevel / Flow Build workflow

Create and publish **Beyond the Tender 2026 — RSVP Confirmation** with an
Inbound Webhook trigger. Map the contact fields from the JSON payload and use
the `attending` field for the confirmation branch:

- First, create or update the GHL contact using `email`, `firstName`,
  `lastName`, and `companyName`. Contact-dependent actions are skipped if this
  step is omitted from an inbound-webhook workflow.
- `Yes`: send the place-confirmation email and apply the attending tag.
- `No`: send a short acknowledgement and apply the declined tag.

Every payload includes `beyond-the-tender-2026-rsvp` plus exactly one of:

- `beyond-the-tender-2026-attending`
- `beyond-the-tender-2026-declined`

Other fields are `email`, `firstName`, `lastName`, `fullName`, `companyName`,
`event`, `rsvp_timestamp_iso`, `hotel_preference`, `dietary_notes`, and
`submission_id`.

## Verification

Before publishing the website change:

1. Open the web-app URL and confirm the service-health JSON appears.
2. Put the GHL trigger into its request-listening mode.
3. Submit one attending test RSVP from the preview page.
4. Confirm the Sheet row, GHL contact/tags and confirmation email.
5. Submit one declined test RSVP and confirm the declined branch.
6. Remove or clearly mark the two test records.
