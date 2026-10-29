// First-run and upgrade checks use actual remote-style DOM key events.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const preview=await openPreview({publicFonts:true});
const report={engine:await preview.browser.version(),checks:[],errors:[]};
const check=(name,condition)=>{assert.ok(condition,name);report.checks.push(name);};
async function open(seed){
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',e=>report.errors.push(e.message));await page.route('https://**/*',r=>r.abort());
 await page.addInitScript(seed=>{
  if(!sessionStorage.getItem('seeded')){if(seed)localStorage.setItem('cleanhome.home.v1',JSON.stringify(seed));sessionStorage.setItem('seeded','yes');}
  const original=Storage.prototype.setItem;window.__failSave=false;
  Storage.prototype.setItem=function(k,v){if(window.__failSave&&k==='cleanhome.home.v1')throw new DOMException('Full','QuotaExceededError');return original.call(this,k,v);};
  window.__launches=[];
  window.tizen={application:{getAppsInfo(ok){setTimeout(()=>ok([
   {id:'AppOne0001.Main',name:'Alpha',show:true},{id:'AppTwo0002.Main',name:'Beta',show:true},
   {id:'AppThree03.Main',name:'Gamma',show:true},{id:'ExtraFour1.Main',name:'Delta',show:true},{id:'ExtraFive1.Main',name:'Epsilon',show:true},{id:'ExtraSix01.Main',name:'Zeta',show:true},{id:'ExtraSeven.Main',name:'Eta',show:true},{id:'VideoTV001.Video',name:'YouTube',show:true},{id:'MusicTV001.Player',name:'Spotify',show:true}
  ]),20);},launch(id,ok){__launches.push(id);ok();},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};}}};
 },seed);
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready()&&ShoreQA.state().catalog.loaded&&!ShoreQA.state().catalog.loading);return page;
}
const state=page=>page.evaluate(()=>ShoreQA.state());
const act=async(page,action)=>{await page.waitForFunction(action=>ShoreQA.actions().indexOf(action)>=0,action);return page.evaluate(action=>{if(!ShoreQA.activate(action))throw Error('Missing action: '+action);},action);};
try{
 let page=await open();
 check('Fresh install has no assumed favourites',(await state(page)).dock.length===0);
 check('Fresh install shows exactly one focused plus',await page.evaluate(()=>document.querySelectorAll('.dock .tile').length===1&&document.querySelector('[data-action="home.add-app"].is-focus')));
 await page.keyboard.press('Enter');check('Plus opens the installed-app picker',(await state(page)).view==='apps');
 await act(page,'apps.open.AppOne0001.Main');
 check('Choosing an app fills the first slot',JSON.stringify((await state(page)).dock)==='["AppOne0001.Main"]');
 check('Choosing never launches the app',await page.evaluate(()=>__launches.length===0));
 check('One plus remains after adding',await page.evaluate(()=>document.querySelectorAll('[data-action="home.add-app"]').length===1));
 await page.keyboard.press('ArrowRight');await page.keyboard.press('Enter');await act(page,'apps.open.AppTwo0002.Main');
 check('Second choice appends to the plus position',JSON.stringify((await state(page)).dock)==='["AppOne0001.Main","AppTwo0002.Main"]');
 await page.keyboard.down('Enter');await page.keyboard.down('Enter');await page.waitForTimeout(750);
 check('Holding OK opens replacement without launching',(await state(page)).view==='apps'&&await page.evaluate(()=>__launches.length===0));
 await page.keyboard.up('Enter');check('Releasing a long press does not choose an app',(await state(page)).view==='apps');
 await act(page,'apps.open.AppThree03.Main');
 check('Replacement preserves the slot and other favourites',JSON.stringify((await state(page)).dock)==='["AppOne0001.Main","AppThree03.Main"]');
 await page.keyboard.press('Enter');check('Short OK launches once',await page.evaluate(()=>__launches.length===1&&__launches[0]==='AppThree03.Main'));
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.keyboard.down('Enter');await page.keyboard.press('ArrowLeft');await page.keyboard.up('Enter');await page.waitForTimeout(700);
 check('Navigation cancels a pending hold',(await state(page)).view==='home'&&await page.evaluate(()=>__launches.length===1));
 await page.keyboard.down('Enter');await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await page.keyboard.up('Enter');await page.waitForTimeout(700);
 check('Blur cancels a pending hold',(await state(page)).view==='home'&&await page.evaluate(()=>__launches.length===1));
 await page.keyboard.down('Enter');await page.waitForTimeout(700);await page.keyboard.up('Enter');
 const before=(await state(page)).dock;
 await page.evaluate(()=>window.__failSave=true);await act(page,'apps.open.AppTwo0002.Main');
 check('Save failure keeps the old slot and picker',JSON.stringify((await state(page)).dock)===JSON.stringify(before)&&(await state(page)).view==='apps');
 await page.evaluate(()=>window.__failSave=false);await page.keyboard.press('Escape');
 check('Cancel does not change the dock',JSON.stringify((await state(page)).dock)===JSON.stringify(before));
 await page.reload();await page.waitForFunction(()=>ShoreQA.ready()&&!ShoreQA.state().catalog.loading);
 check('Custom choices and the add tile survive reload',JSON.stringify((await state(page)).dock)===JSON.stringify(before)&&await page.evaluate(()=>!!document.querySelector('[data-action="home.add-app"]')));
 await page.evaluate(()=>ShoreQA.look({layout:'list'}));await page.waitForFunction(()=>ShoreQA.ready());
 check('The list layout also renders an add row',await page.evaluate(()=>!!document.querySelector('.ph-row[data-action="home.add-app"]')));
 await page.close();
 page=await open({home:['youtube','nuvio','spotify','moonlight'],lastApp:'spotify',dailyBing:false,ui:3,look:{apps:'icons',layout:'dock'}});
 check('Existing four favourites retain exact order',JSON.stringify((await state(page)).dock)==='["youtube","nuvio","spotify","moonlight"]');
 check('Existing installs receive no extra add tile',await page.evaluate(()=>!document.querySelector('[data-action="home.add-app"]')));
 check('Existing last selection is preserved',(await state(page)).selected==='spotify');
 await page.keyboard.press('Enter');check('Existing apps still launch with short OK',await page.evaluate(()=>__launches.length===1));
 await page.close();
 page=await open({home:['AppOne0001.Main','AppTwo0002.Main','AppThree03.Main','ExtraFour1.Main','ExtraFive1.Main','ExtraSix01.Main','VideoTV001.Video','MusicTV001.Player'],addTile:true,dailyBing:false});
 await act(page,'home.add-app');await act(page,'apps.open.AppOne0001.Main');
 check('Choosing an existing favourite does not duplicate it',(await state(page)).dock.length===8&&(await state(page)).view==='apps');
 await act(page,'apps.open.ExtraSeven.Main');
 check('Ninth choice fills the final slot',(await state(page)).dock.length===9&&(await state(page)).dock[8]==='ExtraSeven.Main');
 check('Full dock hides the add tile',await page.evaluate(()=>!document.querySelector('[data-action="home.add-app"]')));
 await page.keyboard.down('Enter');await page.waitForTimeout(700);await page.keyboard.up('Enter');await act(page,'apps.open.AppOne0001.Main');
 check('Replacement cannot create a duplicate',(await state(page)).dock.length===9&&(await state(page)).dock[8]==='ExtraSeven.Main'&&(await state(page)).view==='apps');
 await page.keyboard.press('Escape');await page.close();
 check('No uncaught runtime errors',report.errors.length===0);
 console.log(JSON.stringify({engine:report.engine,checks:report.checks.length,errors:report.errors}));
}finally{mkdirSync(root+'.local/qa',{recursive:true});writeFileSync(root+'.local/qa/onboarding.json',JSON.stringify(report,null,2)+'\n');await preview.close();}
