"""Headless check of the /vsl Meta Conversions API (CAPI) browser side.

Every external host is stubbed: the FlowBuild webhook and a fake CAPI receiver
are intercepted and answered locally, the Meta and Google libraries load as
empty scripts, nothing real is contacted. Uses fictional people and Ofcom drama
numbers (07700 900xxx). Starts its own static server over www/.

Run from the repo root (CHROME = path to a Chromium/Chrome binary):
  CHROME=".../Google Chrome for Testing" uv run --with playwright python3 scripts/check_vsl_capi_browser.py

What it proves:
  1. Qualified submit: browser Lead carries an eventID, and exactly one
     receiver POST is sent by fetch (keepalive, credentials omit, text/plain,
     never sendBeacon) with the same event_id and all fields, including
     consent_ads.
  2. fbp/fbc are '' and consent_ads is false without advertising consent (no
     choice, declined, analytics only, revoked); with it, consent_ads is true
     and fbp/fbc come from the _fbp/_fbc cookies.
  3. Not-qualified submit: no receiver POST and no Lead.
  4. The FlowBuild webhook body is byte-identical to origin/main for the same inputs.
  5. CAPI_URL empty (as shipped): no receiver POST at all. No phone: no
     receiver POST.
  Also: a double submit sends everything once; event ids are always
  vsl-<uuid>, even without randomUUID/getRandomValues; a failing receiver
  (500 or network error) still redirects; analytics-only or revoked ad
  consent keeps fbp/fbc empty.
  6. The privacy page shows the new Meta paragraph and rows; the form shows
     the new consent line.
"""
import functools, http.server, json, os, re, socketserver, subprocess, sys, threading, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, 'www')
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
BASE_REF = os.environ.get('BASE_REF', 'origin/main')
SHOTS = os.environ.get('SHOTS')  # optional folder for screenshots
PORT = 8766
ORIGIN = f'http://127.0.0.1:{PORT}'
WEBHOOK = 'services.leadconnectorhq.com/hooks/'
FAKE_CAPI = 'https://capi-receiver.test.invalid/meta-event'
FBP, FBC = 'fb.1.1764200000000.1234567890', 'fb.1.1764200000000.TESTCLID123'

