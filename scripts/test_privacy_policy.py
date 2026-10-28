#!/usr/bin/env python3
"""Guards for the corrected privacy and cookie policy page."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "www/privacy/index.html").read_text(encoding="utf-8")
BODY = (ROOT / "content/privacy-policy-body.html").read_text(encoding="utf-8")
MAIN = HTML[HTML.index("<main"):HTML.index("</main>")]
VISIBLE = re.sub(r"<!--.*?-->|<style.*?</style>", "", MAIN, flags=re.S)
TEXT = re.sub(r"<[^>]+>", " ", VISIBLE)


class PrivacyPolicyTest(unittest.TestCase):
    def test_body_in_page_and_idempotent(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import apply_privacy_policy as ap
        again, _ = ap.apply(HTML, BODY)
        self.assertEqual(again, HTML)

    def test_no_false_popup_claim(self):
        self.assertNotIn("you will be shown a pop-up", TEXT)
        self.assertNotIn("By viewing the pop-up", TEXT)
        self.assertNotIn("by exiting from our website", TEXT.lower())

    def test_no_tools_the_site_does_not_use(self):
        for name in ("Zoho", "Mouseflow", "Infusionsoft", "Pinterest", "Twitter", "Data Molino"):
            self.assertNotIn(name, TEXT)

    def test_names_real_trackers_and_providers(self):
        for name in ("Google Analytics", "Microsoft Clarity", "Cabin", "ActiveCampaign",
                     "Meta", "Google Ads", "Stripe", "Vercel", "FlowBuild", "CookieYes",
                     "_fbp", "_gcl_au", "_clck", "prism_27070320", "_ga_PXT2VCVFLW", "_ga_EX5H3P27NP"):
            self.assertIn(name, TEXT)

    def test_names_both_legal_regimes(self):
        self.assertIn("Australian Privacy Principles", TEXT)
        self.assertIn("Information Commissioner", TEXT)
        self.assertIn("oaic.gov.au", MAIN)
        self.assertIn("ico.org.uk", MAIN)

    def test_cookie_settings_link_and_anchor(self):
        self.assertIn('id="cookies"', MAIN)
        self.assertIn('class="cky-banner-element"', MAIN)

    def test_no_visible_review_banners(self):
        self.assertNotIn("dc-review-note", MAIN)
        self.assertNotIn("data-dc-review-note", MAIN)
        self.assertNotIn("data-dc-transfer-review-note", MAIN)
        self.assertNotRegex(TEXT, r"(?i)for (greg and )?(lawyer|legal) review|remove this box|corrected draft|pending (lawyer|legal)")

    def test_cost_tracker_pro_data_is_in_mumbai_india(self):
        self.assertIn("database, file storage and app servers are in Mumbai, India", TEXT)
        self.assertIn("personal data of its UK and Australian users is processed in India", TEXT)
        self.assertNotRegex(MAIN, r"London|eu-west-2|lhr1|Version 2")

    def test_transfer_wording_is_honest_about_safeguards(self):
        self.assertIn("We are confirming which safeguard applies", TEXT)
        self.assertNotRegex(TEXT, r"(?i)we use approved transfer safeguards|safeguards (are|is) in place|details of the safeguards")
        self.assertIn("<!-- OPEN: LAWYER REVIEW", MAIN)

    def test_company_details(self):
        for s in ("666 725 659", "47 666 725 659", "PO Box 181", "hello@develop-coaching.com"):
            self.assertIn(s, TEXT)

    def test_only_develop_coaching_com_links(self):
        self.assertNotRegex(MAIN, r"developcoaching\.(co\.uk|com\.au)")
        self.assertNotRegex(MAIN, r"develop-coaching\.(co\.uk|com\.au)")

    def test_no_em_dashes_in_copy(self):
        self.assertNotIn("\u2014", TEXT)
        self.assertNotIn("&mdash;", MAIN)

    def test_jarvis_google_section_unchanged(self):
        for s in ("Limited Use requirements", "does not sell your Google data".replace("does not", "do not"),
                  "https://developers.google.com/terms/api-services-user-data-policy",
                  "https://myaccount.google.com/permissions",
                  "Google API Services User Data Policy"):
            self.assertIn(s, TEXT)

    def test_headings_unique_ids(self):
        ids = re.findall(r'<h2 id="([^"]+)"', MAIN)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 14)

    def test_open_questions_marked(self):
        self.assertGreaterEqual(MAIN.count("OPEN:"), 10)
        self.assertTrue((ROOT / "docs/privacy-page-open-questions.md").exists())


if __name__ == "__main__":
    unittest.main()
