#!/usr/bin/env python3
"""Swap the body of www/privacy/index.html for content/privacy-policy-body.html.

Idempotent. Edit the body file, then run this script. It also keeps the page's
modified dates and the sitemap lastmod in step with MODIFIED.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www/privacy/index.html"
BODY = ROOT / "content/privacy-policy-body.html"
SITEMAP = ROOT / "www/page-sitemap.xml"
MODIFIED = "2026-10-28T05:00:00+00:00"
TITLE = "Privacy and Cookie Policy"
DESCRIPTION = (
    "How Develop Coaching Pty Ltd collects, uses and protects your data, "
    "which cookies this site uses, and how to change your cookie choices."
)

BODY_RE = re.compile(
    r'(<div class="page-content">\s*)(?:<!-- dc-privacy-body:start -->.*?<!-- dc-privacy-body:end -->'
    r'|<p><strong>Background</strong></p>.*?</ol>)(\s*<div class="post-tags">)',
    re.S,
)


def apply(html, body, sitemap=None):
    html, n = BODY_RE.subn(lambda m: m.group(1) + body.strip() + m.group(2), html, count=1)
    if n != 1:
        raise SystemExit("privacy page body not found")
    html = re.sub(r"<title>Privacy Policy - Develop Coaching Pty Ltd</title>",
                  f"<title>{TITLE} - Develop Coaching Pty Ltd</title>", html)
    html = html.replace("Privacy Policy &#8211; Develop Coaching Pty Ltd",
                        f"{TITLE} &#8211; Develop Coaching Pty Ltd")
    html = html.replace('content="Privacy Policy - Develop Coaching Pty Ltd"',
                        f'content="{TITLE} - Develop Coaching Pty Ltd"')
    html = re.sub(r'(<meta (?:name|property)="(?:description|og:description|twitter:description)" content=")[^"]*(")',
                  lambda m: m.group(1) + DESCRIPTION + m.group(2), html)
    html = re.sub(r'(og:updated_time" content=")[^"]*(")', lambda m: m.group(1) + MODIFIED + m.group(2), html)
    html = re.sub(r'(article:modified_time" content=")[^"]*(")', lambda m: m.group(1) + MODIFIED + m.group(2), html)
    html = re.sub(r'("dateModified":")[^"]*(")', lambda m: m.group(1) + MODIFIED + m.group(2), html)
    if sitemap is not None:
        sitemap = re.sub(
            r"(<loc>https://develop-coaching\.com/privacy/</loc>\s*<lastmod>)[^<]*(</lastmod>)",
            lambda m: m.group(1) + MODIFIED[:10] + m.group(2), sitemap)
    return html, sitemap


def main():
    body = BODY.read_text(encoding="utf-8")
    html, sitemap = apply(PAGE.read_text(encoding="utf-8"), body, SITEMAP.read_text(encoding="utf-8"))
    PAGE.write_text(html, encoding="utf-8")
    SITEMAP.write_text(sitemap, encoding="utf-8")
    print("updated", PAGE.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
