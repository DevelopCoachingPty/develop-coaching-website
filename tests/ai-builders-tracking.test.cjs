const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../www/ai-for-builders-september-2026/tracking.js'), 'utf8');
const prefix = 'dc-ai-builders-sep-2026:';
const fields = { source:'facebook', medium:'paid_social', campaign:'ai_sep_2026', content:'greg_video', term:'builders' };
function storage(initial = {}) { const data = new Map(Object.entries(initial)); return { getItem: key => data.get(key) || null, setItem: (key, value) => data.set(key, value), removeItem: key => data.delete(key) }; }
function run({ search='', local=storage(), session=storage(), hostname='develop-coaching.com', pathname='/ai-for-builders-september-2026/', privacy={}, existingGtag=true, deferDom=false }={}) {
  const calls=[], google=[], scripts=[], buttons=[], events={}, nodes=[], links=[];
  function element(tag) { const node={style:{},setAttribute(){},append(){},addEventListener(name,fn){this[name]=fn;}};nodes.push({tag,node});if(tag==='button')buttons.push(node);return node; }
  const cta=element('a');links.push(cta);
  const window={localStorage:local,sessionStorage:session,fbq:(...args)=>calls.push(args),gtag:(...args)=>google.push(args)};
  if(!existingGtag)delete window.gtag;
  vm.runInNewContext(source,{window,URLSearchParams,location:{search,hostname,pathname},navigator:privacy,document:{querySelectorAll:()=>links,createElement:element,addEventListener:(name,fn)=>events[name]=fn,head:{append:node=>scripts.push(node)},body:{append(){}}}});
  if(!deferDom)events.DOMContentLoaded();
  return {window,calls,google,scripts,buttons,local,session,nodes,cta,events,purchases:()=>calls.filter(call=>call[1]==='Purchase')};
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
 assert.equal(result.purchases().length,1);assert.equal(result.calls.filter(call=>call[1]==='InitiateCheckout').length,0);
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
 assert.equal(first.purchases().length,1);assert.equal(first.purchases()[0][3].eventID,paid.transactionId);assert.equal(first.google.find(call=>call[1]==='purchase')[2].transaction_id,paid.transactionId);
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

test('loads the verified GA4 stream only after opt-in and sends one clean page view',()=>{
 const result=run({search:'?utm_source=email&utm_medium=email&utm_campaign=ai-builders-september-2026&email=person%40example.com'});
 assert.equal(result.google.length,0);
 result.buttons[0].click();result.window.dcWorkshop.checkoutReady();
 assert.equal(result.scripts.filter(script=>script.src==='https://www.googletagmanager.com/gtag/js?id=G-PXT2VCVFLW').length,1);
 const config=result.google.find(call=>call[0]==='config');
 assert.equal(config[1],'G-PXT2VCVFLW');assert.equal(config[2].send_page_view,false);
 assert.equal(config[2].page_location,'https://develop-coaching.com/ai-for-builders-september-2026/');
 assert.equal(config[2].campaign_source,'email');
 assert.equal(result.google.filter(call=>call[1]==='page_view').length,1);
 assert.equal(JSON.stringify(result.google).includes('person@example.com'),false);
});
test('automatic checkout readiness is not intent; CTA clicks emit intent once',()=>{
 const result=run({local:storage({[prefix+'consent']:'yes'})});
 result.window.dcWorkshop.checkoutReady();
 assert.equal(result.calls.filter(call=>call[1]==='InitiateCheckout').length,0);
 assert.equal(result.google.filter(call=>call[1]==='begin_checkout').length,0);
 assert.equal(typeof result.cta.click,'function');result.cta.click();result.cta.click();
 assert.equal(result.calls.filter(call=>call[1]==='InitiateCheckout').length,1);
 assert.equal(result.google.filter(call=>call[1]==='begin_checkout').length,1);
});
test('unknown choice is immediately visible and choices hide the banner with a reopen control',()=>{
 const result=run(), box=result.nodes.find(item=>item.tag==='aside').node;
 assert.match(box.style.cssText,/position:fixed/);assert.equal(box.hidden,false);
 result.buttons[1].click();assert.equal(box.hidden,true);
 const reopen=result.buttons.find(button=>button.textContent==='Tracking preferences');
 assert.ok(reopen);reopen.click();assert.equal(box.hidden,false);
});
test('revocation disables Google collection and regrant does not duplicate page views',()=>{
 const result=run();result.buttons[0].click();result.buttons[1].click();
 assert.equal(result.window['ga-disable-G-PXT2VCVFLW'],true);
 result.buttons[0].click();assert.equal(result.window['ga-disable-G-PXT2VCVFLW'],false);
 assert.equal(result.google.filter(call=>call[1]==='page_view').length,1);
 assert.equal(result.scripts.length,2);
});
test('verified Stripe attribution is used for purchase instead of confirmation UTMs',()=>{
 const result=run({search:'?utm_source=wrong',pathname:'/ai-for-builders-september-2026/thank-you/',local:storage({[prefix+'consent']:'yes'})});
 result.window.dcWorkshop.verified({...paid,attribution:fields});
 const purchase=result.google.find(call=>call[1]==='purchase')[2];
 assert.equal(purchase.campaign_source,'facebook');
 assert.equal(purchase.workshop_id,'ai-for-builders-september-2026');
});

test('initialises a real dataLayer queue when no Google tag exists',()=>{
 const result=run({existingGtag:false,local:storage({[prefix+'consent']:'yes'})});
 const queue=Array.from(result.window.dataLayer,args=>Array.from(args));
 assert.equal(queue.filter(call=>call[0]==='config').length,1);
 assert.equal(queue.filter(call=>call[1]==='page_view').length,1);
 assert.equal(queue[0][0],'consent');assert.equal(queue[0][1],'default');
 assert.equal(queue[0][2].analytics_storage,'denied');
});
test('verification arriving before DOM ready cannot initialise tracking before URL cleanup',()=>{
 const result=run({deferDom:true,local:storage({[prefix+'consent']:'yes'}),pathname:'/ai-for-builders-september-2026/thank-you/'});
 result.window.dcWorkshop.verified(paid);assert.equal(result.scripts.length,0);
 result.events.DOMContentLoaded();assert.equal(result.purchases().length,1);
});
