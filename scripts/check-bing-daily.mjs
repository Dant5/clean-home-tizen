// Real launcher, mocked network only. No TV, provider or personal data contacted.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { openPreview } from './browser.mjs';
const p = await openPreview({ publicFonts: true });
const jpg = fs.readFileSync('app/assets/wallpapers/alpine-thumb.jpg');
const results = [];
const image = (name, date) => ({ url: '/th?id=OHR.' + name + '_1920x1080.jpg', startdate: date, fullstartdate: date + '0800' });
async function scenario(timezoneId) {
  const ctx = await p.browser.newContext({ timezoneId });
  const page = await ctx.newPage();
  const state = { image: image('Old', '20261107'), fail: false, calls: [] };
  await page.clock.setFixedTime(new Date('2026-11-07T15:30:00Z'));
  await page.addInitScript(() => {
    window.tizen = { application: { getAppsInfo: ok => ok([]), getCurrentApplication: () => ({ appInfo: { version: 'test' }, getRequestedAppControl: () => null }) }, tvinputdevice: { registerKeyBatch() {}, getSupportedKeys: () => [] } };
    localStorage.setItem('cleanhome.home.v1', JSON.stringify({ version: 2, ui: 3, look: { apps: 'icons', bg: 'photo' }, home: [], dailyBing: true }));
    window.__archiveOptions = [];
    const fetch = window.fetch;
    window.fetch = function (url, options) { if (String(url).includes('HPImageArchive')) window.__archiveOptions.push(options); return fetch.apply(this, arguments); };
    const decode = HTMLImageElement.prototype.decode;
    if (decode) HTMLImageElement.prototype.decode = function () { return window.__badDecode && this.src.includes('OHR.New') ? Promise.reject(Error('mock decode')) : decode.call(this); };
  });
  await page.route('https://**/*', r => {
    const url = r.request().url();
    if (!url.startsWith('https://www.bing.com/')) return r.abort();
    if (url.includes('HPImageArchive')) {
      state.calls.push(url);
      if (state.fail) return r.fulfill({ status: 503, body: '' });
      const n = +new URL(url).searchParams.get('n');
      return r.fulfill({ contentType: 'application/json', headers: { 'Cache-Control': 'max-age=86400' }, body: JSON.stringify({ images: n === 1 ? [state.image] : [image('Manual', '20261106')] }) });
    }
    return r.fulfill({ contentType: 'image/jpeg', body: jpg });
  });
  const diag = () => page.evaluate(() => ShoreQA.bing());
  const wait = id => page.waitForFunction(id => ShoreQA.bing().selectedIdentity === id && !ShoreQA.bing().busy, id);
  const resume = async time => { await page.clock.setFixedTime(new Date(time)); await page.evaluate(() => document.dispatchEvent(new Event('resume'))); await page.waitForTimeout(200); };
  await page.goto(p.baseURL); await wait('Old');
  assert.equal((await diag()).publication, '20261107');
  assert.equal((await diag()).selectedImageId, 'OHR.Old');
  const oldStamp = (await diag()).lastUpdatedAt;
  await resume('2026-11-07T16:30:00Z'); // Perth midnight; still previous UTC date.
  assert.equal(state.calls.length, 2); assert.equal((await diag()).publication, '20261107');
  assert.equal((await diag()).lastUpdatedAt, oldStamp);
  results.push(timezoneId + ': late publication is retried after midnight without changing identity/date');
  state.image = image('New', '20261108');
  await resume('2026-11-07T17:30:00Z'); await wait('New');
  assert.equal((await diag()).publication, '20261108'); assert.equal(state.calls.length, 3);
  results.push(timezoneId + ': publication arriving later the same local day updates');
  const stamp = (await diag()).lastUpdatedAt;
  for (let i = 0; i < 5; i++) await page.evaluate(() => { document.dispatchEvent(new Event('resume')); window.dispatchEvent(new Event('online')); });
  assert.equal(state.calls.length, 3);
  results.push(timezoneId + ': repeated wake/online events are bounded');
  state.image = image('Old', '20261107');
  await resume('2026-11-07T18:30:00Z'); await wait('New');
  assert.equal((await diag()).lastUpdatedAt, stamp);
  results.push(timezoneId + ': stale archive cannot roll back publication');
  const urls = state.calls.map(url => new URL(url).searchParams.get('ch'));
  assert.equal(new Set(urls).size, urls.length);
  assert((await page.evaluate(() => window.__archiveOptions)).every(o => o.cache === 'no-store'));
  results.push(timezoneId + ': archive cache bypassed, image identity URL stays stable');
  state.image = image('UnknownDate', '');
  await resume('2026-11-07T19:30:00Z'); await wait('New');
  assert.equal((await diag()).publication, '20261108');
  results.push(timezoneId + ': missing publication cannot erase known freshness metadata');
  await page.evaluate(() => ShoreQA.scene('settings'));
  await page.evaluate(() => ShoreQA.activate('settings.group.background')); await page.keyboard.press('Enter');
  await page.evaluate(() => ShoreQA.activate('background.bingNext')); await page.keyboard.press('Enter'); await wait('Manual');
  state.image = image('Newer', '20261109');
  await resume('2026-11-07T20:30:00Z'); await wait('Manual');
  assert.equal((await diag()).dailyIdentity, 'Newer');
  results.push(timezoneId + ': hourly publication change respects manual pick');
  await resume('2026-11-09T12:00:00Z'); await wait('Newer');
  results.push(timezoneId + ': next local day resets manual pick');
  state.image = image('NewDecode', '20261110'); await page.evaluate(() => { window.__badDecode = true; });
  await resume('2026-11-10T12:00:00Z'); await wait('Newer');
  assert.equal((await diag()).publication, '20261109');
  results.push(timezoneId + ': failed decode preserves working wallpaper/metadata');
  const calls = state.calls.length;
  await resume('2026-11-10T12:05:00Z'); assert.equal(state.calls.length, calls);
  await page.evaluate(() => { window.__badDecode = false; });
  await resume('2026-11-10T12:16:00Z'); await wait('NewDecode');
  results.push(timezoneId + ': reconnect/resume recovers after bounded failure backoff');
  state.fail = true;
  await resume('2026-11-11T12:00:00Z'); await wait('NewDecode');
  await page.reload(); await wait('NewDecode');
  assert.equal((await diag()).publication, '20261110');
  results.push(timezoneId + ': restart offline preserves decoded cached photo and identity');
  await ctx.close();
}
try {
  await scenario('Australia/Perth'); await scenario('UTC');
  fs.mkdirSync('.local/qa', { recursive: true });
  fs.writeFileSync('.local/qa/bing-daily.json', JSON.stringify({ passed: true, checks: results, scope: 'Mocked providers; browser engines only; no physical TV contacted' }, null, 2));
  for (const name of results) console.log('PASS ' + name);
} finally { await p.close(); }
