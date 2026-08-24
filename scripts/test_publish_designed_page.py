#!/usr/bin/env python3
"""Focused safety and output checks for publish_designed_page.py."""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_designed_page as designed  # noqa: E402


PAYLOAD = {
    "title": "The Develop Mastermind: Coaching for Builders Doing £750k to £5m",
    "slug": "courses/mastermind-course",
    "meta_description": "A coaching programme for established construction business owners.",
    "content_file": "content/mastermind.html",
    "shell": "about-greg-wilkes",
}

failures = []


def check(name: str, ok: bool) -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def refused(fn) -> bool:
    try:
        fn()
    except SystemExit:
        return True
    return False


def run_main(payload: dict, *flags: str) -> None:
    fd, payload_path = tempfile.mkstemp(prefix="designed-page-", suffix=".json")
    os.close(fd)
    real_argv = sys.argv
    try:
        with open(payload_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        sys.argv = ["publish_designed_page.py", "--json", payload_path, *flags]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            designed.main()
    finally:
        sys.argv = real_argv
        os.unlink(payload_path)


def main() -> None:
    html = designed.build_page(PAYLOAD)
    check(
        "designed body present",
        'class="dc2-page"' in html and "Five pillars. One plan." in html,
    )
    check(
        "main site navigation present",
        html.count('class="dc2-nav__links"') == 1
        and "Free Trainings" in html
        and "Client Wins" in html
        and "My Story" in html
        and "Podcast" in html,
    )
    check("five pillar icons present", html.count('class="dc2-pillar-icon"') == 5)
    check("four software cards present", html.count("<article><span>0") == 4)
    check("nine testimonial videos present", html.count('class="dc2-youtube"') == 9)
    check("nine poster-first testimonials present", html.count('class="dc2-youtube__poster"') == 9)
    check("testimonial player receives keyboard focus", "iframe.tabIndex = 0" in html and "iframe.focus()" in html)
    check("nine high-resolution testimonial images present", html.count("maxresdefault.jpg") == 9)
    check("testimonial videos load on click", "link.replaceWith(iframe)" in html and "?autoplay=1" in html)
    check("pillar headings use aligned rows", "grid-template-rows: auto 64px 1fr" in html)
    check(
        "James result accurately qualified",
        "£1.5m <span>towards £4m</span>" in html
        and "Scaling from £1.5m towards £4m" in html,
    )
    check("Bradley result verified", "From £5k jobs to a £730k project" in html)
    check("Dale result qualified", "Turnover roughly doubled" in html)
    check("testimonial footer removed", 'class="dc2-proof__cta"' not in html)
    check(
        "testimonial qualifiers removed",
        "projected" not in html.lower() and "forecast" not in html.lower(),
    )
    check("site chrome present", "<header" in html and "<footer" in html)
    check("title replaced", f"<title>{PAYLOAD['title']}</title>" in html)
    schema_match = re.search(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    schema = json.loads(schema_match.group(1)) if schema_match else {}
    authors = [
        node for node in schema.get("@graph", [])
        if node.get("@id") == designed.pp.AUTHOR_ID
    ]
    check("JSON-LD has one canonical author", len(authors) == 1)
    schema_text = json.dumps(schema, separators=(",", ":"))
    check(
        "JSON-LD drops shell page identity",
        "/about-greg-wilkes/#webpage" not in schema_text
        and '"@type":"AboutPage"' not in schema_text
        and '"@type":"VideoObject"' not in schema_text,
    )
    check(
        "traversal slug refused",
        refused(lambda: designed.build_page({**PAYLOAD, "slug": "../../tmp/escape"})),
    )
    check(
        "absolute shell refused",
        refused(lambda: designed.build_page({**PAYLOAD, "shell": "/tmp/escape"})),
    )
    check(
        "content escape refused",
        refused(lambda: designed.build_page({**PAYLOAD, "content_file": "/etc/passwd"})),
    )
    check(
        "CSS escape refused",
        refused(lambda: designed.build_page({**PAYLOAD, "css_files": ["/etc/passwd"]})),
    )

    out_file = os.path.join(designed.pp.WWW, PAYLOAD["slug"], "index.html")
    before = hashlib.sha256(open(out_file, "rb").read()).hexdigest()
    check("existing page refused", refused(lambda: run_main(PAYLOAD)))
    run_main(PAYLOAD, "--dry-run")
    after = hashlib.sha256(open(out_file, "rb").read()).hexdigest()
    check("dry run leaves existing page unchanged", before == after)

    if failures:
        raise SystemExit(f"{len(failures)} check(s) failed: {', '.join(failures)}")
    print("all checks passed")


if __name__ == "__main__":
    main()
