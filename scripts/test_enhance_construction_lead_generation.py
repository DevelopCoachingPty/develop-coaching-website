import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www" / "construction-lead-generation" / "index.html"
SCRIPT = ROOT / "scripts" / "enhance_construction_lead_generation.py"
spec = importlib.util.spec_from_file_location("lead_enhancer", SCRIPT)
lead_enhancer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lead_enhancer)


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1_count += 1


def load():
    return PAGE.read_text(encoding="utf-8")


def schema_graph(document):
    match = re.search(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">(.*?)</script>',
        document,
        re.DOTALL,
    )
    return json.loads(match.group(1))["@graph"]


class ConstructionLeadGenerationTests(unittest.TestCase):
    def test_briefing_is_present_once_before_the_conclusion(self):
        document = load()
        self.assertEqual(document.count('id="dc-lead-quality-briefing"'), 1)
        self.assertLess(
            document.index('id="dc-lead-quality-briefing"'),
            document.index("<h2>Conclusion</h2>"),
        )
        self.assertIn("Reduce Reliance on Referrals and Track Better Leads", document)
        self.assertIn("Track the route from enquiry to qualified opportunity", document)

    def test_briefing_has_the_full_pipeline_and_attract_link(self):
        document = load()
        for phrase in (
            "Record the lead source and date received.",
            "Log the first response and whether contact was made.",
            "Mark the enquiry as qualified or not qualified, with a reason.",
            "Track the consultation or site visit, proposal, and final result.",
        ):
            self.assertIn(phrase, document)
        self.assertIn('href="/5-pillars-free-trainings/attract/"', document)

    def test_page_does_not_add_misleading_faq_schema(self):
        document = load()
        self.assertFalse(
            any(node.get("@type") == "FAQPage" for node in schema_graph(document))
        )

    def test_existing_page_signals_are_preserved(self):
        document = load()
        parser = HeadingParser()
        parser.feed(document)
        self.assertEqual(parser.h1_count, 1)
        self.assertIn(
            '<link rel="canonical" href="https://develop-coaching.com/construction-lead-generation/"',
            document,
        )
        self.assertIn('"@type":"BlogPosting"', document)
        self.assertIn("construction-lead-generation.webp", document)

    def test_transform_is_idempotent(self):
        once = lead_enhancer.transform(load())
        twice = lead_enhancer.transform(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
