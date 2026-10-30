// Exercise real XHR completion and cancellation when the engine has no AbortController.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
import {installOnboarding} from '../tests/fixtures/onboarding.mjs';
const preview=await openPreview({publicFonts:true});let checks=0;
try{
 for(const scenario of ['success','malformed','timeout']){
  const page=await preview.browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(installOnboarding,null);
  await page.addInitScript(()=>{window.AbortController=undefined;window.__xhrAborts=0;const abort=XMLHttpRequest.prototype.abort;XMLHttpRequest.prototype.abort=function(){__xhrAborts++;return abort.apply(this,arguments);};const timer=window.setTimeout;window.setTimeout=function(fn,ms){return timer(fn,ms===10000?250:ms);};});
  const archives=[];await page.route('https://**/*',route=>{
   if(route.request().url().includes('HPImageArchive')){archives.push(route.request());if(scenario==='timeout')return;return route.fulfill({contentType:'application/json',body:scenario==='malformed'?'{broken':JSON.stringify({images:[{url:'/th?id=OHR.Compatible_en-US123_1920x1080.jpg'}]})});}
   return route.fulfill({contentType:'image/jpeg',body:readFileSync(root+'app/assets/wallpapers/misty.jpg')});
  });
  await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready());
  if(scenario==='success'){await page.waitForFunction(()=>document.querySelector('img.photo').src.includes('Compatible')&&document.querySelector('img.photo').naturalWidth>0);assert(archives.some(r=>r.resourceType()==='xhr'));checks+=2;}
  else {await page.waitForTimeout(600);assert(await page.evaluate(()=>document.querySelector('img.photo').naturalWidth>0));checks++;if(scenario==='timeout'){assert(await page.evaluate(()=>__xhrAborts>0));checks++;}}
  assert.equal(errors.length,0,scenario+' runtime errors');checks++;await page.close();
 }
 console.log(checks+' legacy photo-network checks passed');
}finally{await preview.close();}
