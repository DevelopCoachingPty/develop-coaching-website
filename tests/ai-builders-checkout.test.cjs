const test = require('node:test');
const assert = require('node:assert/strict');
const create = require('../www/api/create-ai-builders-checkout');
const status = require('../www/api/ai-builders-checkout-status');
Object.assign(process.env, { STRIPE_SECRET_KEY: 'sk_test_mock', STRIPE_AI_BUILDERS_PRICE_ID: 'price_mock' });
function response(){return {headers:{},setHeader(k,v){this.headers[k]=v;},status(n){this.code=n;return this;},json(v){this.body=v;return this;}};}
const request = {method:'POST',headers:{host:'develop-coaching.com',origin:'https://develop-coaching.com'},body:{attemptId:'01234567-8901-2345-6789-012345678901'}};
test('retired workshop rejects every booking request without contacting Stripe',async()=>{
 global.fetch=async()=>{throw Error('must not call');};
 for(const req of [request,{...request,headers:{...request.headers,origin:'https://evil.example'}},{...request,body:{}},{...request,body:'{'}]){
  const res=response();await create(req,res);assert.equal(res.code,410);assert.deepEqual(res.body,{error:'This workshop is no longer accepting bookings.'});assert.equal(res.headers['Cache-Control'],'no-store');
 }
});
test('retired checkout endpoint preserves its POST-only contract',async()=>{
 const res=response();await create({method:'GET'},res);assert.equal(res.code,405);assert.equal(res.headers.Allow,'POST');
});
const paid={mode:'payment',metadata:{event:'ai-for-builders-september-2026'},amount_total:4500,currency:'gbp',line_items:{data:[{quantity:1,price:{id:'price_mock'}}]},status:'complete',payment_status:'paid',customer_details:{email:'private@example.com'}};
test('verified paid return exposes no PII; pending is not paid',async()=>{
 for(const [change,expected] of [[{},'paid'],[{payment_status:'unpaid'},'pending'],[{status:'open'},'pending']]){global.fetch=async()=>({ok:true,json:async()=>({...paid,...change})});const res=response();await status({method:'GET',query:{session_id:'cs_test_example'}},res);assert.equal(res.body.status,expected);assert.equal(JSON.stringify(res.body).includes('private'),false);assert.equal(res.headers['Cache-Control'],'no-store');}
});
test('foreign event, wrong total and wrong product cannot confirm',async()=>{
 for(const change of [{metadata:{event:'other'}},{amount_total:1},{currency:'usd'},{line_items:{data:[{quantity:1,price:{id:'other'}}]}}]){global.fetch=async()=>({ok:true,json:async()=>({...paid,...change})});const res=response();await status({method:'GET',query:{session_id:'cs_test_example'}},res);assert.equal(res.code,400);}
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
