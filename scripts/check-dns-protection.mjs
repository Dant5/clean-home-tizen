// Mock data is confined to this browser test, never shipped as live statistics.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const widget=process.argv.includes('--widget');
const preview=await openPreview(widget?{widgetPath:root+'dist/CleanHome-Q60B-unsigned.wgt'}:{});
const errors=[],writes=[];let gets=0,unavailable=false,delay=0;
const now=new Date().toISOString();
const data={schema:1,sampledAt:now,timezone:'Australia/Perth',protectionEnabled:true,pausedUntil:null,
 scope:'Dedicated TV / soundbar resolver',coverage:'Other DNS paths have not been ruled out',history:'Available query log only; missing history is not zero activity',
 resolver:'AdGuard Home',complete:true,lastQueryAt:now,filters:['Fixture list'],today:{queries:120,blocked:30,percent:25},
 days:Array.from({length:7},(_,i)=>({date:'2026-11-'+String(13+i),queries:50+i*10,blocked:10+i})),
 topToday:[{domain:'tracker.example.org',count:30}],top:[{domain:'tracker.example.org',count:30}],recent:Array.from({length:12},(_,i)=>({domain:i?'ads.example.org':'<img src=x onerror="window.__injected=1">',time:now,reason:'Blocklist',source:'Fixture list',category:'Not provided by list'})),
 observedClientProtocols:{'':120},observedUpstreamTransport:{Encrypted:90}};
