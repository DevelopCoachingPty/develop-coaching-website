import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www" / "index.html"
SCRIPT = ROOT / "scripts" / "enhance_homepage.py"
spec = importlib.util.spec_from_file_location("homepage_enhancer", SCRIPT)
homepage_enhancer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(homepage_enhancer)


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1_count += 1


def load():
    return PAGE.read_text(encoding="utf-8")


def main_markup(document):
    return re.search(r'<main id="content"[^>]*>(.*?)</main>', document, re.DOTALL).group(1)


def schema_graph(document):
    match = re.search(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">(.*?)</script>',
        document,
        re.DOTALL,
    )
    return json.loads(match.group(1))["@graph"]


class HomepageEnhancerTests(unittest.TestCase):
    def test_owned_main_and_styles_are_present_once(self):
        document = load()
        self.assertEqual(document.count('class="dc-home"'), 1)
        self.assertEqual(
            document.count('id="dc-homepage-control-board-styles"'), 1
        )
        self.assertNotIn("elementor-invisible", main_markup(document))

    def test_page_has_one_clear_h1_and_natural_metadata(self):
        document = load()
        parser = HeadingParser()
        parser.feed(document)
        self.assertEqual(parser.h1_count, 1)
        self.assertIn(
            "Build a more profitable construction business that", document
        )
        self.assertIn(f"<title>{homepage_enhancer.TITLE}</title>", document)
        self.assertNotIn(
            "Award Winning Construction business coach and Trades Contractor Coaching",
            main_markup(document),
        )

    def test_five_pillars_and_primary_routes_are_complete(self):
        document = load()
        for slug in ("plan", "attract", "convert", "deliver", "scale"):
            self.assertIn(f'href="/5-pillars-free-trainings/{slug}/"', document)
        self.assertIn('href="/courses/mastermind-course/"', document)
        self.assertIn('href="/client-wins/"', document)
        self.assertIn('href="/schedule-a-call/"', document)

    def test_client_proof_uses_cautious_source_matched_language(self):
        document = load()
        self.assertIn(
            "Marek reports turnover of just over £1 million before joining, then doubling within a year",
            document,
        )
        self.assertIn(
            "Richard reports turnover moving from about £750,000 to £1.1 million",
            document,
        )
        self.assertIn(
            "Jordan says better CRM processes and lead handling", document
        )
        self.assertIn("Results vary with the business", document)
        self.assertNotIn("guaranteed results", main_markup(document).lower())

    def test_faq_is_visible_and_aligned_with_schema(self):
        document = load()
        webpage = next(
            node
            for node in schema_graph(document)
            if node.get("@id") == "https://develop-coaching.com/#webpage"
        )
        self.assertIn("FAQPage", webpage["@type"])
        visible_questions = [question for question, _ in homepage_enhancer.FAQS]
        schema_questions = [item["name"] for item in webpage["mainEntity"]]
        self.assertEqual(schema_questions, visible_questions)
        for question, answer in homepage_enhancer.FAQS:
            self.assertIn(f"<summary>{question}</summary>", document)
            self.assertIn(f"<p>{answer}</p>", document)

    def test_existing_site_signals_are_preserved(self):
        document = load()
        self.assertIn(
            '<link rel="canonical" href="https://develop-coaching.com/"', document
        )
        graph = schema_graph(document)
        self.assertTrue(any(node.get("@id") == "https://develop-coaching.com/#organization" for node in graph))
        self.assertTrue(any(node.get("@id") == "https://develop-coaching.com/#website" for node in graph))
        self.assertIn('data-dc-modern-footer', document)
        self.assertIn('data-elementor-type="header"', document)

    def test_accessibility_and_responsive_guards_are_present(self):
        document = load()
        self.assertIn(":focus-visible", document)
        self.assertIn("prefers-reduced-motion:reduce", document)
        self.assertIn("@media(max-width:600px)", document)
        self.assertIn("overflow:clip", document)
        self.assertIn('aria-label="Explore the Five Pillars"', document)
        self.assertIn('alt="Greg Wilkes discussing a construction business plan', document)

    def test_transform_is_idempotent(self):
        once = homepage_enhancer.transform(load())
        twice = homepage_enhancer.transform(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
