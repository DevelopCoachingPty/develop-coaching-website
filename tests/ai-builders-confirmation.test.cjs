const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../www/ai-for-builders-september-2026/confirmation.js'),'utf8');
const paid={status:'paid',event:'ai-for-builders-september-2026',amount:4500,currency:'gbp',transactionId:'cs_test_fixture123',live:false};
async function run({search='?session_id=cs_test_fixture123',data=paid,ok=true,reject=false,stored=null}={}) {
 const nodes={},calls=[],verified=[],historyCalls=[],saved=[];
 for(const id of ['confirmation-title','confirmation-message','confirmation-retry','confirmed-details']) nodes[id]={hidden:true,addEventListener(name,fn){this[name]=fn;}};
 const window={sessionStorage:{getItem:()=>stored,setItem:(...args)=>saved.push(args)},dcWorkshop:{verified:data=>verified.push(data)}};
 await vm.runInNewContext(source,{window,URLSearchParams,AbortSignal,location:{search,pathname:'/ai-for-builders-september-2026/thank-you/'},history:{replaceState:(...args)=>historyCalls.push(args)},document:{getElementById:id=>nodes[id],querySelector:()=>({addEventListener(){}})},fetch:async(url)=>{calls.push(url);if(reject)throw Error('provider');return {ok,json:async()=>data};}});
 return {nodes,calls,verified,historyCalls,saved};
}
test('shows paid details only after full server contract matches and removes URL reference',async()=>{
 const result=await run();assert.equal(result.nodes['confirmed-details'].hidden,false);assert.equal(result.verified.length,1);assert.equal(result.calls.length,1);assert.match(result.calls[0],/^\/api\/ai-builders-checkout-status/);assert.equal(result.historyCalls[0][2],'/ai-for-builders-september-2026/thank-you/');
});
test('pending and mismatched server contracts cannot show success or emit purchase',async()=>{
 for(const change of [{status:'pending'},{event:'other'},{amount:1},{currency:'usd'},{transactionId:'cs_test_other'}]) {
  const result=await run({data:{...paid,...change}});assert.equal(result.nodes['confirmed-details'].hidden,true);assert.equal(result.verified.length,0);assert.equal(result.nodes['confirmation-retry'].hidden,false);
 }
});
test('provider failures offer a status retry without creating checkout',async()=>{
 for(const options of [{reject:true},{ok:false}]) {
  const result=await run(options);assert.equal(result.verified.length,0);assert.equal(result.nodes['confirmation-retry'].hidden,false);await result.nodes['confirmation-retry'].click();assert.equal(result.calls.length,2);assert.ok(result.calls.every(url=>url.startsWith('/api/ai-builders-checkout-status')));
 }
});
test('missing or malformed references never call provider or confirm; reload uses stored reference',async()=>{
 for(const search of ['','?session_id=invalid','?checkout=complete']){const result=await run({search});assert.equal(result.calls.length,0);assert.equal(result.verified.length,0);}
 const reload=await run({search:'',stored:paid.transactionId});assert.equal(reload.verified.length,1);
});
