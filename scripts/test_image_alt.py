import tempfile
import unittest
from pathlib import Path

from audit_image_alt import audit, is_decorative_meta_pixel
from build_site import add_meta_pixel_empty_alt


class ImageAltTests(unittest.TestCase):
    def test_hidden_meta_pixel_is_classified_as_decorative(self):
        image = {
            "src": "https://www.facebook.com/tr?id=123&ev=PageView&noscript=1",
            "height": "1",
            "width": "1",
            "style": "display:none",
        }
        self.assertTrue(is_decorative_meta_pixel(image))

    def test_noscript_meta_pixel_is_decorative_without_inline_style(self):
        image = {
            "src": "https://www.facebook.com/tr?id=123&ev=PageView\n&noscript=1",
            "height": "1",
            "width": "1",
            "style": "",
        }
        self.assertTrue(is_decorative_meta_pixel(image))

    def test_content_image_is_not_classified_as_decorative(self):
        image = {
            "src": "/wp-content/uploads/team.jpg",
            "height": "600",
            "width": "800",
            "style": "",
        }
        self.assertFalse(is_decorative_meta_pixel(image))

    def test_build_rewrite_adds_empty_alt_only_when_missing(self):
        missing = (
            '<noscript><img height="1" width="1" style="display:none" '
            'src="https://www.facebook.com/tr?id=123&ev=PageView"></noscript>'
        )
        labelled = missing.replace("<img ", '<img alt="tracking" ')
        self.assertIn('<img alt="" height="1"', add_meta_pixel_empty_alt(missing))
        self.assertEqual(labelled, add_meta_pixel_empty_alt(labelled))

    def test_audit_reports_missing_and_empty_alt_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text(
                '<img src="content.jpg"><img src="spacer.svg" alt="">',
                encoding="utf-8",
            )
            result = audit(Path(directory))
        self.assertEqual(1, result["missing_alt_references"])
        self.assertEqual(1, result["missing_alt_unresolved"])
        self.assertEqual(1, result["empty_alt_references"])

    def test_deployable_site_has_no_missing_alt_attributes(self):
        root = Path(__file__).resolve().parents[1] / "www"
        result = audit(root)
        self.assertEqual([], result["missing_details"])


if __name__ == "__main__":
    unittest.main()
