/* dc-consent.js - cookie consent gate for develop-coaching.com
 *
 * Loaded synchronously as the FIRST script in <head> on every page that carries
 * a tracker. It does four things, in this order:
 *   1. Sets Google Consent Mode v2 to "denied" before any Google tag can exist.
 *   2. Holds back every tracker script (GTM, GA4, Google Ads, Meta Pixel,
 *      Microsoft Clarity, ActiveCampaign, Cabin) until the visitor consents to
 *      that category. Held scripts are released in place, so the existing inline
 *      snippets keep working and their queued calls (fbq, clarity, vgo,
 *      dataLayer) replay as normal.
 *   3. Loads the hosted consent banner (CookieYes) using CONSENT_TOOL_ID.
 *   4. Watches for the consent choice (a Consent Mode "update" on the data layer,
 *      or the banner's own event) and releases the right scripts.
 *
 * Fails closed: if CONSENT_TOOL_ID is not a real CookieYes website key no
 * banner can load, so no tracker ever loads. Nothing here sets a cookie.
 *
 * Static <script type="text/plain" data-dc-category="..."> tags (Cabin, gtag.js
 * on the /software pages) are switched on by the same release step.
 *
 * Limits: a script added with document.write is not seen. Withdrawing consent
 * stops further sending where the vendor allows it, and a reload clears the rest.
 */
