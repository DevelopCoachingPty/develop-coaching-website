#!/usr/bin/env python3
"""Checks publish_page.py still fits the exported template.

The template is a frozen WordPress export, so these assertions are really
guarding against template drift: if a re-export changes the markup, the
publisher must fail loudly here rather than ship a broken page.

    python3 scripts/test_publish_page.py
"""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_page  # noqa: E402

TEMPLATE = publish_page.DEFAULT_TEMPLATE
PAYLOAD = {
    "title": "Test Page Title Alpha",
    "slug": "unit-test-page",
    "meta_description": "Test meta description for the publisher self-check.",
    "category": "Convert",
    "date": "2026-01-02",
    "image_url": "/wp-content/uploads/2023/06/planner.png",
    "body_html": '<p>Body paragraph one.</p>\n<h2>Body heading</h2>\n<p>A <a href="https://develop-coaching.com/client-wins/">link</a>.</p>',
}

failures = []


def check(name: str, ok: bool) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def refused(fn) -> bool:
    """True if fn() bails out the way the publisher reports a bad payload."""
    try:
        fn()
    except SystemExit:
        return True
    except Exception:  # any other error means the guard is not the thing firing
        return False
    return False


def run_cli(www: str, payload: dict, *flags: str) -> None:
    """Run the publisher end to end against a throwaway site directory."""
    real_www, real_argv = publish_page.WWW, sys.argv
    payload_path = os.path.join(www, "_payload.json")
    json.dump(payload, open(payload_path, "w", encoding="utf-8"))
    publish_page.WWW = www
    sys.argv = ["publish_page.py", "--json", payload_path, *flags]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            publish_page.main()
    finally:
        publish_page.WWW, sys.argv = real_www, real_argv


def check_paths_are_contained() -> None:
    """A slug or template that walks out of www/ must never reach the disk."""
    check(
        "traversal slug refused",
        refused(lambda: publish_page.build_page(
            {**PAYLOAD, "slug": "../../../../../../tmp/pwned-by-publish-page"}
        )),
    )
    check(
        "absolute slug refused",
        refused(lambda: publish_page.build_page({**PAYLOAD, "slug": "/tmp/pwned-by-publish-page"})),
    )
    check(
        "empty slug refused",
        refused(lambda: publish_page.build_page({**PAYLOAD, "slug": "///"})),
    )
    check(
        "traversal template refused",
        refused(lambda: publish_page.build_page({**PAYLOAD, "template": "../../../../etc"})),
    )
    check(
        "traversal slug wrote nothing",
        not os.path.exists("/tmp/pwned-by-publish-page"),
    )


def check_overwrite_needs_opt_in() -> None:
    """An existing page is only replaced when the caller says so.

    This runs against a copy of the template in a temp directory, so a real
    page under www/ is never a test subject.
    """
    www = tempfile.mkdtemp(prefix="publish-page-test-")
    try:
        os.makedirs(os.path.join(www, TEMPLATE))
        shutil.copy(
            os.path.join(publish_page.WWW, TEMPLATE, "index.html"),
            os.path.join(www, TEMPLATE, "index.html"),
        )
        out_file = os.path.join(www, PAYLOAD["slug"], "index.html")

        run_cli(www, PAYLOAD)
        check("first publish writes the page", os.path.exists(out_file))
        first = open(out_file, encoding="utf-8").read()

        second = {**PAYLOAD, "title": "Test Page Title Beta"}
        check("second publish refused", refused(lambda: run_cli(www, second)))
        check("refused publish left the page alone", open(out_file, encoding="utf-8").read() == first)

        run_cli(www, second, "--dry-run")
        check("dry run left the page alone", open(out_file, encoding="utf-8").read() == first)

        run_cli(www, second, "--overwrite")
        check(
            "overwrite flag replaces the page",
            "<title>Test Page Title Beta</title>" in open(out_file, encoding="utf-8").read(),
        )

        run_cli(www, {**PAYLOAD, "title": "Test Page Title Gamma", "overwrite": True})
        check(
            "overwrite payload field replaces the page",
            "<title>Test Page Title Gamma</title>" in open(out_file, encoding="utf-8").read(),
        )
    finally:
        shutil.rmtree(www, ignore_errors=True)


def main() -> None:
    template_html = open(
        os.path.join(publish_page.WWW, TEMPLATE, "index.html"), encoding="utf-8"
    ).read()
    html = publish_page.build_page(PAYLOAD)

    # New content is present
    check("title swapped", "<title>Test Page Title Alpha</title>" in html)
    check(
        "canonical swapped",
        '<link rel="canonical" href="https://develop-coaching.com/unit-test-page/" />' in html,
    )
    check("h1 swapped", ">Test Page Title Alpha</h1>" in html)
    check("body content inserted", "Body heading" in html)
    check("body links preserved", 'href="https://develop-coaching.com/client-wins/"' in html)
    check("hero image swapped", "2023/06/planner.png" in html)

    # Template content is gone
    check("template title removed", "Sales Funnel for Construction Company" not in html)
    check("template body removed", "Most construction businesses at" not in html)
    check("template author removed", "digital-progress" not in html)
    check("gravatar removed", "gravatar.com" not in html)
    check("wp-json link removed", 'rel="alternate" title="JSON"' not in html)

    # Chrome that must survive intact, including the per-post Elementor
    # stylesheets: rewriting those ids strips the page's styling.
    for asset in re.findall(r"elementor/css/[a-z0-9-]+\.css", template_html):
        if asset not in html:
            check(f"stylesheet kept: {asset}", False)
            break
    else:
        check("stylesheets kept", True)
    check(
        "nav intact",
        html.count("SCHEDULE A CALL") == template_html.count("SCHEDULE A CALL"),
    )
    check("document closed", html.strip().endswith("</html>"))

    # Structured data
    m = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        check("json-ld present", False)
    else:
        graph = json.loads(m.group(1))["@graph"]
        article = next((n for n in graph if "BlogPosting" in str(n.get("@type"))), None)
        check("json-ld article present", article is not None)
        if article:
            check("json-ld headline", article.get("headline") == PAYLOAD["title"])
            check("json-ld date", article.get("datePublished") == PAYLOAD["date"])
            check("json-ld author is Greg", article.get("author") == {"@id": publish_page.AUTHOR_ID})
        people = [n.get("name") for n in graph if n.get("@type") == "Person"]
        check("json-ld single author node", people == ["Greg Wilkes"])

    # Payload paths and existing pages
    check_paths_are_contained()
    check_overwrite_needs_opt_in()

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
