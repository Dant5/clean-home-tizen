// Check the local setup page with a fake companion. No TV is contacted.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {chromium} from 'playwright';
const server=spawn('python3',['tests/fixtures/home-setup-server.py'],{stdio:['ignore','pipe','pipe']});
let browser;
try{
 const url=await new Promise((resolve,reject)=>{let text='';server.stdout.on('data',b=>{text+=b;const m=text.match(/http:\/\/127\.0\.0\.1:\d+/);if(m)resolve(m[0]);});server.once('exit',()=>reject(Error('Setup fixture failed')));setTimeout(()=>reject(Error('Setup fixture timeout')),10000).unref();});
 browser=await chromium.launch({headless:true,executablePath:process.env.CLEANHOME_CHROMIUM||undefined,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[],calls=[];
 const click=async selector=>{const box=await page.$eval(selector,e=>{e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};});await page.mouse.click(box.x,box.y);};
 const fill=async(selector,text)=>{await page.$eval(selector,e=>e.focus());await page.keyboard.press('Control+A');await page.keyboard.type(text);};
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST')calls.push(r.url());});
 await page.addInitScript(()=>{window.__requests=[];const original=window.fetch;window.fetch=function(url,options){if(options&&options.method==='POST')window.__requests.push(JSON.parse(options.body));return original.apply(this,arguments);};});
 await page.goto(url);assert(await page.locator('#apply').isDisabled());assert(await page.locator('#undo').isDisabled());
 await click('#consent');assert(await page.locator('#apply').isDisabled());
 await fill('#host','TV_FIXTURE');await click('#inspect');
 await page.waitForFunction(()=>!document.getElementById('apply').disabled);assert.equal(calls.length,1);assert.equal(await page.evaluate(()=>__requests[0].action),'diagnose');
 mkdirSync('.local/qa/home-setup',{recursive:true});await page.screenshot({path:'.local/qa/home-setup/ready.png',fullPage:true});
 await fill('#host','DIFFERENT_TV');assert(await page.locator('#apply').isDisabled());await fill('#host','TV_FIXTURE');assert(await page.locator('#apply').isDisabled());
 await click('#inspect');await page.waitForFunction(()=>!document.getElementById('apply').disabled);await click('#apply');await page.waitForFunction(()=>document.getElementById('message').textContent==='Clean Home setup verified.');
 assert.equal(await page.evaluate(()=>__requests.filter(c=>c.action==='apply').length),1);assert.equal(await page.evaluate(()=>__requests.find(c=>c.action==='apply').confirmed),true);assert(await page.locator('#apply').isDisabled());assert.equal(await page.$eval('#reportPreview',e=>JSON.parse(e.textContent).action),'apply');
 await click('#inspect');await page.waitForFunction(()=>document.getElementById('message').textContent==='Clean Home is already set up.');assert(await page.locator('#undo').isDisabled());
 await click('#undoConsent');assert(await page.locator('#undo').isEnabled());await click('#undo');await page.waitForFunction(()=>document.getElementById('message').textContent==='Original Samsung Home restored.');
 assert.equal(await page.evaluate(()=>__requests.filter(c=>c.action==='undo').length),1);assert.equal(await page.evaluate(()=>__requests.find(c=>c.action==='undo').confirmed),true);
 await fill('#host','UNSUPPORTED');await click('#inspect');await page.waitForFunction(()=>document.getElementById('message').textContent.indexOf('needs review')>=0);assert(await page.locator('#apply').isDisabled());assert(await page.locator('#undo').isDisabled());
 await click('#checksDisclosure > summary');assert.equal(await page.locator('#checks p').count(),15);assert((await page.locator('#checks').innerText()).includes('MISSING_SYMBOL'));assert(await page.locator('#send').isDisabled());
 assert.equal(await page.evaluate(()=>__requests.filter(c=>c.action==='send-report').length),0);
 const nonce=await page.$eval('script[nonce]',e=>e.nonce);const savedResponse=await fetch(url+'/report/'+nonce+'.json');assert(savedResponse.headers.get('content-disposition').includes('clean-home-compatibility.json'));const saved=await savedResponse.text();assert(!saved.includes('UNSUPPORTED')&&!saved.includes('PRIVATE_LOCAL_RECOVERY'));assert.equal(JSON.parse(saved).profile,'needs-review');await click('#save');
 await click('#reportConsent');await click('#send');await page.waitForFunction(()=>document.getElementById('receipt').textContent.indexOf('Report received.')===0);
 assert.equal(await page.evaluate(()=>__requests.find(c=>c.action==='send-report').confirmed),true);
 await click('#send');await page.waitForFunction(()=>document.getElementById('receipt').textContent.indexOf('Already received.')===0);
 await page.screenshot({path:'.local/qa/home-setup/unsupported-report.png',fullPage:true});
 await fill('#host','DIFFERENT_TV');assert(await page.locator('#send').isDisabled());assert.deepEqual(errors,[]);
 console.log('Local Home Setup + cross-model report flows passed in '+await browser.version()+'. Fake devices/receiver only.');
}finally{if(browser)await browser.close();server.kill();}
