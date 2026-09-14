// booking-tracking.test.js - node:test + node:vm, no packages.
"use strict";

const test = require("node:test");
const assert = require("node:assert");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const file = path.join(__dirname, "../www/booking-tracking.js");
const SRC = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";

const ORIGIN = "https://link.flow-build.com";
const PATH = "/widget/booking/zXUkPVoGKzRyirwYa0Ck";
const CAL = "zXUkPVoGKzRyirwYa0Ck";

function makeEnv(opts) {
  opts = opts || {};
  const hostname = opts.hostname || "develop-coaching.com";
  const listeners = { message: [], pageshow: [] };
  const pushed = [];

  const iframes = [];
  function makeIframe(src, connected) {
    const contentWindow = {};
    const attrs = { src: src };
    const f = {
      contentWindow,
      isConnected: connected !== false,
      getAttribute: (n) => (n in attrs ? attrs[n] : null)
    };
    iframes.push(f);
    return f;
  }

  const document = {
    baseURI: "https://" + hostname + "/",
    querySelectorAll: (sel) => (sel === "iframe" ? iframes.slice() : [])
  };

  const window = {
    location: { hostname, href: "https://" + hostname + "/" },
    dataLayer: { push: (o) => pushed.push(JSON.parse(JSON.stringify(Array.from(o)))) },
    addEventListener: (type, fn) => {
      if (listeners[type]) listeners[type].push(fn);
    }
  };

  const sandbox = {
    window,
    document,
    URL,
    Object,
    Array,
    console
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  return {
    sandbox,
    window,
    document,
    iframes,
    pushed,
    listeners,
    makeIframe,
    run() {
      vm.runInContext(SRC, sandbox, { filename: "booking-tracking.js" });
    },
    fireMessage(origin, source, data) {
      for (const fn of listeners.message) fn({ origin, source, data });
    },
    firePageshow(persisted) {
      for (const fn of listeners.pageshow) fn({ persisted });
    }
  };
}

function trustedFrame(env, src) {
  return env.makeIframe(src || ORIGIN + PATH, true);
}

test("trusted complete fires exactly once", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { fingerprint: "abc", calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
  assert.deepStrictEqual(env.pushed[0], ["event", "scale_session_booked", {
    send_to:"G-PXT2VCVFLW", transport_type:"beacon", scheduler_provider:"FlowBuild", booking_calendar_id:CAL
  }]);
});

test("malformed arrays and data rejected", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  const bad = [
    "not-array",
    [],
    ["msgsndr-booking-complete"],
    ["msgsndr-booking-complete", null],
    ["msgsndr-booking-complete", "str"],
    ["msgsndr-booking-complete", []],
    ["msgsndr-booking-complete", { calendarId: CAL }, "extra"],
    ["wrong-event", { calendarId: CAL }],
    ["msgsndr-booking-complete", { calendarId: "other" }],
    ["msgsndr-booking-complete", { calendarId: CAL, extra: 1, __proto__: null }]
  ];
  for (const d of bad) env.fireMessage(ORIGIN, f.contentWindow, d);
  // last one is a valid plain object with correct calendarId -> should fire
  assert.strictEqual(env.pushed.length, 1);
});

test("wrong origin rejected", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage("https://evil.example", f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 0);
});

test("wrong source rejected", () => {
  const env = makeEnv();
  env.run();
  trustedFrame(env);
  env.fireMessage(ORIGIN, {}, ["msgsndr-booking-complete", { calendarId: CAL }]);
  assert.strictEqual(env.pushed.length, 0);
});

test("wrong calendar rejected", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: "nope" }
  ]);
  assert.strictEqual(env.pushed.length, 0);
});

test("evil URL lookalike iframe rejected", () => {
  const env = makeEnv();
  env.run();
  const f = env.makeIframe("https://link.flow-build.com.evil.example" + PATH, true);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 0);
});

test("iframe with wrong pathname rejected", () => {
  const env = makeEnv();
  env.run();
  const f = env.makeIframe(ORIGIN + "/widget/booking/OTHER", true);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 0);
});

test("disconnected iframe rejected", () => {
  const env = makeEnv();
  env.run();
  const f = env.makeIframe(ORIGIN + PATH, false);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 0);
});

test("duplicate responsive widgets dedupe to one event", () => {
  const env = makeEnv();
  env.run();
  const a = trustedFrame(env);
  const b = trustedFrame(env);
  env.fireMessage(ORIGIN, a.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  env.fireMessage(ORIGIN, b.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
});

test("unrelated form/focus messages produce no event", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, ["form-focus", {}]);
  env.fireMessage(ORIGIN, f.contentWindow, ["click", { x: 1 }]);
  env.fireMessage(ORIGIN, f.contentWindow, { type: "focus" });
  assert.strictEqual(env.pushed.length, 0);
});

test("preview/local hostname disabled", () => {
  for (const h of ["localhost", "preview.example.com", "develop-coaching.com.evil.example"]) {
    const env = makeEnv({ hostname: h });
    env.run();
    const f = trustedFrame(env);
    env.fireMessage(ORIGIN, f.contentWindow, [
      "msgsndr-booking-complete",
      { calendarId: CAL }
    ]);
    assert.strictEqual(env.pushed.length, 0, "host " + h);
  }
});

test("replay script installed twice adds no extra listener", () => {
  const env = makeEnv();
  env.run();
  env.run();
  assert.strictEqual(env.listeners.message.length, 1);
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
});

test("private fields never emitted", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { fingerprint: "SECRET", calendarId: CAL, email: "a@b.c", phone: "123" }
  ]);
  assert.strictEqual(env.pushed.length, 1);
  const out = JSON.stringify(env.pushed[0]);
  assert.ok(!out.includes("SECRET"));
  assert.ok(!out.includes("a@b.c"));
  assert.ok(!out.includes("123"));
  assert.deepStrictEqual(Object.keys(env.pushed[0][2]).sort(), [
    "booking_calendar_id",
    "scheduler_provider",
    "send_to",
    "transport_type"
  ]);
});

test("bfcache restore allows a new deliberate booking", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
  env.firePageshow(true);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 2);
});

test("non-persisted pageshow does not clear dedup", () => {
  const env = makeEnv();
  env.run();
  const f = trustedFrame(env);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  env.firePageshow(false);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
});

test("trailing slash and query on iframe src accepted", () => {
  const env = makeEnv();
  env.run();
  const f = env.makeIframe(ORIGIN + PATH + "/?x=1", true);
  env.fireMessage(ORIGIN, f.contentWindow, [
    "msgsndr-booking-complete",
    { calendarId: CAL }
  ]);
  assert.strictEqual(env.pushed.length, 1);
});

test("privacy preferences and GA opt out prevent events", () => {
  for (const settings of [{navigator:{globalPrivacyControl:true}}, {navigator:{doNotTrack:'1'}}, {'ga-disable-G-PXT2VCVFLW':true}]) {
    const env = makeEnv(); Object.assign(env.window, settings); env.run();
    const f = trustedFrame(env);
    env.fireMessage(ORIGIN, f.contentWindow, ['msgsndr-booking-complete',{calendarId:CAL}]);
    assert.strictEqual(env.pushed.length,0);
  }
});
test("no existing analytics layer means no new tracker is created", () => {
  const env=makeEnv(); delete env.window.dataLayer; env.run(); const f=trustedFrame(env);
  env.fireMessage(ORIGIN,f.contentWindow,['msgsndr-booking-complete',{calendarId:CAL}]);
  assert.strictEqual(env.pushed.length,0); assert.strictEqual(env.window.dataLayer,undefined);
});
