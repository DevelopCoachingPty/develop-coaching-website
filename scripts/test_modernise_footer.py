import unittest
from unittest.mock import patch

import scripts.modernise_footer as footer_module
from scripts.modernise_footer import modernise_footer


LEGACY = """<!doctype html><html><head></head><body class="BODY_CLASSES">
<main>Page</main>
<footer data-elementor-type="footer" data-elementor-id="9008" class="elementor elementor-9008 elementor-location-footer"><div>Old footer</div></footer>
</body></html>"""


class ModerniseFooterTests(unittest.TestCase):
    def test_editorial_page_gets_book_award_and_footer(self):
        html = LEGACY.replace("BODY_CLASSES", "single single-post")
        result = modernise_footer(html, "construction-business-plan/index.html")
        self.assertIn('class="dc-book-award"', result)
        self.assertIn('data-dc-modern-footer', result)
        self.assertIn("Best Construction Training Company 2024", result)
        self.assertNotIn("Old footer", result)

    def test_mastermind_page_gets_current_shared_footer_without_book_award(self):
        html = LEGACY.replace("BODY_CLASSES", "page-template-default page")
        result = modernise_footer(html, "courses/mastermind-course/index.html")
        self.assertNotIn('class="dc-book-award"', result)
        self.assertEqual(result.count('data-dc-modern-footer'), 1)
        self.assertEqual(result.count('id="dc-modern-footer"'), 1)
        self.assertIn('.dc-site-footer__brand { display: block; }', result)
        self.assertNotIn(
            '.dc-site-footer__brand { display: block; padding:',
            result,
        )
        self.assertNotIn("Old footer", result)

    def test_general_sales_page_gets_compact_footer_only(self):
        html = LEGACY.replace("BODY_CLASSES", "page-template-default page")
        result = modernise_footer(html, "contact/index.html")
        self.assertNotIn('class="dc-book-award"', result)
        self.assertIn('data-dc-modern-footer', result)
        self.assertIn('id="site-footer"', result)

    def test_five_pillars_child_gets_book_award(self):
        html = LEGACY.replace("BODY_CLASSES", "page-template-default page")
        result = modernise_footer(html, "5-pillars-free-trainings/plan/index.html")
        self.assertIn('class="dc-book-award"', result)

    def test_podcast_index_gets_book_award(self):
        html = LEGACY.replace("BODY_CLASSES", "archive")
        result = modernise_footer(html, "podcast/index.html")
        self.assertIn('class="dc-book-award"', result)

    def test_uppercase_head_close_receives_styles(self):
        html = LEGACY.replace("BODY_CLASSES", "page").replace("</head>", "</HEAD>")
        result = modernise_footer(html, "contact/index.html")
        self.assertIn('id="dc-modern-footer"', result)
        self.assertIn("</HEAD>", result)

    def test_css_backslash_escapes_are_preserved_exactly(self):
        html = LEGACY.replace("BODY_CLASSES", "page")
        escaped_style = '<style id="dc-modern-footer">.icon:before{content:"\\f004"}</style>'
        with patch.object(footer_module, "STYLE", escaped_style):
            result = modernise_footer(html, "contact/index.html")
        self.assertIn(r'content:"\f004"', result)
        self.assertNotIn("\f", result)

    def test_custom_page_without_legacy_footer_is_untouched(self):
        html = "<html><head></head><body><main>Custom</main></body></html>"
        self.assertEqual(modernise_footer(html, "campaign/index.html"), html)

    def test_five_pillars_hub_keeps_its_own_footer(self):
        html = LEGACY.replace(
            '<main>Page</main>',
            '<main class="fp-hub"><section class="fp-book"></section><footer class="fp-footer"></footer></main>',
        ).replace("BODY_CLASSES", "page-template-default page")
        result = modernise_footer(html, "5-pillars-free-trainings/index.html")
        self.assertIn('class="fp-book"', result)
        self.assertIn('class="fp-footer"', result)
        self.assertNotIn('data-dc-modern-footer', result)
        self.assertNotIn('class="dc-book-award"', result)
        self.assertNotIn("Old footer", result)

    def test_transform_is_idempotent(self):
        html = LEGACY.replace("BODY_CLASSES", "single single-post")
        first = modernise_footer(html, "article/index.html")
        second = modernise_footer(first, "article/index.html")
        self.assertEqual(first, second)
        self.assertEqual(second.count('id="dc-modern-footer"'), 1)
        self.assertEqual(second.count('data-dc-modern-footer'), 1)

    def test_shared_footer_brand_has_no_white_background_or_padding(self):
        import re
        from pathlib import Path
        css_path = Path(__file__).resolve().parents[1] / 'content' / '_shared-footer.css'
        css = css_path.read_text(encoding='utf-8')
        brand_rule = re.search(r'\.dc-site-footer__brand\s*{([^}]+)}', css)
        self.assertIsNotNone(brand_rule, 'dc-site-footer__brand rule not found in _shared-footer.css')
        brand_props = brand_rule.group(1)
        self.assertNotIn('background', brand_props, 'dc-site-footer__brand should not have a background property')
        self.assertNotIn('padding', brand_props, 'dc-site-footer__brand should not have padding')
        self.assertIn('dc-site-footer__brand', footer_module.FOOTER)
        self.assertIn('aria-label="Develop Coaching home"', footer_module.FOOTER)
        self.assertIn('/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg', footer_module.FOOTER)


if __name__ == "__main__":
    unittest.main()
