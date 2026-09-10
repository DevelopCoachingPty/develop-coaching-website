const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, '../www/ai-for-builders-september-2026/index.html'), 'utf8');
const source = html.slice(html.indexOf('async function mountCheckout(){'), html.indexOf('const target=new Date'));

async function run(search = '', fail = false, paymentStatus = 'paid') {
  const calls = [], buttons = [], redirects = [], requests = []; let ready = 0;
  function element() { return { textContent: '', children: [], classList: { add() {}, remove() {} }, setAttribute() {}, remove() { this.removed = true; }, replaceChildren(...children) { this.children = children; }, addEventListener(name, fn) { this[name] = fn; }, scrollIntoView() {} }; }
  const nodes = Object.fromEntries(['stripe-checkout', 'checkout-status', 'stripe-fallback', 'register'].map(id => [id, element()]));
  let mounts = 0;
  const context = { URLSearchParams, location: { search, replace: url => redirects.push(url) }, window: { dcWorkshop: { attribution: { source: 'facebook' }, checkoutReady() { ready++; } } }, crypto: { randomUUID: () => 'test-attempt-12345678' }, sessionStorage: { getItem: key => { assert.equal(key, 'ai-builders-attempt-v2'); return null; }, setItem(key) { assert.equal(key, 'ai-builders-attempt-v2'); } },
    document: { getElementById: id => nodes[id], createElement: tag => { const node = element(); if (tag === 'button') buttons.push(node); return node; } },
    fetch: async (url, options) => { calls.push(url); requests.push(options); return { ok: !fail, json: async () => url.includes('checkout-status') ? { status: paymentStatus } : { clientSecret: 'fixture', publishableKey: 'fixture' } }; },
    Stripe: () => ({ initEmbeddedCheckout: async () => ({ mount: () => { mounts++; } }) }) };
  await vm.runInNewContext(source, context);
  return { calls, buttons, nodes, redirects, requests, ready: () => ready, mounts: () => mounts };
}
test('loads checkout automatically with no initial button click', async () => {
  const result = await run();
  assert.deepEqual(result.calls, ['/api/create-ai-builders-checkout']);
  assert.equal(result.mounts(), 1);
  assert.equal(result.ready(), 1);
  assert.deepEqual(JSON.parse(result.requests[0].body).attribution, { source: 'facebook' });
  assert.equal(result.nodes['checkout-status'].removed, true);
});
test('failure shows retry and retry remains usable', async () => {
  const result = await run('', true);
  assert.equal(result.buttons[0].textContent, 'Try secure checkout again');
  assert.equal(result.buttons[0].disabled, false);
  await result.buttons[0].click();
  assert.equal(result.calls.length, 2);
});
test('paid, pending and invalid returns never create another payment session', async () => {
  for (const [fail, state] of [[false, 'paid'], [false, 'pending'], [true, 'paid']]) {
    const result = await run('?checkout=complete&session_id=cs_test_example', fail, state);
    assert.equal(result.calls.length, 0);
    assert.equal(result.redirects[0], '/ai-for-builders-september-2026/thank-you/?checkout=complete&session_id=cs_test_example');
    assert.equal(result.mounts(), 0);
    assert.equal(result.buttons.length, 0);
  }
});
