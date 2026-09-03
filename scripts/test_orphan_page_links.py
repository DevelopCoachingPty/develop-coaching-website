#!/usr/bin/env python3
"""Regression tests for the high-value orphan links added in this change."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"

ARTICLE_LINKS = {
    "grow-groundworks-business": "/groundwork-business-coach/",
    "grow-painting-business": "/decorating-business-coach/",
    "grow-carpentry-business": "/carpentry-business-coach/",
    "how-to-expand-electrical-business": "/electrical-business-coach/",
    "grow-plastering-business": "/plastering-business-coach/",
    "grow-landscaping-business": "/landscaping-business-coach/",
}


class OrphanPageLinkTests(unittest.TestCase):
    def test_home_page_links_to_priority_hubs_and_terms(self):
        home = (WWW / "index.html").read_text(encoding="utf-8")
        for href in ("/blog/", "/trades-pipeline-diagnostic/", "/terms-conditions/"):
            self.assertIn(f'href="{href}"', home)
            self.assertTrue((WWW / href.lstrip("/") / "index.html").exists())

    def test_trade_guides_link_to_their_matching_coaching_pages(self):
        for slug, href in ARTICLE_LINKS.items():
            with self.subTest(slug=slug):
                page = (WWW / slug / "index.html").read_text(encoding="utf-8")
                self.assertEqual(page.count(f'href="{href}"'), 1)
                self.assertTrue((WWW / href.lstrip("/") / "index.html").exists())

    def test_trade_link_configuration_survives_article_regeneration(self):
        for slug, href in ARTICLE_LINKS.items():
            with self.subTest(slug=slug):
                spec = json.loads(
                    (ROOT / "content" / "blog-system" / f"{slug}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(spec["related_service"]["href"], href)

    def test_report_records_exactly_76_reproducible_baseline_urls(self):
        report = (ROOT / "docs" / "orphan-page-audit.md").read_text(encoding="utf-8")
        baseline = report.split("## Reproducible 76-URL baseline", 1)[1].split(
            "## Method", 1
        )[0]
        urls = [line for line in baseline.splitlines() if line.startswith("/")]
        self.assertEqual(len(urls), 76)
        self.assertEqual(len(set(urls)), 76)


if __name__ == "__main__":
    unittest.main()
