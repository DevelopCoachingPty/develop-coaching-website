# Enquiry attribution

Goal: know which page, search or AI tool brought in each enquiry. Gap #1 in the
16 Nov SEO/GEO gap analysis.

## What runs on the site

`www/enquiry-attribution.js`, installed by `scripts/install_enquiry_attribution.py`
on every page with a FlowBuild form, survey, quiz or booking iframe, plus the
`/busy-trap/` application (413 pages on 16 Nov 2026). New pages from
`publish_page.py` get it automatically. It sits straight after `dc-consent.js`
and is not deferred, so it sees each FlowBuild iframe as it is inserted.

1. **First touch.** Landing page, `utm_source`/`utm_medium`/`utm_campaign`,
   external referrer and an AI flag (`chatgpt`, `perplexity`, `gemini`,
   `copilot`, `claude`, `deepseek`, `grok` and others, from the referrer host or
   ChatGPT's own `utm_source=chatgpt.com`). Query strings are stripped; labels
   containing `@` are dropped.
2. **Hidden fields.** The values are added to each FlowBuild iframe URL as
   `dc_landing_page`, `dc_utm_source`, `dc_utm_medium`, `dc_utm_campaign`,
   `dc_referrer`, `dc_ai_referrer`, `dc_enquiry_page`. FlowBuild fills any form
   field whose *query key* matches (confirmed in the form widget code).
3. **GA4 key event.** `generate_lead` to `G-PXT2VCVFLW` via the existing data
   layer when FlowBuild reports a completed form
   (`["set-sticky-contacts","embedded_iframe_<id>",...]`) or booking
   (`["msgsndr-booking-complete",...]`), and on the `/busy-trap/` application
   submit. Parameters: `lead_type`, `form_id`, `form_name`, `landing_page`,
   `ai_referrer`, `first_utm_source/medium/campaign`. Only sent with analytics
   consent. The existing `scale_session_booked` event is unchanged.

Storage: sessionStorage for the visit. localStorage (90 days) only after
analytics consent, removed on withdrawal, never with GPC/DNT. If storage is
blocked the current page's values are still passed; the landing page is left
blank rather than guessed.

## GHL setup

Contact custom fields (created via API, 16 Nov 2026):

| Field | Key | Hidden field query key |
|---|---|---|
| Enquiry Landing Page | `contact.enquiry_landing_page` | `dc_landing_page` |
| Enquiry UTM Source | `contact.enquiry_utm_source` | `dc_utm_source` |
| Enquiry UTM Medium | `contact.enquiry_utm_medium` | `dc_utm_medium` |
| Enquiry UTM Campaign | `contact.enquiry_utm_campaign` | `dc_utm_campaign` |
| Enquiry Referrer | `contact.enquiry_referrer` | `dc_referrer` |
| Enquiry AI Referrer | `contact.enquiry_ai_referrer` | `dc_ai_referrer` |
| Enquiry Page | `contact.enquiry_page` | `dc_enquiry_page` |

Each field must be on these forms as a **hidden** field with the query key
above. The GHL API cannot edit forms (it needs a signed-in user), so this is
done in the form builder:

- `USUhO24FJYoYAYFPx4Lt` 15 Minute Scale Session (/contact/)
- `HiKgokGLY3muLJWDE8GX` T&C Optin (the Scale Session calendar's form)
- `LrwamDnwkXRzgaIuSFn2` Newsletter UK Subscribe (site-wide)
- `DM8MfGpKqOlTWsW9Mvh1` Download UK Book
- `OuWMAAl7r2K93aA7W3xm` The Perfect Project registration
- `Ftx9UWAyx0xmzdt9n4KN` 30-Day Construction CEO Experience

Until then the script is harmless: FlowBuild ignores unknown parameters.

## Not covered

- The Mastermind application forms (`DC Application Step 1-4`) are not
  embedded on this site, so no first-touch data reaches them.
- `/busy-trap/` posts to a webhook that is still empty (`WEBHOOK_URL`); the
  `dc_*` values are in its payload once it is set.
- `/fire-figure/` and `/win-big-clients-webinar/` use old Elementor forms.

## Tests

    node --test tests/enquiry-attribution.test.cjs
    python3 -m unittest scripts.test_enquiry_attribution_install
    python3 scripts/install_enquiry_attribution.py --check
