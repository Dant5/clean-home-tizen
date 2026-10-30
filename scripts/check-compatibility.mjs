// Reuse the packaged preview and onboarding fixture over stable page CDP commands.
// Older TV-generation engines predate Playwright's browser-context download API.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {mkdtempSync,readFileSync,existsSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {installOnboarding} from '../tests/fixtures/onboarding.mjs';
const root=new URL('../',import.meta.url).pathname;
const binary=process.env.CLEANHOME_CHROMIUM;
assert(binary,'Set CLEANHOME_CHROMIUM to a pinned local test browser.');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const profile=mkdtempSync(join(tmpdir(),'clean-home-compat-'));
const widget=process.argv[2]||join(root,'dist/CleanHome-Q60B-unsigned.wgt');
const server=spawn('python3',['scripts/preview.py','--port','0','--widget',widget],{cwd:root,stdio:['ignore','pipe','pipe']});
let chrome,ws,seq=0;
const pending=new Map(),errors=[],checks=[],screens=[];
const report={scope:'Actual unsigned widget, fake Tizen boundary, no TV contacted',widgetSha256:createHash('sha256').update(readFileSync(widget)).digest('hex'),checks,errors};
function check(name,value){assert(value,name);checks.push(name);}
async function until(fn,label){for(let i=0;i<150;i++){const value=await fn();if(value)return value;await sleep(100);}throw Error('Timed out: '+label);}
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout: '+method));},10000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}
const state=()=>evaluate('ShoreQA.state()');
async function action(a){await until(()=>evaluate('ShoreQA.actions().indexOf('+JSON.stringify(a)+')>=0'),a);await evaluate('ShoreQA.activate('+JSON.stringify(a)+')');await sleep(60);}
async function key(code,held=0){const name={13:'Enter',27:'Escape',37:'ArrowLeft',38:'ArrowUp',39:'ArrowRight',40:'ArrowDown'}[code];await send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code:name,windowsVirtualKeyCode:code,nativeVirtualKeyCode:code});if(held)await sleep(held);await send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code:name,windowsVirtualKeyCode:code,nativeVirtualKeyCode:code});await sleep(100);}
async function screenshot(label){const r=await send('Page.captureScreenshot',{format:'png'});screens.push({label,data:r.data});}
async function geometry(){return evaluate(`(function(){var out=[];Array.prototype.forEach.call(document.querySelectorAll('[data-action],.u-content>*,.caption>*,.setting-choice>*,.setting-options>*,.settings-group>*,.panel-content>*,.er>*,.eo>*'),function(e){var r=e.getBoundingClientRect(),s=getComputedStyle(e);if(r.width&&r.height&&s.visibility!=='hidden'&&s.display!=='none'&&e.getClientRects().length)out.push({key:e.getAttribute('data-action')||e.className.baseVal||e.className,x:r.left,y:r.top,w:r.width,h:r.height});});return out;}())`);}
async function spacing(label){
 await sleep(450);
 const old=await evaluate('document.documentElement.classList.contains("no-flex-gap")');
 if(old){check(label+' uses the older-engine spacing fallback',true);return;}
 const a=await geometry();await evaluate('document.documentElement.classList.add("no-flex-gap")');await sleep(180);const b=await geometry();
 await evaluate('document.documentElement.classList.remove("no-flex-gap")');await sleep(180);
 assert.equal(a.length,b.length,label+' geometry member count');
 const differences=[];for(let i=0;i<a.length;i++)for(const k of ['x','y','w','h'])if(Math.abs(a[i][k]-b[i][k])>.6)differences.push({element:a[i].key,axis:k,native:a[i][k],fallback:b[i][k]});
 if(differences.length){report.spacingDifferences={label,differences};throw Error(label+' fallback changes layout: '+JSON.stringify(differences.slice(0,4)));}
 check(label+' preserves native layout with fallback',true);
}
try{
 const baseURL=await new Promise((resolve,reject)=>{let out='';const t=setTimeout(()=>reject(Error('Preview startup timeout')),10000);server.stdout.on('data',b=>{out+=b;const m=out.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(t);resolve(m[0]);}});server.once('error',reject);});
 chrome=spawn(binary,['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--no-first-run','--no-default-browser-check','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
 let browserLog='';chrome.stderr.on('data',b=>browserLog=(browserLog+b).slice(-2000));
 const port=await until(()=>{if(chrome.exitCode!==null)throw Error('Browser exited: '+browserLog);const file=join(profile,'DevToolsActivePort');return existsSync(file)&&readFileSync(file,'utf8').split('\n')[0];},'debug port');
 const targets=await(await fetch('http://127.0.0.1:'+port+'/json/list')).json();
 ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);});
 report.engine=(await send('Browser.getVersion')).product;
 await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.setBlockedURLs',{urls:['https://*']});
 await send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
 await send('Page.addScriptToEvaluateOnNewDocument',{source:'('+installOnboarding.toString()+')(null);'});
 await send('Page.navigate',{url:baseURL+'/home/'});
 await until(()=>evaluate('typeof ShoreQA!=="undefined"&&ShoreQA.ready()&&ShoreQA.state().catalog.loaded'),'fresh Home');
 check('Fresh installation has no assumed favourites',!(await state()).dock.length);
 check('Fresh installation has one focused plus',await evaluate('document.querySelectorAll(".dock .tile").length===1&&!!document.querySelector("[data-action=\\"home.add-app\\"].is-focus")'));
 check('Public Manrope face loads',await evaluate('document.fonts.check("500 40px Manrope")'));
 await spacing('Empty Home');await key(13);await action('apps.open.AppOne0001.Main');
 check('First choice is saved without launching',(await state()).dock[0]==='AppOne0001.Main'&&await evaluate('__launches.length===0'));
 await key(39);await key(13);await action('apps.open.AppTwo0002.Main');
 check('Second choice appends',JSON.stringify((await state()).dock)==='["AppOne0001.Main","AppTwo0002.Main"]');
 await spacing('Populated Home');await screenshot('home');await key(13,750);
 check('Hold Select opens replacement picker',(await state()).view==='apps');await screenshot('picker');await action('apps.open.AppThree03.Main');
 check('Replacement keeps slot order',JSON.stringify((await state()).dock)==='["AppOne0001.Main","AppThree03.Main"]');
 await key(13);check('Short Select launches the discovered ID once',await evaluate('__launches.length===1&&__launches[0]==="AppThree03.Main"'));
 await send('Page.reload');await until(()=>evaluate('typeof ShoreQA!=="undefined"&&ShoreQA.ready()&&ShoreQA.state().catalog.loaded'),'reload');
 check('Choices survive reload without auto-launch',JSON.stringify((await state()).dock)==='["AppOne0001.Main","AppThree03.Main"]'&&await evaluate('__launches.length===0'));
 await evaluate('ShoreQA.scene("settings")');await spacing('Settings overview');
 for(const group of ['layout','typography','background','focus','samsung','bindings']){await evaluate('ShoreQA.scene("settings")');await action('settings.group.'+group);await spacing('Settings '+group);}
 await evaluate('ShoreQA.scene("editor")');await spacing('App editor');
 for(const layout of ['dock','list'])for(const controls of ['icons','both','text'])for(const apps of ['icons','both','text']){await evaluate('ShoreQA.scene("home");ShoreQA.look('+JSON.stringify({layout,controls,apps})+')');await until(()=>evaluate('ShoreQA.ready()'),'appearance');await spacing(layout+' '+controls+' '+apps);}
 await evaluate('ShoreQA.scene("home");ShoreQA.look({layout:"list"})');await until(()=>evaluate('ShoreQA.ready()'),'list');await spacing('List Home');
 check('One visible remote focus target',await evaluate('ShoreQA.where().focusCount===1'));
 await evaluate('ShoreQA.scene("settings")');await action('settings.group.samsung');await action('samsung.diagnostics');
 check('TV report opens without sharing',await evaluate('ShoreQA.state().view==="tvreport"&&document.querySelector(".tv-report-qr canvas").hidden'));
 await action('report.1');await until(()=>evaluate('!document.querySelector(".tv-report-qr canvas").hidden'),'locally generated report code');
 check('TV report QR renders on this engine',await evaluate('document.querySelector(".tv-report-qr canvas").width>=300'));
 check('Report QR script is loaded only once',await evaluate('document.querySelectorAll("script[src=\\"assets/qr/qrcode.js\\"]").length===1'));
 await screenshot('tv-report');await key(27);
 check('Report Back restores settings focus',await evaluate('ShoreQA.where().settingsGroup==="samsung"&&ShoreQA.where().focusCount===1'));
 check('No uncaught runtime errors',errors.length===0);
 report.features=await evaluate('({fallback:document.documentElement.classList.contains("no-flex-gap"),imageDecode:typeof Image.prototype.decode,abortController:typeof AbortController,userAgent:navigator.userAgent})');
 console.log(JSON.stringify({engine:report.engine,widgetSha256:report.widgetSha256,checks:checks.length,errors}));
}finally{
 const major=(report.engine||'unknown').match(/\d+/)?.[0]||'unknown';const folder=join(root,'.local/qa/compatibility-'+major);mkdirSync(folder,{recursive:true});writeFileSync(join(folder,'report.json'),JSON.stringify(report,null,2)+'\n');for(const s of screens)writeFileSync(join(folder,s.label+'.png'),Buffer.from(s.data,'base64'));
 if(ws)ws.close();if(chrome)chrome.kill('SIGKILL');server.kill();await sleep(200);rmSync(profile,{recursive:true,force:true});
}
