#!/usr/bin/env python3
"""Checks published articles are linked from the blog, category hubs, and related posts.

    python3 scripts/test_link_published_article.py
"""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import link_published_article as linker  # noqa: E402
import publish_page  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
ORPHANS = linker.ORPHAN_SLUGS
FUNNEL = linker.FUNNEL


def page(title, category, date, body="Post body.", book=True):
    chip = ""
    if category:
        hub = linker.category_hub(category)
        chip = (
            f'<a href="/category/{hub}/" class="elementor-post-info__terms-list-item">{category}</a>'
        )
    award = '<section class="dc-book-award">award</section>' if book else ""
    return f"""<!DOCTYPE html>
<html><head><title>{title}</title>
<meta property="article:section" content="{category or ""}" />
<meta property="article:published_time" content="{date}T00:00:00+00:00" />
</head><body>
<div class="elementor-widget-theme-post-content">{body}</div>
{chip}
{award}
<footer>footer</footer>
</body></html>
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot(root: Path):
    files = {}
    for path in root.rglob("*"):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="link-published-")
        self.www = Path(self.tmp) / "www"
        posts = {
            "markup-vs-margin": ("Markup vs Margin", "Convert", "2026-11-01", "TARGET-SENTINEL"),
            "construction-profit-margin-uk": ("Construction Profit Margin", "Plan", "2021-09-09", "MARGIN-SENTINEL"),
            "how-to-price-construction-work": ("How to Price Construction Work", "Convert", "2025-11-17", "PRICE-SENTINEL"),
            "construction-job-pricing": ("How to Price a Construction Job", "Convert", "2025-09-22", "JOB-SENTINEL"),
            "how-to-stop-wasting-time-on-quotes": ("How to Stop Wasting Time on Quotes", "Convert", "2019-06-24", "QUOTES-SENTINEL"),
            "fill-the-order-book": ("Fill The Order Book", "", "2026-10-12", "FUNNEL-SENTINEL"),
        }
        locs = []
        for slug, (title, category, date, body) in posts.items():
            write(self.www / slug / "index.html", page(title, category, date, body))
            locs.append(
                f"<url><loc>https://develop-coaching.com/{slug}/</loc><lastmod>{date}</lastmod></url>"
            )
        write(self.www / "post-sitemap.xml", "<urlset>" + "".join(locs) + "</urlset>")
        write(
            self.www / "blog" / "index.html",
            """<!DOCTYPE html><html><head><title>Blog</title></head><body>
<div class="page-content">
<div class="elementor-loop">ELEMENTOR-LOOP</div>
</div>
</body></html>
""",
        )
        write(
            self.www / "category" / "convert" / "index.html",
            """<!DOCTYPE html><html><head><title>Convert</title></head><body>