CURRENT = open(os.path.join(WWW, 'vsl/index.html'), encoding='utf-8').read()
BASELINE = subprocess.run(['git', 'show', f'{BASE_REF}:www/vsl/index.html'], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
assert "CAPI_URL: ''," in CURRENT, 'CAPI_URL must ship empty'
WITH_CAPI = CURRENT.replace("CAPI_URL: '',", f"CAPI_URL: '{FAKE_CAPI}',", 1)
# Test-only variant: ukPhone() yields '' (the form's own validation never lets
# that happen, so the guard can only be reached this way).
assert WITH_CAPI.count('function ukPhone(raw){') == 1
NO_PHONE = WITH_CAPI.replace('function ukPhone(raw){', "function ukPhone(raw){ return '';", 1)
FIELDS = {'event_id', 'event_time', 'event_source_url', 'email', 'phone', 'first_name',
          'last_name', 'fbp', 'fbc', 'fbclid', 'consent_ads'}
# Records how the page calls fetch / sendBeacon for the receiver.
SPY = """(() => { window.__capi = []; const f = window.fetch, b = navigator.sendBeacon;
  window.fetch = function(url, init){ if (String(url).indexOf(%r) === 0) window.__capi.push({via: 'fetch',
    method: init && init.method, keepalive: init && init.keepalive, credentials: init && init.credentials,
    headers: init && init.headers}); return f.apply(this, arguments); };
  if (b) navigator.sendBeacon = function(url){ if (String(url).indexOf(%r) === 0) window.__capi.push({via: 'beacon'});
    return b.apply(this, arguments); };
})();""" % (FAKE_CAPI, FAKE_CAPI)

QUALIFIED = {'work_source': 'Word of mouth and repeat clients',
             'business_type': 'Building company (residential or commercial)',
             'turnover': '£1.5m to £3m', 'approach': "I'm not sure yet"}
NOT_QUALIFIED = dict(QUALIFIED, turnover='Under £750k')
PERSON = {'first_name': 'Testy', 'last_name': "O'Builder", 'business_name': 'Fictional Builds Ltd',
          'email': 'testy.capi@example.com', 'phone': '07700 900123'}
QUERY = '?utm_source=facebook&utm_medium=paid&fbclid=TESTCLID123'

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True
srv = S(('127.0.0.1', PORT), functools.partial(Q, directory=WWW))
threading.Thread(target=srv.serve_forever, daemon=True).start()

failures = []
def check(cond, label):
    print(('PASS ' if cond else 'FAIL ') + label)
    if not cond: failures.append(label)


UUID_ID = re.compile(r'vsl-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')
CONSENT = {  # each step: (accepted, rejected) as CookieYes sends them
    'decline': [([], ['analytics', 'advertisement'])],
    'accept': [(['analytics', 'advertisement'], [])],
    'analytics': [(['analytics'], ['advertisement'])],
    'revoke': [(['analytics', 'advertisement'], []), (['analytics'], ['advertisement'])],
}


def run(browser, html, answers, consent=None, cookies=False, no_uuid=False, no_rng=False,
        capi='ok', submits=1, shot=None):
    """Fill and submit the form. consent: None (no choice) or a CONSENT key.
    capi: 'ok', '500' or 'abort' (network error) for the stubbed receiver."""
    ctx = browser.new_context()
    if cookies:
        ctx.add_cookies([{'name': '_fbp', 'value': FBP, 'url': ORIGIN},
                         {'name': '_fbc', 'value': FBC, 'url': ORIGIN}])
    if no_uuid or no_rng:
        ctx.add_init_script('try{Object.defineProperty(Crypto.prototype,"randomUUID",{value:undefined})}catch(e){}')
    if no_rng:
        ctx.add_init_script('try{Object.defineProperty(Crypto.prototype,"getRandomValues",{value:function(){throw new Error("no rng")}})}catch(e){}')
    ctx.add_init_script(SPY)
    page = ctx.new_page()
    capi_mode = capi
    hooks, capi, errors = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def handle(route):
        req = route.request; url = req.url
        if url.startswith(ORIGIN + '/vsl/') and req.resource_type == 'document' and '/vsl/book' not in url and '/vsl/free-training' not in url:
            return route.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)
        if url.startswith(ORIGIN):
            return route.continue_()
        if WEBHOOK in url:
            hooks.append(req.post_data)
            return route.fulfill(status=200, content_type='application/json', body='{}')
        if url.startswith(FAKE_CAPI):
            capi.append({'method': req.method, 'body': req.post_data, 'ctype': req.headers.get('content-type'),
                         'type': req.resource_type, 'cookie': req.headers.get('cookie')})
            if capi_mode == 'abort': return route.abort('failed')
            return route.fulfill(status=500 if capi_mode == '500' else 200, content_type='application/json', body='{}')
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
    t0 = int(time.time())
    # requestSubmit runs the handler synchronously, so fbq's queue is complete
    # on return, before the page navigates away.
    meta, calls = page.evaluate("""(n)=>{ const f = document.getElementById('applyForm');
        for (let i = 0; i < n; i++) f.requestSubmit();
        return [(window.fbq && fbq.queue || []).map(a => JSON.parse(JSON.stringify(Array.from(a)))),
                window.__capi || []]; }""", submits)
    page.wait_for_timeout(900)
    final_url = page.url
    ctx.close()
    return {'hooks': hooks, 'capi': capi, 'calls': calls, 'meta': meta, 'errors': errors, 't0': t0, 'url': final_url,
            'consent_line': consent_line, 'consent_html': consent_html, 'link_color': link_color}


