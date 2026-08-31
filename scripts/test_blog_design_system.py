#!/usr/bin/env python3
"""Tests for the shared blog design system transformer."""

import copy
import json
import re
import unittest
from pathlib import Path

import blog_design_system as bds


SPEC = {
    "slug": "example-article",
    "pillar": "Convert",
    "title": "Example Article: A Title Under Sixty Five Characters",
    "meta_description": (
        "An example meta description written to sit inside the range the design "
        "system enforces, which is one hundred and ten to one sixty five."
    ),
    "h1": "Example Article: A Title Under Sixty Five Characters",
    "hero_subtitle": "A practical guide to the thing this article is about.",
    "intro": {
        "answer": "The direct answer to the question the reader searched for.",
        "image": {"src": "/wp-content/uploads/example.webp", "alt": "Example", "width": 940, "height": 788},
        "roadmap": "This guide covers the ground in the order it matters.",
    },
    "briefing": {
        "eyebrow": "Example site briefing",
        "title": "The Practical Briefing Heading",
        "intro": "Why this briefing sits here rather than further down the page.",
        "panels": [
            {"heading": "A question a reader would type?", "paragraphs": ["First answer.", "Second answer."]},
            {"heading": "A process heading", "paragraphs": ["Lead in."], "steps": ["One.", "Two."]},
        ],
        "review": {"label": "Review weekly", "text": "What to compare each week."},
        "cta": {"text": "Explore the Convert pillar resources", "href": "/5-pillars-free-trainings/convert/"},
    },
    "brief_before_heading": "Second Heading",
    "intro_replaces_paragraphs": 2,
    "date_modified": "2026-08-31T00:00:00+10:00",
}


SCHEMA = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "item": {"@id": "https://develop-coaching.com/", "name": "Home"}},
                {"@type": "ListItem", "position": 2, "item": {"@id": "x", "name": "Old"}},
                {"@type": "ListItem", "position": 3, "item": {"@id": "y", "name": "Old title"}},
            ],
        },
        {"@type": "WebPage", "@id": "https://develop-coaching.com/example-article/", "name": "Old", "description": "Old"},
        {"@type": "BlogPosting", "headline": "Old headline", "description": "Old"},
    ],
}


def page(body_paragraphs: str = "", broken_anchor: bool = False) -> str:
    anchor = (
        '<div>\n  <a href="https://youtube.com/watch?v=x" rel="noopener noreferrer"></p>\n<p>  </a>\n</div>\n'
        if broken_anchor
        else ""
    )
    body = body_paragraphs or (
        "<p>The first opening paragraph of the article, long enough to count as substantial prose.</p>\n"
        "<p>The second opening paragraph of the article, also long enough to count as substantial prose.</p>\n"
        '<p><img src="/wp-content/uploads/example.webp" alt="Example" width="940" height="788"></p>\n'
        "<h2>First Heading</h2>\n<p>Body copy under the first heading.</p>\n"
        "<h2>Second Heading</h2>\n<p>Body copy under the second heading.</p>\n"
    )
    return f"""<!DOCTYPE html>
<html><head>
<title>Old title</title>
<meta name="description" content="Old description" />
<meta property="og:title" content="Old" />
<meta property="og:description" content="Old" />
<meta name="twitter:title" content="Old" />
<meta name="twitter:description" content="Old" />
<meta property="article:section" content="Uncategorized" />
<meta property="og:updated_time" content="2020-01-01T00:00:00+00:00" />
<meta property="article:modified_time" content="2020-01-01T00:00:00+00:00" />
<link rel="canonical" href="https://develop-coaching.com/example-article/" />
<script type="application/ld+json" class="rank-math-schema-pro">{json.dumps(SCHEMA)}</script>
</head>
<body class="single-post category-plan category-scale postid-1">
<span class="elementor-post-info__terms-list"><a href="/category/plan/">Plan</a></span>
<h1 class="elementor-heading-title elementor-size-default">Old H1</h1>
<div data-widget_type="theme-post-content.default">
{anchor}{body}</div>
</body></html>"""


