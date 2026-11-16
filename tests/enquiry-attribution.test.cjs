// enquiry-attribution.test.cjs - node:test + node:vm, no packages.
// Run: node --test tests/enquiry-attribution.test.cjs
"use strict";

const test = require("node:test");
const assert = require("node:assert");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const SRC = fs.readFileSync(path.join(__dirname, "../www/enquiry-attribution.js"), "utf8");
const FB = "https://link.flow-build.com";
const FORM = FB + "/widget/form/USUhO24FJYoYAYFPx4Lt";
const BOOK = FB + "/widget/booking/zXUkPVoGKzRyirwYa0Ck";

function memStorage(shared) {
  const m = shared || new Map();
  return {
    _m: m,
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k)
  };
}
function brokenStorage() {
  const boom = () => { throw new Error("SecurityError"); };
  return { getItem: boom, setItem: boom, removeItem: boom };
}

function makeIframe(src, attrs) {
  const a = Object.assign({ src }, attrs || {});
  return {
    tagName: "IFRAME",
    nodeType: 1,
    contentWindow: {},
    getAttribute: (n) => (n in a ? a[n] : null),
    setAttribute: (n, v) => { a[n] = String(v); },
    get src() { return a.src; }
  };
}

function run(opts) {
  opts = opts || {};
  const listeners = {};
  const pushed = [];
  const consent = { analytics: !!opts.consent, cbs: [] };
  const frames = (opts.frames || [FORM, BOOK]).map((s) => makeIframe(s));
  const document = {
    referrer: opts.referrer || "",
    readyState: "complete",
    documentElement: {},
    getElementsByTagName: (t) => (t === "iframe" ? frames : []),
    addEventListener: () => {}
  };
  const window = {
    location: new URL(opts.url || "https://develop-coaching.com/contact/"),
    navigator: opts.navigator || {},
    sessionStorage: opts.session || memStorage(),
    localStorage: opts.local || memStorage(),
    dataLayer: opts.noDataLayer ? undefined : { push: (x) => pushed.push(Array.from(x)) },
    dcConsent: opts.noConsentApi ? undefined : {
      allowed: (c) => c === "analytics" && consent.analytics,
      onChange: (fn) => consent.cbs.push(fn)
    },
    addEventListener: (t, fn) => { (listeners[t] = listeners[t] || []).push(fn); }
  };
  const ctx = { window, document, URL, URLSearchParams, JSON, Date, String, Array, Object };
  vm.runInNewContext(SRC, ctx);
  return {
    window, frames, pushed, consent,
    params: () => window.dcAttribution.params(),
    src: (i) => new URL(frames[i].getAttribute("src")),
    message: (data, origin, frameIndex) => (listeners.message || []).forEach((fn) => fn({
      origin: origin || FB,
      data,
      source: frameIndex === -1 ? {} : frames[frameIndex || 0].contentWindow
    })),
    setConsent: (v) => { consent.analytics = v; consent.cbs.forEach((fn) => fn()); }
  };
}

test("search landing: first touch captured, query strings stripped", () => {
  const e = run({
    url: "https://develop-coaching.com/construction-cash-flow-forecast/?utm_source=Google&utm_medium=cpc&utm_campaign=Q4-Builders&email=a@b.com",
    referrer: "https://www.google.com/search?q=secret"
  });
  const p = e.params();
  assert.strictEqual(p.dc_landing_page, "https://develop-coaching.com/construction-cash-flow-forecast/");
  assert.strictEqual(p.dc_utm_source, "google");
  assert.strictEqual(p.dc_utm_medium, "cpc");
  assert.strictEqual(p.dc_utm_campaign, "q4-builders");
  assert.strictEqual(p.dc_referrer, "https://www.google.com/search");
  assert.strictEqual(p.dc_ai_referrer, "none");
  const u = e.src(0);
  assert.strictEqual(u.origin + u.pathname, FORM);
  assert.strictEqual(u.searchParams.get("dc_utm_source"), "google");
  assert.ok(!e.frames[0].getAttribute("src").includes("secret"));
  assert.ok(!e.frames[0].getAttribute("src").includes("a%40b.com"));
});

test("AI referrers are flagged from the referrer host or ChatGPT's utm_source", () => {
  assert.strictEqual(run({ referrer: "https://www.perplexity.ai/" }).params().dc_ai_referrer, "perplexity");
  assert.strictEqual(run({ referrer: "https://gemini.google.com/app" }).params().dc_ai_referrer, "gemini");
  assert.strictEqual(run({ referrer: "https://copilot.microsoft.com/" }).params().dc_ai_referrer, "copilot");
  assert.strictEqual(run({ url: "https://develop-coaching.com/?utm_source=chatgpt.com" }).params().dc_ai_referrer, "chatgpt");
  assert.strictEqual(run({ referrer: "https://notchatgpt.com.evil.io/" }).params().dc_ai_referrer, "none");
});

test("email addresses never pass through as campaign labels", () => {
  const p = run({ url: "https://develop-coaching.com/?utm_source=jo@example.com&utm_campaign=x" }).params();
  assert.strictEqual(p.dc_utm_source, "");
  assert.strictEqual(p.dc_utm_campaign, "x");
});