data.days[6]={date:'2026-11-19',queries:120,blocked:30};
data.devices=[{id:'tv',label:'TV',configured:true,today:{queries:100,blocked:20,percent:20},days:data.days,topToday:data.topToday,top:data.top,recent:data.recent,lastQueryAt:now,complete:true},{id:'soundbar',label:'Soundbar',configured:true,today:{queries:20,blocked:10,percent:50},days:data.days,topToday:data.topToday,top:data.top,recent:data.recent,lastQueryAt:now,complete:true}];
try{
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://**/*',r=>r.abort());
 await page.route('http://127.0.0.1:18768/**',async route=>{
  const req=route.request();
  const headers={'access-control-allow-origin':'*','access-control-allow-headers':'authorization,content-type','access-control-allow-methods':'GET, POST, OPTIONS'};
  if(req.method()==='OPTIONS')return route.fulfill({status:204,headers});
  assert.equal(req.headers().authorization,'Bearer '+'x'.repeat(40));
  if(req.method()==='POST'){
   const {action}=req.postData()?JSON.parse(req.postData()):await page.evaluate(i=>window.__dnsBodies[i],writes.length);writes.push(action);
   data.protectionEnabled=action==='enable';data.pausedUntil=action.startsWith('pause')?now:null;
   return route.fulfill({json:{accepted:true},headers});
  }
  gets++;if(delay)await new Promise(r=>setTimeout(r,delay));
  return route.fulfill({status:unavailable?503:200,json:unavailable?{}:data,headers});
 });
 await page.addInitScript(()=>{
  localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false}));
  window.__dnsBodies=[];
  var send=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(body){if(typeof body==='string'&&body.indexOf('"action"')>=0)window.__dnsBodies.push(JSON.parse(body));return send.apply(this,arguments);};
 });
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready());
 // An ordinary public installation makes no request and claims no protection.
 await page.evaluate(()=>{ShoreQA.scene('settings');ShoreQA.activate('settings.group.privacy');ShoreQA.activate('dns.open');});
 await page.waitForFunction(()=>document.body.textContent.includes('Not connected'));
 assert.equal(gets,0);
 await page.keyboard.press('Escape');await page.keyboard.press('Escape');
 await page.evaluate(()=>{CleanHomeConfig.dnsProtection={endpoint:'http://127.0.0.1:18768',token:'x'.repeat(40)};ShoreQA.activate('settings.group.privacy');ShoreQA.activate('dns.open');});
 await page.waitForFunction(()=>document.body.textContent.includes('DNS filtering enabled'));
 assert.match(await page.locator('.dns-cards').innerText(),/30[\s\S]*120[\s\S]*25%/);
 assert.equal(await page.evaluate(()=>window.__injected),undefined);
 assert.equal(await page.locator('.dns-day').count(),7);
 const timing=await page.evaluate(()=>{var results=[],mutations=0,body=document.querySelector('.dns-scroll'),observer=new MutationObserver(function(rows){mutations+=rows.length;});observer.observe(body,{childList:true});for(var i=0;i<40;i++){var start=performance.now();ShoreQA.nav(i%2?'left':'right');body.offsetHeight;results.push(performance.now()-start);}mutations+=observer.takeRecords().length;observer.disconnect();results.sort(function(a,b){return a-b;});return {p95:results[Math.floor(results.length*.95)],max:results[results.length-1],bodyReplacements:mutations};});
 assert.equal(timing.bodyReplacements,0,'Remote navigation keeps the static statistics body intact');
 mkdirSync(root+'.local/qa',{recursive:true});writeFileSync(root+'.local/qa/dns-navigation'+(process.env.CLEANHOME_CHROMIUM?'-85':'')+'.json',JSON.stringify(timing,null,2)+'\n');

 assert(await page.evaluate(()=>{var panel=document.querySelector('.dns-panel').getBoundingClientRect(),hint=document.querySelector('.dns-hint').getBoundingClientRect(),pill=document.querySelector('.dns-pill').getBoundingClientRect(),hit=document.elementFromPoint(pill.left+pill.width/2,pill.top+pill.height/2);return hint.bottom<panel.bottom&&!!hit.closest('.dns-pill');}),'Pill is unobstructed and footer stays inside the panel');
 assert.equal(await page.evaluate(()=>ShoreQA.where().focusCount),1,'Only the privacy control is highlighted');
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 assert.match(await page.locator('.dns-cards').innerText(),/20[\s\S]*100[\s\S]*20%/);
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 assert.match(await page.locator('.dns-cards').innerText(),/10[\s\S]*20[\s\S]*50%/);
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 assert.match(await page.locator('.dns-cards').innerText(),/30[\s\S]*120[\s\S]*25%/);
 // Hardware-style arrow keys, not only programmatic clicks.
 await page.evaluate(()=>{ShoreQA.activate('dns.refresh');});await page.waitForFunction(()=>document.body.textContent.includes('DNS filtering enabled'));
 await page.keyboard.press('ArrowRight');await page.waitForTimeout(60);await page.keyboard.press('ArrowRight');await page.keyboard.press('Enter');
 assert.match(await page.locator('.dns-warning').innerText(),/until you enable/);
 assert.deepEqual(writes,[]);
 await page.keyboard.press('Escape');
 await page.evaluate(()=>ShoreQA.activate('dns.pause15'));
 await page.waitForFunction(()=>document.body.textContent.includes('Protection paused'));
 assert.deepEqual(writes,['pause15']);
 await page.evaluate(()=>ShoreQA.activate('dns.enable'));
 await page.waitForFunction(()=>document.body.textContent.includes('DNS filtering enabled'));
 assert.deepEqual(writes,['pause15','enable']);
 await page.evaluate(()=>{for(var i=0;i<25;i++)ShoreQA.nav('down');});
 assert(await page.evaluate(()=>{var e=document.querySelector('.dns-scroll');return e.scrollTop>500 && e.scrollTop+e.clientHeight>=e.scrollHeight-1;}),'All details reachable by remote');
 await page.evaluate(()=>{for(var i=0;i<25;i++)ShoreQA.nav('up');});
 mkdirSync(root+'.local/qa',{recursive:true});
 await page.screenshot({path:root+'.local/qa/dns-dashboard'+(process.env.CLEANHOME_CHROMIUM?'-85':'')+'.png'});
 if(process.argv.includes('--update-preview')){
  await page.evaluate(()=>{var label=document.createElement('div');label.id='dns-preview-label';label.textContent='BROWSER PREVIEW · TEST DATA';label.style.cssText='position:fixed;left:60px;bottom:42px;padding:10px 18px;border-radius:12px;background:#202125;color:#ddd;font:600 18px Manrope,sans-serif;z-index:1000;letter-spacing:1px';document.body.appendChild(label);});
  mkdirSync(root+'docs/images',{recursive:true});await page.screenshot({path:root+'docs/images/dns-protection-preview.png'});
  await page.evaluate(()=>document.getElementById('dns-preview-label').remove());
 }

 data.complete=false;await page.evaluate(()=>ShoreQA.activate('dns.refresh'));
 await page.waitForFunction(()=>document.body.textContent.includes('At least 30'));
 assert.match(await page.locator('.dns-cards strong').first().innerText(),/≥30/);
 data.complete=true;
 unavailable=true;await page.evaluate(()=>ShoreQA.activate('dns.refresh'));
 await page.waitForFunction(()=>document.body.textContent.includes('Protection unknown'));
 assert.equal(await page.locator('.dns-cards').count(),0,'Unavailable data is never presented as current');
 assert(!await page.evaluate(()=>ShoreQA.actions().includes('dns.disable')));
 unavailable=false;delay=300;
 await page.evaluate(()=>{ShoreQA.activate('dns.refresh');ShoreQA.nav('back');});
 await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>ShoreQA.where().view),'privacy');
 await page.keyboard.press('Escape');await page.keyboard.press('Escape');const before=gets;
 await page.waitForTimeout(1100);assert.equal(gets,before,'No polling or DNS stats on Home');
 assert.deepEqual(errors,[]);
 writeFileSync(root+'.local/qa/dns-browser'+(process.env.CLEANHOME_CHROMIUM?'-85':'')+'.json',JSON.stringify({engine:await preview.browser.version(),scope:'Browser fixtures, not TV traffic',errors,passed:true},null,2)+'\n');
 console.log('DNS dashboard workflow and error-state checks passed in '+await preview.browser.version());
}finally{await preview.close();}
