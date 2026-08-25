import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "www" / "5-pillars-free-trainings"
PILLARS = ("plan", "attract", "convert", "deliver", "scale")
FILES = [HUB / "index.html", *(HUB / pillar / "index.html" for pillar in PILLARS)]
MASTERMIND = ROOT / "www" / "courses" / "mastermind-course" / "index.html"


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("href"):
            self.links.append(values)


def load(path):
    return path.read_text(encoding="utf-8")


def schema_graph(document):
    match = re.search(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">(.*?)</script>',
        document,
        re.DOTALL,
    )
    if not match:
        raise AssertionError("Rank Math schema was not found")
    return json.loads(match.group(1))["@graph"]


class FivePillarsSeoTests(unittest.TestCase):
    def test_each_hub_page_has_one_h1_and_valid_html_structure(self):
        for path in FILES:
            with self.subTest(path=path):
                parser = DocumentParser()
                parser.feed(load(path))
                self.assertEqual(parser.h1_count, 1)
                self.assertIn("five-pillars-guide", load(path))

    def test_schema_uses_organization_and_collection_page(self):
        for path in FILES:
            with self.subTest(path=path):
                document = load(path)
                graph = schema_graph(document)
                organization = next(node for node in graph if node.get("@id") == "https://develop-coaching.com/#organization")
                self.assertEqual(organization["@type"], "Organization")
                self.assertNotIn("openingHours", organization)
                self.assertNotIn("address", organization)
                page = next(node for node in graph if node.get("@id", "").endswith("#webpage"))
                self.assertIn("CollectionPage", page["@type"])
                self.assertNotIn("seo@digital-progress.co.uk", document)
                self.assertFalse(any(node.get("@type") == "Article" for node in graph))

    def test_visible_faqs_match_faq_schema(self):
        for path in FILES:
            with self.subTest(path=path):
                document = load(path)
                graph = schema_graph(document)
                faq = next(node for node in graph if node.get("@type") == "FAQPage")
                self.assertGreaterEqual(len(faq["mainEntity"]), 3)
                for question in faq["mainEntity"]:
                    self.assertIn(question["name"], document)
                    self.assertIn(question["acceptedAnswer"]["text"], document)

    def test_every_video_object_has_google_required_fields(self):
        required = ("name", "description", "thumbnailUrl", "uploadDate")
        for path in FILES:
            with self.subTest(path=path):
                videos = [node for node in schema_graph(load(path)) if node.get("@type") == "VideoObject"]
                for video in videos:
                    for field in required:
                        self.assertTrue(video.get(field), f"{path}: missing {field}")
                    self.assertTrue(video.get("embedUrl") or video.get("contentUrl"))

    def test_social_images_are_present(self):
        for path in FILES:
            with self.subTest(path=path):
                document = load(path)
                self.assertIn('property="og:image"', document)
                self.assertIn('name="twitter:image"', document)

    def test_current_pillar_routes_replace_legacy_redirects(self):
        legacy = (
            "/5-pillars-plan/",
            "/the-5-pillars-attract/",
            "/the-5-pillars-convert/",
            "/the-5-pillars-deliver/",
            "/the-5-pillars-scale/",
        )
        for path in FILES[1:]:
            document = load(path)
            with self.subTest(path=path):
                for route in legacy:
                    self.assertNotIn(f'href="{route}"', document)

    def test_hub_and_mastermind_have_direct_reciprocal_links(self):
        hub_document = load(FILES[0])
        mastermind_document = load(MASTERMIND)
        for pillar in PILLARS:
            route = f'/5-pillars-free-trainings/{pillar}/'
            self.assertIn(f'href="{route}"', hub_document)
            self.assertIn(f'href="{route}"', mastermind_document)
        for path in FILES[1:]:
            self.assertIn('href="/courses/mastermind-course/"', load(path))

    def test_analytics_events_and_dimensions_are_instrumented(self):
        expected = (
            "five_pillars_pillar_select",
            "five_pillars_resource_click",
            "five_pillars_mastermind_click",
            "source_page",
            "pillar_name",
        )
        for path in FILES:
            document = load(path)
            with self.subTest(path=path):
                for value in expected:
                    self.assertIn(value, document)
                self.assertIn("send_page_view:false", document)
        self.assertIn("five_pillars_pillar_select", load(MASTERMIND))

    def test_duplicate_resources_expose_primary_pillar(self):
        combined = "\n".join(load(path) for path in FILES[1:])
        for primary in ("plan", "attract", "convert", "deliver", "scale"):
            self.assertIn(f'data-primary-pillar="{primary}"', combined)


if __name__ == "__main__":
    unittest.main()