test("first touch survives internal navigation in the same visit", () => {
  const session = memStorage();
  run({ session, url: "https://develop-coaching.com/blog/x/?utm_source=linkedin", referrer: "https://www.linkedin.com/" });
  const second = run({ session, url: "https://develop-coaching.com/contact/", referrer: "https://develop-coaching.com/blog/x/" });
  const p = second.params();
  assert.strictEqual(p.dc_landing_page, "https://develop-coaching.com/blog/x/");
  assert.strictEqual(p.dc_utm_source, "linkedin");
  assert.strictEqual(p.dc_enquiry_page, "https://develop-coaching.com/contact/");
});

test("blocked storage degrades safely: no crash, no guessed landing page", () => {
  const e = run({ session: brokenStorage(), local: brokenStorage(), referrer: "https://develop-coaching.com/about/" });
  const p = e.params();
  assert.strictEqual(p.dc_landing_page, "");
  assert.strictEqual(p.dc_referrer, "");
  assert.strictEqual(p.dc_enquiry_page, "https://develop-coaching.com/contact/");
  assert.ok(e.src(0).searchParams.has("dc_enquiry_page"));
});

test("cross-visit memory only with analytics consent, removed on withdrawal", () => {
  const local = memStorage();
  const e = run({ local, referrer: "https://www.bing.com/" });
  assert.strictEqual(local._m.size, 0);
  e.setConsent(true);
  assert.strictEqual(local._m.size, 1);
  e.setConsent(false);
  assert.strictEqual(local._m.size, 0);
  const gpc = memStorage();
  run({ local: gpc, consent: true, navigator: { globalPrivacyControl: true } });
  assert.strictEqual(gpc._m.size, 0);
});

test("a consented return visit keeps the original source", () => {
  const local = memStorage();
  run({ local, consent: true, url: "https://develop-coaching.com/pillar/?utm_source=chatgpt.com" });
  const back = run({ local, consent: true, url: "https://develop-coaching.com/contact/" });
  assert.strictEqual(back.params().dc_ai_referrer, "chatgpt");
  assert.strictEqual(back.params().dc_landing_page, "https://develop-coaching.com/pillar/");
});

test("form success message fires one generate_lead with labels", () => {
  const e = run({ consent: true, referrer: "https://chatgpt.com/" });
  e.message(["set-sticky-contacts", "_ud", "{\"email\":\"x@y.z\"}", "loc", "fp"]);
  assert.strictEqual(e.pushed.length, 0, "the contact payload message is ignored");
  e.message(["set-sticky-contacts", "embedded_iframe_inline-USUhO24FJYoYAYFPx4Lt", "inline-USUhO24FJYoYAYFPx4Lt", "loc", "fp"]);
  e.message(["set-sticky-contacts", "embedded_iframe_inline-USUhO24FJYoYAYFPx4Lt", "inline-USUhO24FJYoYAYFPx4Lt", "loc", "fp"]);
  assert.strictEqual(e.pushed.length, 1);
  const [cmd, name, params] = e.pushed[0];
  assert.strictEqual(cmd, "event");
  assert.strictEqual(name, "generate_lead");
  assert.strictEqual(params.send_to, "G-PXT2VCVFLW");
  assert.strictEqual(params.lead_type, "contact");
  assert.strictEqual(params.form_id, "USUhO24FJYoYAYFPx4Lt");
  assert.strictEqual(params.ai_referrer, "chatgpt");
  assert.ok(!JSON.stringify(params).includes("x@y.z"));
});

test("booking completion fires generate_lead as a booking", () => {
  const e = run({ consent: true });
  e.message(["msgsndr-booking-complete", { calendarId: "zXUkPVoGKzRyirwYa0Ck" }], FB, 1);
  assert.strictEqual(e.pushed.length, 1);
  assert.strictEqual(e.pushed[0][2].lead_type, "booking");
});

test("spoofed or unrelated messages are ignored", () => {
  const e = run({ consent: true });
  e.message(["set-sticky-contacts", "embedded_iframe_x", "x"], "https://evil.example", 0);
  e.message(["set-sticky-contacts", "embedded_iframe_x", "x"], FB, -1);
  e.message(["msgsndr-booking-complete", {}], FB, 0);
  e.message("[iFrameSizer]x:1:2:init", FB, 0);
  assert.strictEqual(e.pushed.length, 0);
});

test("no analytics consent, no GA4 event (but the form still gets its fields)", () => {
  const e = run({ consent: false });
  e.message(["set-sticky-contacts", "embedded_iframe_a", "a"]);
  assert.strictEqual(e.pushed.length, 0);
  assert.ok(e.src(0).searchParams.has("dc_ai_referrer"));
  // Consent given later on the same page: the next submit still counts.
  e.setConsent(true);
  e.message(["set-sticky-contacts", "embedded_iframe_a", "a"]);
  assert.strictEqual(e.pushed.length, 1);
});

test("lookalike hosts and non-widget iframes are left alone", () => {
  const e = run({ frames: ["https://link.flow-build.com.evil.io/widget/form/abc", "https://www.youtube.com/embed/x", FB + "/js/form_embed.js"] });
  assert.strictEqual(e.frames[0].getAttribute("src"), "https://link.flow-build.com.evil.io/widget/form/abc");
  assert.strictEqual(e.frames[1].getAttribute("src"), "https://www.youtube.com/embed/x");
  assert.strictEqual(e.frames[2].getAttribute("src"), FB + "/js/form_embed.js");
});

test("existing iframe query parameters are kept", () => {
  const e = run({ frames: [FORM + "?notrack=true"] });
  assert.strictEqual(e.src(0).searchParams.get("notrack"), "true");
  assert.ok(e.src(0).searchParams.has("dc_enquiry_page"));
});
