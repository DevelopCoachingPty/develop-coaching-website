# Cookie consent on develop-coaching.com

Status: built and tested on a branch. Not live. Needs one value from Greg (the
consent tool site ID) and a few GTM container changes before it can go out.
This is engineering documentation, not legal advice. The wording of the banner
and the cookie lists need Greg/legal review.

## What changed

| Piece | Where |
|---|---|
| Consent gate (defaults, script hold, banner loader) | `www/dc-consent.js` |
| Site-wide installer (idempotent, same style as `install_booking_tracking.py`) | `scripts/install_cookie_consent.py` |
| Tests | `scripts/test_cookie_consent.py` and `scripts/check_consent_gate_browser.py` (needs Playwright, optional) |
| "Cookie settings" footer link | modern footer template in `scripts/modernise_footer.py`, plus every other footer shape (see below) |
| New pages inherit the gate | `scripts/publish_page.py` and `scripts/publish_designed_page.py` call the installer last |

418 pages under `www/` carry a tracker, so 418 pages got the gate. Pages with no
tracker (5) are untouched. `export/reference/` is not touched: it is only the
input to `build_site.py`, which must not be run.

## How tracking loaded before (audit of `www/` on main)

Everything below fired on page load, before any choice. Checked by loading each
page type in headless Chrome with no clicks (before and after, same script).

| Tracker | How it loads | Pages | Fired pre-consent |
|---|---|---|---|
| Google Tag Manager GTM-T4HBRD3 (carries GA4 G-PXT2VCVFLW, Google Ads AW-626535904, and probably ActiveCampaign) | inline loader, plus `<noscript>` iframe | 406 | yes |
| Meta Pixel 260128381862353 | inline loader, plus `<noscript>` image | 410 | yes |
| Microsoft Clarity 9izd804cl6 | inline loader | 382 | yes |
| ActiveCampaign (account 27070320) | inline `vgo` loader | 405 | yes |
| Cabin | static `<script src>` | 382 | yes |
| GA4 G-PXT2VCVFLW on its own `ga4EventLayer` | inline loader on `/5-pillars-free-trainings/*` and `/schedule-a-call/`, and written into pages by `publish_designed_page.py` | 8 | yes |
| GA4 G-EX5H3P27NP and Meta Pixel 1934173480574455 | static gtag.js plus inline pixel | Pixel on 7 `/software/*` pages. gtag on those 7 plus `/5-profit-leaks-workshop/`, its thank-you page and `/book-a-call/` | yes |
| GA4 G-PXT2VCVFLW, static gtag.js | static `<script src>` | `/fill-the-order-book/` and its thank-you page | yes |
| `booking-tracking.js` event push | dataLayer only, already honours GPC and DNT | 61 | no network call of its own; now also checks consent |

Not gated, and flagged as open questions (see the end):
YouTube embeds, FlowBuild/GoHighLevel form and calendar iframes
(`link.flow-build.com`), Trustindex widget, Google Fonts.

## How the gate works

1. `dc-consent.js` is the first script in `<head>` on every tracker page. It
   sets Consent Mode v2 to `denied` for `ad_storage`, `analytics_storage`,
   `ad_user_data` and `ad_personalization` before any Google tag exists.
2. It holds back tracker scripts (GTM, GA4, Google Ads, Meta, Clarity,
   ActiveCampaign, Cabin) that the page adds from JavaScript, and releases them in
   place after consent. The existing inline snippets are unchanged, so their
   queued calls (`fbq`, `clarity`, `vgo`, `dataLayer`) replay normally once the
   script arrives. This is "basic" Consent Mode: the hard-coded Google loaders are held,
   so they send no cookieless pings until the visitor says yes. If GTM is released by
   advertising-only consent, GA4 inside GTM can still send cookieless pings unless
   the GTM change for GA4 (analytics_storage required) has been made.
3. Static tags that cannot be intercepted (Cabin, gtag.js on the software pages)
   are rewritten to `type="text/plain" data-dc-category="..."` in the HTML and
   switched on by the same release step.
4. The `<noscript>` GTM iframe and Meta pixel image are removed. They load with
   no consent step and cannot be gated. Visitors with JavaScript off now send
   nothing.
5. It loads the hosted banner from `https://cdn-cookieyes.com/client_data/<ID>/script.js`.
6. It listens for the visitor's choice (a Consent Mode `update` on the data
   layer, or the banner's `cookieyes_consent_update` event) and releases scripts:
   - Analytics yes: GTM, GA4, Clarity, Cabin
   - Marketing and advertising yes: GTM, Google Ads, Meta Pixel, ActiveCampaign
   - ActiveCampaign is treated as marketing, not analytics. Change `RULES` in
     `dc-consent.js` if Greg wants it under analytics.
7. The second data layer (`ga4EventLayer`) gets its own denied default and its
   own update, so it follows the same choice.
8. On withdrawal it sends the vendor's own opt-out where one exists (Clarity
   `consentv2`, Meta `consent revoke`, GA4 `ga-disable-<id>`). Already loaded
   scripts cannot be unloaded, so a page reload completes it.

It fails closed. Until `CONSENT_TOOL_ID` is a real key, no banner can load and so
no tracker ever loads. Do not deploy before the ID is set unless a tracking
blackout is acceptable. `window.dcConsent.allowed('analytics' | 'advertising')`
is available to other scripts.

## Consent tool recommendation: CookieYes

CookieYes, paid "Basic" plan. List price at time of research is about 8 GBP a
month (about 80 GBP a year billed yearly). Greg to confirm current price at
checkout.

