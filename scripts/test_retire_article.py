#!/usr/bin/env python3
"""Tests for the article retirement helper."""

import tempfile
import unittest
import json
from pathlib import Path
from unittest import mock

import retire_article


ROOT = Path(__file__).resolve().parents[1]


class RetireSourceTests(unittest.TestCase):
    def test_removes_all_existing_managed_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            (source_dir / "old.json").write_text("{}", encoding="utf-8")
            (source_dir / "old.body.html").write_text("<p>Old</p>", encoding="utf-8")
            with mock.patch.object(retire_article, "BLOG_SYSTEM", source_dir), mock.patch.object(
                retire_article.subprocess, "run"
            ) as run:
                self.assertEqual(retire_article.retire_sources("old", check=False), 2)

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:5], ["git", "rm", "-q", "--", str(source_dir / "old.json")])
        self.assertEqual(command[5], str(source_dir / "old.body.html"))
        self.assertTrue(run.call_args.kwargs["check"])

    def test_check_mode_reports_sources_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            (source_dir / "old.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(retire_article, "BLOG_SYSTEM", source_dir), mock.patch.object(
                retire_article.subprocess, "run"
            ) as run:
                self.assertEqual(retire_article.retire_sources("old", check=True), 1)
                run.assert_not_called()


class RetirementOperationTests(unittest.TestCase):
    def test_rejects_destination_that_is_already_redirected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual = root / "manual.json"
            vercel = root / "vercel.json"
            manual.write_text(
                json.dumps([{"source": "/keeper", "destination": "/final/"}]),
                encoding="utf-8",
            )
            vercel.write_text(json.dumps({"redirects": []}), encoding="utf-8")
            with mock.patch.object(retire_article, "ROOT", root), mock.patch.object(
                retire_article, "MANUAL_REDIRECTS", manual
            ), mock.patch.object(retire_article, "VERCEL", vercel):
                with self.assertRaisesRegex(SystemExit, "destination is already redirected"):
                    retire_article.validate_destination_not_redirected("/keeper/")

    def test_rejects_retirement_with_inbound_redirects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual = root / "manual.json"
            vercel = root / "vercel.json"
            manual.write_text(
                json.dumps([{"source": "/legacy", "destination": "/old/"}]),
                encoding="utf-8",
            )
            vercel.write_text(json.dumps({"redirects": []}), encoding="utf-8")
            with mock.patch.object(retire_article, "ROOT", root), mock.patch.object(
                retire_article, "MANUAL_REDIRECTS", manual
            ), mock.patch.object(retire_article, "VERCEL", vercel):
                with self.assertRaisesRegex(SystemExit, "existing redirects point to /old/"):
                    retire_article.validate_no_inbound_redirects("old")

    def test_sitemap_removal_does_not_match_neighboring_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            sitemap = Path(tmp) / "post-sitemap.xml"
            sitemap.write_text(
                "<urlset><url><loc>https://develop-coaching.com/foo/</loc></url>"
                "<url><loc>https://develop-coaching.com/foo-2/</loc></url></urlset>",
                encoding="utf-8",
            )
            with mock.patch.object(retire_article, "SITEMAP", sitemap):
                self.assertEqual(retire_article.drop_from_sitemap("foo", check=False), 1)
            result = sitemap.read_text(encoding="utf-8")
            self.assertNotIn("/foo/", result)
            self.assertIn("/foo-2/", result)

    def test_search_removal_does_not_match_neighboring_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            search_index = Path(tmp) / "search-index.json"
            search_index.write_text(
                json.dumps([{"u": "/foo/"}, {"u": "/foo-2/"}]), encoding="utf-8"
            )
            with mock.patch.object(retire_article, "SEARCH_INDEX", search_index):
                self.assertEqual(retire_article.drop_from_search_index("foo", check=False), 1)
            self.assertEqual(json.loads(search_index.read_text(encoding="utf-8")), [{"u": "/foo-2/"}])
            self.assertTrue(search_index.read_text(encoding="utf-8").endswith("\n"))

    def test_link_repointing_does_not_match_neighboring_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            www = Path(tmp)
            page = www / "page" / "index.html"
            retired_page = www / "foo" / "index.html"
            page.parent.mkdir()
            retired_page.parent.mkdir()
            page.write_text(
                '<a href="/foo/">Old</a><a href="/foo-2/">Neighbor</a>', encoding="utf-8"
            )
            retired_page.write_text('<a href="/foo/">Self</a>', encoding="utf-8")
            with mock.patch.object(retire_article, "WWW", www):
                self.assertEqual(retire_article.repoint_links("foo", "/keeper/", check=False), 1)
            self.assertIn('href="/keeper/"', page.read_text(encoding="utf-8"))
            self.assertIn('href="/foo-2/"', page.read_text(encoding="utf-8"))
            self.assertIn('href="/foo/"', retired_page.read_text(encoding="utf-8"))

    def test_link_repointing_treats_destination_as_literal_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            www = Path(tmp)
            page = www / "page" / "index.html"
            page.parent.mkdir()
            page.write_text('<a href="/foo/">Old</a>', encoding="utf-8")
            destination = r"/keeper/\g<0>/"
            with mock.patch.object(retire_article, "WWW", www):
                self.assertEqual(retire_article.repoint_links("foo", destination, check=False), 1)
            self.assertIn(destination, page.read_text(encoding="utf-8"))

    def test_listing_cards_are_removed_but_contextual_links_remain(self):
        with tempfile.TemporaryDirectory() as tmp:
            www = Path(tmp)
            page = www / "archive" / "index.html"
            page.parent.mkdir()
            page.write_text(
                '<style>.site-heading{color:blue}</style><h1>Keep this heading</h1>'
                '<style>.e-loop-item-42{color:red}</style>'
                '<style id="loop-7">.shared-card{color:black}</style>'
                '<div data-elementor-type="loop-item" class="e-loop-item post-42 post">'
                '<div><a href="/old/">Old card</a></div></div>'
                '<p><a href="/old/">Useful contextual link</a></p>',
                encoding="utf-8",
            )
            with mock.patch.object(retire_article, "WWW", www):
                self.assertEqual(retire_article.drop_listing_cards("42", check=False), 1)
            result = page.read_text(encoding="utf-8")
            self.assertNotIn("Old card", result)
            self.assertNotIn("e-loop-item-42", result)
            self.assertIn("<h1>Keep this heading</h1>", result)
            self.assertIn(".site-heading{color:blue}", result)
            self.assertIn(".shared-card{color:black}", result)
            self.assertIn("Useful contextual link", result)

    def test_orphaned_dynamic_style_is_removed_without_a_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            www = Path(tmp)
            page = www / "archive" / "index.html"
            page.parent.mkdir()
            page.write_text(
                '<style>.e-loop-item-42{background:red}</style><h1>Archive</h1>',
                encoding="utf-8",
            )
            with mock.patch.object(retire_article, "WWW", www):
                self.assertEqual(retire_article.drop_listing_cards("42", check=False), 0)
            result = page.read_text(encoding="utf-8")
            self.assertNotIn("e-loop-item-42", result)
            self.assertIn("<h1>Archive</h1>", result)

    def test_archive_article_card_is_removed_in_check_and_write_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            www = Path(tmp)
            page = www / "archive" / "index.html"
            page.parent.mkdir()
            card = (
                '<article class="elementor-post post-42 post"><div><a href="/old/">'
                "Old card</a></div></article>"
            )
            page.write_text(card, encoding="utf-8")
            with mock.patch.object(retire_article, "WWW", www):
                self.assertEqual(retire_article.drop_listing_cards("42", check=True), 1)
                self.assertEqual(page.read_text(encoding="utf-8"), card)
                self.assertEqual(retire_article.drop_listing_cards("42", check=False), 1)
            self.assertNotIn("Old card", page.read_text(encoding="utf-8"))

    def test_add_redirects_updates_both_sources_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual = root / "manual.json"
            vercel = root / "vercel.json"
            manual.write_text("[]\n", encoding="utf-8")
            vercel.write_text('{"redirects": []}\n', encoding="utf-8")
            with mock.patch.object(retire_article, "MANUAL_REDIRECTS", manual), mock.patch.object(
                retire_article, "VERCEL", vercel
            ):
                self.assertEqual(retire_article.add_redirects("old", "/keeper/", check=False), 4)
                self.assertEqual(retire_article.add_redirects("old", "/keeper/", check=False), 0)
            self.assertEqual(len(json.loads(manual.read_text(encoding="utf-8"))), 2)
            self.assertEqual(len(json.loads(vercel.read_text(encoding="utf-8"))["redirects"]), 2)


class PublishedListingTests(unittest.TestCase):
    def test_retired_post_cards_are_absent(self):
        retired_post_ids = ("2494", "17557", "2165", "2213", "2372", "17558", "2323")
        for page in (ROOT / "www").rglob("index.html"):
            html = page.read_text(encoding="utf-8")
            for post_id in retired_post_ids:
                with self.subTest(page=page, post_id=post_id):
                    self.assertNotRegex(html, rf"\bpost-{post_id}\b")
                    self.assertNotIn(f"e-loop-item-{post_id}", html)

    def test_retired_featured_widget_is_removed_from_blog(self):
        blog = (ROOT / "www/blog/index.html").read_text(encoding="utf-8")
        self.assertNotIn('data-id="8389dcd"', blog)


if __name__ == "__main__":
    unittest.main()
