#!/usr/bin/env python3
"""Focused metadata regression checks for the three cost-guide pages."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "aus-cost-guide-download": "AUS Cost Guide - Download - Develop Coaching",
    "uk-cost-guide": "UK Cost Guide - Book Call - Develop Coaching",
    "uk-cost-guide-download": "UK Cost Guide - Download - Develop Coaching",
}


class CostGuideMetadataTest(unittest.TestCase):
    def test_each_page_has_one_canonical_title(self):
        for slug, expected_title in PAGES.items():
            with self.subTest(slug=slug):
                html = (ROOT / "www" / slug / "index.html").read_text()
                titles = re.findall(r"<title(?:\s[^>]*)?>(.*?)</title>", html, re.I | re.S)
                self.assertEqual(titles, [expected_title])


if __name__ == "__main__":
    unittest.main()
