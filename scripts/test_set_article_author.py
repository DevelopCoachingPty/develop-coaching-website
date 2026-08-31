#!/usr/bin/env python3
"""Tests for crediting Greg as the author of every article."""

import copy
import json
import re
import unittest

import set_article_author as saa


def page(author=None, extra_nodes=()) -> str:
    posting = {"@type": "BlogPosting", "headline": "Example"}
    graph = [{"@type": "WebPage", "@id": "https://develop-coaching.com/example/"}]
    if author:
        graph.append(
            {
                "@type": "Person",
                "@id": author["@id"],
                "name": author["name"],
                "url": author["@id"],
            }
        )
        posting["author"] = {"@id": author["@id"], "name": author["name"]}
    graph.extend(copy.deepcopy(list(extra_nodes)))
    graph.append(posting)
    schema = {"@context": "https://schema.org", "@graph": graph}
    return (
        '<html><head><script type="application/ld+json" class="rank-math-schema-pro">'
        + json.dumps(schema)
        + "</script></head><body></body></html>"
    )


def graph_of(document: str) -> list:
    body = re.search(r'class="rank-math-schema-pro">(.*?)</script>', document, re.DOTALL)
    return json.loads(body.group(1))["@graph"]


AGENCY = {"@id": "https://develop-coaching.com/author/seodigital/", "name": "seo@digital-progress.co.uk"}
OLD_GREG = {"@id": "https://develop-coaching.com/author/gregwilkes/", "name": "gregwilkes"}


class AuthorTests(unittest.TestCase):
    def test_agency_author_is_replaced(self):
        out, previous = saa.set_author(page(AGENCY))
        self.assertEqual(previous, "seo@digital-progress.co.uk")
        posting = next(n for n in graph_of(out) if n["@type"] == "BlogPosting")
        self.assertEqual(posting["author"]["name"], "Greg Wilkes")
        self.assertEqual(posting["author"]["@id"], saa.AUTHOR_ID)

    def test_old_person_node_is_removed(self):
        out, _ = saa.set_author(page(AGENCY))
        ids = [n.get("@id") for n in graph_of(out) if n.get("@type") == "Person"]
        self.assertEqual(ids, [saa.AUTHOR_ID])

    def test_missing_author_is_added(self):
        out, previous = saa.set_author(page(author=None))
        self.assertEqual(previous, "")
        people = [n for n in graph_of(out) if n.get("@type") == "Person"]
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["name"], "Greg Wilkes")

    def test_author_url_points_at_a_page_that_exists(self):
        out, _ = saa.set_author(page(OLD_GREG))
        person = next(n for n in graph_of(out) if n.get("@type") == "Person")
        self.assertEqual(person["url"], "https://develop-coaching.com/about-greg-wilkes/")
        self.assertNotIn("/author/gregwilkes/", out)

    def test_idempotent(self):
        once, _ = saa.set_author(page(AGENCY))
        twice, _ = saa.set_author(once)
        self.assertEqual(once, twice)

    def test_no_duplicate_person_node_on_rerun(self):
        once, _ = saa.set_author(page(AGENCY))
        twice, _ = saa.set_author(once)
        people = [n for n in graph_of(twice) if n.get("@type") == "Person"]
        self.assertEqual(len(people), 1)

    def test_other_person_nodes_are_left_alone(self):
        other = {"@type": "Person", "@id": "https://example.com/#someone", "name": "Someone Quoted"}
        out, _ = saa.set_author(page(AGENCY, extra_nodes=[other]))
        names = sorted(n["name"] for n in graph_of(out) if n.get("@type") == "Person")
        self.assertEqual(names, ["Greg Wilkes", "Someone Quoted"])

    def test_missing_blogposting_raises(self):
        document = page(AGENCY).replace('"BlogPosting"', '"WebPage"')
        with self.assertRaises(ValueError):
            saa.set_author(document)

    def test_missing_schema_raises(self):
        with self.assertRaises(ValueError):
            saa.set_author("<html><head></head><body></body></html>")


class LiveArticleTests(unittest.TestCase):
    def test_every_article_transforms_and_is_idempotent(self):
        slugs = saa.article_slugs()
        # Count is not hard coded: articles are retired as duplicate pairs are
        # merged, so assert every sitemap entry has a page instead of a number.
        self.assertTrue(slugs, "no articles found in the post sitemap")
        for slug in slugs:
            self.assertTrue((saa.WWW / slug / "index.html").exists(), slug)
        for slug in slugs:
            with self.subTest(article=slug):
                document = (saa.WWW / slug / "index.html").read_text(encoding="utf-8")
                once, _ = saa.set_author(document)
                twice, _ = saa.set_author(once)
                self.assertEqual(once, twice)
                posting = next(n for n in graph_of(once) if n["@type"] == "BlogPosting")
                self.assertEqual(posting["author"]["name"], "Greg Wilkes")


if __name__ == "__main__":
    unittest.main()
