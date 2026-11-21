// Opt-in file-origin browser -> real loopback adapter -> real AdGuard integration.
// Never points at a TV or production LAN. Test device labels are not real hardware.
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {chromium} from 'playwright';
import {pathToFileURL} from 'node:url';
const root=new URL('../',import.meta.url).pathname;
const profile=JSON.parse(readFileSync(root+'.local/dns-protection/browser-lab/widget.json','utf8'));
assert.equal(profile.endpoint,'http://127.0.0.1:8768');
const browser=await chromium.launch({headless:true,...(process.env.CLEANHOME_CHROMIUM?{executablePath:process.env.CLEANHOME_CHROMIUM}:{})});
const page=await browser.newPage({viewport:{width:1920,height:1080}});const errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.route('https://**/*',r=>r.abort());
 await page.goto(pathToFileURL(root+'app/index.html').href);
 await page.waitForFunction(()=>typeof ShoreQA!=='undefined'&&ShoreQA.ready());
 await page.evaluate(c=>{CleanHomeConfig.dnsProtection=c;ShoreQA.scene('settings');ShoreQA.activate('settings.group.privacy');},profile);
 await page.waitForFunction(()=>document.body.textContent.includes('DNS filtering enabled'));
 assert.match(await page.locator('.dns-scroll').innerText(),/TV: DNS received[\s\S]*Soundbar: DNS received/);
 assert.equal(await page.locator('.dns-cards strong').nth(1).innerText(),'4');
 assert.equal(await page.locator('.dns-cards strong').nth(0).innerText(),'2');
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 assert.equal(await page.locator('.dns-cards strong').nth(1).innerText(),'2');
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 assert.equal(await page.locator('.dns-cards strong').nth(0).innerText(),'1');
 await page.evaluate(()=>ShoreQA.activate('dns.device'));
 await page.evaluate(()=>ShoreQA.activate('dns.pause15'));
 await page.waitForFunction(()=>document.body.textContent.includes('Protection paused'));
 await page.evaluate(()=>ShoreQA.activate('dns.enable'));
 await page.waitForFunction(()=>document.body.textContent.includes('DNS filtering enabled'));
 assert.deepEqual(errors,[]);
 mkdirSync(root+'.local/qa',{recursive:true});
 const suffix=process.env.CLEANHOME_CHROMIUM?'-85':'';
 await page.screenshot({path:root+'.local/qa/dns-real-loopback'+suffix+'.png'});
 writeFileSync(root+'.local/dns-protection/live-browser'+suffix+'.json',JSON.stringify({scope:'File-origin browser through real loopback adapter and AdGuard; controlled test traffic, not hardware',engine:await browser.version(),passed:true,errors},null,2)+'\n');
 console.log('Real file-origin dashboard/adapter/resolver integration passed in '+await browser.version());
}finally{await browser.close();}
