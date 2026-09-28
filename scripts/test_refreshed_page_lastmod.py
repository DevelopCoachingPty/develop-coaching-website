"""Guard discovery dates for the September SEO/GEO page releases."""

import json
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://develop-coaching.com"
RELEASE_DATES = {
    "business-coaching-for-construction": "2026-09-15T02:02:01Z",
    "construction-job-pricing": "2026-09-15T00:33:22Z",
    "construction-profit-margin-uk": "2026-09-15T00:33:22Z",
    "construction-business-systems": "2026-09-15T01:27:57Z",
    "attract-the-right-clients": "2026-09-15T02:02:01Z",
    "construction-sales-funnel": "2026-09-15T02:02:01Z",
    "courses/mastermind-course": "2026-09-22T05:00:14Z",
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

        for slug, release_time in RELEASE_DATES.items():
            with self.subTest(slug=slug):
                utc = datetime.fromisoformat(release_time.replace("Z", "+00:00"))
                local = utc.astimezone(ZoneInfo("Australia/Sydney"))
                expected_date = utc.date().isoformat()
                expected_utc = utc.strftime("%Y-%m-%dT%H:%M:%S")
                expected_local = local.isoformat(timespec="seconds")
                url = f"{DOMAIN}/{slug}/"
                self.assertIn(url, sitemaps)
                self.assertIn(url, exports)
                self.assertEqual(exports[url]["modified_gmt"], expected_utc)
                self.assertEqual(sitemaps[url], expected_date)

                if not slug.startswith("courses/"):
                    source = json.loads(
                        (ROOT / "content" / "blog-system" / f"{slug}.json").read_text()
                    )
                    self.assertEqual(source["date_modified"], expected_local)

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
                    self.assertEqual(node["dateModified"], expected_local)

                if not slug.startswith("courses/"):
                    article_time = re.search(
                        r'<meta property="article:modified_time" content="([^"]+)"', html
                    )
                    self.assertIsNotNone(article_time)
                    self.assertEqual(article_time.group(1), expected_local)


if __name__ == "__main__":
    unittest.main()
