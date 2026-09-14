#!/usr/bin/env python3
"""Install the booking success listener without rebuilding the exported site."""
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CALENDAR_PATH = '/widget/booking/zXUkPVoGKzRyirwYa0Ck'
TAG = '<script defer src="/booking-tracking.js" data-booking-tracking></script>'

class BookingFrames(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = False

    def handle_starttag(self, tag, attrs):
        if tag != 'iframe':
            return
        url = urlsplit(dict(attrs).get('src') or '')
        if url.scheme == 'https' and url.netloc == 'link.flow-build.com' and url.path.rstrip('/') == CALENDAR_PATH:
            self.found = True


def install(html):
    parser = BookingFrames()
    parser.feed(html)
    if not parser.found or 'data-booking-tracking' in html:
        return html
    return re.sub(r'<head\b[^>]*>', lambda m: m.group(0) + '\n' + TAG + '\n', html, count=1, flags=re.I)


def main():
    changed = []
    for folder in ('www', 'export/reference'):
        for path in (ROOT / folder).rglob('*.html'):
            old = path.read_bytes().decode("utf-8")
            new = install(old)
            if new != old:
                path.write_bytes(new.encode("utf-8"))
                changed.append(str(path.relative_to(ROOT)))
    print(f'Updated {len(changed)} booking pages and source copies.')

if __name__ == '__main__':
    main()
