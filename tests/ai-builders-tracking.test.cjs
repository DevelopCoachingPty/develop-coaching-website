const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../www/ai-for-builders-september-2026/tracking.js'), 'utf8');
const prefix = 'dc-ai-builders-sep-2026:';
const fields = { source:'facebook', medium:'paid_social', campaign:'ai_sep_2026', content:'greg_video', term:'builders' };
function storage(initial = {}) { const data = new Map(Object.entries(initial)); return { getItem: key => data.get(key) || null, setItem: (key, value) => data.set(key, value), removeItem: key => data.delete(key) }; }
function run({ search='', local=storage(), session=storage(), hostname='develop-coaching.com', pathname='/ai-for-builders-september-2026/', privacy={} }={}) {
  const calls=[], google=[], scripts=[], buttons=[], events={};
  function element(tag) { const node={style:{},setAttribute(){},append(){},addEventListener(name,fn){this[name]=fn;}};if(tag==='button')buttons.push(node);return node; }
  const window={localStorage:local,sessionStorage:session,fbq:(...args)=>calls.push(args),gtag:(...args)=>google.push(args)};
  vm.runInNewContext(source,{window,URLSearchParams,location:{search,hostname,pathname},navigator:privacy,document:{createElement:element,addEventListener:(name,fn)=>events[name]=fn,head:{append:node=>scripts.push(node)},body:{append(){}}}});
  events.DOMContentLoaded();
  return {window,calls,google,scripts,buttons,local,session,purchases:()=>calls.filter(call=>call[1]==='Purchase')};
}
const paid = {status:'paid',live:true,transactionId:'cs_live_fixture123'};
test('captures all five campaign labels and preserves first touch through same-tab campaign changes and direct return',()=>{
 const search='?'+new URLSearchParams(Object.entries(fields).map(([k,v])=>['utm_'+k,v]));
 const first=run({search});
 assert.deepEqual(JSON.parse(JSON.stringify(first.window.dcWorkshop.attribution)),fields);
 for(const nextSearch of ['?utm_source=google','']) {
  const next=run({search:nextSearch,session:first.session,local:first.local});
  assert.deepEqual(JSON.parse(JSON.stringify(next.window.dcWorkshop.attribution)),fields);
 }
 assert.equal(first.local.getItem(prefix+'attribution'),null);
});
test('consented first touch survives a new tab and unlabelled visits use direct',()=>{
 const local=storage({[prefix+'consent']:'yes'});
 run({local,search:'?utm_source=facebook&utm_campaign=sep'});
 assert.equal(run({local}).window.dcWorkshop.attribution.source,'facebook');
 assert.equal(run().window.dcWorkshop.attribution.source,'direct');
});
test('rejects PII-shaped, long, and markup campaign values',()=>{
 const result=run({search:'?'+new URLSearchParams({utm_source:'person@example.com',utm_medium:'<script>',utm_campaign:'a'.repeat(51),utm_content:'UPPER-CASE',utm_term:'two words'})});
 assert.deepEqual(JSON.parse(JSON.stringify(result.window.dcWorkshop.attribution)),{source:'direct',medium:'',campaign:'',content:'upper-case',term:''});
});
test('unknown or denied consent and privacy signals suppress marketing even after verification',()=>{
 for(const consent of [undefined,'no']) {
  const result=run({local:storage(consent?{[prefix+'consent']:consent}:{})});result.window.dcWorkshop.checkoutReady();result.window.dcWorkshop.verified(paid);
  assert.equal(result.calls.length,0);assert.equal(result.scripts.length,0);
 }
 for(const privacy of [{globalPrivacyControl:true},{doNotTrack:'1'}]) {
  const result=run({local:storage({[prefix+'consent']:'yes'}),privacy});result.window.dcWorkshop.verified(paid);assert.equal(result.calls.length,0);
 }
});
test('consent grant releases pending verified conversion once; revoke prevents future conversion',()=>{
 const result=run();result.window.dcWorkshop.checkoutReady();result.window.dcWorkshop.verified(paid);result.buttons[0].click();
 assert.equal(result.purchases().length,1);assert.equal(result.calls.filter(call=>call[1]==='InitiateCheckout').length,1);
 result.buttons[1].click();result.window.dcWorkshop.verified({...paid,transactionId:'cs_live_other'});
 assert.equal(result.purchases().length,1);assert.equal(result.local.getItem(prefix+'attribution'),null);
});
test('only live paid verified data can purchase; sandbox and preview never purchase',()=>{
 for(const data of [{...paid,status:'pending'},{...paid,live:false},{...paid,transactionId:'cs_test_fixture123'},{...paid,transactionId:'bad'}]) {
  const result=run({local:storage({[prefix+'consent']:'yes'})});result.window.dcWorkshop.verified(data);assert.equal(result.purchases().length,0);
 }
 const preview=run({hostname:'localhost',local:storage({[prefix+'consent']:'yes'})});preview.window.dcWorkshop.verified(paid);assert.equal(preview.calls.length,0);assert.equal(preview.scripts.length,0);
});
test('purchase uses stable transaction ID and deduplicates repeated verification and reloads',()=>{
 const local=storage({[prefix+'consent']:'yes'}), first=run({local,pathname:'/ai-for-builders-september-2026/thank-you/'});
 first.window.dcWorkshop.verified(paid);first.window.dcWorkshop.verified(paid);
 assert.equal(first.purchases().length,1);assert.equal(first.purchases()[0][3].eventID,paid.transactionId);assert.equal(first.google[0][2].transaction_id,paid.transactionId);
 assert.equal(first.calls.filter(call=>call[1]==='ViewContent').length,0);
 const second=run({local});second.window.dcWorkshop.verified(paid);assert.equal(second.purchases().length,0);
});
test('blocked storage does not break tracking and fails closed for purchase',()=>{
 const blocked={getItem:key=>key===prefix+'consent'?'yes':null,setItem(){throw Error('blocked');},removeItem(){throw Error('blocked');}};
 const result=run({local:blocked,session:blocked});result.window.dcWorkshop.verified(paid);assert.equal(result.purchases().length,0);
});
test('legacy returns never initialise pixels even with stored consent before redirect commits',()=>{
 for(const search of ['?session_id=cs_live_old','?checkout=complete']) {
  const result=run({search,local:storage({[prefix+'consent']:'yes'})});
  result.window.dcWorkshop.checkoutReady();result.window.dcWorkshop.verified(paid);
  assert.equal(result.calls.length,0);assert.equal(result.scripts.length,0);
 }
});
