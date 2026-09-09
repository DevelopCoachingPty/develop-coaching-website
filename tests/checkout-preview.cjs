// Local browser fixture only: no Stripe requests or real payments.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../www');
http.createServer((req,res)=>{
 if(req.url.startsWith('/api/ai-builders-checkout-status')){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({status:'paid',amount:4500,currency:'gbp'}));return;}
 if(req.url.startsWith('/api/create-ai-builders-checkout')){res.writeHead(503,{'Content-Type':'application/json'});res.end('{}');return;}
 let name=path.join(root,decodeURIComponent(req.url.split('?')[0]));if(name.endsWith('/'))name+='index.html';if(!name.startsWith(root+'/')){res.writeHead(403);res.end();return;}
 fs.readFile(name,(e,data)=>{if(e){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',name.endsWith('.html')?'text/html':name.endsWith('.png')?'image/png':name.endsWith('.webm')?'video/webm':'application/octet-stream');res.end(data);});
}).listen(4198,'127.0.0.1');
