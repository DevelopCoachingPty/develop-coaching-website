/* enquiry-attribution.js - which page, search or AI tool brought in each enquiry
 *
 * Loaded synchronously in <head>, straight after dc-consent.js, on every page
 * that embeds a FlowBuild (GoHighLevel) form or booking calendar, or the
 * /busy-trap/ application. It does three things:
 *
 *   1. Works out the visit's first touch: the first landing page, UTM source,
 *      medium and campaign, the external referrer, and an AI-referrer flag
 *      (ChatGPT, Perplexity, Gemini, Copilot, Claude and similar).
 *   2. Passes those values into the FlowBuild iframes as query parameters
 *      (dc_landing_page, dc_utm_source, dc_utm_medium, dc_utm_campaign,
 *      dc_referrer, dc_ai_referrer, dc_enquiry_page). Each form carries a
 *      hidden field with the same "query key", so the values land on the
 *      contact in GHL as "Enquiry ..." custom fields.
 *   3. Pushes a GA4 `generate_lead` event (the enquiry key event) to the
 *      site's existing data layer when a form or booking is actually
 *      completed. FlowBuild signals a completed form with a
 *      ["set-sticky-contacts", "embedded_iframe_<id>", ...] message and a
 *      completed booking with ["msgsndr-booking-complete", {...}].
 *
 * Storage: the first touch is kept in sessionStorage for the visit. It is only
 * written to localStorage (so a return visit within 90 days keeps the original
 * source) once the visitor has allowed analytics cookies, and it is removed
 * from localStorage if they withdraw. If storage is blocked the current page's
 * values are still passed, so nothing breaks; only cross-page memory is lost.
 *
 * No personal data is read, stored or sent. Query strings are stripped from
 * the landing page and referrer, so an email address in a link cannot leak.
 * The GA4 push uses the data layer that already owns the Google tag and
 * consent; nothing is sent unless analytics consent is given.
 */
