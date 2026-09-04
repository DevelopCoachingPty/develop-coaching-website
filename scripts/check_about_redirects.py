"""Read-only HTTP regression for the two legacy About redirects."""
import argparse
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(base):
    opener = build_opener(NoRedirect)
    failures = []
    for slug in ('my-story', 'case-study'):
        for suffix in ('', '/', '?utm_source=redirect-check', '/?utm_source=redirect-check'):
            path = '/' + slug + suffix
            expected = '/about-greg-wilkes/'
            if '?' in suffix:
                expected += '?utm_source=redirect-check'
            try:
                response = opener.open(Request(base + path), timeout=20)
            except HTTPError as response_error:
                response = response_error
            with response:
                location = response.headers.get('Location', '')
                target = urljoin(base + path, location)
                passed = response.code == 308 and target == base + expected
                print(path, response.code, location, 'PASS' if passed else 'FAIL')
                if not passed:
                    failures.append(path)
    with opener.open(base + '/about-greg-wilkes/', timeout=20) as response:
        assert response.code == 200, 'Destination must return 200 without another redirect'
    return failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://develop-coaching.com')
    args = parser.parse_args()
    base = args.base.rstrip('/')
    assert urlsplit(base).scheme in ('http', 'https')
    raise SystemExit(bool(check(base)))