class TransformTests(unittest.TestCase):
    def transform(self, document=None, spec=None):
        return bds.transform(document or page(), spec or SPEC)

    def test_single_h1_after_transform(self):
        out = self.transform()
        self.assertEqual(len(re.findall(r"<h1\b", out)), 1)
        self.assertIn(SPEC["h1"], out)

    def test_exactly_one_of_each_owned_block(self):
        out = self.transform()
        for marker in ('id="dc-article-brief"', 'id="dc-article-intro"',
                       'id="dc-article-hero-subtitle"', 'id="dc-article-system-styles"'):
            self.assertEqual(out.count(marker), 1, marker)

    def test_idempotent(self):
        once = self.transform()
        twice = bds.transform(once, SPEC)
        self.assertEqual(once, twice)

    def test_idempotent_leaves_one_briefing_not_two(self):
        twice = bds.transform(self.transform(), SPEC)
        self.assertEqual(twice.count('id="dc-article-brief"'), 1)

    def test_briefing_sits_before_its_anchor_heading(self):
        out = self.transform()
        self.assertLess(out.index('id="dc-article-brief"'), out.index("<h2>Second Heading</h2>"))
        self.assertGreater(out.index('id="dc-article-brief"'), out.index("<h2>First Heading</h2>"))

    def test_duplicate_lead_image_removed(self):
        out = self.transform()
        start, end = bds.body_span(out)
        self.assertEqual(out[start:end].count("/wp-content/uploads/example.webp"), 1)

    def test_video_embed_and_its_script_survive(self):
        """An unclosed <p> around an embed must not let the intro swallow it."""
        embed = (
            '<p>\n<div class="lite-youtube" data-videoid="abc">\n'
            '  <a href="https://youtube.com/watch?v=abc"></a>\n</div>\n'
            '<script>document.addEventListener("DOMContentLoaded", function(){});</script>\n'
            "<p>The first opening paragraph of the article, long enough to count as substantial prose.</p>\n"
            "<p>The second opening paragraph of the article, also long enough to count as substantial prose.</p>\n"
            "<h2>First Heading</h2>\n<p>Body copy under the first heading.</p>\n"
            "<h2>Second Heading</h2>\n<p>Body copy under the second heading.</p>\n"
        )
        out = bds.transform(page(body_paragraphs=embed), SPEC)
        start, end = bds.body_span(out)
        body = out[start:end]
        self.assertIn("lite-youtube", body)
        self.assertIn("document.addEventListener", body)
        self.assertIn('id="dc-article-intro"', body)
        self.assertNotIn("The first opening paragraph", body)

    def test_broken_anchor_is_closed(self):
        out = self.transform(page(broken_anchor=True))
        self.assertNotIn('rel="noopener noreferrer"></p>', out)
        self.assertIn('rel="noopener noreferrer"></a>', out)

    def test_head_and_schema_carry_the_same_title(self):
        out = self.transform()
        self.assertIn(f"<title>{SPEC['title']}</title>", out)
        schema = json.loads(
            re.search(r'class="rank-math-schema-pro">(.*?)</script>', out, re.DOTALL).group(1)
        )
        posting = next(n for n in schema["@graph"] if n["@type"] == "BlogPosting")
        self.assertEqual(posting["headline"], SPEC["title"])
        self.assertEqual(posting["articleSection"], "Convert")

    def test_single_pillar_category_replaces_the_old_ones(self):
        out = self.transform()
        body_class = re.search(r'<body class="([^"]*)"', out).group(1)
        self.assertIn("category-convert", body_class)
        self.assertNotIn("category-plan", body_class)
        self.assertNotIn("category-scale", body_class)
        self.assertIn('href="/category/convert/"', out)

    def test_contextual_pillar_link_lands_in_the_article_body(self):
        out = self.transform()
        start, end = bds.body_span(out)
        self.assertIn("/5-pillars-free-trainings/convert/", out[start:end])


class FailClosedTests(unittest.TestCase):
    def test_missing_anchor_heading_raises(self):
        spec = copy.deepcopy(SPEC)
        spec["brief_before_heading"] = "A Heading That Is Not There"
        with self.assertRaises(ValueError) as caught:
            bds.transform(page(), spec)
        self.assertIn("not found", str(caught.exception))

    def test_canonical_mismatch_raises(self):
        document = page().replace("/example-article/", "/some-other-article/")
        with self.assertRaises(ValueError) as caught:
            bds.transform(document, SPEC)
        self.assertIn("canonical", str(caught.exception))

    def test_missing_schema_raises(self):
        document = re.sub(r'<script type="application/ld\+json".*?</script>', "", page(), flags=re.DOTALL)
        with self.assertRaises(ValueError):
            bds.transform(document, SPEC)

    def test_too_few_opening_paragraphs_raises(self):
        document = page(body_paragraphs="<p>Only one opening paragraph, but a nice long one all the same.</p>\n<h2>Second Heading</h2>\n")
        with self.assertRaises(ValueError) as caught:
            bds.transform(document, SPEC)
        self.assertIn("opening paragraphs", str(caught.exception))


class ValidationTests(unittest.TestCase):
    def check(self, **overrides):
        spec = copy.deepcopy(SPEC)
        spec.update(overrides)
        bds.validate(spec, Path("example-article.json"))

    def test_valid_spec_passes(self):
        self.check()

    def test_long_title_rejected(self):
        with self.assertRaises(ValueError):
            self.check(title="A" * 66)

    def test_short_meta_description_rejected(self):
        with self.assertRaises(ValueError):
            self.check(meta_description="Too short.")

    def test_em_dash_rejected(self):
        with self.assertRaises(ValueError):
            self.check(hero_subtitle="A guide — to the thing")

    def test_pillar_must_be_one_of_the_five(self):
        with self.assertRaises(ValueError):
            self.check(pillar="Uncategorized")

    def test_cta_must_match_the_pillar(self):
        spec = copy.deepcopy(SPEC)
        spec["briefing"]["cta"]["href"] = "/5-pillars-free-trainings/scale/"
        with self.assertRaises(ValueError):
            bds.validate(spec, Path("example-article.json"))


class LivePageTests(unittest.TestCase):
    """The transformer must stay idempotent against the real pages it owns."""

    def test_every_content_file_is_valid_and_idempotent(self):
        files = sorted(bds.CONTENT.glob("*.json"))
        self.assertTrue(files, "no content files to check")
        for path in files:
            with self.subTest(article=path.stem):
                spec = bds.load(path.stem)
                document = (bds.WWW / path.stem / "index.html").read_text(encoding="utf-8")
                once = bds.transform(document, spec)
                self.assertEqual(once, bds.transform(once, spec))
                self.assertEqual(len(re.findall(r"<h1\b", once)), 1)
                self.assertEqual(once.count('id="dc-article-brief"'), 1)


if __name__ == "__main__":
    unittest.main()
