const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
function fixture({model='QA55Q60BAWXXY',firmware='T-NKLBUABC-1720.7',keys=[{name:'SmartHub',code:10071}],missing=false,failRegister=false,failUnregister=false}={}) {
  const listeners={},calls=[];
  const add=(target)=>(name,fn)=>{(listeners[target+name] ||= []).push(fn);};
  const common={getSpecialSupportedKeys:()=>keys,registerKey(names){calls.push(['register',...names]);if(failRegister)throw Error('denied');},unregisterKey(names){calls.push(['unregister',...names]);if(failUnregister)throw Error('temporary');}};
  const context={document:{hidden:false,addEventListener:add('document')},addEventListener:add('window'),webapis:missing?undefined:{productinfo:{getRealModel:()=>model,getFirmware:()=>firmware},appcommon:common}};
  context.window=context;vm.runInNewContext(readFileSync('app/privacy-home-key.js','utf8'),context);
  return {api:context.FramePrivacyHomeKey,calls,document:context.document,event(target,name){for(const fn of listeners[target+name]||[])fn();},allowCleanup(){failUnregister=false;}};
}
test('only the verified model/firmware and SmartHub code are eligible',()=>{
 for(const options of [{missing:true},{model:'OTHER'},{firmware:'T-NKLBUABC-9999.0'},{keys:[]},{keys:[{name:'SmartHub',code:999}]}]){
  const f=fixture(options);f.api.setEnabled(true);assert.equal(f.api.active(),false);assert.deepEqual(f.calls,[]);
 }
});
test('page entry/exit is idempotent and owns SmartHub only',()=>{
 const f=fixture();f.api.setEnabled(false);assert.deepEqual(f.calls,[]);
 f.api.setEnabled(true);f.api.setEnabled(true);assert.equal(f.api.active(),true);
 f.api.setEnabled(false);f.api.setEnabled(false);assert.equal(f.api.active(),false);
 assert.deepEqual(f.calls,[['register','SmartHub'],['unregister','SmartHub']]);
});
test('blur, suspend, return and pagehide release/reacquire only while wanted',()=>{
 const f=fixture();f.api.setEnabled(true);f.event('window','blur');assert.equal(f.api.active(),false);
 f.api.setEnabled(true);assert.equal(f.calls.length,2,'background renders cannot re-register');
 f.event('window','focus');assert.equal(f.api.active(),true);
 f.document.hidden=true;f.event('document','visibilitychange');assert.equal(f.api.active(),false);
 f.document.hidden=false;f.event('document','visibilitychange');assert.equal(f.api.active(),true);
 f.event('window','pagehide');assert.equal(f.api.active(),false);
 f.event('window','focus');assert.equal(f.api.active(),false);
});
test('registration denial is contained; cleanup failure remains retryable',()=>{
 const denied=fixture({failRegister:true});assert.doesNotThrow(()=>denied.api.setEnabled(true));assert.equal(denied.api.active(),false);
 const f=fixture({failUnregister:true});f.api.setEnabled(true);f.api.setEnabled(false);assert.equal(f.api.active(),true);
 f.allowCleanup();f.api.setEnabled(false);assert.equal(f.api.active(),false);
});
