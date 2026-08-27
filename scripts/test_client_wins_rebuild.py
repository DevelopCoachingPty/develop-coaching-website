#!/usr/bin/env python3
"""Verify the evidence-led Client Wins page and its video schema."""

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www/client-wins/index.html"
DATA = ROOT / "content/client-wins.json"
SCHEMA_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*'
    r'class=["\']rank-math-schema-pro["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def schema_types(item):
    value = item.get("@type")
    return value if isinstance(value, list) else [value]


class ClientWinsRebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        match = SCHEMA_RE.search(cls.html)
        if not match:
            raise AssertionError("Rank Math JSON-LD graph not found")
        cls.schema = json.loads(match.group(1))
        cls.graph = cls.schema.get("@graph", [])
        cls.videos = [item for item in cls.graph if "VideoObject" in schema_types(item)]

    def test_one_h1_and_useful_metadata(self):
        self.assertEqual(1, len(re.findall(r"<h1\b", self.html, re.IGNORECASE)))
        self.assertIn("Construction Business Coaching Results | Develop Coaching", self.html)
        self.assertIn("builders and construction business owners share", self.html)
        self.assertIn(
            "James reports annual revenue grew from £1.5m, with a £4m forecast.",
            self.html,
        )
        self.assertNotIn("£1.5m to £2m", self.html)

    def test_exactly_twenty_five_visible_source_linked_cards(self):
        self.assertEqual(
            25,
            len(re.findall(r"<article\b[^>]*\bdata-client-win(?:\s|>)", self.html)),
        )
        self.assertEqual(25, self.html.count('class="cw-docket__source"'))
        self.assertEqual(26, self.html.count("data-video-play="))
        self.assertEqual(26, self.html.count("client story\">"))

    def test_visible_and_schema_video_ids_match_approved_data(self):
        approved = {item["id"] for item in self.data}
        visible = set(re.findall(r'data-youtube-id="([A-Za-z0-9_-]+)"', self.html))
        schema_ids = {
            re.search(r"(?:embed/|v=)([A-Za-z0-9_-]+)", item["embedUrl"]).group(1)
            for item in self.videos
        }
        self.assertEqual(25, len(approved))
        self.assertEqual(approved, visible)
        self.assertEqual(approved, schema_ids)
        self.assertNotIn("XHOmBV4js_E", self.html)

    def test_video_schema_is_complete_unique_and_source_safe(self):
        self.assertEqual(25, len(self.videos))
        names = [item.get("name") for item in self.videos]
        self.assertEqual(25, len(set(names)))
        self.assertEqual({item["title"] for item in self.data}, set(names))
        required = (
            "name",
            "description",
            "uploadDate",
            "duration",
            "thumbnailUrl",
            "embedUrl",
            "contentUrl",
        )
        for item in self.videos:
            for field in required:
                self.assertTrue(item.get(field), f"{item.get('@id')} missing {field}")
            self.assertNotIn("Enjoy the videos and music", item["description"])

    def test_schema_strings_cannot_close_the_json_ld_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            page = temp / "index.html"
            data = temp / "client-wins.json"
            css = temp / "client-wins.css"
            hostile = [dict(item) for item in self.data]
            hostile[0]["summary"] = "</script><script>alert('unsafe')</script>"
            page.write_text(self.html, encoding="utf-8")
            data.write_text(json.dumps(hostile), encoding="utf-8")
            css.write_text(".dc-client-wins {}", encoding="utf-8")
            subprocess.run(
                [
                    "node",
                    "-e",
                    "const {renderClientWins}=require('./scripts/render_client_wins.js');"
                    "renderClientWins({pagePath:process.argv[1],dataPath:process.argv[2],cssPath:process.argv[3]});",
                    str(page),
                    str(data),
                    str(css),
                ],
                cwd=ROOT,
                check=True,
            )
            rendered = page.read_text(encoding="utf-8")
            self.assertNotIn("</script><script>alert('unsafe')</script>", rendered)
            self.assertIn(r"\u003c/script>\u003cscript>alert('unsafe')\u003c/script>", rendered)

    def test_no_unsupported_review_schema_or_rating_markup(self):
        types = [schema_type for item in self.graph for schema_type in schema_types(item)]
        self.assertNotIn("Review", types)
        self.assertNotIn("AggregateRating", types)
        self.assertNotIn('itemprop="reviewRating"', self.html)
        self.assertNotIn("Rated 5 out of 5", self.html)

    def test_known_cross_client_copy_is_removed(self):
        mismatched = (
            "Everybody needs a coach in life",
            "Implementing new processes that Greg introduced",
            "You will earn more, retain more and have less stress",
        )
        for text in mismatched:
            self.assertNotIn(text, self.html)

    def test_numerical_outcomes_are_attributed_to_each_client(self):
        numerical_ids = {
            "7iLnXeuYoMg",
            "GSEM3O9HYvg",
            "zhoS5F5oYy4",
            "1C2yT_tP-Aw",
            "yXqEwu6FEog",
            "D-M9a1i4PQU",
            "r572G_WcimQ",
            "snrx2DrLISg",
            "9i31Jk89THQ",
            "H1eWYQjMaFA",
            "Kfx-SeLmNig",
            "ecKFCE1r-18",
            "in8bRqFRC0I",
        }
        attribution_terms = (
            "report",
            "says",
            "recounts",
            "shares",
            "credits",
            "describes",
        )
        for item in self.data:
            if item["id"] in numerical_ids:
                summary = item["summary"].lower()
                self.assertTrue(
                    any(term in summary for term in attribution_terms),
                    f"{item['name']} numerical outcome lacks direct attribution",
                )
        self.assertIn("James reports annual revenue grew", self.html)

    def test_public_names_and_results_note_are_visible(self):
        for item in self.data:
            self.assertIn(f"<h3>{item['name']}</h3>", self.html)
        self.assertIn("individual results", self.html)

    def test_scaled_businesses_are_prioritised_in_display_order(self):
        visible_order = re.findall(r'data-youtube-id="([A-Za-z0-9_-]+)"', self.html)
        self.assertEqual(
            [
                "D-M9a1i4PQU",
                "ecKFCE1r-18",
                "B5ZTJu97_Gs",
                "in8bRqFRC0I",
                "i0p_SEU2xpg",
                "9J1c94plNRE",
            ],
            visible_order[:6],
        )
        featured = re.search(
            r'class="cw-featured__video"[^>]*data-video-play="([A-Za-z0-9_-]+)"',
            self.html,
        )
        self.assertIsNotNone(featured)
        self.assertEqual("D-M9a1i4PQU", featured.group(1))

    def test_customer_facing_copy_replaces_internal_audit_language(self):
        removed = (
            "Named video sources",
            "No anonymous claims",
            "Source-linked",
            "Clearly labelled",
            "Client-reported",
            "result docket",
        )
        for text in removed:
            self.assertNotIn(text, self.html)
        self.assertIn("Find the story closest to where your business is now", self.html)
        self.assertIn("Book my Scale Session", self.html)
        self.assertIn('class="cw-mid-cta"', self.html)

    def test_richard_uses_a_real_video_frame_thumbnail(self):
        expected = "https://i.ytimg.com/vi/9i31Jk89THQ/maxres1.jpg"
        self.assertIn(expected, self.html)
        richard = next(item for item in self.videos if "9i31Jk89THQ" in item["embedUrl"])
        self.assertEqual(expected, richard["thumbnailUrl"])

    def test_contextual_links_and_accessibility_are_present(self):
        for href in (
            "/courses/mastermind-course/",
            "/5-pillars-free-trainings/",
            "/schedule-a-call/",
        ):
            self.assertIn(f'href="{href}"', self.html)
        self.assertEqual(26, len(re.findall(r'aria-label="Play [^"]+ client story"', self.html)))
        self.assertEqual(25, len(re.findall(r'alt="[^"]+ sharing their construction business experience"', self.html)))
        self.assertIn("youtube-nocookie.com/embed/", self.html)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.html)


if __name__ == "__main__":
    unittest.main()