(function (w, d) {
  'use strict';
  if (w.dcConsent) return;

  // Supplied by Greg: the CookieYes "website key" (24 hex characters, from
  // CookieYes dashboard > Advanced settings > Get installation code).
  var CONSENT_TOOL_ID = 'e5ee5d26e0341217ffb7eccd';

  var state = { analytics: false, advertising: false };
  var held = [];
  var listeners = [];
  var layers = {};
  var gaIds = {};
  var disabledByUs = {};

  // ---- 1. Consent Mode v2 defaults, before any tag ----
  w.dataLayer = w.dataLayer || [];
  function gtag() { w.dataLayer.push(arguments); }
  if (typeof w.gtag !== 'function') w.gtag = gtag;
  gtag('consent', 'default', {
    ad_storage: 'denied',
    analytics_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500
  });

  // ---- which scripts belong to which category ----
  var RULES = [
    [/googletagmanager\.com\/gtm\.js/i, 'gtm'],
    [/googletagmanager\.com\/gtag\/js\?[^#]*\bid=AW-/i, 'advertising'],
    [/googletagmanager\.com\/gtag\/js/i, 'analytics'],
    [/google-analytics\.com\//i, 'analytics'],
    [/googleadservices\.com\/|doubleclick\.net\//i, 'advertising'],
    [/connect\.facebook\.net\//i, 'advertising'],
    [/\.clarity\.ms\//i, 'analytics'],
    [/\.app-us1\.com\/|trackcmp\.net\//i, 'advertising'],
    [/scripts\.withcabin\.com\//i, 'analytics']
  ];

  function classify(src) {
    for (var i = 0; i < RULES.length; i++) if (RULES[i][0].test(src)) return RULES[i][1];
    return null;
  }

  function allowed(cat) {
    if (cat === 'gtm') return state.analytics || state.advertising;
    return !!state[cat];
  }

  function rememberGtag(src) {
    var id = /[?&]id=([^&]+)/.exec(src);
    var layer = /[?&]l=([^&]+)/.exec(src);
    if (id) gaIds[id[1]] = true;
    if (layer && layer[1] !== 'dataLayer' && !layers[layer[1]]) {
      // A second data layer (ga4EventLayer) is not covered by the default above.
      var name = layer[1];
      var target = (w[name] = w[name] || []);
      var def = (function () { return arguments; })('consent', 'default', {
        ad_storage: 'denied', analytics_storage: 'denied',
        ad_user_data: 'denied', ad_personalization: 'denied'
      });
      target.unshift(def);
      layers[name] = target;
      if (state.analytics || state.advertising) {
        // Consent was already given (stored choice replayed early): tell the new layer too.
        target.push((function () { return arguments; })('consent', 'update', {
          analytics_storage: g(state.analytics),
          ad_storage: g(state.advertising),
          ad_user_data: g(state.advertising),
          ad_personalization: g(state.advertising)
        }));
      }
    }
  }

  // ---- 2. hold tracker scripts inserted from JavaScript ----
  function heldCategory(node) {
    if (!node || node.nodeType !== 1 || node.tagName !== 'SCRIPT') return null;
    if (node.hasAttribute('data-dc-passthrough')) return null;
    var src = node.getAttribute('src');
    if (!src) return null;
    var cat = classify(src);
    // Always give a second gtag data layer its denied default, even when the script is not held.
    if (cat && /googletagmanager\.com\/gtag\/js/i.test(src)) rememberGtag(src);
    if (!cat || allowed(cat)) return null;
    return cat;
  }

  function hold(cat, node, run) {
    var src = node.getAttribute('src') || '';
    if (/googletagmanager\.com\/gtag\/js/i.test(src)) rememberGtag(src);
    held.push({ cat: cat, node: node, run: run });
  }

  function patch(proto, name, kind) {
    var orig = proto && proto[name];
    if (typeof orig !== 'function') return;
    proto[name] = function () {
      var self = this, args = arguments, i, cat;
      if (kind === 'insertBefore') {
        cat = heldCategory(args[0]);
        if (cat) {
          hold(cat, args[0], function () {
            try { orig.apply(self, args); } catch (e) { orig.call(self, args[0], null); }
          });
          return args[0];
        }
      } else if (kind === 'single') {
        cat = heldCategory(args[0]);
        if (cat) {
          hold(cat, args[0], function () { orig.apply(self, args); });
          return args[0];
        }
      } else if (kind === 'adjacent') {
        cat = heldCategory(args[1]);
        if (cat) {
          hold(cat, args[1], function () { orig.apply(self, args); });
          return args[1];
        }
      } else if (kind === 'many') {
        var keep = [], any = false;
        for (i = 0; i < args.length; i++) {
          cat = heldCategory(args[i]);
          if (cat) {
            any = true;
            (function (node, c) { hold(c, node, function () { orig.call(self, node); }); })(args[i], cat);
          } else {
            keep.push(args[i]);
          }
        }
        if (any) return keep.length ? orig.apply(self, keep) : undefined;
      }
      return orig.apply(self, args);
    };
  }

  patch(w.Node && w.Node.prototype, 'appendChild', 'single');
  patch(w.Node && w.Node.prototype, 'insertBefore', 'insertBefore');
  patch(w.Element && w.Element.prototype, 'append', 'many');
  patch(w.Element && w.Element.prototype, 'prepend', 'many');
  patch(w.Element && w.Element.prototype, 'before', 'many');
  patch(w.Element && w.Element.prototype, 'after', 'many');
  patch(w.Element && w.Element.prototype, 'insertAdjacentElement', 'adjacent');

  // ---- release ----
  function g(v) { return v ? 'granted' : 'denied'; }

  var metaRevoked = false;

  function sendVendorSignals(prev) {
    // Clarity: Microsoft's consent API v2 (queued by the stub until Clarity loads).
    try {
      if (typeof w.clarity === 'function') {
        w.clarity('consentv2', { ad_Storage: g(state.advertising), analytics_Storage: g(state.analytics) });
      }
    } catch (e) {}
    // Meta Pixel: loads only after consent, so only a later withdrawal needs a call.
    try {
      if (typeof w.fbq === 'function') {
        if (prev.advertising && !state.advertising) { w.fbq('consent', 'revoke'); metaRevoked = true; }
        else if (state.advertising && metaRevoked) { w.fbq('consent', 'grant'); metaRevoked = false; }
      }
    } catch (e) {}
    // GA4: stop further sending if analytics is withdrawn, undo only our own stop.
    Object.keys(gaIds).forEach(function (id) {
      var key = 'ga-disable-' + id;
      if (!state.analytics && !w[key]) { w[key] = true; disabledByUs[key] = true; }
      if (state.analytics && disabledByUs[key]) { w[key] = false; delete disabledByUs[key]; }
    });
  }

  function mirrorToLayers() {
    var update = {
      analytics_storage: g(state.analytics),
      ad_storage: g(state.advertising),
      ad_user_data: g(state.advertising),
      ad_personalization: g(state.advertising)
    };
    Object.keys(layers).forEach(function (name) {
      layers[name].push((function () { return arguments; })('consent', 'update', update));
    });
  }

  function activateStatic() {
    var nodes = d.querySelectorAll('script[type="text/plain"][data-dc-category]');
    for (var i = 0; i < nodes.length; i++) {
      var old = nodes[i];
      var cat = old.getAttribute('data-dc-category');
      if (!allowed(cat === 'analytics' || cat === 'advertising' ? cat : 'gtm')) continue;
      var src = old.getAttribute('src') || '';
      if (/googletagmanager\.com\/gtag\/js/i.test(src)) rememberGtag(src);
      var s = d.createElement('script');
      for (var j = 0; j < old.attributes.length; j++) {
        var a = old.attributes[j];
        if (a.name === 'type' || a.name === 'data-dc-category') continue;
        s.setAttribute(a.name, a.value);
      }
      s.setAttribute('data-dc-passthrough', '1');
      if (old.parentNode) old.parentNode.replaceChild(s, old);
    }
  }

  function release() {
    var pending = held.slice(), i;
    held.length = 0;
    for (i = 0; i < pending.length; i++) {
      if (allowed(pending[i].cat)) {
        try { pending[i].run(); } catch (e) {
          try { (d.head || d.documentElement).appendChild(pending[i].node); } catch (e2) {}
        }
      } else {
        held.push(pending[i]);
      }
    }
    activateStatic();
  }

  function setState(analytics, advertising) {
    var prev = { analytics: state.analytics, advertising: state.advertising };
    if (typeof analytics === 'boolean') state.analytics = analytics;
    if (typeof advertising === 'boolean') state.advertising = advertising;
    if (prev.analytics === state.analytics && prev.advertising === state.advertising) return;
    mirrorToLayers();
    sendVendorSignals(prev);
    release();
    for (var i = 0; i < listeners.length; i++) {
      try { listeners[i](api.state()); } catch (e) {}
    }
  }

  // ---- 4. watch for the visitor's choice ----
  function fromConsentCommand(item) {
    if (!item || item.length < 3) return;
    if (item[0] !== 'consent' || item[1] !== 'update') return;
    var v = item[2] || {};
    setState(
      v.analytics_storage ? v.analytics_storage === 'granted' : undefined,
      v.ad_storage ? v.ad_storage === 'granted' : undefined
    );
  }

  var rawPush = w.dataLayer.push;
  w.dataLayer.push = function () {
    var out = rawPush.apply(this, arguments);
    for (var i = 0; i < arguments.length; i++) {
      try { fromConsentCommand(arguments[i]); } catch (e) {}
    }
    return out;
  };

  // Consent that was already pushed before this script ran (none expected).
  for (var k = 0; k < w.dataLayer.length; k++) fromConsentCommand(w.dataLayer[k]);

  // The banner's own event. detail.accepted / detail.rejected list the categories.
  d.addEventListener('cookieyes_consent_update', function (e) {
    var detail = (e && e.detail) || {};
    var acc = detail.accepted || [], rej = detail.rejected || [];
    function pick(names) {
      for (var i = 0; i < names.length; i++) {
        if (acc.indexOf(names[i]) !== -1) return true;
        if (rej.indexOf(names[i]) !== -1) return false;
      }
      return undefined;
    }
    setState(pick(['analytics']), pick(['advertisement']));
  });

  d.addEventListener('DOMContentLoaded', activateStatic);

  // "Cookie settings" links carry the banner's own class; keep "#" from scrolling.
  d.addEventListener('click', function (e) {
    var el = e.target && e.target.closest && e.target.closest('.dc-cookie-settings');
    if (el) e.preventDefault();
  });

  var api = {
    version: 1,
    allowed: function (cat) { return allowed(cat === 'marketing' ? 'advertising' : cat); },
    state: function () { return { analytics: state.analytics, advertising: state.advertising }; },
    onChange: function (fn) { if (typeof fn === 'function') listeners.push(fn); }
  };
  w.dcConsent = api;

  // ---- 3. load the hosted banner ----
  if (/^[a-f0-9]{16,}$/i.test(CONSENT_TOOL_ID)) {
    var cmp = d.createElement('script');
    cmp.src = 'https://cdn-cookieyes.com/client_data/' + CONSENT_TOOL_ID + '/script.js';
    cmp.async = true;
    cmp.setAttribute('data-dc-passthrough', '1');
    (d.head || d.documentElement).appendChild(cmp);
  } else if (w.console && w.console.warn) {
    w.console.warn('dc-consent: CONSENT_TOOL_ID is not set. No banner will load and trackers stay off.');
  }
})(window, document);
