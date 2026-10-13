import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PODCASTS = (
    'growing-a-140m-plumbing-company-with-charlie-mullins',
    'top-mistakes-construction-business-owners-make-and-how-to-avoid-them-with-jason-graystone',
    'building-a-strong-construction-team-tips-for-successful-recruiting-with-gaelle-blake',
)

class SeoFollowupTests(unittest.TestCase):
    def test_slashless_redirects_precede_platform_normalisation(self):
        config = json.loads((ROOT / 'www/vercel.json').read_text())
        self.assertTrue(config['trailingSlash'])
        self.assertEqual(config.get('bulkRedirectsPath'), 'priority-redirects.json')
        rules = json.loads((ROOT / 'www' / config['bulkRedirectsPath']).read_text())
        # Bulk redirects cannot take a host condition and run before every
        # deployment route, so they are pinned to the .com hosts with fully
        # qualified sources (never fire on developcoaching.com.au).
        hosts = ('https://develop-coaching.com', 'https://www.develop-coaching.com')
        paths = {'/my-story', '/case-study', '/contact-2', '/contact-2/'}
        self.assertEqual(len(rules), 8)
        self.assertEqual({r['source'] for r in rules}, {h + p for h in hosts for p in paths})
        manual = json.loads((ROOT / 'export/manual-redirects.json').read_text())
        for rule in rules:
            path = rule['source'].split('.com', 1)[1]
            expected = '/contact/' if path.startswith('/contact-2') else '/about-greg-wilkes/'
            self.assertEqual(rule['destination'], expected)
            self.assertIs(rule['permanent'], True)
            self.assertIs(rule['caseSensitive'], True)
            self.assertIs(rule['preserveQueryParams'], True)
            if path.startswith('/contact-2'):
                continue  # priority-only rule (c0f072f); no fallback copy kept
            for existing in (config['redirects'], manual):
                self.assertTrue(any(r['source'] == path and
                                    r['destination'] == rule['destination']
                                    for r in existing))

    def test_about_redirects_skip_trailing_slash_hop(self):
        for filename in ('export/manual-redirects.json', 'www/vercel.json'):
            data = json.loads((ROOT / filename).read_text())
            rules = data['redirects'] if isinstance(data, dict) else data
            for slug in ('my-story', 'case-study'):
                for suffix in ('', '/'):
                    matching = [r for r in rules if r['source'] == '/' + slug + suffix]
                    self.assertEqual(len(matching), 1, (filename, slug, suffix))
                    self.assertEqual(matching[0]['destination'], '/about-greg-wilkes/')

    def test_priority_podcast_links(self):
        page = (ROOT / 'www/podcast/index.html').read_text()
        for slug in PODCASTS:
            self.assertIn('href="/podcast/' + slug + '/"', page)
            self.assertTrue((ROOT / 'www/podcast' / slug / 'index.html').is_file())

    def test_testimonial_links_match_existing_videos(self):
        page = (ROOT / 'www/client-wins/index.html').read_text()
        for slug, video in [('brad-testimonial', 'AePCs4liO0Q'),
                            ('stephen-and-ashley-testimonial-2', 'MGAD2pxmNrc')]:
            self.assertIn('href="/' + slug + '/"', page)
            self.assertIn(video, (ROOT / 'www' / slug / 'index.html').read_text())

if __name__ == '__main__':
    unittest.main()
