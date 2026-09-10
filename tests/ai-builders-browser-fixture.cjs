// Local-only browser fixture: never connects to Stripe or creates a real session.
const http = require('node:http');
const fs = require('node:fs');
const html = fs.readFileSync(require('node:path').join(__dirname, '../www/ai-for-builders-september-2026/index.html'), 'utf8');
const source = html.slice(html.indexOf('async function mountCheckout(){'), html.indexOf('const target=new Date'));
http.createServer((req, res) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.end(`<!doctype html><title>Checkout initialization fixture</title><h1>Local checkout fixture — no real payments</h1><section id="register"><div id="stripe-checkout"><div id="checkout-status"></div></div><div id="stripe-fallback"></div></section><output id="requests">0 session requests</output><script>
  let calls=0;
  window.fetch=async url=>{if(url.includes('create-'))document.getElementById('requests').textContent=(++calls)+' session requests';return {ok:!location.search.includes('fail'),json:async()=>url.includes('checkout-status')?{status:'paid'}:{clientSecret:'fixture',publishableKey:'fixture'}}};
  window.Stripe=()=>({initEmbeddedCheckout:async()=>({mount:selector=>{document.querySelector(selector).innerHTML='<h2>£45 checkout fixture loaded automatically</h2><label>Email <input type="email"></label><label>Card number <input placeholder="Test fixture only"></label>'}})});
  ${source}</script>`);
}).listen(4197, '127.0.0.1', () => console.log('Fixture: http://127.0.0.1:4197'));
