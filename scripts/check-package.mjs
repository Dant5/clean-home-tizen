// Exercise the actual generic unsigned release bytes; no device is contacted.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPreview,root} from './browser.mjs';
const widgetPath=process.argv[2]||root+'dist/CleanHome-Q60B-unsigned.wgt';
const report={scope:'Actual generic widget; mocked Tizen inventory; no TV contacted',sha256:createHash('sha256').update(readFileSync(widgetPath)).digest('hex'),checks:[],errors:[]};
const check=(name,value)=>{assert.ok(value,name);report.checks.push(name);};
const preview=await openPreview({widgetPath});report.engine=await preview.browser.version();
try{
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',e=>report.errors.push(e.message));await page.route('https://**/*',r=>r.abort());
 await page.addInitScript(()=>{
  window.__launches=[];
  window.tizen={application:{getAppsInfo(ok){ok([{id:'VideoTV001.Video',name:'YouTube',show:true}]);},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};},launch(id,ok){__launches.push(id);ok();}}};
  if(!localStorage.getItem('cleanhome.home.v1'))localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false}));
 });
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready()&&ShoreQA.state().catalog.loaded);
 check('No personal verified-app profile',await page.evaluate(()=>!CleanHomeConfig.verifiedAppIds||!Object.keys(CleanHomeConfig.verifiedAppIds).length));
 check('Fresh widget starts empty with one plus',await page.evaluate(()=>!ShoreQA.state().dock.length&&document.querySelectorAll('[data-action="home.add-app"]').length===1));
 check('No automatic app launch',await page.evaluate(()=>!__launches.length));
 await page.keyboard.press('Enter');await page.waitForFunction(()=>ShoreQA.actions().some(a=>a.indexOf('apps.open.')===0));
 await page.evaluate(()=>ShoreQA.activate(ShoreQA.actions().filter(a=>a.indexOf('apps.open.')===0)[0]));
 check('Picker saves discovered app without launching',await page.evaluate(()=>ShoreQA.state().dock.length===1&&!__launches.length));
 await page.keyboard.press('Enter');check('Short Select launches the actual discovered ID',await page.evaluate(()=>__launches.length===1&&__launches[0]==='VideoTV001.Video'));
 await page.reload();await page.waitForFunction(()=>ShoreQA.ready());
 check('Reload preserves the chosen app',await page.evaluate(()=>ShoreQA.state().dock.length===1));
 check('Reload never launches it automatically',await page.evaluate(()=>!__launches.length));
 check('No runtime errors',!report.errors.length);
}finally{mkdirSync(root+'.local/qa',{recursive:true});writeFileSync(root+'.local/qa/package'+(process.env.CLEANHOME_CHROMIUM?'-chromium85':'')+'.json',JSON.stringify(report,null,2)+'\n');await preview.close();console.log(report.checks.length+' packaged-widget checks passed in '+report.engine);}
