// Reproducible public documentation images: mock inventory, fixed clock, offline.
import {mkdirSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const p=await openPreview({publicFonts:true});mkdirSync(root+'docs/images',{recursive:true});
try{
 for(const fresh of [false,true]){
  const page=await p.browser.newPage({viewport:{width:1920,height:1080}});await page.route('https://**/*',r=>r.abort());
  await page.addInitScript(fresh=>{
   const RealDate=Date;function FixedDate(){return arguments.length?new (Function.prototype.bind.apply(RealDate,[null].concat(Array.prototype.slice.call(arguments))))():new RealDate('2026-10-29T10:24:00Z');}
   FixedDate.now=()=>RealDate.parse('2026-10-29T10:24:00Z');FixedDate.parse=RealDate.parse;FixedDate.UTC=RealDate.UTC;FixedDate.prototype=RealDate.prototype;window.Date=FixedDate;
   localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false,home:fresh?[]:['youtube','spotify','moonlight'],addTile:true,wall:'misty',ui:3,look:{apps:'icons',layout:'dock'}}));
   window.tizen={application:{getAppsInfo(ok){ok([{id:'VideoTV001.Video',name:'YouTube',show:true},{id:'MusicTV001.Player',name:'Spotify',show:true},{id:'StreamTV01.Main',name:'Moonlight',show:true}]);},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};}}};
  },fresh);
  await page.goto(p.baseURL);await page.waitForFunction(()=>ShoreQA.ready()&&ShoreQA.state().catalog.loaded);await page.waitForTimeout(400);
  await page.screenshot({path:root+'docs/images/'+(fresh?'first-run':'home-example')+'.jpg',type:'jpeg',quality:85});
  if(fresh){await page.keyboard.press('Enter');await page.waitForTimeout(200);await page.screenshot({path:root+'docs/images/app-picker.jpg',type:'jpeg',quality:85});}
  await page.close();
 }
}finally{await p.close();}
