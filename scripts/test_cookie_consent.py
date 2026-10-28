"""Tests for the cookie consent gate (scripts/install_cookie_consent.py, www/dc-consent.js).

Run from the repo root:  PYTHONPATH=. python3 scripts/test_cookie_consent.py
"""
import re
import unittest
from pathlib import Path

from scripts.install_cookie_consent import COOKIE_LINK, HEAD_TAG, install, has_tracker

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"

PAGE = """<!doctype html>
<html><head><script data-preview-guard>1</script>
<script data-no-optimize="1" type="text/javascript"  async src="https://scripts.withcabin.com/hello.js"></script>
<script>(function(w,d,s,l,i){var j=d.createElement(s);j.src='https://www.googletagmanager.com/gtm.js?id='+i;})(window,document,'script','dataLayer','GTM-T4HBRD3');</script>
<script>fbq('init','1');</script>
<noscript><img alt="" height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=1&ev=PageView&noscript=1"
/></noscript>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-T4HBRD3"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<footer><p><a href="/privacy/">Privacy Policy</a> · <a href="/corporate-structure-notice/">Corporate Structure Notice</a></p></footer>
</body></html>"""

SOFTWARE = """<html><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-EX5H3P27NP"></script>
<script>window.dataLayer=[];function gtag(){dataLayer.push(arguments)}</script>
</head><body>
<footer class="footer">
  <div class="wrap">
    <div>x</div>
    <div><a href="mailto:hello@develop-coaching.com">hello@develop-coaching.com</a> · <a href="https://develop-coaching.com">develop-coaching.com</a></div>
  </div>
</footer></body></html>"""

LANDING = '<html><head><script>fbq("init","1")</script></head><body><p>hi</p></body></html>'
ELEMENTOR = ('<html><head><script>fbq("init","1")</script></head><body>'
             '<p>© Copyright 2024 by Develop Coaching Pty Ltd. All Rights Reserved. <a href="/privacy/">Privacy Policy </a></p></body></html>')


class InstallerTests(unittest.TestCase):
    def test_gate_goes_first_in_head_and_is_idempotent(self):
        out = install(PAGE)
        self.assertTrue(out.startswith("<!doctype html>\n<html><head>\n" + HEAD_TAG + "\n<script data-preview-guard>"))
        self.assertEqual(install(out), out)
        self.assertEqual(out.count("data-dc-consent"), 1)

    def test_static_trackers_wait_for_consent(self):
        out = install(PAGE)
        self.assertIn('<script type="text/plain" data-dc-category="analytics" data-no-optimize="1" async src="https://scripts.withcabin.com/hello.js"></script>', out)
        out = install(SOFTWARE)
        self.assertIn('<script type="text/plain" data-dc-category="analytics" async src="https://www.googletagmanager.com/gtag/js?id=G-EX5H3P27NP"></script>', out)
        ads = install('<head></head><script async src="https://www.googletagmanager.com/gtag/js?id=AW-123"></script>')
        self.assertIn('data-dc-category="advertising"', ads)

    def test_noscript_pixels_removed(self):
        out = install(PAGE)
        self.assertNotIn("ns.html", out)
        self.assertNotIn("facebook.com/tr", out)
        self.assertNotIn("<noscript", out)

    def test_cookie_settings_link_in_every_footer_shape(self):
        for page in (PAGE, SOFTWARE, ELEMENTOR, LANDING):
            out = install(page)
            self.assertEqual(out.count(COOKIE_LINK), 1, page[:60])
            self.assertEqual(install(out), out)
        self.assertIn('Corporate Structure Notice</a> · ' + COOKIE_LINK, install(PAGE))
        self.assertIn('dc-cookie-fallback', install(LANDING))

    def test_pages_without_trackers_are_untouched(self):
        page = "<html><head></head><body>plain</body></html>"
        self.assertEqual(install(page), page)
        self.assertFalse(has_tracker(page))

    def test_booking_tag_does_not_displace_the_gate(self):
        from scripts.install_booking_tracking import install as install_booking, TAG
        page = PAGE.replace("</body>", '<iframe src="https://link.flow-build.com/widget/booking/zXUkPVoGKzRyirwYa0Ck"></iframe></body>')
        gated = install(page)
        both = install_booking(gated)
        self.assertIn(TAG, both)
        self.assertLess(both.index(HEAD_TAG), both.index(TAG))
        self.assertEqual(install(both), both)
        other_way = install(install_booking(page))
        self.assertLess(other_way.index(HEAD_TAG), other_way.index(TAG))


class SiteTests(unittest.TestCase):
    """Whole-site invariants over the committed pages in www/."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {p: p.read_bytes().decode("utf-8") for p in sorted(WWW.rglob("*.html"))}

    def test_every_tracker_page_is_gated(self):
        tracked = 0
        for path, html in self.pages.items():
            if not has_tracker(html):
                continue
            tracked += 1
            rel = str(path.relative_to(WWW))
            head = html[html.lower().index("<head"):]
            first_script = re.search(r"<script\b[^>]*>", head).group(0)
            self.assertIn("data-dc-consent", first_script, f"{rel}: gate is not the first script in <head>")
            self.assertIn(COOKIE_LINK, html, f"{rel}: no Cookie settings link")
            self.assertNotRegex(html, r"googletagmanager\.com/ns\.html", f"{rel}: GTM noscript iframe")
            self.assertNotRegex(html, r"facebook\.com/tr\?", f"{rel}: Meta noscript pixel")
            for m in re.finditer(r"<script\b[^>]*\bsrc=[\"'][^\"']*(withcabin\.com|googletagmanager\.com/gtag/js)[^>]*>", html):
                self.assertIn('type="text/plain"', m.group(0), f"{rel}: ungated static tracker {m.group(0)[:80]}")
        self.assertGreater(tracked, 400)

    def test_gate_script_shape(self):
        js = (WWW / "dc-consent.js").read_text()
        self.assertRegex(js, r"var CONSENT_TOOL_ID = '(CONSENT_TOOL_ID|[A-Fa-f0-9]{24})';")
        # default denied is set before anything else can run
        self.assertLess(js.index("'consent', 'default'"), js.index("function patch"))
        for key in ("ad_storage", "analytics_storage", "ad_user_data", "ad_personalization"):
            self.assertRegex(js, rf"{key}: 'denied'")
        # fail closed: the banner only loads for a real key
        self.assertIn("/^[a-f0-9]{16,}$/i.test(CONSENT_TOOL_ID)", js)

    def test_publish_scripts_install_the_gate(self):
        for name in ("publish_page.py", "publish_designed_page.py"):
            self.assertIn("install_cookie_consent", (ROOT / "scripts" / name).read_text(), name)

    def test_footer_template_carries_the_link(self):
        from scripts.modernise_footer import FOOTER
        self.assertIn(COOKIE_LINK, FOOTER)


if __name__ == "__main__":
    unittest.main()
