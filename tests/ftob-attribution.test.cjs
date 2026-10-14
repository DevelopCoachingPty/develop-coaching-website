const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.join(__dirname,'../www');
function run(search='',saved=null,blocked=false){
 const store={dc_ftob_utm:saved};
 const link={href:'https://buy.stripe.com/bJe9AT3Wtfrtamk7uF9k40F'};
 const ctx={URL,URLSearchParams,window:{location:{search}},localStorage:{getItem:k=>{if(blocked)throw Error();return store[k]},setItem:(k,v)=>{if(blocked)throw Error();store[k]=v}},document:{querySelectorAll:()=>[link]}};
 ctx.window.localStorage=ctx.localStorage;
 vm.createContext(ctx);
 const helper=path.join(root,'assets/ftob-attribution.js');
 if(fs.existsSync(helper))vm.runInContext(fs.readFileSync(helper,'utf8'),ctx);
 const html=fs.readFileSync(path.join(root,'fill-the-order-book/index.html'),'utf8');
 const script=html.split('// Source attribution packed')[1].split('// Checkout intent')[0];
 vm.runInContext(script.slice(script.indexOf('(function')),ctx);
 const thanks=fs.readFileSync(path.join(root,'fill-the-order-book-thank-you/index.html'),'utf8');
 const pickup=thanks.split('window.dcUtm = ')[1].split('</script>')[0];
 vm.runInContext('window.dcUtm = '+pickup,ctx);
 return {ref:new URL(link.href).searchParams.get('client_reference_id'),saved:store.dc_ftob_utm,utm:JSON.parse(JSON.stringify(ctx.window.dcUtm))};
}
test('email return retains source, campaign and email identity in Stripe links',()=>{
 const first=run('?utm_source=flowbuild&utm_medium=email&utm_campaign=fill-the-order-book&utm_content=e1');
 const back=run('',first.saved);
 assert.equal(back.ref,'s-flowbuild__c-fill-the-order-book__a-e1');assert.equal(back.utm.utm_source,'flowbuild');
});
test('paid ad return retains source and ad identity',()=>{const x=run('?utm_source=facebook&utm_medium=paid_social&utm_campaign=ftob&utm_content=ad7');const y=run('',x.saved);assert.equal(y.ref,'s-facebook__c-ftob__a-ad7');assert.equal(y.utm.utm_medium,'paid_social')});
test('new tagged email replaces previous ad without stale fields',()=>{const x=run('?utm_source=flowbuild&utm_medium=email',JSON.stringify({utm_source:'facebook',utm_campaign:'old',utm_content:'ad1'}));assert.equal(x.ref,'s-flowbuild');assert.deepEqual(x.utm,{utm_source:'flowbuild',utm_medium:'email'})});
test('partial untagged query cannot mix campaigns',()=>{const x=run('?utm_campaign=other',JSON.stringify({utm_source:'flowbuild',utm_campaign:'ftob'}));assert.equal(x.ref,'s-flowbuild__c-ftob');assert.equal(x.utm.utm_campaign,'ftob')});
test('direct, corrupt and malformed records fail safely',()=>{for(const saved of [null,'broken','[]','null','{"utm_source":{}}'])assert.equal(run('',saved).ref,'s-direct')});
test('blocked storage preserves current tagged source',()=>{assert.equal(run('?utm_source=facebook',null,true).ref,'s-facebook');assert.equal(run('',null,true).ref,'s-direct')});
