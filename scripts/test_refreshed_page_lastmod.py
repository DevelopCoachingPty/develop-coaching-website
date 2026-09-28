"""Guard discovery dates for the September SEO/GEO page releases."""

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://develop-coaching.com"
RELEASE_DATES = {
    "business-coaching-for-construction": "2026-09-15",
    "construction-job-pricing": "2026-09-15",
    "construction-profit-margin-uk": "2026-09-15",
    "construction-business-systems": "2026-09-15",
    "attract-the-right-clients": "2026-09-15",
    "construction-sales-funnel": "2026-09-15",
    "courses/mastermind-course": "2026-09-22",
}
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class RefreshedPageLastmodTest(unittest.TestCase):
    def test_refreshed_pages_have_consistent_discovery_dates(self):
        sitemaps = {}
        for filename in ("post-sitemap.xml", "courses-sitemap.xml"):
            root = ET.parse(ROOT / "www" / filename).getroot()
            for node in root.findall("s:url", NS):
                loc = node.findtext("s:loc", namespaces=NS)
                sitemaps[loc] = node.findtext("s:lastmod", namespaces=NS)

        exports = {}
        for kind in ("posts", "courses"):
            for item in json.loads((ROOT / "export" / "content" / f"{kind}.json").read_text()):
                exports[item.get("link")] = item

        for slug, release_date in RELEASE_DATES.items():
            with self.subTest(slug=slug):
                url = f"{DOMAIN}/{slug}/"
                self.assertIn(url, sitemaps)
                self.assertIn(url, exports)
                exported_date = exports[url]["modified_gmt"][:10]
                self.assertGreaterEqual(exported_date, release_date)
                self.assertEqual(sitemaps[url], exported_date)

                if not slug.startswith("courses/"):
                    source = json.loads(
                        (ROOT / "content" / "blog-system" / f"{slug}.json").read_text()
                    )
                    self.assertEqual(source["date_modified"][:10], exported_date)

                html = (ROOT / "www" / slug / "index.html").read_text()
                match = re.search(
                    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                    html, re.DOTALL,
                )
                self.assertIsNotNone(match)
                graph = json.loads(match.group(1))["@graph"]
                dated = [node for node in graph if node.get("@type") in ("WebPage", "BlogPosting")]
                self.assertTrue(dated)
                for node in dated:
                    self.assertGreaterEqual(node["dateModified"][:10], release_date)

                if not slug.startswith("courses/"):
                    article_time = re.search(
                        r'<meta property="article:modified_time" content="([^"]+)"', html
                    )
                    self.assertIsNotNone(article_time)
                    self.assertGreaterEqual(article_time.group(1)[:10], release_date)


if __name__ == "__main__":
    unittest.main()
