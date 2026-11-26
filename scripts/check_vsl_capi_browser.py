"""Headless check of the /vsl Meta Conversions API (CAPI) browser side.

The page sends no event to any CAPI receiver itself. It adds four keys to the
FlowBuild webhook (event_id, fbp, fbc, client_user_agent) and FlowBuild passes
them on to Meta. Every external host is stubbed: the FlowBuild webhook is
intercepted and answered locally, the Meta and Google libraries load as empty
scripts, nothing real is contacted. Uses fictional people and Ofcom drama
numbers (07700 900xxx). Starts its own static server over www/.

Run from the repo root (CHROME = path to a Chromium/Chrome binary):
  CHROME=".../Google Chrome for Testing" uv run --with playwright python3 scripts/check_vsl_capi_browser.py

What it proves:
  1. Qualified submit: one browser Lead with eventID, one FlowBuild webhook
     whose event_id matches, and no request to any other endpoint (no
     receiver, no sendBeacon).
  2. Webhook fbp/fbc carry the _fbp/_fbc cookies only with advertising consent
     on the qualified route; '' with no choice, declined, analytics only,
     revoked, or no cookies.
  3. Not qualified: no Lead; webhook event_id, fbp, fbc, client_user_agent are ''.
  4. The webhook body is origin/main's byte for byte plus only the trailing
     keys fbp, fbc, client_user_agent, for every scenario.
  5. client_user_agent is navigator.userAgent, cut to 512 characters.
  6. Double submit sends once; event ids are vsl-<v4 uuid> even without
     randomUUID/getRandomValues; a failing webhook never blocks the redirect;
     no contact details in the URL, dataLayer, fbq queue or console.
  7. The privacy page and the form consent line show the approved wording.
"""
import functools, http.server, json, os, re, socketserver, subprocess, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, 'www')
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
BASE_REF = os.environ.get('BASE_REF', 'origin/main')
SHOTS = os.environ.get('SHOTS')  # optional folder for screenshots
PORT = 8766
ORIGIN = f'http://127.0.0.1:{PORT}'
WEBHOOK = 'services.leadconnectorhq.com/hooks/'
FBP, FBC = 'fb.1.1764200000000.1234567890', 'fb.1.1764200000000.TESTCLID123'
LONG_UA = ('Mozilla/5.0 (Linux; Android 14; Fictional Test Device) AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/140.0.0.0 Mobile Safari/537.36 ' + ' '.join(f'[FBAN/FB4A;FBAV/{i}.0.0.1;FBLC/en_GB]' for i in range(40)))[:700]
assert len(LONG_UA) == 700
NEW_KEYS = ('fbp', 'fbc', 'client_user_agent')

