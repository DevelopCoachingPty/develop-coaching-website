import unittest

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

    def test_mastermind_page_keeps_its_purpose_built_footer_only(self):
        html = LEGACY.replace("BODY_CLASSES", "page-template-default page")
        result = modernise_footer(html, "courses/mastermind-course/index.html")
        self.assertNotIn('class="dc-book-award"', result)
        self.assertNotIn('data-dc-modern-footer', result)
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


if __name__ == "__main__":
    unittest.main()
