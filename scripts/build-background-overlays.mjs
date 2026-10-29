// Render the existing CSS shading once, with the same Chromium generation as the Q60B.
// Only the fixed shading is cached; photographs, content and navigation stay live.
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {openPreview,root} from './browser.mjs';
const output=root+'app/assets/background-overlays/';
const preview=await openPreview({publicFonts:true});
const manifest={engine:await preview.browser.version(),sourceHashes:Object.fromEntries(['app/style.css','app/assets/adaptive-ink.js','app/assets/wallpapers/catalog.js'].map(file=>[file,createHash('sha256').update(readFileSync(root+file)).digest('hex')])),entries:[]};
try{
 if(!manifest.engine.startsWith('85.'))throw Error('Use CLEANHOME_CHROMIUM with Chromium 85 to regenerate the Q60B shading.');
 mkdirSync(output,{recursive:true});
 const page=await preview.browser.newPage({viewport:{width:1920,height:1080}});
 // Always render the original CSS, including when regenerating an existing cache.
 await page.route('**/assets/background-overlays/overlays.css',route=>route.fulfill({contentType:'text/css',body:''}));
 await page.route('https://**/*',route=>route.abort());
 await page.addInitScript(()=>localStorage.setItem('cleanhome.home.v1',JSON.stringify({dailyBing:false})));
 await page.goto(preview.baseURL);await page.waitForFunction(()=>ShoreQA.ready());
 await page.addStyleTag({content:'html,body,.stage,.scene{background:transparent!important}.home,.appearance,.sheet{display:none!important}#bg>.photo{visibility:hidden!important}'});
 const walls=await page.evaluate(()=>CleanFrameWallpapers.map(wall=>wall.id));
 for(const wall of walls)for(const layout of ['dock','list']){
  await page.evaluate(patch=>ShoreQA.look(patch),{wall,layout,bg:'photo'});
  await page.waitForFunction(({wall,layout})=>ShoreQA.ready()&&ShoreQA.state().shown.wall===wall&&ShoreQA.state().layout===layout,{wall,layout});
  const png=await page.screenshot({omitBackground:true,clip:{x:0,y:0,width:1920,height:1080}});
  const file=createHash('sha256').update(png).digest('hex').slice(0,16)+'.png';
  writeFileSync(output+file,png);manifest.entries.push({wall,layout,file});
 }
 const groups=new Map();
 for(const entry of manifest.entries){
  if(!groups.has(entry.file))groups.set(entry.file,[]);
  groups.get(entry.file).push('.stage.bg-photo.l-'+entry.layout+'[data-wall="'+entry.wall+'"]');
 }
 const css=['/* Generated from the original style.css by build-background-overlays.mjs; do not edit. */'];
 for(const [file,selectors] of groups){
  css.push(selectors.map(s=>s+' #bg>div').join(',')+'{display:none!important}');
  css.push(selectors.map(s=>s+' #bg::after').join(',')+'{content:"";position:absolute;left:0;top:0;width:1920px;height:1080px;pointer-events:none;background:url("'+file+'") no-repeat}');
 }
 writeFileSync(output+'overlays.css',css.join('\n')+'\n');
 writeFileSync(output+'manifest.json',JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({entries:manifest.entries.length,unique:groups.size,engine:manifest.engine}));
}finally{await preview.close();}