CURRENT = open(os.path.join(WWW, 'vsl/index.html'), encoding='utf-8').read()
BASELINE = subprocess.run(['git', 'show', f'{BASE_REF}:www/vsl/index.html'], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
assert 'CAPI_URL' not in CURRENT and 'sendBeacon' not in CURRENT, 'the page must not call a receiver'

QUALIFIED = {'work_source': 'Word of mouth and repeat clients',
             'business_type': 'Building company (residential or commercial)',
             'turnover': '£1.5m to £3m', 'approach': "I'm not sure yet"}
NOT_QUALIFIED = dict(QUALIFIED, turnover='Under £750k')
PERSON = {'first_name': 'Testy', 'last_name': "O'Builder", 'business_name': 'Fictional Builds Ltd',
          'email': 'testy.capi@example.com', 'phone': '07700 900123'}
QUERY = '?utm_source=facebook&utm_medium=paid&fbclid=TESTCLID123'
# Contact details must never reach the URL, dataLayer, fbq or the console.
PII = [PERSON['first_name'], PERSON['last_name'], PERSON['business_name'], PERSON['email'],
       PERSON['phone'], '7700900123', 'testy.capi%40example.com', 'O%27Builder']
PII_RUNS = []  # (label, leaks) for every run()
UUID_ID = re.compile(r'vsl-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')
CONSENT = {  # each step: (accepted, rejected) as CookieYes sends them
    'decline': [([], ['analytics', 'advertisement'])],
    'accept': [(['analytics', 'advertisement'], [])],
    'analytics': [(['analytics'], ['advertisement'])],
    'revoke': [(['analytics', 'advertisement'], []), (['analytics'], ['advertisement'])],
}
# Records any sendBeacon call (the page must make none).
SPY = """(() => { window.__beacons = []; const b = navigator.sendBeacon;
  if (b) navigator.sendBeacon = function(url){ window.__beacons.push(String(url)); return b.apply(this, arguments); };
})();"""

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = S(('127.0.0.1', PORT), functools.partial(Q, directory=WWW))
threading.Thread(target=srv.serve_forever, daemon=True).start()

failures = []
def check(cond, label):
    print(('PASS ' if cond else 'FAIL ') + label)
    if not cond: failures.append(label)


def run(browser, html, answers, consent=None, cookies=False, no_uuid=False, no_rng=False,
        hook='ok', submits=1, ua=None, shot=None):
    """Fill and submit the form. consent: None (no choice) or a CONSENT key.
    hook: 'ok', '500' or 'abort' (network error) for the stubbed FlowBuild webhook."""
    ctx = browser.new_context(user_agent=ua) if ua else browser.new_context()
    if cookies:
        ctx.add_cookies([{'name': '_fbp', 'value': FBP, 'url': ORIGIN},
                         {'name': '_fbc', 'value': FBC, 'url': ORIGIN}])
    if no_uuid or no_rng:
        ctx.add_init_script('try{Object.defineProperty(Crypto.prototype,"randomUUID",{value:undefined})}catch(e){}')
    if no_rng:
        ctx.add_init_script('try{Object.defineProperty(Crypto.prototype,"getRandomValues",{value:function(){throw new Error("no rng")}})}catch(e){}')
    ctx.add_init_script(SPY)
    page = ctx.new_page()
    hooks, other, errors, console = [], [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: console.append(m.text))
    def handle(route):
        req = route.request; url = req.url
        if url.startswith(ORIGIN + '/vsl/') and req.resource_type == 'document' and '/vsl/book' not in url and '/vsl/free-training' not in url:
            return route.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)
        if url.startswith(ORIGIN):
            return route.continue_()
        if WEBHOOK in url:
            hooks.append(req.post_data)
            if hook == 'abort': return route.abort('failed')
            return route.fulfill(status=500 if hook == '500' else 200, content_type='application/json', body='{}')
        # Anything else that sends data (fetch, XHR, beacon, POST) is a call the page must not make.
        if req.method != 'GET' or req.resource_type in ('fetch', 'xhr', 'ping', 'eventsource', 'websocket'):
            other.append((req.method, req.resource_type, url))
        if req.resource_type == 'script':
            return route.fulfill(status=200, content_type='application/javascript', body='')
        return route.fulfill(status=204, body='')
    ctx.route('**/*', handle)
    page.goto(ORIGIN + '/vsl/' + QUERY, wait_until='load')
    for acc, rej in CONSENT.get(consent, []):
        page.evaluate("""([a,r])=>document.dispatchEvent(new CustomEvent('cookieyes_consent_update',
                         {detail:{accepted:a,rejected:r}}))""", [acc, rej])
    for name in ('work_source', 'business_type', 'turnover', 'approach'):
        page.locator(f'input[name="{name}"][value="{answers[name]}"]').check(force=True)
        page.click('#nextBtn')
    for k, v in PERSON.items():
        page.fill(f'#applyForm [name="{k}"]', v)
    consent_line = page.inner_text('#consentLine') if page.is_visible('#consentLine') else None
    consent_html = page.eval_on_selector('#consentLine', 'e=>e.innerHTML')
    link_color = page.evaluate("()=>{const a=document.querySelector('#consentLine a'); return a ? getComputedStyle(a).color : null}")
    if shot:
        page.locator('#apply').screenshot(path=shot)
    # requestSubmit runs the handler synchronously, so fbq's queue is complete
    # on return, before the page navigates away.
    meta, beacons, layer, page_ua = page.evaluate("""(n)=>{ const f = document.getElementById('applyForm');
        for (let i = 0; i < n; i++) f.requestSubmit();
        const str = x => { try { return JSON.stringify(x && x.length !== undefined && typeof x !== 'string' ? Array.from(x) : x); }
                           catch (e) { return String(x); } };
        return [(window.fbq && fbq.queue || []).map(a => JSON.parse(JSON.stringify(Array.from(a)))),
                window.__beacons || [], (window.dataLayer || []).map(str), navigator.userAgent]; }""", submits)
    page.wait_for_timeout(900)
    final_url = page.url
    ctx.close()
    seen = {'url': final_url, 'dataLayer': ' '.join(layer), 'fbq': json.dumps(meta, ensure_ascii=False),
            'console': ' '.join(console)}
    leaks = [(where, v) for where, text in seen.items() for v in PII if v.lower() in text.lower()]
    PII_RUNS.append((f'{"qualified" if answers is QUALIFIED else "not qualified"}, consent={consent}', leaks))
    return {'hooks': hooks, 'other': other, 'beacons': beacons, 'meta': meta, 'errors': errors,
            'url': final_url, 'ua': page_ua, 'consent_line': consent_line, 'consent_html': consent_html,
            'link_color': link_color}


