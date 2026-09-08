"""Utility URLs must work without being advertised for discovery."""
import json
from html.parser import HTMLParser
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UTILITIES = ('/10795-2/', '/thank-you-5m-builder-gameplan/')

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.robots.append(attrs.get('content', ''))

class UtilityIndexationTests(unittest.TestCase):
    def test_utilities_remain_available_but_noindex(self):
        for path in UTILITIES:
            with self.subTest(path=path):
                parser = Metadata()
                parser.feed((ROOT / 'www' / path.strip('/') / 'index.html').read_text())
                self.assertEqual(len(parser.robots), 1)
                self.assertIn('noindex', parser.robots[0].split(', '))

    def test_utilities_absent_from_discovery(self):
        urls = set()
        for sitemap in (ROOT / 'www').glob('*sitemap.xml'):
            urls.update(n.text for n in ET.parse(sitemap).iter() if n.tag.endswith('}loc'))
        search = json.loads((ROOT / 'www/search-index.json').read_text())
        for path in UTILITIES:
            with self.subTest(path=path):
                self.assertNotIn('https://develop-coaching.com' + path, urls)
                self.assertNotIn(path, [row['u'] for row in search])

if __name__ == '__main__':
    unittest.main()
