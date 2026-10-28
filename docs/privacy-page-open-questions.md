# Privacy and cookie policy: audit and open questions

For Greg and legal review. This is not legal advice. Page: `www/privacy/index.html`,
text source: `content/privacy-policy-body.html`, applied by `scripts/apply_privacy_policy.py`.
Every item below is also marked `OPEN:` in the page source (invisible to visitors).

## What was wrong on the old page

| Old text | Problem | Now |
|---|---|---|
| 12.4: "you will be shown a pop-up ... by viewing the pop-up you are giving us consent" | There was no pop-up and no consent tool. Most serious item. Viewing a banner is also not consent. | Replaced by a cookie policy (section 11) that matches the new banner |
| Cookie tables: Facebook, Zoho Sales IQ, Google, Mouseflow, YouTube | Zoho and Mouseflow were not found on the pages tested. Missing: Clarity, Google Ads, ActiveCampaign, Cabin | New table by category, from the Part B table in the audit draft |
| Provider list: Infusionsoft, Twitter, Pinterest, Power BI, Zoho and others | Not visible on the site. Missing: ActiveCampaign, Clarity, Stripe, Vercel, FlowBuild, Supabase | New list of real providers |
| "EU GDPR", "English and EU Cookie Law" only | No mention of UK GDPR, PECR or the Australian Privacy Act | Names UK/EU law, the Australian Privacy Principles, the ICO and the OAIC |
| 6.2: you are "deemed to accept" transfers outside the EEA | Not a valid safeguard | New "Sending data abroad" section |
| 1: use of the site means you accept the policy | A privacy notice informs. Acceptance is not how consent works | Removed |
| 5.4: submitting your data means you "agree to be contacted by phone" | Not valid consent | New marketing section with opt-out |
| 5.1: "contract" is the lawful basis | Not true for marketing or analytics | Legal basis table |
| 6.4: all staff and contractors are trained, evaluated, bound by contract | Could not be checked for a small company | Removed, generic security line kept |
| 7.3: stats shared with investors, affiliates and advertisers | Could not be checked | Removed |
| 4.9 "Demographics" | Nothing found that collects it | Removed |
| 8.2 typo "you will] be contacted" | Typo | Fixed |

Kept exactly as it was: the Jarvis and Google Account section (it is the text Google
reviewed for OAuth).

## Open questions

1. **UK representative and ICO registration** (UK GDPR Art. 27). Not confirmed. Launch plan lists both as to do. Name and address go in section 1 when known.
2. **Does the Australian Privacy Act apply in full** (small business exemption)? Lawyer to confirm.
3. **Marketing legal basis** per list: consent, or legitimate interests for business contacts.
4. **Which transfer tool covers which provider** (IDTA, UK Addendum, other) and whether it is signed. The page says only that such safeguards exist on request. Make it true or soften it.
5. **Where CostTrackerPro data lives.** Mumbai today. Decision 1 in the draft is move to London or Sydney, or stay and disclose. The website page is silent on this. The CostTrackerPro notice must say it.
6. **Old provider names removed** (Zoho, Infusionsoft, Twitter, Pinterest, LinkedIn, Instagram, Power BI, DocuSign, SharePoint/OneDrive, Data Molino, Royal Mail). If any still handle customer data, add them back. A generic line about accounting, storage and e-signing tools stays.
7. **Email sending service.** Resend is listed as a cost in the launch plan but was not seen in site code.
8. **What ActiveCampaign is used for** beyond site tracking, and whether it is analytics or marketing for the banner. In code it is "advertising and marketing" (`www/dc-consent.js` RULES, on the banner branch).
9. **Retention.** Closed account deletion period (the CostTrackerPro notice says 30 days, backups?), Google Analytics retention setting, Clarity retention.
10. **Clarity masking** for form fields. The cookie table says form entries are hidden. Check the Clarity project setting.
11. **Cabin cookies.** "No cookie" is the vendor's claim, not checked.
12. **Embedded content** (YouTube, Trustindex, FlowBuild forms, Google Fonts) loads before any banner choice and is not gated. Options: add a click to load step and an "embedded content" category, self-host fonts, or accept and disclose. The page currently discloses.
13. **Consent tool name and settings.** The page names CookieYes and says choices last 12 months and Reject all is on the first layer. These must match what is set in the CookieYes dashboard. Once the first scan exists, paste CookieYes's generated cookie list under the table or update the table.
14. **Universal Analytics** (UA-136319056-1) is not listed because it is retired. Remove it from GTM. If it stays it must be listed.
15. **Jarvis section** ends with "contact greg@develop-coaching.com", every other contact is hello@develop-coaching.com. Left as is because changing text Google reviewed may need a new review.
16. **Org schema phone.** The page's JSON-LD (and the site template) carries a UK phone number, +44 20 8610 9674, and `en-GB`, `HomeAndConstructionBusiness`. Not touched here. Check it is a live number.
17. **Date.** "Last updated: 28 October 2026" and the modified dates in the page head and sitemap are set to the day of drafting. Update them on the day it goes live.
18. **Review box.** The orange "For Greg and legal review" box at the top of the page must be deleted from `content/privacy-policy-body.html` before merge. The test `test_review_marker_present` expects it, so remove that test line too.

## Order of release

1. Consent banner branch (`feat/cookie-consent-banner`) set up with the real CookieYes key and merged.
2. This page. If it goes live first, it describes a banner that does not exist yet, which is the same mistake as the old page.
3. CostTrackerPro notice, same day.
