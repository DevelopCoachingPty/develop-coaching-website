/* Campaign attribution is first-touch for this workshop. Never put customer data in UTMs. */
(function () {
  'use strict';
  const event = 'ai-for-builders-september-2026', gaId = 'G-PXT2VCVFLW';
  const prefix = 'dc-ai-builders-sep-2026:', fields = ['source', 'medium', 'campaign', 'content', 'term'];
  const clean = value => typeof value === 'string' && /^[a-z0-9][a-z0-9_-]{0,49}$/.test(value.toLowerCase()) ? value.toLowerCase() : '';
  const sanitise = value => Object.fromEntries(fields.map(field => [field, clean(value?.[field]) || (field === 'source' ? 'direct' : '')]));
  function read(storage, key) { try { return storage.getItem(prefix + key); } catch { return null; } }
  function write(storage, key, value) { try { storage.setItem(prefix + key, value); return true; } catch { return false; } }
  // Accessing storage itself may throw in privacy modes.
  let local, session; try { local = window.localStorage; } catch {} try { session = window.sessionStorage; } catch {}
  let consent = read(local, 'consent'), attribution;
  const params = new URLSearchParams(location.search);
  try { attribution = JSON.parse(read(session, 'attribution') || (consent === 'yes' && read(local, 'attribution')) || 'null'); } catch {}
  if (!attribution || typeof attribution !== 'object') attribution = Object.fromEntries(fields.map(field => [field, params.get('utm_' + field)]));
  attribution = sanitise(attribution);
  write(session, 'attribution', JSON.stringify(attribution));
  let domReady = false, intent = false, paid = null, loaded = false, viewed = false, started = false;
  const sent = new Set();
  const production = /^(www\.)?develop-coaching\.com$/.test(location.hostname);
  const confirmation = location.pathname.includes('/thank-you/');
  const legacyReturn = !confirmation && (params.has('session_id') || params.get('checkout') === 'complete');
  const privacyBlocked = () => navigator.globalPrivacyControl || navigator.doNotTrack === '1';
  const campaign = value => ({campaign_source:value.source,campaign_medium:value.medium,campaign_name:value.campaign,campaign_content:value.content,campaign_term:value.term});
  const item = {item_id:event,item_name:'AI for Builders',price:45,quantity:1};
  function google(name, details = {}) {
    window.gtag('event', name, {send_to:gaId,workshop_id:event,...details});
  }
  function flush() {
    // Wait until deferred confirmation.js has removed payment references from the URL.
    if (!domReady || legacyReturn || consent !== 'yes' || privacyBlocked()) return;
    write(local, 'attribution', JSON.stringify(attribution));
    if (!production) return;
    if (!loaded) {
      loaded = true;
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
      window['ga-disable-' + gaId] = false;
      window.gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
      window.gtag('consent','update',{analytics_storage:'granted'});
      window.gtag('js',new Date());
      // Never transmit the query string, fragment, payment reference or incoming referrer.
      window.gtag('config',gaId,{send_page_view:false,page_location:'https://develop-coaching.com' + location.pathname,page_referrer:'',allow_google_signals:false,allow_ad_personalization_signals:false,...campaign(attribution)});
      const ga = document.createElement('script'); ga.async = true; ga.src = 'https://www.googletagmanager.com/gtag/js?id=' + gaId; document.head.append(ga);
      const fbq = window.fbq = window.fbq || function () { fbq.callMethod ? fbq.callMethod.apply(fbq, arguments) : fbq.queue.push(arguments); };
      fbq.queue = fbq.queue || []; fbq.loaded = true; fbq.version = '2.0'; window._fbq = fbq;
      const script = document.createElement('script'); script.async = true; script.src = 'https://connect.facebook.net/en_US/fbevents.js'; document.head.append(script);
      fbq('init', '260128381862353');
    }
    if (!viewed) {
      viewed = true; window.fbq('track', 'PageView'); google('page_view');
      if (!confirmation) {
        window.fbq('track', 'ViewContent', {content_name:'AI for Builders September 2026',value:45,currency:'GBP'});
        google('view_item',{value:45,currency:'GBP',items:[item]});
      }
    }
    if (intent && !started && !confirmation) {
      started = true; window.fbq('track', 'InitiateCheckout', {value:45,currency:'GBP'});
      google('begin_checkout',{value:45,currency:'GBP',items:[item]});
    }
    if (!paid || paid.status !== 'paid' || paid.live !== true || !/^cs_live_[a-zA-Z0-9]+$/.test(paid.transactionId)) return;
    const id = paid.transactionId;
    if (sent.has(id) || read(local, 'purchase:' + id) || read(session, 'purchase:' + id)) return;
    // Require durable deduplication before emitting; fail closed if storage is blocked.
    if (!write(local, 'purchase:' + id, '1') && !write(session, 'purchase:' + id, '1')) return;
    sent.add(id);
    window.fbq('track', 'Purchase', {value:45,currency:'GBP',content_name:'AI for Builders September 2026'}, {eventID:id});
    google('purchase',{transaction_id:id,value:45,currency:'GBP',items:[item],...campaign(paid.attribution ? sanitise(paid.attribution) : attribution)});
  }
  window.dcWorkshop = {
    attribution,
    // Loading the automatically mounted form is not evidence of customer intent.
    checkoutReady() {},
    verified(data) { paid = data; flush(); }
  };
  document.addEventListener('DOMContentLoaded', () => {
    domReady = true;
    for (const link of document.querySelectorAll('a[href="#register"]')) link.addEventListener('click', () => { intent = true; flush(); });
    const box = document.createElement('aside'); box.setAttribute('aria-label','Tracking preferences');
    box.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:10000;max-height:50vh;overflow:auto;padding:12px 20px;background:#fff;border-top:1px solid #ddd;box-shadow:0 -2px 12px #0002;color:#414042;text-align:center;font:14px Inter,Arial,sans-serif';
    box.hidden = consent === 'yes' || consent === 'no';
    const label = document.createElement('span');label.style.cssText='display:block;margin-bottom:4px;line-height:1.5';
    label.textContent=privacyBlocked()?'Your browser privacy preference keeps tracking off. ':'Allow analytics and marketing tracking to help us measure workshop campaigns? ';
    const yes = document.createElement('button'), no = document.createElement('button'), reopen = document.createElement('button');
    yes.textContent='Allow tracking'; no.textContent='Decline tracking'; reopen.textContent='Tracking preferences';yes.disabled=!!privacyBlocked();
    for (const button of [yes,no,reopen]) { button.type='button';button.style.cssText='margin:6px;padding:10px;border:1px solid #414042;border-radius:5px;background:#fff;color:#414042;cursor:pointer'; }
    function choose(value) {
      consent=value;write(local,'consent',value);box.hidden=true;
      if (value==='no' || privacyBlocked()) {
        try { local.removeItem(prefix+'attribution'); } catch {}
        window['ga-disable-' + gaId] = true;
        if(loaded)window.gtag('consent','update',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
        if(window.fbq)window.fbq('consent','revoke');
      } else {
        window['ga-disable-' + gaId] = false;
        if(loaded)window.gtag('consent','update',{analytics_storage:'granted'});
        if(window.fbq)window.fbq('consent','grant');flush();
      }
    }
    yes.addEventListener('click',()=>choose('yes')); no.addEventListener('click',()=>choose('no'));
    reopen.addEventListener('click',()=>{box.hidden=false;});
    box.append(label,yes,no);document.body.append(box,reopen);flush();
  });
})();