def leads(meta): return [m for m in meta if m[:2] == ['track', 'Lead']]


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])

    # 1 + 2a: qualified, CAPI on, cookies present but no consent choice.
    r = run(b, WITH_CAPI, QUALIFIED, cookies=True)
    check(not r['errors'], f'1: no page errors {r["errors"]}')
    check(len(r['capi']) == 1, f'1: exactly one receiver POST (got {len(r["capi"])})')
    check(len(leads(r['meta'])) == 1, '1: exactly one browser Lead')
    if r['capi'] and leads(r['meta']):
        lead = leads(r['meta'])[0]; body = json.loads(r['capi'][0]['body'])
        print('   Lead call:', lead)
        print('   receiver body:', body)
        eid = (lead[3] if len(lead) > 3 else {}).get('eventID')
        check(lead[2] == {'content_name': 'VSL Application (vsl)'}, '1: Lead params unchanged')
        check(bool(eid) and UUID_ID.fullmatch(eid or '') is not None, f'1: Lead eventID is vsl-<uuid> ({eid})')
        check(body.get('event_id') == eid, '1: receiver event_id == Lead eventID')
        check(set(body) == FIELDS, f'1: receiver has exactly the agreed fields {sorted(body)}')
        check(isinstance(body.get('event_time'), int) and abs(body['event_time'] - r['t0']) <= 5, '1: event_time is unix seconds, now')
        check(body.get('event_source_url') == ORIGIN + '/vsl/' + QUERY, '1: event_source_url is location.href')
        check(body.get('email') == PERSON['email'] and body.get('first_name') == 'Testy'
              and body.get('last_name') == "O'Builder", '1: email and names')
        hook = json.loads(r['hooks'][0]) if r['hooks'] else {}
        check(body.get('phone') == '+447700900123' == hook.get('phone'), '1: phone is ukPhone() form, same as webhook')
        check(body.get('fbclid') == 'TESTCLID123', '1: fbclid from page URL')
        check(body.get('fbp') == '' and body.get('fbc') == '' and body.get('consent_ads') is False,
              '2: no consent choice, fbp/fbc empty even with cookies set, consent_ads false')
        c = r['capi'][0]
        check(c['method'] == 'POST' and (c['ctype'] or '').startswith('text/plain') and c['type'] == 'fetch'
              and not c['cookie'], f'1: fetch POST, text/plain, no cookies ({c["type"]}, {c["ctype"]})')
        check(r['calls'] == [{'via': 'fetch', 'method': 'POST', 'keepalive': True, 'credentials': 'omit',
                              'headers': {'Content-Type': 'text/plain'}}],
              f'1: one fetch call, keepalive, credentials omit, never sendBeacon {r["calls"]}')
    check(len(r['hooks']) == 1, '1: webhook still sent once')
    check(r['url'].startswith(ORIGIN + '/vsl/book/'), f'1: redirects to /vsl/book/ ({r["url"]})')

    # 2b: advertising declined in the banner.
    r = run(b, WITH_CAPI, QUALIFIED, consent='decline', cookies=True)
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == '' and body.get('fbc') == '' and body.get('consent_ads') is False,
          '2: declined, fbp/fbc empty, consent_ads false')

    # 2c: advertising accepted, cookies present.
    r = run(b, WITH_CAPI, QUALIFIED, consent='accept', cookies=True)
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == FBP and body.get('fbc') == FBC and body.get('consent_ads') is True,
          f'2: accepted, fbp/fbc filled, consent_ads true ({body.get("fbp")}, {body.get("fbc")}, {body.get("consent_ads")})')

    # 2d: accepted but no Meta cookies yet.
    r = run(b, WITH_CAPI, QUALIFIED, consent='accept')
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == '' and body.get('fbc') == '' and body.get('consent_ads') is True,
          '2: accepted, no cookies, fbp/fbc empty, consent_ads true')

    # 2e: analytics only, and advertising accepted then revoked.
    for mode in ('analytics', 'revoke'):
        r = run(b, WITH_CAPI, QUALIFIED, consent=mode, cookies=True)
        body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
        check(len(r['capi']) == 1 and body.get('fbp') == '' and body.get('fbc') == ''
              and body.get('consent_ads') is False, f'2: {mode} consent, fbp/fbc empty, consent_ads false')

    # Fallbacks: no randomUUID (getRandomValues), then no crypto RNG at all.
    for label, kw in (('no randomUUID', {'no_uuid': True}), ('no crypto RNG', {'no_rng': True})):
        r = run(b, WITH_CAPI, QUALIFIED, **kw)
        body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
        eid = (leads(r['meta'])[0][3] if leads(r['meta']) else {}).get('eventID')
        check(bool(eid) and UUID_ID.fullmatch(eid) is not None and body.get('event_id') == eid and not r['errors'],
              f'fallback ({label}): vsl-<v4 uuid>, ids match ({eid})')

    # Double submit: everything goes once.
    r = run(b, WITH_CAPI, QUALIFIED, consent='accept', submits=2)
    check(len(r['capi']) == 1 and len(r['hooks']) == 1 and len(leads(r['meta'])) == 1,
          f'double submit: 1 receiver POST, 1 webhook, 1 Lead (got {len(r["capi"])}, {len(r["hooks"])}, {len(leads(r["meta"]))})')
    r = run(b, WITH_CAPI, NOT_QUALIFIED, submits=2)
    check(len(r['hooks']) == 1 and r['meta'].count(['trackCustom', 'ApplicationNotQualified']) == 1,
          'double submit (not qualified): 1 webhook, 1 ApplicationNotQualified')

    # Receiver down: the visitor still reaches the booking page.
    for mode in ('500', 'abort'):
        r = run(b, WITH_CAPI, QUALIFIED, capi=mode)
        check(len(r['capi']) == 1 and len(r['hooks']) == 1 and not r['errors']
              and r['url'].startswith(ORIGIN + '/vsl/book/'), f'receiver {mode}: still redirects to /vsl/book/ ({r["url"]})')

    # No phone: no receiver POST, but the Lead and webhook still go.
    r = run(b, NO_PHONE, QUALIFIED, consent='accept', cookies=True)
    check(r['capi'] == [] and r['calls'] == [], '5: empty phone, no receiver POST')
    check(len(leads(r['meta'])) == 1 and len(r['hooks']) == 1 and not r['errors'],
          '5: empty phone, Lead and webhook still sent')

    # 3: not qualified, CAPI on, consent accepted.
    r = run(b, WITH_CAPI, NOT_QUALIFIED, consent='accept', cookies=True)
    check(r['capi'] == [], '3: not qualified, no receiver POST')
    check(leads(r['meta']) == [], '3: not qualified, no Lead')
    check(['trackCustom', 'ApplicationNotQualified'] in r['meta'], '3: ApplicationNotQualified still fires')
    check(len(r['hooks']) == 1 and json.loads(r['hooks'][0])['route'] == 'free-training', '3: webhook still sent')

    # 5: as shipped (CAPI_URL empty).
    r = run(b, CURRENT, QUALIFIED, consent='accept', cookies=True,
            shot=os.path.join(SHOTS, 'vsl-consent-line.png') if SHOTS else None)
    check(r['capi'] == [] and r['calls'] == [], '5: CAPI_URL empty, no receiver POST')
    check(len(leads(r['meta'])) == 1 and 'eventID' in leads(r['meta'])[0][3], '5: Lead still carries eventID')
    want = ('By applying you agree we can call, text or email you about your application. '
            'Some of your details are shared with Meta (see our Privacy Policy).')
    check(r['consent_line'] == want, f'6: consent line text: {r["consent_line"]!r}')
    check('<a href="/privacy/">Privacy Policy</a>' in r['consent_html'], '6: consent line links to /privacy/')
    check(r['link_color'] == 'rgb(138, 104, 0)', f'6: consent link colour #8a6800 ({r["link_color"]})')

    # 4: webhook body byte-identical to the base branch, both routes.
    for label, answers in (('qualified', QUALIFIED), ('not qualified', NOT_QUALIFIED)):
        old = run(b, BASELINE, answers, consent='accept', cookies=True)
        new = run(b, WITH_CAPI, answers, consent='accept', cookies=True)
        same = len(old['hooks']) == len(new['hooks']) == 1 and old['hooks'][0] == new['hooks'][0]
        check(same, f'4: webhook body byte-identical to {BASE_REF} ({label})')
        if label == 'qualified': print('   webhook body:', new['hooks'][0] if new['hooks'] else None)

    # 6: privacy page.
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
        check(needle in text, f'6: privacy shows "{needle[:60]}"')
    check('Google, Meta, Microsoft, Cabin' not in text, '6: old combined Meta row gone')
    para = page.locator('p:has-text("Meta Conversions API.")')
    check(para.count() == 1 and para.is_visible(), '6: Meta paragraph visible once')
    for w, h, name in ((390, 844, 'mobile'), (1280, 900, 'desktop')):
        page.set_viewport_size({'width': w, 'height': h})
        page.wait_for_timeout(200)
        check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'6: privacy, no sideways scroll at {w}px')
        if SHOTS:
            para.scroll_into_view_if_needed(); page.screenshot(path=os.path.join(SHOTS, f'privacy-meta-{name}.png'))
    page.goto(ORIGIN + '/vsl/', wait_until='load')
    page.set_viewport_size({'width': 390, 'height': 844}); page.wait_for_timeout(200)
    check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), '6: vsl, no sideways scroll at 390px')
    ctx.close()
    b.close()

srv.shutdown()
print('\n%d failure(s)' % len(failures) if failures else '\nALL PASS')
sys.exit(1 if failures else 0)
