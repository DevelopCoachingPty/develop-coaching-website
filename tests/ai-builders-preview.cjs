// Full-page local preview. No provider calls, cards, or real marketing events.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../www');
http.createServer((req,res)=>{
 const url=new URL(req.url,'http://127.0.0.1');
 res.setHeader('Content-Security-Policy',"connect-src 'self'; script-src 'self' 'unsafe-inline'; frame-src https://link.flow-build.com");
 if(url.pathname==='/api/create-ai-builders-checkout'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({clientSecret:'local-fixture',publishableKey:'local-fixture'}));}
 if(url.pathname==='/api/ai-builders-checkout-status'){
  const id=url.searchParams.get('session_id');res.setHeader('Content-Type','application/json');
  if(id==='cs_test_failure'){res.statusCode=502;return res.end('{}');}
  return res.end(JSON.stringify({status:id==='cs_test_pending'?'pending':'paid',event:'ai-for-builders-september-2026',amount:4500,currency:'gbp',transactionId:id,live:false}));
 }
 let file=path.join(root,decodeURIComponent(url.pathname));if(!file.startsWith(root+path.sep)){res.statusCode=403;return res.end();}
 if(url.pathname.endsWith('/'))file=path.join(file,'index.html');
 if(!fs.existsSync(file)){res.statusCode=404;return res.end();}
 const ext=path.extname(file);res.setHeader('Content-Type',({'.html':'text/html','.js':'application/javascript','.png':'image/png','.jpeg':'image/jpeg','.jpg':'image/jpeg','.webm':'video/webm','.mp4':'video/mp4'})[ext]||'application/octet-stream');
 if(ext==='.html'){
 let html=fs.readFileSync(file,'utf8').replace('<script src="https://js.stripe.com/v3/"></script>',`<script>window.Stripe=()=>({initEmbeddedCheckout:async()=>({mount:selector=>{document.querySelector(selector).innerHTML='<div style="padding:40px;color:#414042">Local £45 checkout fixture. No payment is taken.<p><a href="/ai-for-builders-september-2026/thank-you/?session_id=cs_test_paid">Preview verified confirmation</a></p></div>'}})});</script>`);
 // Opening the local design preview directly always shows its simulated paid state.
 // Production HTML and API verification are unchanged.
 if(url.pathname==='/ai-for-builders-september-2026/thank-you/' && !url.searchParams.has('session_id')) {
   html=html.replace('<head>', '<head><script>history.replaceState(null,"",location.pathname+"?session_id=cs_test_paid"+location.hash);</script>');
 }
 return res.end(html);
 }
 fs.createReadStream(file).pipe(res);
}).listen(4296,'127.0.0.1',()=>console.log('Safe preview: http://127.0.0.1:4296/ai-for-builders-september-2026/'));
