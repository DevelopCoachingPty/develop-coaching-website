#!/usr/bin/env python3
"""Replace the shared legacy Elementor footer with the Develop design system."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_CSS = (ROOT / "content/_shared-footer.css").read_text(encoding="utf-8")
STYLE = f'<style id="dc-modern-footer">\n{SHARED_CSS}\n</style>'
STYLE_RE = re.compile(r'<style id="dc-modern-footer">.*?</style>', re.S | re.I)
LEGACY_FOOTER_RE = re.compile(
    r'<footer\b(?=[^>]*\bdata-elementor-id="9008")'
    r'(?=[^>]*\bclass="[^"]*\belementor-location-footer\b[^"]*")[^>]*>'
    r'.*?</footer>',
    re.S | re.I,
)
MODERN_BOOK_RE = re.compile(
    r'<section\b[^>]*class="[^"]*\bdc-book-award\b[^"]*"[^>]*>.*?</section>',
    re.S | re.I,
)
MODERN_FOOTER_RE = re.compile(
    r'<footer\b[^>]*\bdata-dc-modern-footer\b[^>]*>.*?</footer>',
    re.S | re.I,
)

BOOK_AWARD = """<section class="dc-book-award" aria-labelledby="dc-book-award-title">
  <div class="dc-footer-wrap dc-book-award__inner">
    <div class="dc-book-award__visual">
      <img src="/wp-content/uploads/2024/03/Build-Your-Future-Dollar.webp" alt="Building Your Future by Greg Wilkes" loading="lazy">
    </div>
    <div class="dc-book-award__copy">
      <p class="dc-book-award__kicker">Free ebook</p>
      <h2 id="dc-book-award-title">Download a copy of Greg’s #1 Amazon Bestseller.</h2>
      <p><em>Building Your Future</em> will change everything you ever thought about your construction business.</p>
      <a class="dc-book-award__button" href="/download-book/">Download the book</a>
    </div>
    <a class="dc-award-card" href="https://smenews.digital/winners/develop-coaching-2/" target="_blank" rel="noopener">
      <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 6 40 10 49 9 53 17 61 22 59 31 62 40 54 46 51 55 41 55 32 61 23 55 13 55 10 46 2 40 5 31 3 22 11 17 15 9 24 10Z"/><path d="m21 32 7 7 15-16"/></svg>
      <span>SME News<br>UK Enterprise Awards</span>
      <strong>Best Construction Training Company 2024</strong>
      <small>View the award <span aria-hidden="true">↗</span></small>
    </a>
  </div>
</section>"""

FOOTER = """<footer id="site-footer" class="dc-site-footer" data-dc-modern-footer>
  <div class="dc-footer-wrap dc-site-footer__top">
    <a class="dc-site-footer__brand" href="/" aria-label="Develop Coaching home">
      <img src="/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg" alt="Develop Coaching" loading="lazy">
    </a>
    <div class="dc-site-footer__links">
      <a href="mailto:hello@develop-coaching.com">hello@develop-coaching.com</a>
      <a href="https://www.facebook.com/developcoach/" target="_blank" rel="noopener">Facebook</a>
      <a href="https://www.linkedin.com/company/developcoaching/" target="_blank" rel="noopener">LinkedIn</a>
      <a href="https://www.instagram.com/greg.wilkes.coach" target="_blank" rel="noopener">Instagram</a>
      <a href="https://www.youtube.com/@DevelopCoaching" target="_blank" rel="noopener">YouTube</a>
    </div>
  </div>
  <div class="dc-footer-wrap dc-site-footer__bottom">
    <p>© Copyright 2026 by Develop Coaching Pty Ltd. All Rights Reserved.</p>
    <p><a href="/privacy/">Privacy Policy</a> · <a href="/corporate-structure-notice/">Corporate Structure Notice</a></p>
    <p class="dc-site-footer__disclaimer">This site is not part of or endorsed by Facebook Inc. FACEBOOK is a trademark of FACEBOOK, Inc.</p>
  </div>
</footer>"""


def should_include_book_award(relative_path: str, html: str) -> bool:
    """Use the richer CTA on editorial and Five Pillars resource pages."""
    route = "/" + relative_path.replace("index.html", "").removesuffix(".html")
    body_match = re.search(r'<body\b[^>]*class="([^"]*)"', html, re.I)
    body_classes = body_match.group(1).split() if body_match else []
    if "single-post" in body_classes or "single-podcast" in body_classes:
        return True
    return (
        route == "/"
        or route == "/about-greg-wilkes/"
        or route.startswith("/blog")
        or route.startswith("/category/")
        or route.startswith("/podcast/")
        or route.startswith("/podcast-transcript/")
        or route.startswith("/construction-podcast/")
        or route.startswith("/5-pillars-free-trainings/")
    )


def modernise_footer(html: str, relative_path: str) -> str:
    """Replace footer template 9008, preserving custom pages without it."""
    if 'class="fp-hub"' in html:
        html = MODERN_BOOK_RE.sub("", html)
        html = MODERN_FOOTER_RE.sub("", html)
        html = LEGACY_FOOTER_RE.sub("", html)
        html = STYLE_RE.sub("", html)
        return re.sub(r'\n(?:[ \t]*\n){2,}(?=[ \t]*<script)', "\n\n", html)
    if 'data-dc-modern-footer' in html:
        html = MODERN_FOOTER_RE.sub(lambda _match: FOOTER, html, count=1)
        include_book = should_include_book_award(relative_path, html)
        if include_book and MODERN_BOOK_RE.search(html):
            html = MODERN_BOOK_RE.sub(lambda _match: BOOK_AWARD, html, count=1)
        elif include_book:
            html = html.replace(FOOTER, BOOK_AWARD + "\n" + FOOTER, 1)
        else:
            html = MODERN_BOOK_RE.sub("", html)
        return STYLE_RE.sub(lambda _match: STYLE, html, count=1)
    if not LEGACY_FOOTER_RE.search(html):
        return html
    replacement = FOOTER
    if should_include_book_award(relative_path, html):
        replacement = BOOK_AWARD + "\n" + replacement
    html = LEGACY_FOOTER_RE.sub(lambda _match: replacement, html, count=1)
    if STYLE_RE.search(html):
        return STYLE_RE.sub(lambda _match: STYLE, html, count=1)
    return re.sub(
        r"</head>",
        lambda match: f"{STYLE}\n{match.group(0)}",
        html,
        count=1,
        flags=re.I,
    )


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "www")
    changed = 0
    for path in sorted(root.rglob("*.html")):
        original = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = path.relative_to(root).as_posix()
        updated = modernise_footer(original, relative_path)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Modernised footer in {changed} HTML files")


if __name__ == "__main__":
    main()
