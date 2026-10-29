// Compare every cached shading variant against its original CSS on the same live UI.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {openPreview,root} from './browser.mjs';
const output=root+'.local/qa/backgrounds/';mkdirSync(output,{recursive:true});
const preview=await openPreview({publicFonts:true});
const report={engine:await preview.browser.version(),scope:'Original CSS versus cached background shading, all bundled walls and both layouts. Foreground layout checked separately; text antialiasing excluded from background pixels. Not an optical TV comparison.',checks:[],errors:[]};
try{
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',error=>report.errors.push(error.message));
 await page.clock.setFixedTime(new Date('2026-10-29T12:00:00Z'));
 await page.route('https://**/*',route=>route.abort());
 await page.addInitScript(()=>localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false})));
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready());
 const walls=await page.evaluate(()=>CleanFrameWallpapers.map(wall=>wall.id));
 for(const wall of walls)for(const layout of ['dock','list']){
  await page.evaluate(patch=>ShoreQA.look(patch),{wall,layout,bg:'photo'});
  await page.waitForFunction(()=>ShoreQA.ready());await page.waitForTimeout(240);
  const name=wall+'-'+layout;
  await page.evaluate(()=>{document.querySelector('link[href*="background-overlays"]').disabled=true;});
  await page.waitForTimeout(80);const before=await page.evaluate(()=>ShoreQA.where());
  await page.addStyleTag({content:'.home{visibility:hidden!important}'});
  await page.screenshot({path:output+name+'-original.png'});
  await page.evaluate(()=>{document.querySelector('link[href*="background-overlays"]').disabled=false;});
  await page.waitForFunction(()=>getComputedStyle(document.getElementById('bg'),'::after').backgroundImage.indexOf('url(')===0);
  await page.evaluate(async()=>{
   const css=getComputedStyle(document.getElementById('bg'),'::after').backgroundImage;
   const image=new Image();image.src=css.slice(5,-2);await image.decode();
  });
  await page.waitForTimeout(80);const after=await page.evaluate(()=>ShoreQA.where());
  // visibility:hidden preserves layout. Compare geometry again after restoring content.
  await page.evaluate(()=>{const rules=Array.from(document.querySelectorAll('style'));rules.filter(s=>s.textContent==='.home{visibility:hidden!important}').forEach(s=>s.remove());});
  const restored=await page.evaluate(()=>ShoreQA.where());
  assert.deepEqual(restored,before,name+': focus/geometry unchanged');
  await page.addStyleTag({content:'.home{visibility:hidden!important}'});
  await page.screenshot({path:output+name+'-cached.png'});
  await page.evaluate(()=>{Array.from(document.querySelectorAll('style')).filter(s=>s.textContent==='.home{visibility:hidden!important}').forEach(s=>s.remove());});
  report.checks.push(name);
 }
 assert.equal(report.errors.length,0);
 const python=process.env.CLEANHOME_PYTHON||root+'.local/venv/bin/python';
 const comparison=spawnSync(python,['-c',`import json,sys
from PIL import Image,ImageChops,ImageStat
from pathlib import Path
out=[]
for name in json.loads(sys.stdin.read()):
 a=Image.open(Path(sys.argv[1])/(name+'-original.png')).convert('RGB')
 b=Image.open(Path(sys.argv[1])/(name+'-cached.png')).convert('RGB')
 d=ImageChops.difference(a,b)
 maximum=max(v[1] for v in d.getextrema());mean=sum(ImageStat.Stat(d).mean)/3
 out.append({'variant':name,'maximumChannelDifference':maximum,'meanChannelDifference':mean})
print(json.dumps(out))
`,output],{input:JSON.stringify(report.checks),encoding:'utf8'});
 assert.equal(comparison.status,0,comparison.stderr);report.pixels=JSON.parse(comparison.stdout);
 // Six original translucent shading layers round at each blend; their flattened
 // RGBA cache differs by at most six 8-bit channel levels (mean under 1.25).
 for(const pixel of report.pixels){assert.ok(pixel.maximumChannelDifference<=6,pixel.variant+': shading changed');assert.ok(pixel.meanChannelDifference<1.25,pixel.variant+': overall colour changed');}
 console.log(JSON.stringify({engine:report.engine,variants:report.checks.length,maximumChannelDifference:Math.max(...report.pixels.map(p=>p.maximumChannelDifference)),errors:report.errors}));
}finally{writeFileSync(output+'results.json',JSON.stringify(report,null,2)+'\n');await preview.close();}
