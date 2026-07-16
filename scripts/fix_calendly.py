#!/usr/bin/env python3
"""Swap the dead Calendly widget for the working GoHighLevel booking widget.

The Calendly event calendly.com/develop-coaching/15-minute-call was deleted
upstream (confirmed 404 directly from Calendly, broken on live WordPress too).
5 pages embed it. The GHL booking widget (link.flow-build.com) is already used
successfully elsewhere on the site (e.g. /contact/), so this swaps in that
same working embed.
"""
import re

PAGES = [
    "event-booking",
    "stephen-and-salina-testimonial",
    "the-schedule-page-subscribers",
    "the-schedule-page",
    "valy-testimonial",
]

CALENDLY_RE = re.compile(
    r'(<!--\s*Calendly inline widget begin\s*-->\s*)?'
    r'<div class="calendly-inline-widget" data-url="https://calendly\.com/develop-coaching/15-minute-call[^"]*"[^>]*></div>\s*'
    r'<script[^>]*calendly[^>]*></script>\s*'
    r'(<!--\s*Calendly inline widget end\s*-->)?',
    re.S,
)

GHL_REPLACEMENT = (
    '<iframe src="https://link.flow-build.com/widget/booking/zXUkPVoGKzRyirwYa0Ck" '
    'style="width: 100%;border:none;overflow: hidden;height:730px;" scrolling="no" '
    'id="ghl-booking-widget-fix"></iframe>'
    '<script src="https://link.flow-build.com/js/form_embed.js" type="text/javascript" async></script>'
)


def main():
    for name in PAGES:
        path = f"export/reference/{name}.html"
        html = open(path, encoding="utf-8", errors="ignore").read()
        new_html, count = CALENDLY_RE.subn(GHL_REPLACEMENT, html)
        if count == 0:
            print(f"WARNING: no Calendly widget matched in {name}")
            continue
        open(path, "w", encoding="utf-8").write(new_html)
        print(f"{name}: replaced {count} widget(s)")


if __name__ == "__main__":
    main()