(function (w, d) {
  'use strict';
  if (w.dcAttribution) return;

  var KEY = 'dc_attr_v1';
  var TTL_MS = 90 * 24 * 60 * 60 * 1000;
  var MAX = 200;
  var GA_ID = 'G-PXT2VCVFLW';
  var FB_ORIGIN = 'https://link.flow-build.com';
  var WIDGET_RE = /^\/widget\/(form|survey|quiz|booking)\/([A-Za-z0-9]+)\/?$/;
  var OWN_HOSTS = /(^|\.)develop-coaching\.com$/i;

  // Lead labels for the reports. Any other FlowBuild form still counts as a
  // lead; it is just labelled by its id.
  var FORMS = {
    USUhO24FJYoYAYFPx4Lt: ['contact', 'Scale Session enquiry'],
    LrwamDnwkXRzgaIuSFn2: ['newsletter', 'Newsletter UK Subscribe'],
    DM8MfGpKqOlTWsW9Mvh1: ['lead_magnet', 'Download UK Book'],
    OuWMAAl7r2K93aA7W3xm: ['lead_magnet', 'The Perfect Project registration'],
    Ftx9UWAyx0xmzdt9n4KN: ['lead_magnet', '30-Day Construction CEO Experience'],
    zXUkPVoGKzRyirwYa0Ck: ['booking', 'Scale Session booking']
  };

  // Hostname (or a parent domain of it) -> AI engine label.
  var AI_HOSTS = [
    ['chatgpt.com', 'chatgpt'], ['chat.openai.com', 'chatgpt'], ['openai.com', 'chatgpt'],
    ['perplexity.ai', 'perplexity'],
    ['gemini.google.com', 'gemini'], ['bard.google.com', 'gemini'], ['aistudio.google.com', 'gemini'],
    ['copilot.microsoft.com', 'copilot'], ['copilot.cloud.microsoft', 'copilot'],
    ['claude.ai', 'claude'],
    ['you.com', 'you'], ['phind.com', 'phind'],
    ['chat.deepseek.com', 'deepseek'], ['deepseek.com', 'deepseek'],
    ['grok.com', 'grok'], ['meta.ai', 'meta_ai'], ['chat.mistral.ai', 'mistral'],
    ['poe.com', 'poe'], ['kagi.com', 'kagi']
  ];
  // utm_source values AI tools add themselves (ChatGPT adds utm_source=chatgpt.com).
  var AI_SOURCES = {
    'chatgpt.com': 'chatgpt', chatgpt: 'chatgpt', openai: 'chatgpt',
    'perplexity.ai': 'perplexity', perplexity: 'perplexity',
    gemini: 'gemini', 'gemini.google.com': 'gemini',
    copilot: 'copilot', 'copilot.microsoft.com': 'copilot',
    'claude.ai': 'claude', claude: 'claude'
  };

  function clip(v) {
    v = String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f]/g, '').trim();
    return v.length > MAX ? v.slice(0, MAX) : v;
  }

  // Campaign labels: keep them readable but never let free text through.
  function label(v) {
    v = clip(v).toLowerCase();
    if (!v) return '';
    if (v.indexOf('@') !== -1) return '';
    return v.replace(/[^a-z0-9._\-+ ]/g, '').slice(0, 100);
  }

  function aiFromHost(host) {
    host = String(host || '').toLowerCase().replace(/^www\./, '');
    for (var i = 0; i < AI_HOSTS.length; i++) {
      var h = AI_HOSTS[i][0];
      if (host === h || host.slice(-(h.length + 1)) === '.' + h) return AI_HOSTS[i][1];
    }
    return '';
  }

  function parseUrl(u) {
    try { return new URL(u, w.location.href); } catch (e) { return null; }
  }

  // origin + path only: drops query strings and fragments.
  function bare(u) {
    var p = parseUrl(u);
    if (!p || (p.protocol !== 'https:' && p.protocol !== 'http:')) return '';
    return clip(p.origin + p.pathname);
  }

  function isOwnHost(host) {
    return OWN_HOSTS.test(host) || host === w.location.hostname;
  }

  function currentTouch() {
    var q;
    try { q = new URLSearchParams(w.location.search); } catch (e) { q = { get: function () { return null; } }; }
    var ref = parseUrl(d.referrer);
    var external = !!(ref && ref.hostname && !isOwnHost(ref.hostname));
    var src = label(q.get('utm_source'));
    var ai = aiFromHost(external ? ref.hostname : '') || AI_SOURCES[src] || '';
    return {
      lp: bare(w.location.href),
      src: src,
      med: label(q.get('utm_medium')),
      camp: label(q.get('utm_campaign')),
      ref: external ? bare(d.referrer) : '',
      ai: ai,
      // A visit starts a new touch only when it arrives from outside: a
      // campaign link, another site, or nothing at all (typed or bookmarked).
      fresh: !!(src || external || !d.referrer),
      at: Date.now()
    };
  }

  function store(kind) {
    try {
      var s = w[kind];
      var probe = '__dc_attr_probe__';
      s.setItem(probe, '1');
      s.removeItem(probe);
      return s;
    } catch (e) { return null; }
  }

  function read(s) {
    if (!s) return null;
    try {
      var v = JSON.parse(s.getItem(KEY) || 'null');
      if (!v || typeof v !== 'object' || typeof v.at !== 'number') return null;
      if (Date.now() - v.at > TTL_MS) { s.removeItem(KEY); return null; }
      return v;
    } catch (e) { return null; }
  }

  function write(s, v) {
    if (!s) return;
    try { s.setItem(KEY, JSON.stringify(v)); } catch (e) {}
  }

  function analyticsAllowed() {
    if (w.navigator && (w.navigator.globalPrivacyControl || w.navigator.doNotTrack === '1')) return false;
    return !!(w.dcConsent && w.dcConsent.allowed('analytics'));
  }

  var session = store('sessionStorage');
  var local = store('localStorage');
  var now = currentTouch();

  // First touch wins. The visit's own record is kept for the whole session;
  // a consented 90-day record carries it across visits.
  var first = read(session) || (analyticsAllowed() ? read(local) : null);
  if (!first) {
    first = now.fresh ? now : {
      // Arrived from another page of this site with nothing remembered
      // (storage blocked, or a new tab). Be honest rather than guess.
      lp: '', src: now.src, med: now.med, camp: now.camp, ref: '', ai: now.ai, at: now.at
    };
  }
  delete first.fresh;
  write(session, first);

  function persistIfAllowed() {
    if (analyticsAllowed()) write(local, first);
    else if (local) { try { local.removeItem(KEY); } catch (e) {} }
  }
  persistIfAllowed();
  if (w.dcConsent && typeof w.dcConsent.onChange === 'function') w.dcConsent.onChange(persistIfAllowed);

  function params() {
    return {
      dc_landing_page: first.lp || '',
      dc_utm_source: first.src || '',
      dc_utm_medium: first.med || '',
      dc_utm_campaign: first.camp || '',
      dc_referrer: first.ref || (first.lp ? '(direct)' : ''),
      dc_ai_referrer: first.ai || 'none',
      dc_enquiry_page: now.lp
    };
  }

  function widgetOf(src) {
    var u = parseUrl(src);
    if (!u || u.origin !== FB_ORIGIN) return null;
    var m = WIDGET_RE.exec(u.pathname);
    return m ? { url: u, kind: m[1], id: m[2] } : null;
  }

  // ---- 2. hand the values to FlowBuild iframes ----
  function tagFrame(f) {
    if (!f || f.tagName !== 'IFRAME' || f.getAttribute('data-dc-attr') === '1') return;
    var wd = widgetOf(f.getAttribute('src') || '');
    if (!wd) return;
    var p = params();
    var changed = false;
    for (var k in p) {
      if (!p[k]) continue;
      if (wd.url.searchParams.get(k) === p[k]) continue;
      wd.url.searchParams.set(k, p[k]);
      changed = true;
    }
    f.setAttribute('data-dc-attr', '1');
    if (changed) f.setAttribute('src', wd.url.href);
  }

  function scan(root) {
    var list = (root || d).getElementsByTagName ? (root || d).getElementsByTagName('iframe') : [];
    for (var i = 0; i < list.length; i++) tagFrame(list[i]);
  }

  // Catch each iframe as the parser inserts it, so its src changes as early as
  // possible. The browser may already have started the first request; that
  // one is then abandoned and the form loads with the parameters.
  if (w.MutationObserver) {
    var mo = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var added = records[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var n = added[j];
          if (n.nodeType !== 1) continue;
          if (n.tagName === 'IFRAME') tagFrame(n);
          else if (n.getElementsByTagName) scan(n);
        }
      }
    });
    mo.observe(d.documentElement, { childList: true, subtree: true });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', function () { scan(d); });
  else scan(d);

  // ---- 3. GA4 key event on a completed form or booking ----
  var sent = {};

  function lead(info) {
    info = info || {};
    var id = clip(info.form_id || 'unknown');
    if (sent[id]) return false;
    var known = FORMS[id] || [];
    var dl = w.dataLayer;
    if (!dl || typeof dl.push !== 'function') return false;
    if (!analyticsAllowed()) return false;
    if (w['ga-disable-' + GA_ID]) return false;
    sent[id] = true;
    var p = params();
    // gtag() form (an arguments object), as booking-tracking.js does, so the
    // Google tag already on the page processes it. No second config or client ID.
    function googleEvent() { dl.push(arguments); }
    googleEvent('event', 'generate_lead', {
      send_to: GA_ID,
      transport_type: 'beacon',
      lead_type: clip(info.lead_type || known[0] || 'form'),
      form_id: id,
      form_name: clip(info.form_name || known[1] || id),
      landing_page: p.dc_landing_page,
      ai_referrer: p.dc_ai_referrer,
      first_utm_source: p.dc_utm_source,
      first_utm_medium: p.dc_utm_medium,
      first_utm_campaign: p.dc_utm_campaign
    });
    return true;
  }

  function frameFor(source) {
    var list = d.getElementsByTagName('iframe');
    for (var i = 0; i < list.length; i++) {
      if (list[i].contentWindow === source) return list[i];
    }
    return null;
  }

  w.addEventListener('message', function (e) {
    if (e.origin !== FB_ORIGIN) return;
    var data = e.data;
    if (!Array.isArray(data) || typeof data[0] !== 'string') return;
    var f = frameFor(e.source);
    var wd = f && widgetOf(f.getAttribute('src') || '');
    if (!wd) return;
    if (data[0] === 'set-sticky-contacts') {
      // Only the per-iframe success message; the "_ud" one carries the contact
      // and is ignored. This is sent after FlowBuild has saved the submission.
      if (typeof data[1] !== 'string' || data[1].indexOf('embedded_iframe_') !== 0) return;
      if (wd.kind === 'booking') return;
      lead({ form_id: wd.id, form_name: f.getAttribute('data-form-name') || '' });
    } else if (data[0] === 'msgsndr-booking-complete') {
      if (wd.kind !== 'booking') return;
      lead({ form_id: wd.id, lead_type: 'booking' });
    }
  });

  w.addEventListener('pageshow', function (e) { if (e && e.persisted) sent = {}; });

  // For forms that are not FlowBuild iframes (the /busy-trap/ application).
  w.dcAttribution = {
    version: 1,
    params: params,
    lead: lead
  };
})(window, document);
