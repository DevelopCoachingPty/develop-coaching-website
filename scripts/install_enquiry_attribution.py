#!/usr/bin/env python3
"""Install the enquiry attribution script on every page with an enquiry form.

A page qualifies when it embeds a FlowBuild (GoHighLevel) form, survey, quiz or
booking iframe, or carries the /busy-trap/ application form (#applyForm).
The tag goes straight after the cookie consent gate, which must stay the first
script in <head>. It is a plain (not deferred) script on purpose: it has to see
each FlowBuild iframe as the parser inserts it, so the form loads once with the
attribution parameters.

Idempotent. Touches only www/. export/reference/ is the frozen input to
build_site.py, which must not be run, so it is left alone.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TAG = '<script src="/enquiry-attribution.js" data-enquiry-attribution></script>'
WIDGET = re.compile(r'^/widget/(form|survey|quiz|booking)/[A-Za-z0-9]+/?$')


class EnquiryForms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form' and a.get('id') == 'applyForm':
            self.found = True
        if tag != 'iframe':
            return
        url = urlsplit(a.get('src') or '')
        if url.scheme == 'https' and url.netloc == 'link.flow-build.com' and WIDGET.match(url.path):
            self.found = True


def install(html):
    if 'data-enquiry-attribution' in html:
        return html
    parser = EnquiryForms()
    parser.feed(html)
    if not parser.found:
        return html
    consent = re.search(r'<script\b[^>]*\bdata-dc-consent\b[^>]*></script>[ \t]*\n?', html)
    if consent:
        end = consent.end()
        sep = '' if html[end - 1:end] == '\n' else '\n'
        return html[:end] + sep + TAG + '\n' + html[end:]
    return re.sub(r'<head\b[^>]*>', lambda m: m.group(0) + '\n' + TAG + '\n', html, count=1, flags=re.I)


def main(argv):
    root = ROOT / 'www'
    changed = []
    for path in sorted(root.rglob('*.html')):
        old = path.read_bytes().decode('utf-8')
        new = install(old)
        if new != old:
            if '--check' not in argv:
                path.write_bytes(new.encode('utf-8'))
            changed.append(str(path.relative_to(ROOT)))
    verb = 'Would update' if '--check' in argv else 'Updated'
    print(f'{verb} {len(changed)} enquiry pages.')
    return 1 if ('--check' in argv and changed) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
