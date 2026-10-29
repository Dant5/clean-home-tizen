// Exercise real DOM keyboard input before optional startup work has completed.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const preview=await openPreview({publicFonts:true});
const report={engine:await preview.browser.version(),scope:'Browser CPU 4x; actual keyboard events and production UI, mocked TV/network. Not physical-remote or hardware-wake timing.',checks:[],runs:[]};
try{
 for(const daily of [false,true]){
  const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
  const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.route('https://**/*',async route=>{
   if(route.request().url().includes('HPImageArchive'))return route.fulfill({contentType:'application/json',body:JSON.stringify({images:[{url:'/th?id=OHR.Startup_1920x1080.jpg'}]})});
   if(route.request().url().startsWith('https://www.bing.com/th?')){await new Promise(resolve=>setTimeout(resolve,300));return route.fulfill({contentType:'image/jpeg',body:readFileSync(root+'app/assets/wallpapers/misty.jpg')});}
   return route.abort();
  });
  await page.addInitScript(daily=>{
   localStorage.setItem('cleanhome.home.v1',JSON.stringify({home:['youtube','nuvio','spotify','moonlight'],dailyBing:daily}));
   window.tizen={application:{getAppsInfo(ok){window.__releaseStartupCatalog=()=>ok([]);},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};}}};
   window.__startupKeys=[];
   document.addEventListener('keydown',event=>{
    const at=performance.now();requestAnimationFrame(()=>{
     const tile=document.querySelector('.dock .tile.is-focus');
     __startupKeys.push({code:event.keyCode,eventAgeMs:at-event.timeStamp,nextFrameMs:performance.now()-at,focus:tile&&tile.getAttribute('data-action')});
    });
   },true);
  },daily);
  await page.goto(preview.baseURL,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.ShoreQA&&document.querySelector('[data-action="home.app.youtube"].is-focus'));
  // Deliberately do not wait for network idle, QA.ready, registry completion or warm-up.
  for(let i=0;i<24;i++){
   const expected=i%2?'youtube':'nuvio';
   await page.keyboard.press(i%2?'ArrowLeft':'ArrowRight');
   await page.waitForFunction(expected=>document.querySelector('[data-action="home.app.'+expected+'"].is-focus'),expected,{timeout:1500});
   await page.waitForTimeout(60);
  }
  await page.waitForFunction(()=>window.__releaseStartupCatalog);
  assert.equal(await page.evaluate(()=>ShoreQA.state().catalog.loading),true,'Registry stayed pending during first inputs');
  await page.evaluate(()=>__releaseStartupCatalog());
  await page.waitForFunction(()=>!ShoreQA.state().catalog.loading&&ShoreQA.ready());
  const keys=await page.evaluate(()=>__startupKeys);assert.equal(keys.length,24);assert.equal(errors.length,0);
  report.checks.push('First 24 real arrow presses work while registry is pending, daily='+daily);
  report.runs.push({daily,keys,errors});await page.close();
 }
 console.log(JSON.stringify({engine:report.engine,checks:report.checks.length,keys:report.runs.reduce((n,r)=>n+r.keys.length,0),maximumFrameMs:Math.max(...report.runs.flatMap(r=>r.keys.map(k=>k.nextFrameMs)))}));
}finally{mkdirSync(root+'.local/qa/startup-input',{recursive:true});writeFileSync(root+'.local/qa/startup-input/results.json',JSON.stringify(report,null,2)+'\n');await preview.close();}
