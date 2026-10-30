// Actual XHR and remote-input UI, with a fake HTTPS receiver. Never sends live reports.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
import {installOnboarding} from '../tests/fixtures/onboarding.mjs';
const widget=process.argv.includes('--widget'),preview=await openPreview(widget?{widgetPath:root+'dist/CleanHome-Q60B-unsigned.wgt'}:{publicFonts:true});
const endpoint='https://clean-home-feedback.perkymule6.chatgpt.site/api/reports';
const receipt='CH-00000000-0000-4000-8000-000000000001';
const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'};
const report={engine:await preview.browser.version(),scope:widget?'Packaged widget':'Source preview',checks:[],errors:[]};
const folder=root+'.local/qa/report-send-'+(process.env.CLEANHOME_CHROMIUM?'85':'current')+(widget?'-widget':'');mkdirSync(folder,{recursive:true});
function check(label,value){assert(value,label);report.checks.push(label);}
async function open(mode='success'){
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});page.on('pageerror',e=>report.errors.push(e.message));
 await page.route('https://**/*',r=>r.abort());let count=0;
 await page.route(endpoint,async route=>{
  if(route.request().method()==='OPTIONS'){await route.fulfill({status:204,headers});return;}
  count++;
  if(mode==='offline'){await route.abort();return;}
  if(mode==='timeout'){await new Promise(r=>setTimeout(r,500));try{await route.fulfill({status:201,headers,contentType:'application/json',body:JSON.stringify({accepted:true,id:receipt})});}catch{}return;}
  await new Promise(r=>setTimeout(r,180));
  const status=mode==='busy'?429:mode==='server'?500:mode==='html'?200:201;
  const body=mode==='html'?'<html>private server details</html>':JSON.stringify({accepted:true,id:mode==='bad-receipt'?'private-token':receipt});
  try{await route.fulfill({status,headers,contentType:'application/json',body});}catch{}
 });
 await page.addInitScript(installOnboarding,{dailyBing:false});
 await page.addInitScript(()=>{
  window.__reportBodies=[];window.__privateCalls=0;
  const original=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(body){if(typeof body==='string'&&body.indexOf('"schema"')>=0)__reportBodies.push(JSON.parse(body));return original.apply(this,arguments);};
  window.webapis={productinfo:{getRealModel:()=> 'EXAMPLE_TV',getFirmware:()=> 'T-TEST-1000.0',getDuid(){__privateCalls++;return'PRIVATE';}}};tizen.systeminfo={getCapability:()=> '6.5'};
 });
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready()&&ShoreQA.state().catalog.loaded);
 await page.evaluate(()=>{ShoreQA.scene('settings');ShoreQA.activate('settings.group.samsung');ShoreQA.activate('samsung.diagnostics');});
 return{page,count:()=>count};
}
try{
 let h=await open(),page=h.page;
 const before=await page.evaluate(()=>localStorage.getItem('cleanhome.home.v1'));
 check('Default report shows reviewable details and explicit Send',await page.evaluate(()=>document.querySelector('.tv-report-data').textContent.includes('EXAMPLE_TV')&&document.querySelector('[data-action="report.0"]').textContent==='Send: works'));
 check('Opening a report sends nothing and loads no QR encoder',h.count()===0&&await page.evaluate(()=>__reportBodies.length===0&&typeof qrcode==='undefined'));
 await page.keyboard.press('Enter');await page.keyboard.press('Enter');
 await page.waitForFunction(()=>document.querySelector('.tv-report-status').textContent.indexOf('Thank you')>=0);
 check('Explicit Send succeeds with a receipt and duplicate presses send once',h.count()===1&&await page.evaluate(()=>__reportBodies.length===1&&document.querySelector('.tv-report-status').textContent.indexOf('CH-00000000')>=0));
 const body=await page.evaluate(()=>__reportBodies[0]);
 check('Only the exact 17 allowlisted report fields are submitted',Object.keys(body).length===17&&body.model==='EXAMPLE_TV'&&body.result==='Works on my TV'&&!JSON.stringify(body).includes('AppOne'));
 check('Sending never reads a unique identifier or launches another app',await page.evaluate(()=>__privateCalls===0&&__launches.length===0));
 check('Sending does not change saved preferences',before===await page.evaluate(()=>localStorage.getItem('cleanhome.home.v1')));
 for(const size of [{width:1920,height:1080},{width:1280,height:720}]){
  await page.setViewportSize(size);await page.waitForTimeout(100);
  check('Direct report remains in the app surface at '+size.width,await page.evaluate(()=>{const s=document.getElementById('stage').getBoundingClientRect();return Array.from(document.querySelectorAll('.tv-report h2,.tv-report-intro,.tv-report-data,.tv-report-actions,.tv-report-note,.tv-report-qr')).every(e=>{const r=e.getBoundingClientRect();return r.left>=s.left&&r.right<=s.right&&r.top>=s.top&&r.bottom<=s.bottom&&e.scrollHeight<=e.clientHeight+2;});}));
 }
 await page.screenshot({path:folder+'/sent.png'});await page.keyboard.press('Escape');
 check('Back restores Samsung settings after sending',await page.evaluate(()=>ShoreQA.where().settingsGroup==='samsung'&&ShoreQA.where().focusCount===1));
 await page.close();h=await open();page=h.page;await page.keyboard.press('ArrowRight');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelector('.tv-report-status').textContent.indexOf('Thank you')>=0);
 check('Send problem records the chosen outcome',await page.evaluate(()=>__reportBodies[0].result==='There is a problem'));await page.close();
 for(const mode of ['server','busy','html','bad-receipt','offline','timeout']){
  h=await open(mode);page=h.page;
  if(mode==='timeout')await page.evaluate(()=>{const descriptor=Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype,'timeout');Object.defineProperty(XMLHttpRequest.prototype,'timeout',{get:descriptor.get,set(value){descriptor.set.call(this,60);}});});
  await page.keyboard.press('Enter');await page.waitForFunction(()=>{const t=document.querySelector('.tv-report-status').textContent;return t.indexOf('Could not confirm')>=0||t.indexOf('Reports are busy')>=0;});
  check(mode+' never claims successful delivery or exposes raw server data',await page.evaluate(()=>!document.querySelector('.tv-report-status').textContent.includes('private-')&&!document.querySelector('.tv-report-status').textContent.includes('Thank you')));
  await page.waitForTimeout(180);check(mode+' does not retry automatically',h.count()===1);
  await page.keyboard.press('Escape');check(mode+' leaves remote navigation usable',await page.evaluate(()=>ShoreQA.where().settingsGroup==='samsung'));await page.close();
 }
 h=await open('timeout');page=h.page;await page.keyboard.press('Enter');await page.keyboard.press('Escape');await page.waitForTimeout(700);
 check('Cancel suppresses late completion without changing the view',await page.evaluate(()=>ShoreQA.where().settingsGroup==='samsung'&&!document.querySelector('.tv-report')));await page.close();
 h=await open();page=h.page;await page.evaluate(()=>ShoreQA.activate('report.2'));await page.evaluate(()=>ShoreQA.activate('report.0'));await page.waitForFunction(()=>!document.querySelector('.tv-report-qr canvas').hidden);
 check('Phone fallback still works without sending a report',h.count()===0&&await page.evaluate(()=>document.querySelector('.tv-report-note').textContent.includes('public')));await page.close();
 check('No uncaught runtime errors',report.errors.length===0);
 console.log(JSON.stringify({engine:report.engine,scope:report.scope,checks:report.checks.length,errors:report.errors}));
}finally{writeFileSync(folder+'/report.json',JSON.stringify(report,null,2)+'\n');await preview.close();}
