// Viewport checks validate layout and navigation, not unowned TV hardware.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const preview=await openPreview({publicFonts:true});
const report={engine:await preview.browser.version(),scope:'Mock TV at 720p, 768p, 1080p, 1440p and 4K; also ultrawide and 4:3 letterboxing.',checks:[],errors:[]};
try{
 for(const [width,height] of [[1280,720],[1366,768],[1920,1080],[2560,1440],[3840,2160],[2560,1080],[1024,768]]){
  const page=await preview.browser.newPage({viewport:{width,height}});page.on('pageerror',e=>report.errors.push(e.message));
  await page.route('https://**/*',r=>r.abort());
  await page.addInitScript(()=>{
   localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false,home:['youtube','nuvio','spotify','moonlight'],addTile:true}));
   window.tizen={application:{getAppsInfo(ok){ok([]);},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};}}};
  });
  await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready());
  for(const scene of ['home','apps','settings','editor']){
   await page.evaluate(scene=>ShoreQA.scene(scene),scene);
   const bounds=await page.evaluate(()=>{
    const stage=document.querySelector('.stage').getBoundingClientRect();
    const visible=Array.prototype.filter.call(document.querySelectorAll('.is-focus[data-action]'),e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0&&getComputedStyle(e).visibility!=='hidden';});
    return {stage:{x:stage.x,y:stage.y,right:stage.right,bottom:stage.bottom,width:stage.width,height:stage.height},focus:visible.map(e=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,right:b.right,bottom:b.bottom};}),scroll:document.documentElement.scrollWidth>innerWidth+1||document.documentElement.scrollHeight>innerHeight+1};
   });
   assert.ok(bounds.stage.x>=-1&&bounds.stage.y>=-1&&bounds.stage.right<=width+1&&bounds.stage.bottom<=height+1,`${width}x${height} ${scene}: stage fits`);
   assert.ok(Math.abs(bounds.stage.width/bounds.stage.height-16/9)<0.01,'Original aspect ratio retained');
   assert.ok(!bounds.scroll,'No viewport overflow');
   assert.ok(bounds.focus.length===1,`${width}x${height} ${scene}: exactly one visible focus (${bounds.focus.length})`);
   assert.ok(bounds.focus.every(b=>b.x>=-1&&b.y>=-1&&b.right<=width+1&&b.bottom<=height+1),'Focused control is on screen');
   report.checks.push(`${width}x${height} ${scene}: fits, aspect ratio, no overflow, one visible focus`);
  }
  await page.evaluate(()=>ShoreQA.scene('home'));await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>ShoreQA.state().selected),'nuvio');
  report.checks.push(`${width}x${height}: real keyboard navigation`);await page.close();
 }
 assert.equal(report.errors.length,0);console.log(JSON.stringify({engine:report.engine,checks:report.checks.length,errors:report.errors}));
}finally{mkdirSync(root+'.local/qa',{recursive:true});writeFileSync(root+'.local/qa/responsive.json',JSON.stringify(report,null,2)+'\n');await preview.close();}
