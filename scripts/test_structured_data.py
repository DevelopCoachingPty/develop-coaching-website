"""Tests for scripts/install_structured_data.py.

Run from the repo root: python3 -m unittest scripts.test_structured_data
"""
import json
import re
import unittest

from scripts.install_structured_data import (
    GREG_ID, ORG_ID, ROOT, SAME_AS, SITE, extract_faqs, install,
)

JSONLD = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)


def page(body: str, graph=None, url=f"{SITE}/example/") -> str:
    head = f'<html><head><link rel="canonical" href="{url}" />'
    if graph is not None:
        head += ('<script type="application/ld+json" class="rank-math-schema-pro">'
                 + json.dumps({"@context": "https://schema.org", "@graph": graph}) + '</script>')
    return head + '</head><body>' + body + '</body></html>'


def nodes(html: str) -> list:
    out = []

    def walk(x):
        if isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            if x.get("@type"):
                out.append(x)
            for v in x.values():
                walk(v)

    for block in JSONLD.findall(html):
        walk(json.loads(block))
    return out


def of_type(html, t):
    return [n for n in nodes(html) if t in (n["@type"] if isinstance(n["@type"], list) else [n["@type"]])]


EMAIL_AUTHOR = {"@type": "Person", "@id": f"{SITE}/author/nickdigital-progress-co-uk/",
                "name": "nick@digital-progress.co.uk", "worksFor": {"@id": ORG_ID}}
OLD_ORG = {"@type": ["HomeAndConstructionBusiness", "Organization"], "@id": ORG_ID,
           "name": "Develop Coaching", "address": {"@type": "PostalAddress"},
           "telephone": "+440000000000", "location": {"@id": f"{SITE}/#place"}}
PLACE = {"@type": "Place", "@id": f"{SITE}/#place", "address": {"@type": "PostalAddress"}}
FAQ_HTML = ('<h2>Frequently Asked Questions</h2>'
            '<h3>What does it cost?</h3><p>Nothing extra.</p>'
            '<h3>Can I bring my PM?</h3><p>Yes, bring them.</p>'
            '<h2>Next steps</h2><p>Book a call.</p>')


class OrganizationAndPeople(unittest.TestCase):
    def test_page_without_schema_gets_the_organization(self):
        html = install(page('<p>Hello</p>'))
        orgs = of_type(html, "Organization")
        self.assertEqual([o["@id"] for o in orgs], [ORG_ID])
        self.assertEqual(orgs[0]["name"], "Develop Coaching")
        self.assertNotIn("address", orgs[0])
        self.assertNotIn("telephone", orgs[0])

    def test_old_business_node_and_empty_place_are_replaced(self):
        html = install(page('<p>x</p>', [PLACE, OLD_ORG, {"@type": "WebSite", "@id": f"{SITE}/#website"}]))
        self.assertEqual(len(of_type(html, "Organization")), 1)
        self.assertEqual(of_type(html, "Place"), [])
        self.assertNotIn("+440000000000", html)

    def test_email_author_becomes_the_organization(self):
        article = {"@type": "Article", "@id": f"{SITE}/example/#a",
                   "author": {"@id": EMAIL_AUTHOR["@id"], "name": EMAIL_AUTHOR["name"]}}
        html = install(page('<p>x</p>', [OLD_ORG, EMAIL_AUTHOR, article]))
        self.assertNotIn("@digital-progress", html)
        # The only Person left is Greg, as the Organization's founder.
        self.assertEqual({p["@id"] for p in of_type(html, "Person")}, {GREG_ID})
        art = of_type(html, "Article")[0]
        self.assertEqual(art["author"], {"@id": ORG_ID})

    def test_greg_aliases_collapse_to_one_canonical_person(self):
        legacy = {"@type": "Person", "@id": f"{SITE}/#/schema/person/greg-wilkes", "name": "Greg Wilkes"}
        post = {"@type": "BlogPosting", "author": {"@id": legacy["@id"], "name": "Greg Wilkes"},
                "creator": {"@type": "Person", "name": "Greg Wilkes"}}
        html = install(page('<p>x</p>', [legacy, post]))
        ids = {n["@id"] for n in of_type(html, "Person")}
        self.assertEqual(ids, {GREG_ID})
        full = [n for n in of_type(html, "Person") if "jobTitle" in n]
        self.assertEqual(len(full), 1)
        self.assertEqual(full[0]["jobTitle"], "Founder")
        self.assertEqual(of_type(html, "BlogPosting")[0]["author"]["@id"], GREG_ID)

    def test_other_people_are_left_alone(self):
        guest = {"@type": "Person", "name": "Kurt Uhlir"}
        html = install(page('<p>x</p>', [{"@type": "PodcastEpisode", "actor": guest}]))
        self.assertIn({"@type": "Person", "name": "Kurt Uhlir"}, of_type(html, "Person"))

    def test_about_page_is_gregs_profile(self):
        url = f"{SITE}/about-greg-wilkes/"
        webpage = {"@type": "WebPage", "@id": f"{url}#webpage", "url": url}
        html = install(page('<p>x</p>', [OLD_ORG, webpage], url=url))
        profile = of_type(html, "ProfilePage")[0]
        self.assertEqual(profile["mainEntity"], {"@id": GREG_ID})
        self.assertTrue(any(n.get("jobTitle") == "Founder" for n in of_type(html, "Person")))

    def test_idempotent(self):
        for html in [page('<p>x</p>'), page(FAQ_HTML, [PLACE, OLD_ORG, EMAIL_AUTHOR])]:
            once = install(html)
            self.assertEqual(install(once), once)


