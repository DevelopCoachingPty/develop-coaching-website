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
        self.assertEqual(len(rules), 2)
        self.assertEqual({r['source'] for r in rules}, {'/my-story', '/case-study'})
        manual = json.loads((ROOT / 'export/manual-redirects.json').read_text())
        for rule in rules:
            self.assertEqual(rule['destination'], '/about-greg-wilkes/')
            self.assertIs(rule['permanent'], True)
            self.assertIs(rule['caseSensitive'], True)
            self.assertIs(rule['preserveQueryParams'], True)
            for existing in (config['redirects'], manual):
                self.assertTrue(any(r['source'] == rule['source'] and
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
