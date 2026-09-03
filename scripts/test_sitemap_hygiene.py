#!/usr/bin/env python3
"""Regression checks for legacy pages that must stay out of the sitemap."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"

REDIRECTS = {
    "/scale": "/5-pillars-free-trainings/scale/",
    "/testimonial": "/client-wins/",
    "/stephen-and-salina-testimonial-2": "/stephen-and-salina-testimonial/",
}


class SitemapHygieneTests(unittest.TestCase):
    def test_ahrefs_noindex_pages_are_not_in_sitemaps_or_search(self):
        noindex_paths = {
            "/5-steps-to-5-million-events/",
            "/5-steps-to-5-million-london-uk/",
            "/build-your-future/",
            "/podcast-transcript/podcast-2-test-trans/",
            "/scale-hub-page/",
            "/systems-and-processes-subcategory-page/",
        }
        sitemap_text = "\n".join(
            path.read_text() for path in WWW.glob("*sitemap.xml")
        )
        search_urls = {
            item["u"] for item in json.loads((WWW / "search-index.json").read_text())
        }

        for url_path in noindex_paths:
            page = WWW / url_path.lstrip("/") / "index.html"
            html = page.read_text(errors="ignore")
            robots_tags = re.findall(
                r'<meta[^>]+name=["\']robots["\'][^>]*>', html, re.I
            )
            with self.subTest(path=url_path):
                self.assertTrue(any("noindex" in tag.lower() for tag in robots_tags))
                self.assertNotIn(
                    f"https://develop-coaching.com{url_path}", sitemap_text
                )
                self.assertNotIn(url_path, search_urls)

    def test_archive_pagination_links_use_canonical_paths(self):
        for category in ("attract", "plan", "scale", "uncategorized"):
            paths = (
                ROOT / f"export/reference/category__{category}.html",
                ROOT / f"export/reference/category__{category}__page__2.html",
                WWW / f"category/{category}/index.html",
                WWW / f"category/{category}/page/2/index.html",
            )
            for path in paths:
                with self.subTest(path=path):
                    html = path.read_text(errors="ignore")
                    expected_path = (
                        f"/category/{category}/"
                        if "page__2" in path.name or "/page/2/" in path.as_posix()
                        else f"/category/{category}/page/2/"
                    )
                    expected_url = (
                        f"https://develop-coaching.com{expected_path}"
                        if "export/reference" in path.as_posix()
                        else expected_path
                    )
                    self.assertIn(f'href="{expected_url}"', html)
                    self.assertNotRegex(
                        html,
                        rf'href="(?:https://develop-coaching.com)?/category/'
                        rf'{category}/(?:page/2/)?\?[^\"]+"',
                    )

    def test_legacy_urls_have_permanent_redirects(self):
        config = json.loads((WWW / "vercel.json").read_text())
        redirects = {
            item["source"]: item
            for item in config["redirects"]
            if item.get("permanent") is True
        }
        for source, destination in REDIRECTS.items():
            for variant in (source, source + "/"):
                with self.subTest(source=variant):
                    self.assertIn(variant, redirects)
                    self.assertEqual(destination, redirects[variant]["destination"])

    def test_redirects_are_preserved_by_future_builds(self):
        redirects = {
            item["source"]: item
            for item in json.loads(
                (ROOT / "export/manual-redirects.json").read_text()
            )
        }
        for source, destination in REDIRECTS.items():
            with self.subTest(source=source):
                self.assertIn(source, redirects)
                self.assertEqual(destination, redirects[source]["destination"])

    def test_test_page_is_noindex_in_source_and_build(self):
        paths = (
            ROOT / "export/reference/test-landing-page.html",
            WWW / "test-landing-page/index.html",
        )
        for path in paths:
            with self.subTest(path=path):
                html = path.read_text(errors="ignore")
                tags = re.findall(
                    r'<meta[^>]+name=["\']robots["\'][^>]*>', html, re.I
                )
                self.assertTrue(tags)
                self.assertTrue(any("noindex" in tag.lower() for tag in tags))

    def test_noncanonical_urls_are_not_in_sitemaps_or_search(self):
        blocked = {
            "/courses/test/",
            "/podcast-transcript/test-podcast-v1-transcript/",
            "/scale/",
            "/test-page/",
            "/test-landing-page/",
            "/test/",
            "/testimonial/",
            "/testing-sop/",
            "/stephen-and-salina-testimonial-2/",
        }
        sitemap_text = "\n".join(
            path.read_text() for path in WWW.glob("*sitemap.xml")
        )
        search_urls = {
            item["u"] for item in json.loads((WWW / "search-index.json").read_text())
        }
        for path in blocked:
            with self.subTest(path=path):
                self.assertNotIn(f"https://develop-coaching.com{path}", sitemap_text)
                self.assertNotIn(path, search_urls)

    def test_scale_internal_link_uses_canonical_path(self):
        for path in (
            ROOT / "export/reference/systems-and-processes-subcategory-page.html",
            WWW / "systems-and-processes-subcategory-page/index.html",
        ):
            with self.subTest(path=path):
                html = path.read_text(errors="ignore")
                self.assertNotRegex(html, r'href=["\']/scale/?["\']')

    def test_test_page_filter_is_not_a_broad_prefix_match(self):
        source = (ROOT / "scripts/gen_seo_files.py").read_text()
        self.assertNotIn('NOINDEX_HINTS = ("/test"', source)


if __name__ == "__main__":
    unittest.main()
