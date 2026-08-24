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
