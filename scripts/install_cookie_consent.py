#!/usr/bin/env python3
"""Install the cookie consent gate across the exported site, in place.

Idempotent. Never rebuilds the site (do not run build_site.py). For every page
under www/ that carries a tracker it:

  1. puts <script src="/dc-consent.js" data-dc-consent> first in <head>, so the
     Consent Mode v2 "denied" default and the script gate exist before any tag
  2. switches static tracker script tags (Cabin, gtag.js) to type="text/plain",
     which dc-consent.js turns back on after consent. Tags added from JavaScript
     (GTM, Meta Pixel, Clarity, ActiveCampaign) are held at run time instead
  3. removes the <noscript> tracking pixels (GTM iframe, Meta image), which load
     with no consent step and cannot be gated
  4. adds a "Cookie settings" link that reopens the consent banner

Usage: python3 scripts/install_cookie_consent.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEAD_TAG = '<script src="/dc-consent.js" data-dc-consent></script>'
COOKIE_LINK = '<a href="#" class="cky-banner-element dc-cookie-settings">Cookie settings</a>'

# Anything that loads, or queues a call to, one of the gated trackers.
TRACKER_RE = re.compile(
    r"googletagmanager\.com|connect\.facebook\.net|clarity\.ms|withcabin\.com|app-us1\.com|\bfbq\(",
    re.I,
)

HEAD_OPEN_RE = re.compile(r"<head\b[^>]*>", re.I)
HEAD_TAG_RE = re.compile(r"\n[ \t]*<script\b[^>]*\bdata-dc-consent\b[^>]*></script>[ \t]*\n")

NOSCRIPT_GTM_RE = re.compile(
    r"[ \t]*<!-- Google Tag Manager \(noscript\) -->\s*"
    r"<noscript><iframe src=\"https://www\.googletagmanager\.com/ns\.html\?id=GTM-[A-Z0-9]+\".*?</iframe></noscript>\s*"
    r"<!-- End Google Tag Manager \(noscript\) -->[ \t]*\n?",
    re.S,
)
NOSCRIPT_META_RE = re.compile(
    r"[ \t]*<noscript>\s*<img[^>]*facebook\.com/tr\?[^>]*>\s*</noscript>[ \t]*\n?",
    re.S,
)

STATIC_TRACKER_RE = re.compile(
    r"<script\b([^>]*?)\bsrc=([\"'])"
    r"(https://(?:scripts\.withcabin\.com/[^\"']*|www\.googletagmanager\.com/gtag/js\?[^\"']*))"
    r"\2([^>]*)>"
)

MODERN_FOOTER_RE = re.compile(r"(Corporate Structure Notice</a>)(</p>)")
ELEMENTOR_FOOTER_RE = re.compile(r"(All Rights Reserved\. <a href=\"/privacy/\">Privacy Policy\s*</a>)(</p>)")
SOFTWARE_FOOTER_RE = re.compile(
    r"(<footer class=\"footer\">.*?<a href=\"https://develop-coaching\.com\">develop-coaching\.com</a>)(</div>)",
    re.S,
)
FALLBACK_LINE = (
    '<p class="dc-cookie-fallback" style="text-align:center;font-size:12px;margin:0;padding:12px 16px">'
    '<a href="/privacy/">Privacy Policy</a> · ' + COOKIE_LINK + "</p>\n"
)


def has_tracker(html: str) -> bool:
    return bool(TRACKER_RE.search(html))


def _gate_static(match: "re.Match") -> str:
    before, quote, src, after = match.group(1), match.group(2), match.group(3), match.group(4)
    attrs = f"{before} {after}"
    if re.search(r"""\btype=["']text/plain["']""", attrs):
        return match.group(0)
    attrs = re.sub(r"""\btype=(["'])[^"']*\1""", "", attrs)
    attrs = re.sub(r"\s+", " ", attrs).strip()
    category = "advertising" if re.search(r"[?&]id=AW-", src) else "analytics"
    extra = f" {attrs}" if attrs else ""
    return f'<script type="text/plain" data-dc-category="{category}"{extra} src={quote}{src}{quote}>'


def install(html: str) -> str:
    """Return html with the consent gate installed. Pages with no tracker are left alone."""
    if not has_tracker(html) and "data-dc-consent" not in html:
        return html

    # 1. first script in <head>, whatever else was installed there before
    html = HEAD_TAG_RE.sub("", html, count=1)
    html = HEAD_OPEN_RE.sub(lambda m: m.group(0) + "\n" + HEAD_TAG + "\n", html, count=1)

    # 2. static tracker tags wait for consent
    html = STATIC_TRACKER_RE.sub(_gate_static, html)

    # 3. no-JavaScript tracking pixels cannot ask for consent
    html = NOSCRIPT_GTM_RE.sub("", html)
    html = NOSCRIPT_META_RE.sub("", html)

    # 4. a way back to the banner
    if COOKIE_LINK not in html:
        html, n = MODERN_FOOTER_RE.subn(lambda m: f"{m.group(1)} · {COOKIE_LINK}{m.group(2)}", html, count=1)
        if not n:
            html, n = ELEMENTOR_FOOTER_RE.subn(lambda m: f"{m.group(1)} · {COOKIE_LINK}{m.group(2)}", html, count=1)
        if not n:
            html, n = SOFTWARE_FOOTER_RE.subn(
                lambda m: f'{m.group(1)} · <a href="/privacy/">Privacy Policy</a> · {COOKIE_LINK}{m.group(2)}',
                html,
                count=1,
            )
        if not n:
            idx = html.lower().rfind("</body>")
            if idx != -1:
                html = html[:idx] + FALLBACK_LINE + html[idx:]
    return html


def main() -> None:
    changed = 0
    for path in sorted((ROOT / "www").rglob("*.html")):
        old = path.read_bytes().decode("utf-8")
        new = install(old)
        if new != old:
            path.write_bytes(new.encode("utf-8"))
            changed += 1
    print(f"Cookie consent gate installed on {changed} pages.")


if __name__ == "__main__":
    main()
