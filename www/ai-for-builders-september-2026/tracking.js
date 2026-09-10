/* Campaign attribution is first-touch for this workshop. Never put customer data in UTMs. */
(function () {
  'use strict';
  const prefix = 'dc-ai-builders-sep-2026:', fields = ['source', 'medium', 'campaign', 'content', 'term'];
  const clean = value => typeof value === 'string' && /^[a-z0-9][a-z0-9_-]{0,49}$/.test(value.toLowerCase()) ? value.toLowerCase() : '';
  function read(storage, key) { try { return storage.getItem(prefix + key); } catch { return null; } }
  function write(storage, key, value) { try { storage.setItem(prefix + key, value); return true; } catch { return false; } }
  // Accessing storage itself may throw in privacy modes.
  let local, session; try { local = window.localStorage; } catch {} try { session = window.sessionStorage; } catch {}
  let consent = read(local, 'consent'), attribution;
  const params = new URLSearchParams(location.search);
  try { attribution = JSON.parse(read(session, 'attribution') || (consent === 'yes' && read(local, 'attribution')) || 'null'); } catch {}
  if (!attribution || typeof attribution !== 'object') attribution = Object.fromEntries(fields.map(field => [field, clean(params.get('utm_' + field)) || (field === 'source' ? 'direct' : '')]));
  attribution = Object.fromEntries(fields.map(field => [field, clean(attribution[field]) || (field === 'source' ? 'direct' : '')]));
  write(session, 'attribution', JSON.stringify(attribution));
  let ready = false, paid = null, loaded = false, viewed = false, started = false;
  const sent = new Set();
  const production = /^(www\.)?develop-coaching\.com$/.test(location.hostname);
  const confirmation = location.pathname.includes('/thank-you/');
  function flush() {
    if (consent !== 'yes' || navigator.globalPrivacyControl || navigator.doNotTrack === '1') return;
    write(local, 'attribution', JSON.stringify(attribution));
    if (!production) return;
    if (!loaded) {
      loaded = true;
      const fbq = window.fbq = window.fbq || function () { fbq.callMethod ? fbq.callMethod.apply(fbq, arguments) : fbq.queue.push(arguments); };
      fbq.queue = fbq.queue || []; fbq.loaded = true; fbq.version = '2.0'; window._fbq = fbq;
      const script = document.createElement('script'); script.async = true; script.src = 'https://connect.facebook.net/en_US/fbevents.js'; document.head.append(script);
      fbq('init', '260128381862353');
    }
    if (!viewed) { viewed = true; window.fbq('track', 'PageView'); if (!confirmation) window.fbq('track', 'ViewContent', {content_name:'AI for Builders September 2026',value:45,currency:'GBP'}); }
    if (ready && !started) { started = true; window.fbq('track', 'InitiateCheckout', {value:45,currency:'GBP'}); }
    if (!paid || paid.status !== 'paid' || paid.live !== true || !/^cs_live_[a-zA-Z0-9]+$/.test(paid.transactionId)) return;
    const id = paid.transactionId;
    if (sent.has(id) || read(local, 'purchase:' + id) || read(session, 'purchase:' + id)) return;
    // Require durable deduplication before emitting; fail closed if storage is blocked.
    if (!write(local, 'purchase:' + id, '1') && !write(session, 'purchase:' + id, '1')) return;
    sent.add(id);
    window.fbq('track', 'Purchase', {value:45,currency:'GBP',content_name:'AI for Builders September 2026'}, {eventID:id});
    if (typeof window.gtag === 'function') window.gtag('event','purchase',{transaction_id:id,value:45,currency:'GBP',items:[{item_id:'ai-for-builders-september-2026',item_name:'AI for Builders',price:45,quantity:1}]});
  }
  window.dcWorkshop = { attribution, checkoutReady() { ready = true; flush(); }, verified(data) { paid = data; flush(); } };
  document.addEventListener('DOMContentLoaded', () => {
    const box = document.createElement('aside'); box.setAttribute('aria-label','Tracking preferences');
    box.style.cssText='padding:18px 24px;background:#fff;border-top:1px solid #ddd;color:#414042;text-align:center;font:14px Inter,Arial,sans-serif';
    const label = document.createElement('span'); label.textContent='Allow marketing tracking to help us measure workshop campaigns? ';
    const yes = document.createElement('button'), no = document.createElement('button'); yes.textContent='Allow tracking'; no.textContent='Decline tracking';
    for (const button of [yes,no]) { button.type='button';button.style.cssText='margin:6px;padding:10px;border:1px solid #414042;border-radius:5px;background:#fff;color:#414042;cursor:pointer'; }
    function choose(value) { consent=value;write(local,'consent',value);label.textContent=value==='yes'?'Marketing tracking allowed. ':'Marketing tracking declined. '; if (value==='no') { try { local.removeItem(prefix+'attribution'); } catch {} if(window.fbq)window.fbq('consent','revoke'); } else { if(window.fbq)window.fbq('consent','grant');flush(); } }
    yes.addEventListener('click',()=>choose('yes')); no.addEventListener('click',()=>choose('no'));box.append(label,yes,no);document.body.append(box);flush();
  });
})();