def leads(meta): return [m for m in meta if m[:2] == ['track', 'Lead']]
def lead_id(r): return [(m[3] if len(m) > 3 else {}).get('eventID') for m in leads(r['meta'])]
def hook(r): return json.loads(r['hooks'][0]) if r['hooks'] else {}


def scenario(b, label, answers, want_fb, **kw):
    """Run main and this branch with the same inputs; check the webhook keys."""
    old = run(b, BASELINE, answers, **kw)
    new = run(b, CURRENT, answers, **kw)
    q = answers is QUALIFIED
    want = {'fbp': want_fb[0], 'fbc': want_fb[1], 'client_user_agent': new['ua'][:512] if q else ''}
    h = hook(new)
    check(len(old['hooks']) == len(new['hooks']) == 1, f'{label}: one webhook each')
    if old['hooks'] and new['hooks']:
        tail = ''.join(f',"{k}":' + json.dumps(want[k], ensure_ascii=False) for k in NEW_KEYS)
        # main's event_id is a fresh random id, so compare with ours swapped in.
        base = old['hooks'][0].replace(json.dumps(hook(old).get('event_id')), json.dumps(h.get('event_id')), 1)
        check(new['hooks'][0] == base[:-1] + tail + '}',
              f'{label}: webhook = {BASE_REF} + only {", ".join(NEW_KEYS)} '
              f'(fbp={h.get("fbp")!r}, fbc={h.get("fbc")!r}, ua={len(h.get("client_user_agent", ""))} chars)')
        check(set(h) - set(hook(old)) == set(NEW_KEYS), f'{label}: exactly three new keys')
    eid = h.get('event_id')
    if q:
        check(bool(eid) and UUID_ID.fullmatch(eid or '') is not None and lead_id(new) == [eid],
              f'{label}: webhook event_id == Lead eventID ({eid})')
    else:
        check(eid == '' and lead_id(new) == [], f'{label}: no Lead, event_id empty')
    check(not new['other'] and not new['beacons'] and not new['errors'],
          f'{label}: no request to any receiver, no beacon, no page errors {new["other"][:2]} {new["errors"][:2]}')
    dest = '/vsl/book/' if q else '/vsl/free-training/'
    check(new['url'].startswith(ORIGIN + dest), f'{label}: redirects to {dest}')
    return new


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])

    # 1-5: every consent state on both routes, each compared with main.
    r = scenario(b, 'qualified, no consent choice, cookies', QUALIFIED, ('', ''), cookies=True)
    check(r['meta'] and leads(r['meta'])[0][2] == {'content_name': 'VSL Application (vsl)'}, 'Lead params unchanged')
    check(hook(r).get('phone') == '+447700900123' and hook(r).get('source') == 'vsl-application',
          'webhook phone (+44) and source unchanged')
    scenario(b, 'qualified, declined, cookies', QUALIFIED, ('', ''), consent='decline', cookies=True)
    scenario(b, 'qualified, analytics only, cookies', QUALIFIED, ('', ''), consent='analytics', cookies=True)
    scenario(b, 'qualified, accepted then revoked, cookies', QUALIFIED, ('', ''), consent='revoke', cookies=True)
    scenario(b, 'qualified, accepted, no cookies', QUALIFIED, ('', ''), consent='accept')
    scenario(b, 'qualified, accepted, cookies', QUALIFIED, (FBP, FBC), consent='accept', cookies=True)
    scenario(b, 'not qualified, accepted, cookies', NOT_QUALIFIED, ('', ''), consent='accept', cookies=True)
    scenario(b, 'not qualified, no consent choice', NOT_QUALIFIED, ('', ''))
    r = scenario(b, 'qualified, 700-char user agent', QUALIFIED, (FBP, FBC), consent='accept', cookies=True, ua=LONG_UA)
    check(r['ua'] == LONG_UA and hook(r).get('client_user_agent') == LONG_UA[:512],
          f'700-char user agent cut to 512 ({len(hook(r).get("client_user_agent", ""))})')
    r = scenario(b, 'not qualified, 700-char user agent', NOT_QUALIFIED, ('', ''), consent='accept', cookies=True, ua=LONG_UA)

    # 6: event id fallbacks.
    for label, kw in (('no randomUUID', {'no_uuid': True}), ('no crypto RNG', {'no_rng': True})):
        r = run(b, CURRENT, QUALIFIED, **kw)
        eid = hook(r).get('event_id')
        check(bool(eid) and UUID_ID.fullmatch(eid) is not None and lead_id(r) == [eid] and not r['errors'],
              f'fallback ({label}): vsl-<v4 uuid>, webhook and Lead match ({eid})')

    # 6: double submit sends once.
    r = run(b, CURRENT, QUALIFIED, consent='accept', submits=2)
    check(len(r['hooks']) == 1 and len(leads(r['meta'])) == 1,
          f'double submit: 1 webhook, 1 Lead (got {len(r["hooks"])}, {len(leads(r["meta"]))})')
    r = run(b, CURRENT, NOT_QUALIFIED, submits=2)
    check(len(r['hooks']) == 1 and r['meta'].count(['trackCustom', 'ApplicationNotQualified']) == 1,
          'double submit (not qualified): 1 webhook, 1 ApplicationNotQualified')

    # 6: webhook down never blocks the redirect.
    for mode in ('500', 'abort'):
        for label, answers, dest in (('qualified', QUALIFIED, '/vsl/book/'), ('not qualified', NOT_QUALIFIED, '/vsl/free-training/')):
            r = run(b, CURRENT, answers, hook=mode)
            check(len(r['hooks']) == 1 and not r['errors'] and r['url'].startswith(ORIGIN + dest),
                  f'webhook {mode} ({label}): still redirects to {dest} (url={r["url"]}, errors={r["errors"]})')

    # 7: consent line.
    r = run(b, CURRENT, QUALIFIED, shot=os.path.join(SHOTS, 'vsl-consent-line.png') if SHOTS else None)
    want = ('By applying you agree we can call, text or email you about your application. '
            'Some of your details are shared with Meta (see our Privacy Policy).')
    check(r['consent_line'] == want, f'7: consent line text: {r["consent_line"]!r}')
    check('<a href="/privacy/">Privacy Policy</a>' in r['consent_html'], '7: consent line links to /privacy/')
    check(r['link_color'] == 'rgb(138, 104, 0)', f'7: consent link colour #8a6800 ({r["link_color"]})')

    # 6: PII, across every run above (main's runs included).
    leaky = [(label, leaks) for label, leaks in PII_RUNS if leaks]
    check(len(PII_RUNS) >= 25 and not leaky,
          f'PII: none in URL, dataLayer, fbq or console across {len(PII_RUNS)} runs {leaky[:3]}')

    # 7: privacy page.
    ctx = b.new_context(); page = ctx.new_page()
    ctx.route('**/*', lambda rt: rt.continue_() if rt.request.url.startswith(ORIGIN)
              else rt.fulfill(status=200, body='', content_type='application/javascript'
                              if rt.request.resource_type == 'script' else 'text/plain'))
    page.goto(ORIGIN + '/privacy/', wait_until='load')
    text = page.inner_text('body')
    for needle in ('Last updated: 27 November 2026',
                   'Meta Conversions API. When you submit a qualifying application on develop-coaching.com/vsl',
                   'Send qualifying applications and Scale Session bookings from our servers to Meta',
                   'Meta (Facebook and Instagram)\tWebsite advertising cookies if you accept them',
                   'Google, Microsoft, Cabin\tWebsite analytics and advertising',
                   'and sending Scale Session booking events to Meta',
                   'It does not stop the server-side data we send to Meta',
                   'browser cookie only; see section 6 for server-side sharing'):
        check(needle in text, f'7: privacy shows "{needle[:60]}"')
    check('Google, Meta, Microsoft, Cabin' not in text, '7: old combined Meta row gone')
    para = page.locator('p:has-text("Meta Conversions API.")')
    check(para.count() == 1 and para.is_visible(), '7: Meta paragraph visible once')
    for w, h, name in ((390, 844, 'mobile'), (1280, 900, 'desktop')):
        page.set_viewport_size({'width': w, 'height': h})
        page.wait_for_timeout(200)
        check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'7: privacy, no sideways scroll at {w}px')
        if SHOTS:
            para.scroll_into_view_if_needed(); page.screenshot(path=os.path.join(SHOTS, f'privacy-meta-{name}.png'))
    page.goto(ORIGIN + '/vsl/', wait_until='load')
    page.set_viewport_size({'width': 390, 'height': 844}); page.wait_for_timeout(200)
    check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), '7: vsl, no sideways scroll at 390px')
    ctx.close()
    b.close()

srv.shutdown()
print('\n%d failure(s)' % len(failures) if failures else '\nALL PASS')
sys.exit(1 if failures else 0)