class Faqs(unittest.TestCase):
    def test_visible_faq_without_schema_gets_faqpage(self):
        html = install(page(FAQ_HTML, [OLD_ORG]))
        faq = of_type(html, "FAQPage")[0]
        self.assertEqual([q["name"] for q in faq["mainEntity"]], ["What does it cost?", "Can I bring my PM?"])
        self.assertEqual(faq["mainEntity"][1]["acceptedAnswer"]["text"], "Yes, bring them.")

    def test_stale_questions_are_replaced_with_the_visible_ones(self):
        stale = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Old question?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Old."}}]}
        article = {"@type": "Article", "subjectOf": [stale]}
        html = install(page(FAQ_HTML, [OLD_ORG, article]))
        faqs = of_type(html, "FAQPage")
        self.assertEqual(len(faqs), 1)
        self.assertNotIn("Old question?", html)
        # Kept where it was (nested under the Article), not duplicated.
        self.assertIn("FAQPage", json.dumps(of_type(html, "Article")[0]))

    def test_faqpage_removed_when_the_page_shows_no_faqs(self):
        combined = {"@type": ["WebPage", "FAQPage"], "@id": f"{SITE}/example/", "mainEntity": [
            {"@type": "Question", "name": "Hidden?", "acceptedAnswer": {"@type": "Answer", "text": "x"}}]}
        html = install(page('<p>No questions here.</p>', [OLD_ORG, combined]))
        self.assertEqual(of_type(html, "FAQPage"), [])
        self.assertEqual(of_type(html, "WebPage")[0].get("mainEntity"), None)

    def test_accordion_bold_and_screen_reader_patterns(self):
        accordion = ('<section class="faq-section"><h2>Questions Builders Ask</h2>'
                     '<details><summary>Is there an offer?</summary><dl><dt class="elementor-screen-only">'
                     'Answer</dt><dd>Yes, at the end.</dd></dl>'
                     '<p><a class="cta-button" href="#">Get My Ticket</a></p></details></section>')
        self.assertEqual(extract_faqs(page(accordion)), [("Is there an offer?", "Yes, at the end.")])
        bold = '<h2>FAQs</h2><p><strong>How long does it take?</strong><br>About a year.</p>'
        self.assertEqual(extract_faqs(page(bold)), [("How long does it take?", "About a year.")])

    def test_region_hidden_text_is_left_out(self):
        html = ('<html><head></head><body data-region="uk"><section id="faq"><details><summary>Price?</summary>'
                '<p>From <span class="only-uk">£1</span><span class="only-au">A$1</span>.</p>'
                '</details></section></body></html>')
        self.assertEqual(extract_faqs(html), [("Price?", "From £1.")])

    def test_no_faq_section_is_none(self):
        self.assertIsNone(extract_faqs(page('<h2>What is a good margin?</h2><p>It depends.</p>')))


class LiveSite(unittest.TestCase):
    def test_every_page_is_already_installed_and_clean(self):
        for path in sorted((ROOT / "www").rglob("*.html")):
            if "wp-content" in path.relative_to(ROOT / "www").parts:
                continue
            html = path.read_text(encoding="utf-8")
            self.assertEqual(install(html, path=path), html, str(path))
            if "<body" not in html:
                continue
            found = nodes(html)
            self.assertTrue(any(n.get("@id") == ORG_ID for n in found), str(path))
            for n in found:
                if n["@type"] == "Person":
                    self.assertNotIn("@", str(n.get("name", "")), str(path))

    def test_same_as_links_are_the_sites_own_footer_links(self):
        home = (ROOT / "www" / "index.html").read_text(encoding="utf-8")
        for url in SAME_AS:
            self.assertIn(f'href="{url}"', home, url)


if __name__ == "__main__":
    unittest.main()
