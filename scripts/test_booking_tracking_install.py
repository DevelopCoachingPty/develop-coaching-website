import unittest
from pathlib import Path
from scripts.install_booking_tracking import install, TAG, ROOT

class BookingTrackingInstallTests(unittest.TestCase):
    def test_exact_calendar_and_idempotence(self):
        page = '<html><head></head><body><iframe src="https://link.flow-build.com/widget/booking/zXUkPVoGKzRyirwYa0Ck?x=1"></iframe></body></html>'
        updated = install(page)
        self.assertEqual(updated.count(TAG), 1)
        self.assertEqual(install(updated), updated)
        self.assertEqual(updated.replace('\n'+TAG+'\n',''), page)

    def test_no_tracking_on_unrelated_pages_or_lookalike(self):
        for page in ['<head></head><a href="https://link.flow-build.com/widget/booking/zXUkPVoGKzRyirwYa0Ck">Book</a>', '<head></head><iframe src="https://evil.example/widget/booking/zXUkPVoGKzRyirwYa0Ck"></iframe>', '<head></head><iframe src="https://link.flow-build.com/widget/booking/other"></iframe>']:
            self.assertEqual(install(page), page)

    def test_committed_site_and_source_copies_are_covered(self):
        for folder in ['www','export/reference']:
            for path in (ROOT/folder).rglob('*.html'):
                html=path.read_bytes().decode()
                self.assertEqual(install(html),html,str(path))

    def test_confirmation_page_does_not_load_booking_listener(self):
        html=(ROOT/'www/before-your-scale-session-2/index.html').read_text()
        self.assertNotIn(TAG,html)

if __name__ == '__main__':
    unittest.main()