Why:
- Google-certified for Consent Mode v2, and has a Tag Manager template.
- Works on a static site with one script tag (no WordPress plugin).
- The banner can show Accept all, Reject all and a choices panel with equal
  prominence, which the ICO expects. It keeps a consent log and has a floating
  "revisit" button.
- Covers a site this size. The free plan is limited to 5,000 page views a month and
  100 scanned pages (and the banner switches off at the limit), so it is not enough
  for 420 pages with paid traffic.

Alternatives considered: Cookiebot (about 30 EUR a month at this size, free only to
50 sub-pages), Termly (advanced Consent Mode needs Pro+, about 15 USD a month),
iubenda (about 5 to 7 EUR a month for 25k page views). All support Consent Mode
v2. CookieYes is the cheapest that meets the whole checklist.

## What Greg needs to supply and do

1. Create a CookieYes account (Greg, not an agent), add `develop-coaching.com`.
2. Copy the website key: Dashboard, Advanced settings, Get installation code. It is
   the 24 character hex string in `.../client_data/<KEY>/script.js`.
3. Replace `CONSENT_TOOL_ID` in `www/dc-consent.js` with that key. One line.
4. In CookieYes:
   - Advanced settings: turn **Support GCM** on. Leave **Allow Google tags to fire
     before consent** OFF (that is advanced mode, and this build is basic).
   - Banner template: use the strict opt-in (GDPR style) banner for **all
     countries**, not only the EU and UK. Otherwise visitors elsewhere can be
     treated as opted in and the gate will release trackers for them.
   - Show **Reject all** on the first layer, same size and style as **Accept all**.
   - Categories: keep Necessary, Analytics and Advertisement. Switch off or merge
     Functional and Performance, since the gate only reads Analytics and
     Advertisement.
   - Turn on the consent log and the floating revisit button. The floating button
     covers any page that has no footer.
   - Set consent to expire and be asked again after 12 months.
   - Do **not** also add the CookieYes GTM template. It would conflict with the
     script loaded here.
5. Banner copy and the cookie list in CookieYes should match the cookie table on
   the privacy page (branch `feat/privacy-page-correction`).

## GTM container changes (made by hand in GTM, not in this repo)

Not done here: no live container was touched, and I could not open the container,
so this list is from the public container file and has to be checked in GTM.

1. **Remove the Universal Analytics tag** (UA-136319056-1). Google retired it in
   2023 and it only sets `_gid` and `_gat` cookies.
2. GA4 config and event tags (G-PXT2VCVFLW): open Advanced settings, Consent
   settings. Google tags read Consent Mode on their own, but set
   **Require additional consent for tag to fire** to `analytics_storage` as a
   second lock.
3. Google Ads conversion and remarketing tags (AW-626535904): require
   `ad_storage`, `ad_user_data` and `ad_personalization`.
4. Any Custom HTML tag (ActiveCampaign, Meta, Clarity or others, if they live in
   GTM): these have no built-in checks. Require `ad_storage` for Meta and
   ActiveCampaign, and `analytics_storage` for Clarity.
5. **Duplicate loaders.** Meta Pixel, Clarity and ActiveCampaign are also
   hard-coded in the page HTML. If the same tools are also tagged in GTM, they
   fire twice. Keep one copy. If GTM keeps them, the hard-coded copies can be
   deleted later and the gate will still cover GTM.
6. Do not add a default consent state tag in GTM. The default is set in
   `dc-consent.js` before GTM loads, and a second one would fight it.
7. In Preview, check Consent Overview shows all four as denied on first load and
   granted after Accept.
8. Publish only after the site change is live, or at the same time.

## Checks run

- `scripts/test_cookie_consent.py`: installer behaviour and whole-site invariants
  (gate first in `<head>`, no ungated static tracker, no tracking noscript, a
  Cookie settings link on every tracker page).
- `scripts/check_consent_gate_browser.py` (headless Chrome, external hosts stubbed):
  six page types, four scenarios (no banner key, reject, analytics only, accept
  all). With no choice, zero tracker requests. Reject keeps it at zero. Analytics
  only loads GTM, GA4, Clarity and Cabin and not Meta or ActiveCampaign. Accept all
  loads everything. Before this change the same pages made 2 to 6 tracker requests
  on load.
- Not tested: the real CookieYes banner (no key yet), real GTM container contents,
  real Meta/Clarity/ActiveCampaign endpoints, Safari and Firefox.

## Limits and open questions

- Events fired before the visitor chooses (a click on a buy button, a form
  submit) are queued in the page's data layer, and are sent if the visitor then
  accepts later on the same page. They are dropped if the page is left. The one
  exception is the FlowBuild booking-complete event in `booking-tracking.js`, which
  is dropped (not queued) if analytics consent has not been given at that moment.
- The consent tool itself (CookieYes) loads, and sets its own consent cookie,
  before any choice. That is normal for a consent tool and is listed as strictly
  necessary in the privacy page.
- The browser gate check stubs external scripts with empty bodies, so it proves which
  scripts are requested, not what GTM does internally. What GTM fires depends on the
  GTM changes above.
- `document.write` of a tracker is not intercepted. None exist on the site today.
- Google Fonts, YouTube embeds, FlowBuild iframes and the Trustindex widget load
  third-party content before consent and set their own cookies or send IP
  addresses. They are not gated here (not on the list in the brief). Needs
  a decision: use a click-to-load facade for YouTube and host fonts locally.
- Cabin says it is cookieless. Gated anyway to match the banner wording.
- `www/privacy/` still describes the old behaviour until the privacy page branch
  is merged. Merge this first and the privacy page straight after.
- A global Privacy Control or Do Not Track signal is not treated as a "reject" by
  the banner. `booking-tracking.js` still honours both.