<h1>Category: Convert</h1>
<div class="elementor-widget elementor-widget-archive-posts">ARCHIVE</div>
</body></html>
""",
        )
        self.before = snapshot(self.www)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_links_markup_from_blog_hub_and_related_posts(self):
        result = linker.link_published_article(
            self.www, "markup-vs-margin", title="Markup vs Margin", category="Convert", date="2026-11-01"
        )
        self.assertTrue(result["blog"])
        self.assertEqual(result["hub"], "convert")
        self.assertGreaterEqual(len(result["sources"]), 3)
        self.assertLessEqual(len(result["sources"]), 4)
        self.assertNotIn("markup-vs-margin", result["sources"])
        self.assertNotIn("fill-the-order-book", result["sources"])

        blog = (self.www / "blog" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-dc-published-index="blog"', blog)
        self.assertIn(">Latest articles</h2>", blog)
        self.assertIn('data-dc-published-slug="markup-vs-margin"', blog)
        self.assertIn("ELEMENTOR-LOOP", blog)
        self.assertLess(blog.index('<div class="page-content">'), blog.index('data-dc-published-index="blog"'))
        self.assertLess(blog.index('data-dc-published-index="blog"'), blog.index("ELEMENTOR-LOOP"))
        self.assertEqual(blog.count('id="dc-published-links-style"'), 1)
        self.assertNotIn("develop-coaching.com.au", blog)
        self.assertNotIn("developcoaching.com.au", blog)

        hub = (self.www / "category" / "convert" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-dc-published-index="category-convert"', hub)
        self.assertIn(">Latest Convert articles</h2>", hub)
        self.assertIn('data-dc-published-slug="markup-vs-margin"', hub)
        self.assertLess(hub.index('data-dc-published-index="category-convert"'), hub.index("elementor-widget-archive-posts"))

        incoming = []
        for slug in result["sources"]:
            html = (self.www / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'data-dc-related-slug="markup-vs-margin"', html)
            self.assertIn(">Related articles</h2>", html)
            self.assertLess(html.index('data-dc-published-related'), html.index('class="dc-book-award"'))
            self.assertIn("-SENTINEL", html)
            incoming.append(slug)
        self.assertGreaterEqual(len(incoming), 3)

        target = (self.www / "markup-vs-margin" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("data-dc-related", target)
        self.assertNotIn("data-dc-published", target)
        self.assertIn("TARGET-SENTINEL", target)
        funnel = (self.www / "fill-the-order-book" / "index.html").read_bytes()
        self.assertEqual(funnel, self.before["fill-the-order-book/index.html"])
        self.assertNotIn(b"data-dc-related", funnel)
        self.assertNotIn(b"data-dc-published", funnel)

        after = snapshot(self.www)
        again = linker.link_published_article(
            self.www, "markup-vs-margin", title="Markup vs Margin", category="Convert", date="2026-11-01"
        )
        self.assertCountEqual(again["sources"], result["sources"])
        self.assertEqual(snapshot(self.www), after)

    def test_time_token_and_suffixed_duplicate(self):
        root = self.www
        for slug, title, category, date in (
            ("construction-programme", "The Construction Programme", "Scale", "2026-10-26"),
            ("time-in-construction", "Managing Time in Construction", "Deliver", "2022-05-03"),
            ("how-to-stop-wasting-time-on-quotes", "How to Stop Wasting Time on Quotes", "Convert", "2019-06-24"),
            ("how-to-recruit-for-your-construction-business", "How to Recruit", "Plan", "2023-04-29"),
            ("how-to-recruit-for-your-construction-business-2", "How to Recruit Duplicate", "Uncategorized", "2022-04-26"),
            ("construction-company-structure", "Construction Company Structure", "Scale", "2026-11-17"),
        ):
            write(root / slug / "index.html", page(title, category, date, slug))
        existing = (root / "post-sitemap.xml").read_text(encoding="utf-8")
        extra = "".join(
            f"<url><loc>https://develop-coaching.com/{slug}/</loc><lastmod>2026-01-01</lastmod></url>"
            for slug in (
                "construction-programme",
                "time-in-construction",
                "how-to-recruit-for-your-construction-business",
                "how-to-recruit-for-your-construction-business-2",
                "construction-company-structure",
            )
        )
        # how-to-stop-wasting-time-on-quotes is already in the fixture sitemap.
        write(root / "post-sitemap.xml", existing.replace("</urlset>", extra + "</urlset>"))
        duplicate = (root / "how-to-recruit-for-your-construction-business-2" / "index.html").read_bytes()
        wasting = (root / "how-to-stop-wasting-time-on-quotes" / "index.html").read_bytes()

        programme = linker.link_published_article(root, "construction-programme")
        self.assertIn("time-in-construction", programme["sources"])
        self.assertNotIn("how-to-stop-wasting-time-on-quotes", programme["sources"])
        self.assertEqual(
            (root / "how-to-stop-wasting-time-on-quotes" / "index.html").read_bytes(),
            wasting,
        )

        structure = linker.link_published_article(root, "construction-company-structure")
        self.assertIn("how-to-recruit-for-your-construction-business", structure["sources"])
        self.assertNotIn("how-to-recruit-for-your-construction-business-2", structure["sources"])
        self.assertEqual(
            (root / "how-to-recruit-for-your-construction-business-2" / "index.html").read_bytes(),
            duplicate,
        )

    def test_strong_match_does_not_expand_the_candidate(self):
        """A candidate keeps only its own slug tokens.

        Expanding the candidate too would let every "marketing" slug inherit
        the whole marketing topic, and would let snagging, risk, programme and
        subcontractors outrank construction-project-management.
        """
        www = Path(self.tmp) / "score"
        posts = [
            ("construction-programme", "The Construction Programme", "Scale", "2026-10-26"),
            ("snagging-list", "Snagging List", "Deliver", "2026-11-01"),
            ("construction-risk-management", "Construction Risk Management", "Deliver", "2026-11-17"),
            ("managing-subcontractors-on-site", "Managing Subcontractors on Site", "Convert", "2026-11-17"),
            ("construction-project-management", "Construction Project Management", "Plan", "2024-05-06"),
            ("construction-site-set-up-plan", "How to Organise a Construction Site", "Deliver", "2022-02-13"),
            ("time-in-construction", "Managing Time in Construction", "Deliver", "2022-05-03"),
            ("construction-marketing-plan", "Construction Marketing Plan", "Attract", "2026-11-17"),
            ("digital-marketing-construction", "Digital Marketing Construction", "Attract", "2020-01-01"),
            ("digital-marketing-for-construction", "Digital Marketing for Construction", "Attract", "2020-02-01"),
            ("construction-marketing", "Construction Marketing", "Attract", "2020-03-01"),
            ("construction-business-marketing", "Construction Business Marketing", "Attract", "2020-04-01"),
            (
                "the-construction-company-marketing-strategy-to-scale-past-1m",
                "Construction Company Marketing Strategy",
                "Attract",
                "2026-06-05",
            ),
        ]
        locs = []
        for slug, title, category, date in posts:
            write(www / slug / "index.html", page(title, category, date, slug))
            locs.append(
                f"<url><loc>https://develop-coaching.com/{slug}/</loc><lastmod>{date}</lastmod></url>"
            )
        write(www / "post-sitemap.xml", "<urlset>" + "".join(locs) + "</urlset>")

        programme = linker.link_published_article(www, "construction-programme")
        self.assertIn("construction-project-management", programme["sources"])
        self.assertTrue(
            {"construction-site-set-up-plan", "time-in-construction"} & set(programme["sources"])
        )
        self.assertNotIn("snagging-list", programme["sources"])
        self.assertNotIn("construction-risk-management", programme["sources"])

        marketing = linker.link_published_article(www, "construction-marketing-plan")
        self.assertIn(
            "the-construction-company-marketing-strategy-to-scale-past-1m",
            marketing["sources"],
        )
        self.assertNotIn("construction-site-set-up-plan", marketing["sources"])

    def test_refuses_unsafe_slugs_and_funnel_pages(self):
        before = snapshot(self.www)
        for slug in (
            "../etc/passwd",
            "Foo",
            "has space",
            "developcoaching",
            "evil.com.au",
            "a/b",
            "markup_vs_margin",
            "",
            "fill-the-order-book",
        ):
            with self.subTest(slug=slug):
                with self.assertRaises(SystemExit):
                    linker.link_published_article(self.www, slug)
        self.assertEqual(snapshot(self.www), before)


class PublishPageTests(unittest.TestCase):
    def site(self, with_blog: bool) -> str:
        www = tempfile.mkdtemp(prefix="publish-link-")
        template = publish_page.DEFAULT_TEMPLATE
        os.makedirs(os.path.join(www, template))
        shutil.copy(
            os.path.join(publish_page.WWW, template, "index.html"),
            os.path.join(www, template, "index.html"),
        )
        if with_blog:
            write(
                Path(www) / "blog" / "index.html",
                "<!DOCTYPE html><html><head><title>Blog</title></head><body>"
                '<div class="page-content"><p>Existing list</p></div></body></html>',
            )
            write(
                Path(www) / "category" / "convert" / "index.html",
                "<!DOCTYPE html><html><head><title>Convert</title></head><body>"
                '<div class="elementor-widget elementor-widget-archive-posts"></div></body></html>',
            )
        self.addCleanup(shutil.rmtree, www, True)
        return www

    def run_publisher(self, www: str, payload: dict, *flags: str):
        real_www, real_argv = publish_page.WWW, sys.argv
        payload_path = os.path.join(www, "_payload.json")
        with open(payload_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        publish_page.WWW = www
        sys.argv = ["publish_page.py", "--json", payload_path, *flags]
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                publish_page.main()
        finally:
            publish_page.WWW, sys.argv = real_www, real_argv
        return json.loads(stdout.getvalue()), stderr.getvalue()

    def test_publisher_links_when_blog_exists_and_skips_it_on_dry_run(self):
        www = self.site(with_blog=True)
        payload = {
            "title": "Publisher Link Check",
            "slug": "publisher-link-check",
            "meta_description": "A publisher link check.",
            "category": "Convert",
            "date": "2026-11-18",
            "body_html": "<p>Publisher body.</p>",
        }
        blog = Path(www) / "blog" / "index.html"
        before = blog.read_text(encoding="utf-8")
        dry, _stderr = self.run_publisher(www, payload, "--dry-run")
        self.assertTrue(dry["dry_run"])
        self.assertIsNone(dry["internal_links"])
        self.assertEqual(blog.read_text(encoding="utf-8"), before)
        self.assertFalse((Path(www) / "publisher-link-check" / "index.html").exists())

        result, _stderr = self.run_publisher(www, payload)
        self.assertFalse(result["dry_run"])
        self.assertTrue(result["internal_links"]["blog"])
        self.assertEqual(result["internal_links"]["hub"], "convert")
        linked = blog.read_text(encoding="utf-8")
        self.assertIn('data-dc-published-slug="publisher-link-check"', linked)
        hub = (Path(www) / "category" / "convert" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-dc-published-slug="publisher-link-check"', hub)
        self.assertLess(
            hub.index('data-dc-published-index="category-convert"'),
            hub.index("elementor-widget-archive-posts"),
        )
        self.assertTrue((Path(www) / "publisher-link-check" / "index.html").is_file())

    def test_publisher_does_not_create_a_missing_blog(self):
        www = self.site(with_blog=False)
        payload = {
            "title": "Publisher Without Blog",
            "slug": "publisher-without-blog",
            "meta_description": "No blog on this fixture.",
            "category": "Convert",
            "date": "2026-11-18",
            "body_html": "<p>Still published.</p>",
        }
        result, _stderr = self.run_publisher(www, payload)
        self.assertTrue((Path(www) / "publisher-without-blog" / "index.html").is_file())
        self.assertFalse((Path(www) / "blog").exists())
        self.assertFalse((Path(www) / "category").exists())
        self.assertFalse(result["internal_links"]["blog"])
        self.assertIsNone(result["internal_links"]["hub"])


class RealSiteTests(unittest.TestCase):
    def test_audited_orphans_are_linked_and_funnel_pages_are_not(self):
        blog = (WWW / "blog" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("develop-coaching.com.au", blog)
        self.assertNotIn("developcoaching.com.au", blog)
        self.assertIn('data-dc-published-index="blog"', blog)
        self.assertIn(">Latest articles</h2>", blog)
        self.assertLess(blog.index('<div class="page-content">'), blog.index('data-dc-published-index="blog"'))
        self.assertIn("Develop Coaching BLOG", blog)

        listed = re.findall(
            r'data-dc-published-slug="([^"]+)" data-dc-published-date="([^"]+)"',
            blog,
        )
        by_slug = {slug: date for slug, date in listed}
        previous = None
        for slug, date in listed:
            if previous:
                self.assertGreaterEqual(previous[0], date)
                if previous[0] == date:
                    self.assertLess(previous[1], slug)
            previous = (date, slug)

        pages = {}
        for path in WWW.rglob("index.html"):
            pages[path] = path.read_text(encoding="utf-8")

        for slug in ORPHANS:
            with self.subTest(slug=slug):
                self.assertIn(slug, by_slug)
                article = (WWW / slug / "index.html").read_text(encoding="utf-8")
                hub = re.search(
                    r'href="/category/([^"/]+)/" class="elementor-post-info__terms-list-item"',
                    article,
                ).group(1)
                hub_html = (WWW / "category" / hub / "index.html").read_text(encoding="utf-8")
                self.assertIn(f'data-dc-published-slug="{slug}"', hub_html)
                self.assertLess(
                    hub_html.index(f'data-dc-published-index="category-{hub}"'),
                    hub_html.index("elementor-widget-archive-posts"),
                )
                self.assertIn(f">Latest {hub.capitalize()} articles</h2>", hub_html)
                incoming = [
                    path for path, text in pages.items()
                    if f'data-dc-related-slug="{slug}"' in text
                ]
                self.assertGreaterEqual(len(incoming), 3, incoming)
                self.assertLessEqual(len(incoming), 4, incoming)
                for path in incoming:
                    source = path.relative_to(WWW).parts[0]
                    self.assertNotIn(source, FUNNEL)
                    self.assertNotEqual(source, slug)
                    self.assertNotIn("develop-coaching.com.au", pages[path])
                    self.assertNotIn("developcoaching.com.au", pages[path])

        funnel = pages[WWW / "fill-the-order-book" / "index.html"]
        self.assertNotIn("data-dc-related", funnel)
        self.assertNotIn("data-dc-published", funnel)
        duplicate = WWW / "how-to-recruit-for-your-construction-business-2" / "index.html"
        self.assertNotIn("data-dc-related", duplicate.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
