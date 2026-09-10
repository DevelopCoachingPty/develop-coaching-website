(async function () {
  'use strict';
  const title = document.getElementById('confirmation-title'), message = document.getElementById('confirmation-message'), retry = document.getElementById('confirmation-retry');
  const id = new URLSearchParams(location.search).get('session_id');
  // Remove the payment reference before any optional analytics or third-party video loads.
  history.replaceState(null, '', location.pathname);
  let session; try { session = window.sessionStorage; } catch {}
  const key = 'dc-ai-builders-sep-2026:confirmation';
  let reference = id; if (!reference) { try { reference = session.getItem(key); } catch {} }
  if (id && /^cs_(test_|live_)[a-zA-Z0-9]+$/.test(id)) { try { session.setItem(key,id); } catch {} }
  const video = document.querySelector('video'); video.addEventListener('play',()=>video.parentElement.classList.add('is-playing'));video.addEventListener('ended',()=>video.parentElement.classList.remove('is-playing'));
  async function check() {
    retry.hidden = true; title.textContent = 'Checking your payment';
    if (!reference || !/^cs_(test_|live_)[a-zA-Z0-9]+$/.test(reference)) { title.textContent='We need your booking reference';message.textContent='Open the confirmation link from your Stripe checkout. If you have already paid, do not pay again. Contact us for help.';return; }
    try {
      const response = await fetch('/api/ai-builders-checkout-status?session_id='+encodeURIComponent(reference), {cache:'no-store',signal:AbortSignal.timeout(15000)});
      const data = await response.json(); if (!response.ok) throw Error();
      if (data.status === 'paid' && data.event === 'ai-for-builders-september-2026' && data.amount === 4500 && data.currency === 'gbp' && data.transactionId === reference) {
        title.textContent='You’re booked in.';message.textContent='Payment confirmed. We’ve received £45 for your AI for Builders ticket.';document.getElementById('confirmed-details').hidden=false;
        window.dcWorkshop.verified(data);
      } else { title.textContent='Your payment is still being confirmed';message.textContent='Please check again shortly. Do not pay again.';retry.hidden=false; }
    } catch { title.textContent='We could not confirm your payment just now';message.textContent='If you have paid, do not pay again. Check again or contact us for help.';retry.hidden=false; }
  }
  retry.addEventListener('click',check); await check();
})();
