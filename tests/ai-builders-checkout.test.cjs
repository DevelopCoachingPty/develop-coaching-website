const test = require('node:test');
const assert = require('node:assert/strict');
const create = require('../www/api/create-ai-builders-checkout');
const status = require('../www/api/ai-builders-checkout-status');
const env = { STRIPE_SECRET_KEY: 'sk_test_mock', STRIPE_PUBLISHABLE_KEY: 'pk_test_mock', STRIPE_AI_BUILDERS_PRICE_ID: 'price_mock' };
const price = { active:true, product:'prod_T9GTRdidVpjXVZ', type:'one_time', currency:'gbp', unit_amount:4500 };
function response(){return {headers:{},setHeader(k,v){this.headers[k]=v;},status(n){this.code=n;return this;},json(v){this.body=v;return this;}};}
const request = {method:'POST',headers:{host:'develop-coaching.com',origin:'https://develop-coaching.com'},body:{attemptId:'01234567-8901-2345-6789-012345678901'}};
test('checkout contract and idempotent retries',async()=>{
 Object.assign(process.env,env); const calls=[];
 global.fetch=async(url,options)=>{calls.push({url,options});return {ok:true,json:async()=>url.includes('/prices/')?price:{client_secret:'mock_secret'}};};
 for(let i=0;i<2;i++){const res=response();await create(request,res);assert.equal(res.code,200);}
 assert.equal(calls[1].options.headers['Idempotency-Key'],calls[3].options.headers['Idempotency-Key']);
 const body=calls[1].options.body;assert.equal(body.get('metadata[event]'),'ai-for-builders-september-2026');assert.equal(body.get('line_items[0][quantity]'),'1');assert.equal(body.get('payment_method_types[0]'),'card');
});
test('reject wrong price, recurring, inactive, currency; never create session',async()=>{
 for(const override of [{unit_amount:4600},{product:'wrong'},{type:'recurring'},{recurring:{}},{active:false},{currency:'aud'}]){
  let count=0;global.fetch=async()=>{count++;return {ok:true,json:async()=>({...price,...override})};};
  const res=response();await create(request,res);assert.equal(res.code,503);assert.equal(count,1);
 }
});
test('reject foreign origin and malformed attempt before Stripe',async()=>{
 global.fetch=async()=>{throw Error('must not call');};
 for(const req of [{...request,headers:{...request.headers,origin:'https://evil.example'}},{...request,body:{}},{...request,body:'{'}]){const res=response();await create(req,res);assert.ok([400,403].includes(res.code));}
});
const paid={mode:'payment',metadata:{event:'ai-for-builders-september-2026'},amount_total:4500,currency:'gbp',line_items:{data:[{quantity:1,price:{id:'price_mock'}}]},status:'complete',payment_status:'paid',customer_details:{email:'private@example.com'}};
test('verified paid return exposes no PII; pending is not paid',async()=>{
 for(const [change,expected] of [[{},'paid'],[{payment_status:'unpaid'},'pending'],[{status:'open'},'pending']]){global.fetch=async()=>({ok:true,json:async()=>({...paid,...change})});const res=response();await status({method:'GET',query:{session_id:'cs_test_example'}},res);assert.equal(res.body.status,expected);assert.equal(JSON.stringify(res.body).includes('private'),false);assert.equal(res.headers['Cache-Control'],'no-store');}
});
test('foreign event, wrong total and wrong product cannot confirm',async()=>{
 for(const change of [{metadata:{event:'other'}},{amount_total:1},{currency:'usd'},{line_items:{data:[{quantity:1,price:{id:'other'}}]}}]){global.fetch=async()=>({ok:true,json:async()=>({...paid,...change})});const res=response();await status({method:'GET',query:{session_id:'cs_test_example'}},res);assert.equal(res.code,400);}
});
test('provider failure returns controlled unavailable response',async()=>{global.fetch=async()=>{throw Error('provider secret');};const res=response();await create(request,res);assert.equal(res.code,502);assert.equal(JSON.stringify(res.body).includes('secret'),false);});
test('all five campaign labels reach session and payment intent metadata with dedicated return URL',async()=>{
 Object.assign(process.env,env);const calls=[];global.fetch=async(url,options)=>{calls.push({url,options});return {ok:true,json:async()=>url.includes('/prices/')?price:{client_secret:'mock_secret'}};};
 const attribution={source:'facebook',medium:'paid_social',campaign:'ai_sep_2026',content:'greg_video',term:'builders'};
 const res=response();await create({...request,body:{...request.body,attribution}},res);assert.equal(res.code,200);
 const body=calls[1].options.body;for(const [field,value] of Object.entries(attribution)){assert.equal(body.get(`metadata[utm_${field}]`),value);assert.equal(body.get(`payment_intent_data[metadata][utm_${field}]`),value);}
 assert.equal(body.get('return_url'),'https://develop-coaching.com/ai-for-builders-september-2026/thank-you/?session_id={CHECKOUT_SESSION_ID}');
 assert.deepEqual(Object.keys(res.body).sort(),['clientSecret','publishableKey']);
});
test('metadata allowlist drops PII-shaped and arbitrary fields',async()=>{
 let params;global.fetch=async(url,options)=>{if(!url.includes('/prices/'))params=options.body;return {ok:true,json:async()=>url.includes('/prices/')?price:{client_secret:'mock_secret'}};};
 const res=response();await create({...request,body:{...request.body,attribution:{source:'private@example.com',medium:'<script>',campaign:'x'.repeat(51),content:'valid-slug',term:'two words',email:'private@example.com'}}},res);
 assert.equal(res.code,200);assert.equal(params.get('metadata[utm_source]'),'direct');for(const field of ['medium','campaign','term'])assert.equal(params.get(`metadata[utm_${field}]`),'');assert.equal(params.get('metadata[utm_content]'),'valid-slug');assert.equal(params.has('metadata[email]'),false);assert.equal(params.toString().includes('private'),false);
});
test('verified response exposes only contract and allowlisted campaign metadata',async()=>{
 global.fetch=async()=>({ok:true,json:async()=>({...paid,livemode:true,customer:'cus_private',metadata:{...paid.metadata,utm_source:'facebook',utm_medium:'paid_social',utm_campaign:'sep',utm_content:'video',utm_term:'builders',email:'private@example.com'}})});
 const res=response();await status({method:'GET',query:{session_id:'cs_live_fixture123'}},res);
 assert.equal(res.body.transactionId,'cs_live_fixture123');assert.equal(res.body.live,true);assert.deepEqual(res.body.attribution,{source:'facebook',medium:'paid_social',campaign:'sep',content:'video',term:'builders'});assert.equal(JSON.stringify(res.body).includes('private'),false);
 assert.deepEqual(Object.keys(res.body).sort(),['amount','attribution','currency','event','live','status','transactionId']);
});
test('status rejects quantity, multiple lines, foreign mode and malformed references',async()=>{
 for(const change of [{mode:'subscription'},{line_items:{data:[{quantity:2,price:{id:'price_mock'}}]}},{line_items:{data:[paid.line_items.data[0],paid.line_items.data[0]]}}]) {
  global.fetch=async()=>({ok:true,json:async()=>({...paid,...change})});const res=response();await status({method:'GET',query:{session_id:'cs_test_fixture123'}},res);assert.equal(res.code,400);
 }
 global.fetch=async()=>{throw Error('should never call');};for(const id of [undefined,'arbitrary','cs_test_../private',['cs_test_a']]){const res=response();await status({method:'GET',query:{session_id:id}},res);assert.equal(res.code,400);}
});
test('status handles unavailable provider without leaking error text',async()=>{
 for(const failure of ['network','json','http']) {
  global.fetch=async()=>{if(failure==='network')throw Error('secret');return {ok:failure!=='http',json:async()=>{if(failure==='json')throw Error('secret');return {error:'secret'};}};};
  const res=response();await status({method:'GET',query:{session_id:'cs_test_fixture123'}},res);assert.ok([400,502].includes(res.code));assert.equal(JSON.stringify(res.body).includes('secret'),false);assert.equal(res.headers['Cache-Control'],'no-store');
 }
});
