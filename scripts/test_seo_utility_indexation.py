"""Utility URLs must work without being advertised for discovery."""
import json
from html.parser import HTMLParser
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UTILITIES = (
    '/5-profit-leaks-bonus/',

    '/the-build-and-scale-summit-2025/',
    '/build-your-future-event-page/',
    '/5-steps-to-5-million-2/',
    '/5-steps-to-5-million-in-2024-vip/',
    '/upgradelondonvip/',
    '/the-perfect-project/',
    '/the-5m-builder-game-plan-workshop/',

    '/valy-testimonial/',
    '/mike-and-nick-testimonial/',
    '/dan-testimonial/',
    '/dale-testimonial/',
    '/james-wilcock-testimonial/',
    '/bradley-testimonial/',
    '/dave-testimonial/',
    '/stephen-and-salina-testimonial/',
    '/richard-abrahams-testimonial/',
    '/geoff-testimonial/',
    '/lukas-testimonial/',
    '/sam-and-nathan-testimonial/',
    '/james-overton-testimonial/',
    '/george-testimonial/',
    '/sophie-and-neil-testimonial/',
    '/dominic-testimonial/',
    '/richard-jenkinson-testimonial/',
    '/schedule-a-call-book/',
    '/schedule-a-call-subscribe/',
    '/before-your-scale-session-2/',

    '/10795-2/', '/thank-you-5m-builder-gameplan/',
    '/thank-you-built-to-cash-out/', '/thankyou/',
    '/thank-you-build-scale-summit/', '/thank-you/', '/thank-you-subscribe-2/',
)

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.robots.append(attrs.get('content', ''))

RETIRED = ('annual-growth-calculator', 'contact-2', 'how-we-work')

def redirect_rules():
    """Every deployed and source-of-truth redirect, as (file, rule) pairs."""
    for name in ('www/vercel.json', 'export/manual-redirects.json'):
        loaded = json.loads((ROOT / name).read_text())
        rules = loaded['redirects'] if isinstance(loaded, dict) else loaded
        for rule in rules:
            yield name, rule

class UtilityIndexationTests(unittest.TestCase):
    def test_retired_pages_are_not_deployed_or_rebuilt(self):
        for slug in RETIRED:
            with self.subTest(slug=slug):
                self.assertFalse((ROOT / 'www' / slug / 'index.html').exists())
                self.assertFalse((ROOT / 'export/reference' / (slug + '.html')).exists())
                self.assertNotIn('/' + slug + '/',
                                 [r['u'] for r in json.loads((ROOT / 'www/search-index.json').read_text())])
                for sitemap in (ROOT / 'www').glob('*sitemap.xml'):
                    self.assertNotIn('https://develop-coaching.com/' + slug + '/', sitemap.read_text())

    def test_no_redirect_sends_visitors_to_a_retired_page(self):
        for name, rule in redirect_rules():
            destination = rule.get('destination', '').split('?')[0].strip('/')
            if destination in RETIRED:
                self.fail(name + ': ' + rule.get('source', '') + ' redirects to retired /'
                          + destination + '/, which 404s')

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
