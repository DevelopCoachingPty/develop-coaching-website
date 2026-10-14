const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '../www');
const landing = fs.readFileSync(path.join(root, 'fill-the-order-book/index.html'), 'utf8');
const thanks = fs.readFileSync(path.join(root, 'fill-the-order-book-thank-you/index.html'), 'utf8');
const inline = html => Array.from(html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g), match => match[1]);
const checkoutScript = inline(landing).find(script => script.includes('// Source attribution packed'));
const paymentLink = 'https://buy.stripe.com/bJe9AT3Wtfrtamk7uF9k40F';

function run(search = '', saved = null, blocked = false) {
  const links = Array.from(landing.matchAll(/<a\b[^>]*href="(https:\/\/buy\.stripe\.com[^\"]+)"/g), match => ({href: match[1]}));
  const listeners = {}, meta = [], google = [];
  const store = {dc_ftob_utm: saved};
  const window = {location: {search, origin: 'https://develop-coaching.com', pathname: '/fill-the-order-book/'},
    localStorage: {getItem: key => {if (blocked) throw Error('blocked'); return store[key];}, setItem: (key, value) => {if (blocked) throw Error('blocked'); store[key] = value;}}};
  const context = {window, URL, URLSearchParams, Date, document: {querySelectorAll: () => links, addEventListener: (name, fn) => {listeners[name] = fn;}}, gtag: (...args) => google.push(args), fbq: (...args) => meta.push(args)};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(root, 'assets/ftob-attribution.js'), 'utf8'), context);
  vm.runInContext(checkoutScript, context);
  function click(link) {listeners.click({target: {closest: () => link}});}
  return {context, window, links, google, meta, click, store};
}

