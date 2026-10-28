"""Headless check of the cookie consent gate against the pages in www/.

Needs Playwright for Python and Google Chrome (set CHROME to its path).
External hosts are stubbed, nothing real is contacted. Starts its own static server.
Run from the repo root: python3 scripts/check_consent_gate_browser.py
"""
import functools, http.server, os, re, socketserver, threading
from playwright.sync_api import sync_playwright

WWW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'www')
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
PORT = 8765
FAKE = 'abcdef0123456789abcdef01'
PAGES = ['/', '/software/muster/', '/5-pillars-free-trainings/attract/', '/schedule-a-call/',
         '/fill-the-order-book/', '/win-big-clients/']
TRACK = re.compile(r'googletagmanager\.com|facebook\.(com|net)|clarity\.ms|app-us1\.com|withcabin\.com|trackcmp|doubleclick|google-analytics|googleadservices')

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = S(('127.0.0.1', PORT), functools.partial(Q, directory=WWW))
threading.Thread(target=srv.serve_forever, daemon=True).start()

def run(p, path, scenario):
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    ctx = b.new_context(); page = ctx.new_page()
    reqs = []; errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    def handle(route):
        url = route.request.url
        if url.startswith(f'http://127.0.0.1:{PORT}'):
            if url.endswith('/dc-consent.js'):
                # Swap the shipped key: a fake key for the normal scenarios, the
                # not-a-key placeholder for the fail-closed scenario.
                key = 'CONSENT_TOOL_ID' if scenario == 'placeholder' else FAKE
                body = re.sub(r"var CONSENT_TOOL_ID = '[^']*';", f"var CONSENT_TOOL_ID = '{key}';", open(WWW + '/dc-consent.js').read())
                return route.fulfill(status=200, content_type='application/javascript', body=body)
            return route.continue_()
        reqs.append(url)
        rt = route.request.resource_type
        if rt == 'script': return route.fulfill(status=200, content_type='application/javascript', body='')
        if rt == 'image': return route.fulfill(status=200, content_type='image/gif', body=b'GIF89a')
        return route.fulfill(status=200, body='')
    ctx.route('**/*', handle)
    page.goto(f'http://127.0.0.1:{PORT}{path}', wait_until='load')
    page.wait_for_timeout(1500)
    pre = [u for u in reqs if TRACK.search(u)]
    out = {'path': path, 'scenario': scenario, 'pre': pre, 'errors': errs[:3]}
    if scenario != 'placeholder':
        out['cmp_requested'] = any(FAKE in u for u in reqs)
        def choose(an, ad):
            page.evaluate("""([an,ad])=>{ const g=v=>v?'granted':'denied';
              function gtag(){dataLayer.push(arguments)}
              gtag('consent','update',{analytics_storage:g(an),ad_storage:g(ad),ad_user_data:g(ad),ad_personalization:g(ad)}); }""", [an, ad])
            page.wait_for_timeout(1200)
        if scenario == 'reject':
            choose(False, False)
        elif scenario == 'analytics':
            choose(True, False)
        elif scenario == 'all':
            choose(True, True)
        out['post'] = [u for u in reqs if TRACK.search(u)][len(pre):]
        out['static_plain_left'] = page.evaluate("document.querySelectorAll('script[type=\"text/plain\"][data-dc-category]').length")
        out['state'] = page.evaluate("dcConsent.state()")
        out['dl_first'] = page.evaluate("JSON.stringify(Array.from(dataLayer[0]||[]))")
    b.close()
    return out

FAILED = []
with sync_playwright() as p:
    for scenario in ['placeholder', 'reject', 'analytics', 'all']:
        for path in PAGES:
            r = run(p, path, scenario)
            short = lambda L: sorted({re.sub(r'https?://([^/]+)(/[^?]{0,40}).*', r'\1\2', u) for u in L})
            print(scenario.ljust(11), path.ljust(36), 'PRE:', short(r['pre']), 'POST:', short(r.get('post', [])), 'plainLeft', r.get('static_plain_left'), 'err', r['errors'], r.get('state',''))
            expect = {'placeholder': 0, 'reject': 0}
            if scenario in expect and (r['pre'] or r.get('post')):
                FAILED.append((scenario, path))
            if scenario == 'analytics' and any(re.search(r'facebook|app-us1', u) for u in r.get('post', [])):
                FAILED.append((scenario, path))
            if scenario == 'all' and not r.get('post'):
                FAILED.append((scenario, path))
            if r['errors']:
                FAILED.append(('page error', path))
srv.shutdown()
if FAILED:
    print('FAILED:', FAILED)
    raise SystemExit(1)
print('consent gate browser check: ok')
