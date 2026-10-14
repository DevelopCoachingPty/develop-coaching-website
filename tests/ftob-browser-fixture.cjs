// Local browser fixture: checkout navigation is prevented; pixels are stubbed.
// The Google library is real. Block Analytics collection through browser CDP before opening the page.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '../www');
http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1:4198');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  if (url.pathname === '/empty') return res.end('<title>Tracking fixture ready</title><h1>Tracking fixture ready</h1>');
  if (url.pathname === '/assets/ftob-attribution.js') {
    res.setHeader('Content-Type', 'text/javascript');
    return res.end(fs.readFileSync(path.join(root, 'assets/ftob-attribution.js')));
  }
  if (!['/fill-the-order-book/', '/fill-the-order-book-thank-you/'].includes(url.pathname)) {res.statusCode = 204; return res.end();}
  res.setHeader('Content-Security-Policy', "img-src 'self' data:; media-src 'self'; frame-src 'none';");
  const slug = url.pathname === '/fill-the-order-book-thank-you/' ? 'fill-the-order-book-thank-you' : 'fill-the-order-book';
  let html = fs.readFileSync(path.join(root, slug, 'index.html'), 'utf8');
  html = html.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/g, (whole, script) => {
    if (script.includes("fbq('init'")) {
      // Keep the return instrumentation, but prevent loading the real Meta library.
      return '<script>window.fixtureMeta=[];function fbq(){window.fixtureMeta.push(Array.from(arguments));}' +
        (script.includes('// Keep unverified return visits') ? script.slice(script.indexOf('// Keep unverified return visits')) : '') + '</script>';
    }
    if (whole.includes('src=') && !whole.includes('googletagmanager.com') && !whole.includes('/assets/ftob-attribution.js')) return '';
    return whole;
  });
  html = html.replace('</body>', `<aside style="position:fixed;bottom:0;left:0;right:0;max-height:40vh;overflow:auto;background:white;color:black;z-index:99999;padding:10px"><strong>LOCAL TEST: no checkout navigation; Analytics collection must be blocked</strong><pre id="tracking-proof"></pre></aside><script>
    document.addEventListener('click',function(event){if(event.target.closest && event.target.closest('a[href*="buy.stripe.com"]'))event.preventDefault();},true);
    setInterval(function(){document.getElementById('tracking-proof').textContent=JSON.stringify({google:(window.dataLayer||[]).filter(function(x){return x && (x[0]==='config'||x[0]==='event');}).map(function(x){return Array.from(x);}),meta:window.fixtureMeta||[]},null,2);},100);
  </script></body>`);
  res.end(html);
}).listen(4198, '127.0.0.1', () => console.log('Tracking fixture http://127.0.0.1:4198/empty'));
