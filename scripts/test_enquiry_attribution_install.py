import unittest
from scripts.install_enquiry_attribution import install, TAG, ROOT

CONSENT = '<script src="/dc-consent.js" data-dc-consent></script>\n'


class EnquiryAttributionInstallTests(unittest.TestCase):
    def test_goes_straight_after_consent_and_is_idempotent(self):
        page = '<html><head>\n' + CONSENT + '<title>x</title></head><body><iframe src="https://link.flow-build.com/widget/form/USUhO24FJYoYAYFPx4Lt"></iframe></body></html>'
        updated = install(page)
        self.assertEqual(updated.count(TAG), 1)
        self.assertIn(CONSENT + TAG + '\n', updated)
        self.assertEqual(install(updated), updated)

    def test_booking_and_application_pages_qualify(self):
        for body in ['<iframe src="https://link.flow-build.com/widget/booking/zXUkPVoGKzRyirwYa0Ck"></iframe>', '<form id="applyForm" novalidate></form>']:
            self.assertIn(TAG, install('<head></head>' + body))

    def test_unrelated_and_lookalike_pages_untouched(self):
        for page in ['<head></head><a href="https://link.flow-build.com/widget/form/abc">x</a>',
                     '<head></head><iframe src="https://evil.example/widget/form/abc"></iframe>',
                     '<head></head><iframe src="https://link.flow-build.com/js/form_embed.js"></iframe>',
                     '<head></head><form id="search"></form>']:
            self.assertEqual(install(page), page)

    def test_every_enquiry_page_in_www_has_it_after_consent(self):
        for path in (ROOT / 'www').rglob('*.html'):
            html = path.read_text(encoding='utf-8')
            self.assertEqual(install(html), html, str(path))
            if TAG in html and 'data-dc-consent' in html:
                self.assertLess(html.index('data-dc-consent'), html.index(TAG), str(path))


if __name__ == '__main__':
    unittest.main()