test('both pages load only the owner-verified GA4 stream and initialize one automatic page view', () => {
  for (const html of [landing, thanks]) {
    assert.equal((html.match(/gtag\/js\?id=G-PXT2VCVFLW/g) || []).length, 1);
    assert.equal((html.match(/gtag\('config', 'G-PXT2VCVFLW'/g) || []).length, 1);
    assert.doesNotMatch(html, /G-EX5H3P27NP|gtag\('event', 'page_view'/);
  }
});

test('every booking control uses the same attributable Stripe payment link', () => {
  const result = run('?utm_source=flowbuild&utm_medium=email&utm_campaign=fill-the-order-book&utm_content=e2');
  assert.equal(result.links.length, 7); // Five section CTAs, final booking CTA, direct fallback.
  assert.doesNotMatch(landing, /<stripe-buy-button|buy-button\.js/);
  assert.equal(result.google.length, 0); // Loading the page is not checkout intent.
  for (const link of result.links) {
    const destination = new URL(link.href);
    assert.equal(destination.origin + destination.pathname, paymentLink);
    assert.equal(destination.searchParams.get('client_reference_id'), 's-flowbuild__c-fill-the-order-book__a-e2');
    result.click(link);
  }
  assert.equal(result.google.length, 7);
  assert.equal(result.meta.length, 7);
  for (const call of result.google) {
    assert.equal(call[0], 'event'); assert.equal(call[1], 'begin_checkout');
    assert.equal(call[2].send_to, 'G-PXT2VCVFLW');
    assert.equal(call[2].value, 45); assert.equal(call[2].currency, 'GBP');
    assert.equal(call[2].items[0].quantity, 1);
    assert.equal(call[2].campaign_source, 'flowbuild');
    assert.equal(call[2].campaign_medium, 'email');
    assert.equal(call[2].campaign_content, 'e2');
  }
});

test('e1/e2/e3 and Meta ad identities survive checkout intent and direct returns', () => {
  for (const query of [
    ...['e1', 'e2', 'e3'].map(email => '?utm_source=flowbuild&utm_medium=email&utm_campaign=fill-the-order-book&utm_content=' + email),
    '?utm_source=meta&utm_medium=paid_social&utm_campaign=fill-the-order-book-oct-2026&utm_content=ftob-oct26-cold-old-quotes&utm_term=ftob-oct26-cold-uk-purchase-1200aud'
  ]) {
    const tagged = run(query), back = run('', tagged.store.dc_ftob_utm);
    back.click(back.links[0]);
    assert.equal(back.links[0].href, tagged.links[0].href);
    assert.equal(back.google[0][2].campaign_source, new URLSearchParams(query).get('utm_source'));
    assert.equal(back.google[0][2].campaign_content, new URLSearchParams(query).get('utm_content'));
  }
});

test('blocked storage, unrelated clicks and deceptive Stripe URLs cannot manufacture checkout events', () => {
  const result = run('?utm_source=flowbuild&utm_medium=email&utm_content=e3', null, true);
  for (const link of [null, {href: 'https://buy.stripe.com.evil.test/bJe9AT3Wtfrtamk7uF9k40F'}, {href: 'https://buy.stripe.com/another-link'}, {href: 'invalid'}]) result.click(link);
  assert.equal(result.google.length, 0);
  result.click(result.links[0]);
  assert.equal(result.google.length, 1);
  assert.equal(result.google[0][2].campaign_content, 'e3');
  assert.match(result.links[0].href, /client_reference_id=s-flowbuild__a-e3/);
});

test('thank-you URL produces only an unverified GA4 return and keeps session IDs out of Analytics', () => {
  for (const search of ['', '?session_id=cs_live_fake', '?session_id=cs_test_fixture', '?session_id=']) {
    const result = run(search);
    result.window.location.pathname = '/fill-the-order-book-thank-you/';
    result.window.dcUtm = result.window.dcFtobAttribution();
    result.context.dataLayer = result.window.dataLayer = [];
    // Execute the actual GA4 block without loading external pixels.
    vm.runInContext(inline(thanks).find(script => script.includes("gtag('config'")), result.context);
    const calls = Array.from(result.window.dataLayer, args => Array.from(args));
    const config = calls.find(call => call[0] === 'config');
    assert.equal(config[2].page_location, 'https://develop-coaching.com/fill-the-order-book-thank-you/');
    assert.equal(calls.filter(call => call[1] === 'purchase').length, 0);
    assert.equal(JSON.stringify(calls).includes('cs_live_fake'), false);
    const returns = calls.filter(call => call[1] === 'checkout_return');
    assert.equal(returns.length, search ? 1 : 0);
    if (returns.length) {
      assert.equal(returns[0][2].payment_verified, false);
      for (const field of ['value', 'currency', 'items', 'transaction_id']) assert.equal(returns[0][2][field], undefined);
    }
  }
});

// Preserve the existing ad signal until a verified paid-event replacement is separately reviewed.
const legacyMetaReturn = `// Only fire Purchase for genuine buyers redirected from Stripe (Stripe appends ?session_id=cs_... on the redirect).
// Prevents phantom conversions from direct hits, bookmarks, back-button, previews and bots.
if (new URLSearchParams(window.location.search).get('session_id')) {
  fbq('track', 'Purchase', {value: 45.00, currency: 'GBP', content_name: 'Fill The Order Book Ticket', utm_source: window.dcUtm.utm_source || 'direct', utm_campaign: window.dcUtm.utm_campaign || '', utm_content: window.dcUtm.utm_content || '', utm_term: window.dcUtm.utm_term || ''}, {eventID: new URLSearchParams(window.location.search).get('session_id')});
}`;
test('legacy Meta Purchase block remains unchanged with its session gate and event ID', () => {
  const metaScript = inline(thanks).find(script => script.includes("fbq('init'"));
  const metaReturn = metaScript.slice(metaScript.indexOf('// Only fire Purchase')).trim();
  assert.equal(metaReturn, legacyMetaReturn);
  assert.doesNotMatch(metaScript, /CheckoutReturn/);
  for (const search of ['', '?session_id=cs_live_fixture', '?session_id=cs_test_fixture', '?session_id=']) {
    const result = run(search);
    result.window.dcUtm = {utm_source: 'meta', utm_campaign: 'fill-the-order-book-oct-2026', utm_content: 'cold-old-quotes', utm_term: 'cold-uk'};
    vm.runInContext(metaReturn, result.context);
    const purchases = result.meta.filter(call => call[0] === 'track' && call[1] === 'Purchase');
    const sid = new URLSearchParams(search).get('session_id');
    assert.equal(purchases.length, sid ? 1 : 0);
    if (sid) {
      assert.equal(purchases[0][2].value, 45);
      assert.equal(purchases[0][2].currency, 'GBP');
      assert.equal(purchases[0][2].utm_source, 'meta');
      assert.equal(purchases[0][2].utm_content, 'cold-old-quotes');
      assert.equal(purchases[0][3].eventID, sid);
    }
  }
});
