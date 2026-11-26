"""Headless check of the /vsl Meta Conversions API (CAPI) browser side.

Every external host is stubbed: the FlowBuild webhook and a fake CAPI receiver
are intercepted and answered locally, the Meta and Google libraries load as
empty scripts, nothing real is contacted. Uses fictional people and Ofcom drama
numbers (07700 900xxx). Starts its own static server over www/.

Run from the repo root (CHROME = path to a Chromium/Chrome binary):
  CHROME=".../Google Chrome for Testing" uv run --with playwright python3 scripts/check_vsl_capi_browser.py

What it proves:
  1. Qualified submit with CAPI_URL set: browser Lead carries an eventID, and
     exactly one receiver POST is sent with the same event_id and all fields.
  2. fbp/fbc are '' without advertising consent (no choice, or declined), and
     filled from the _fbp/_fbc cookies once advertising is accepted.
  3. Not-qualified submit: no receiver POST and no Lead.
  4. The FlowBuild webhook body is byte-identical to origin/main for the same inputs.
  5. CAPI_URL empty (as shipped): no receiver POST at all.
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


def run(browser, html, answers, consent=None, cookies=False, no_uuid=False, shot=None):
    """Fill and submit the form once. consent: None (no choice), 'decline' or 'accept'."""
    ctx = browser.new_context()
    if cookies:
        ctx.add_cookies([{'name': '_fbp', 'value': FBP, 'url': ORIGIN},
                         {'name': '_fbc', 'value': FBC, 'url': ORIGIN}])
    if no_uuid:
        ctx.add_init_script('try{Object.defineProperty(Crypto.prototype,"randomUUID",{value:undefined})}catch(e){}')
    page = ctx.new_page()
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
            capi.append({'method': req.method, 'body': req.post_data, 'ctype': req.headers.get('content-type')})
            return route.fulfill(status=200, content_type='application/json', body='{}')
        if req.resource_type == 'script':
            return route.fulfill(status=200, content_type='application/javascript', body='')
        return route.fulfill(status=204, body='')
    ctx.route('**/*', handle)
    page.goto(ORIGIN + '/vsl/' + QUERY, wait_until='load')
    if consent:
        acc, rej = (['advertisement'], []) if consent == 'accept' else ([], ['advertisement'])
        page.evaluate("""([a,r])=>document.dispatchEvent(new CustomEvent('cookieyes_consent_update',
                         {detail:{accepted:a,rejected:r}}))""", [acc, rej])
    for name in ('work_source', 'business_type', 'turnover', 'approach'):
        page.locator(f'input[name="{name}"][value="{answers[name]}"]').check(force=True)
        page.click('#nextBtn')
    for k, v in PERSON.items():
        page.fill(f'#applyForm [name="{k}"]', v)
    consent_line = page.inner_text('#consentLine') if page.is_visible('#consentLine') else None
    consent_html = page.eval_on_selector('#consentLine', 'e=>e.innerHTML')
    if shot:
        page.locator('#apply').screenshot(path=shot)
    t0 = int(time.time())
    # requestSubmit runs the handler synchronously, so fbq's queue is complete
    # on return, before the page navigates away.
    meta = page.evaluate("""()=>{ document.getElementById('applyForm').requestSubmit();
        return (window.fbq && fbq.queue || []).map(a => JSON.parse(JSON.stringify(Array.from(a)))); }""")
    page.wait_for_timeout(900)
    ctx.close()
    return {'hooks': hooks, 'capi': capi, 'meta': meta, 'errors': errors, 't0': t0,
            'consent_line': consent_line, 'consent_html': consent_html}


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
        check(bool(eid) and re.fullmatch(r'vsl-[0-9a-f-]{36}', eid or '') is not None, f'1: Lead eventID is vsl-<uuid> ({eid})')
        check(body.get('event_id') == eid, '1: receiver event_id == Lead eventID')
        check(set(body) == {'event_id', 'event_time', 'event_source_url', 'email', 'phone', 'first_name',
                            'last_name', 'fbp', 'fbc', 'fbclid'}, f'1: receiver has exactly the agreed fields {sorted(body)}')
        check(isinstance(body.get('event_time'), int) and abs(body['event_time'] - r['t0']) <= 5, '1: event_time is unix seconds, now')
        check(body.get('event_source_url') == ORIGIN + '/vsl/' + QUERY, '1: event_source_url is location.href')
        check(body.get('email') == PERSON['email'] and body.get('first_name') == 'Testy'
              and body.get('last_name') == "O'Builder", '1: email and names')
        hook = json.loads(r['hooks'][0]) if r['hooks'] else {}
        check(body.get('phone') == '+447700900123' == hook.get('phone'), '1: phone is ukPhone() form, same as webhook')
        check(body.get('fbclid') == 'TESTCLID123', '1: fbclid from page URL')
        check(body.get('fbp') == '' and body.get('fbc') == '', '2: no consent choice, fbp/fbc empty even with cookies set')
        check(r['capi'][0]['method'] == 'POST' and 'application/json' in (r['capi'][0]['ctype'] or ''), '1: POST, JSON')
    check(len(r['hooks']) == 1, '1: webhook still sent once')

    # 2b: advertising declined in the banner.
    r = run(b, WITH_CAPI, QUALIFIED, consent='decline', cookies=True)
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == '' and body.get('fbc') == '', '2: declined, fbp/fbc empty')

    # 2c: advertising accepted, cookies present.
    r = run(b, WITH_CAPI, QUALIFIED, consent='accept', cookies=True)
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == FBP and body.get('fbc') == FBC, f'2: accepted, fbp/fbc filled ({body.get("fbp")}, {body.get("fbc")})')

    # 2d: accepted but no Meta cookies yet.
    r = run(b, WITH_CAPI, QUALIFIED, consent='accept')
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    check(body.get('fbp') == '' and body.get('fbc') == '', '2: accepted, no cookies, fbp/fbc empty')

    # randomUUID missing: fallback id still shared by both events.
    r = run(b, WITH_CAPI, QUALIFIED, no_uuid=True)
    body = json.loads(r['capi'][0]['body']) if r['capi'] else {}
    eid = (leads(r['meta'])[0][3] if leads(r['meta']) else {}).get('eventID')
    check(bool(eid) and eid.startswith('vsl-') and body.get('event_id') == eid and not r['errors'],
          f'fallback: no randomUUID, ids still match ({eid})')

    # 3: not qualified, CAPI on, consent accepted.
    r = run(b, WITH_CAPI, NOT_QUALIFIED, consent='accept', cookies=True)
    check(r['capi'] == [], '3: not qualified, no receiver POST')
    check(leads(r['meta']) == [], '3: not qualified, no Lead')
    check(['trackCustom', 'ApplicationNotQualified'] in r['meta'], '3: ApplicationNotQualified still fires')
    check(len(r['hooks']) == 1 and json.loads(r['hooks'][0])['route'] == 'free-training', '3: webhook still sent')

    # 5: as shipped (CAPI_URL empty).
    r = run(b, CURRENT, QUALIFIED, consent='accept', cookies=True,
            shot=os.path.join(SHOTS, 'vsl-consent-line.png') if SHOTS else None)
    check(r['capi'] == [], '5: CAPI_URL empty, no receiver POST')
    check(len(leads(r['meta'])) == 1 and 'eventID' in leads(r['meta'])[0][3], '5: Lead still carries eventID')
    want = ('By applying you agree we can call, text or email you about your application. '
            'Some of your details are shared with Meta (see our Privacy Policy).')
    check(r['consent_line'] == want, f'6: consent line text: {r["consent_line"]!r}')
    check('<a href="/privacy/">Privacy Policy</a>' in r['consent_html'], '6: consent line links to /privacy/')

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
    if SHOTS:
        page.set_viewport_size({'width': 390, 'height': 844})
        para.scroll_into_view_if_needed(); page.screenshot(path=os.path.join(SHOTS, 'privacy-meta-mobile.png'))
        page.set_viewport_size({'width': 1280, 'height': 900})
        para.scroll_into_view_if_needed(); page.screenshot(path=os.path.join(SHOTS, 'privacy-meta-desktop.png'))
    check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), '6: no sideways scroll')
    ctx.close()
    b.close()

srv.shutdown()
print('\n%d failure(s)' % len(failures) if failures else '\nALL PASS')
sys.exit(1 if failures else 0)
