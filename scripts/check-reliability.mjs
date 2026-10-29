// Failure injection at the real network/Tizen boundary; no TV is contacted.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { openPreview } from './browser.mjs';

const preview = await openPreview({ publicFonts: true });
const jpg = fs.readFileSync('app/assets/wallpapers/alpine-thumb.jpg');
const results = [];
const imageURL = name => 'https://www.bing.com/th?id=OHR.' + name + '_1920x1080.jpg';
async function fixture({ cached = null, badImage = '', malformed = false, offline = false, slowDaily = false, slowDailyImage = false, latePrefs = false, decodeFailure = false, failDisplayed = false, virtualTime = false, trackNetwork = false, trackPhotoWrites = false } = {}) {
  const page = await preview.browser.newPage({ viewport: { width: 1920, height: 1080 } });
  if (process.env.RELIABILITY_MAIN_OVERRIDE) await page.route('**/main.js', route => route.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(process.env.RELIABILITY_MAIN_OVERRIDE, 'utf8') }));
  const errors = [], calls = [];
  const control = { offline, malformed, name: 'Today', delayed: null, badImage, slowDaily, slowDailyImage };
  page.on('pageerror', e => errors.push(e.message));
  await page.clock.setFixedTime(new Date('2026-10-29T12:00:00Z'));
  if (virtualTime) await page.clock.install({ time: new Date('2026-10-29T12:00:00Z') });
  await page.route('https://**/*', async route => {
    const url = route.request().url();
    if (!url.startsWith('https://www.bing.com/')) return route.abort();
    calls.push(url);
    if (control.offline) return route.fulfill({ status: 503, body: '' });
    if (url.includes('HPImageArchive')) {
      const n = +new URL(url).searchParams.get('n');
      if (n === 1 && control.slowDaily) { control.delayed = route; return; }
      const images = n === 1 ? [{ url: imageURL(control.name) }] : [{ url: imageURL('Next'), title: 'Another photo' }];
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ images: n > 1 && control.malformed ? {} : images }) });
    }
    if (control.slowDailyImage && url.includes('OHR.Today_')) { control.delayed = route; return; }
    return route.fulfill(control.badImage && url.includes(control.badImage) ? { status: 404, body: '' } : { contentType: 'image/jpeg', body: jpg });
  });
  await page.addInitScript(({ cached, latePrefs, decodeFailure, failDisplayed, trackNetwork, trackPhotoWrites }) => {
    window.__launches = [];
    window.tizen = { application: {
      getAppsInfo: ok => setTimeout(() => ok(['YouTube', 'Nuvio Legacy', 'Spotify', 'Moonlight'].map((name, i) => ({ id: 'TestApp00' + i + '.App', name, show: true }))), 10),
      getCurrentApplication: () => ({ appInfo: { version: 'QA' }, getRequestedAppControl: () => null }),
      launch: (id, ok) => { window.__launches.push(id); ok(); }, launchAppControl() {}
    }, tvinputdevice: { registerKeyBatch() {}, getSupportedKeys: () => [] } };
    if (!sessionStorage.seeded) {
      sessionStorage.seeded = '1';
      localStorage.setItem('cleanhome.home.v1', JSON.stringify({ version: 2, ui: 3, look: { apps: 'icons', bg: 'photo', wall: latePrefs ? 'cove' : 'misty' }, home: ['youtube', 'nuvio', 'spotify', 'moonlight'], dailyBing: !latePrefs }));
      if (cached) localStorage.setItem('cleanhome.bing', JSON.stringify(cached));
    }
    if (latePrefs) {
      const get = Storage.prototype.getItem;
      Storage.prototype.getItem = function (key) { return key === 'cleanhome.home.v1' && !window.__releasePrefs ? null : get.call(this, key); };
    }
    if (decodeFailure) {
      window.__failDecode = true;
      const decode = HTMLImageElement.prototype.decode;
      HTMLImageElement.prototype.decode = function () { return window.__failDecode && this.src.startsWith('https:') ? Promise.reject(Error('Injected decode failure')) : decode.call(this); };
    }
    if (failDisplayed || trackPhotoWrites) {
      window.__failDisplayed = failDisplayed; window.__redundantPhotoWrites = 0;
      const src = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
      Object.defineProperty(HTMLImageElement.prototype, 'src', { ...src, set(value) {
        if (this.classList.contains('photo') && this.getAttribute('src') === value) window.__redundantPhotoWrites++;
        src.set.call(this, window.__failDisplayed && this.classList.contains('photo') && value.startsWith('https:') ? value.replace('OHR.Today_', 'OHR.Missing_') : value);
      } });
    }
    if (trackNetwork) {
      const fetch = window.fetch;
      window.__requests = [];
      window.fetch = function (url, options) { window.__requests.push({ url, signal: options && options.signal }); return fetch.apply(this, arguments); };
    }
  }, { cached, latePrefs, decodeFailure, failDisplayed, trackNetwork, trackPhotoWrites });
  await page.goto(preview.baseURL + '/', { waitUntil: 'load' });
  const visible = () => page.evaluate(() => {
    const im = document.querySelector('img.photo');
    return im && im.complete && im.naturalWidth > 0 ? im.getAttribute('data-live') || im.src : '';
  });
  const saved = () => page.evaluate(() => JSON.parse(localStorage.getItem('cleanhome.bing') || 'null'));
  const ready = () => page.waitForFunction(() => ShoreQA.ready(), null, { timeout: 4000 });
  const action = async name => {
    assert(await page.evaluate(name => !!ShoreQA.activate(name), name), 'Action must actually exist: ' + name);
  };
  return { page, control, calls, errors, visible, saved, ready, action };
}
async function run(name, fn) {
  if (process.env.RELIABILITY_SECTION && !name.includes(process.env.RELIABILITY_SECTION)) return;
  const start = Date.now();
  try { await fn(); results.push({ name, passed: true, ms: Date.now() - start }); }
  catch (e) { results.push({ name, passed: false, ms: Date.now() - start, error: e.message }); }
  console.log((results.at(-1).passed ? 'PASS ' : 'FAIL ') + name + (results.at(-1).error ? ': ' + results.at(-1).error : ''));
}
try {
  await run('unavailable cached photo cannot block offline startup or app discovery', async () => {
    const f = await fixture({ cached: { url: imageURL('Missing'), date: '2026-10-29' }, offline: true });
    try { await f.ready(); assert(await f.visible(), 'A decoded bundled photo must be visible'); await f.page.waitForFunction(() => ShoreQA.state().catalog.loaded); assert.equal(f.errors.length, 0); }
    finally { await f.page.close(); }
  });
  await run('retained launcher refreshes the daily photo immediately on next-day resume', async () => {
    const f = await fixture();
    try {
      await f.ready(); await f.page.waitForFunction(() => JSON.parse(localStorage.getItem('cleanhome.bing') || '{}').url);
      f.control.name = 'Tomorrow'; await f.page.clock.setFixedTime(new Date('2026-10-30T12:00:00Z'));
      await f.page.evaluate(() => document.dispatchEvent(new Event('resume')));
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Tomorrow'), null, { timeout: 3000 });
    } finally { await f.page.close(); }
  });
  await run('failed daily image never commits its date and resume recovery retries', async () => {
    const f = await fixture();
    try {
      await f.ready(); await f.page.waitForFunction(() => (JSON.parse(localStorage.getItem('cleanhome.bing') || '{}').url || '').includes('Today'));
      f.control.name = 'Tomorrow'; f.control.badImage = 'Tomorrow';
      await f.page.clock.setFixedTime(new Date('2026-10-30T12:00:00Z'));
      await f.page.evaluate(() => document.dispatchEvent(new Event('resume'))); await f.page.waitForTimeout(300);
      assert.notEqual((await f.saved()).date, '2026-10-30');
      f.control.badImage = ''; await f.page.evaluate(() => document.dispatchEvent(new Event('resume')));
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Tomorrow'), null, { timeout: 3000 });
      assert.equal((await f.saved()).date, '2026-10-30');
    } finally { await f.page.close(); }
  });
  await run('malformed Bing archive releases Next and allows a successful retry', async () => {
    const f = await fixture({ malformed: true });
    try {
      await f.ready(); await f.page.waitForTimeout(300); await f.page.evaluate(() => ShoreQA.scene('appearance'));
      await f.action('background.bingNext'); await f.page.waitForTimeout(300);
      f.control.malformed = false; await f.action('background.bingNext');
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Next'), null, { timeout: 3000 });
      assert.equal(f.errors.length, 0);
    } finally { await f.page.close(); }
  });
  await run('late daily fetch cannot overwrite a newer manual photo choice', async () => {
    const f = await fixture({ slowDaily: true });
    try {
      await f.ready(); await f.page.waitForFunction(() => ShoreQA.state().catalog.loaded);
      assert(f.control.delayed, 'Daily request must really be pending');
      await f.page.evaluate(() => ShoreQA.scene('appearance')); await f.action('background.bingNext');
      await f.page.waitForFunction(() => (JSON.parse(localStorage.getItem('cleanhome.bing') || '{}').pick || '').includes('Next'));
      await f.control.delayed.fulfill({ contentType: 'application/json', body: JSON.stringify({ images: [{ url: imageURL('Today') }] }) });
      await f.page.waitForTimeout(300); assert((await f.visible()).includes('Next')); assert((await f.saved()).pick.includes('Next'));
    } finally { await f.page.close(); }
  });
  await run('late daily image decode cannot overwrite a newer manual photo choice', async () => {
    const f = await fixture({ slowDailyImage: true });
    try {
      await f.ready(); await f.page.waitForTimeout(200);
      assert(f.control.delayed, 'Daily image must really be pending');
      await f.page.evaluate(() => ShoreQA.scene('appearance')); await f.action('background.bingNext');
      await f.page.waitForFunction(() => (JSON.parse(localStorage.getItem('cleanhome.bing') || '{}').pick || '').includes('Next'));
      f.control.slowDailyImage = false;
      await f.control.delayed.fulfill({ contentType: 'image/jpeg', body: jpg });
      await f.page.waitForTimeout(300); assert((await f.visible()).includes('Next')); assert((await f.saved()).url.includes('Next'));
    } finally { await f.page.close(); }
  });
  await run('loaded but undecodable daily photo keeps the fallback and can recover', async () => {
    const f = await fixture({ decodeFailure: true });
    try {
      await f.ready(); await f.page.waitForTimeout(300); assert((await f.visible()).includes('/wallpapers/'));
      await f.page.evaluate(() => { window.__failDecode = false; window.dispatchEvent(new Event('online')); });
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Today'), null, { timeout: 3000 });
    } finally { await f.page.close(); }
  });
  await run('late source enumeration cannot reopen a panel after Home', async () => {
    const f = await fixture();
    try {
      await f.ready(); await f.page.evaluate(() => { FrameDevice.sources = done => { window.__finishSources = done; }; ShoreQA.scene('settings'); });
      await f.action('settings.group.samsung'); await f.action('samsung.inputs');
      await f.page.evaluate(() => { window.dispatchEvent(new Event('appcontrol')); window.__finishSources(null, [{ type: 'HDMI', number: 1, name: 'HDMI 1' }]); });
      assert.equal(await f.page.evaluate(() => ShoreQA.state().view), 'home');
    } finally { await f.page.close(); }
  });
  await run('Home closes application-ID keyboard without saving its draft', async () => {
    const f = await fixture();
    try {
      await f.ready(); await f.page.evaluate(() => ShoreQA.scene('settings')); await f.action('settings.group.bindings'); await f.action('binding.youtube');
      await f.page.locator('.id-entry input').fill('DraftOnly.App', { force: true });
      const before = await f.page.evaluate(() => localStorage.getItem('cleanhome.q60b.bindings.v1'));
      await f.page.evaluate(() => window.dispatchEvent(new Event('appcontrol')));
      assert.equal(await f.page.locator('.id-entry').count(), 0);
      assert.equal(await f.page.evaluate(() => localStorage.getItem('cleanhome.q60b.bindings.v1')), before);
      assert.equal(await f.page.evaluate(() => ShoreQA.where().focusCount), 1);
    } finally { await f.page.close(); }
  });
  await run('late preferences restore the matching wallpaper bundle', async () => {
    const f = await fixture({ latePrefs: true });
    try {
      await f.ready(); await f.page.evaluate(() => { window.__releasePrefs = true; });
      await f.page.waitForFunction(() => ShoreQA.state().committed.wall === 'cove', null, { timeout: 4000 });
      await f.ready(); assert((await f.visible()).includes('cove.jpg'));
    } finally { await f.page.close(); }
  });
  await run('display-image failure after preloading restores a bundled photo', async () => {
    const f = await fixture({ failDisplayed: true, badImage: 'Missing' });
    try {
      await f.ready(); await f.page.waitForTimeout(350); assert((await f.visible()).includes('/wallpapers/'));
      await f.page.evaluate(() => { window.__failDisplayed = false; window.dispatchEvent(new Event('online')); });
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Today') && document.querySelector('img.photo').naturalWidth > 0, null, { timeout: 3000 });
    } finally { await f.page.close(); }
  });
  await run('a hung daily request is aborted at timeout and online can retry', async () => {
    const f = await fixture({ virtualTime: true, slowDaily: true, trackNetwork: true });
    try {
      await f.ready(); await f.page.waitForTimeout(100); assert(f.control.delayed);
      await f.page.clock.fastForward(11000);
      assert(await f.page.evaluate(() => __requests.some(r => r.url.includes('HPImageArchive') && r.signal && r.signal.aborted)), 'Timed-out request must actually be aborted');
      f.control.slowDaily = false; await f.page.evaluate(() => window.dispatchEvent(new Event('online')));
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('Today'), null, { timeout: 3000 });
    } finally { await f.page.close(); }
  });
  await run('installing a decoded wallpaper does not reload that same image', async () => {
    const f = await fixture({ trackPhotoWrites: true, offline: true });
    try { await f.ready(); assert.equal(await f.page.evaluate(() => __redundantPhotoWrites), 0); }
    finally { await f.page.close(); }
  });
  await run('repeated wallpaper and preference changes release resources and survive restart', async () => {
    const f = await fixture(); const session = await f.page.context().newCDPSession(f.page);
    try {
      await f.ready(); await f.page.evaluate(() => ShoreQA.scene('appearance')); await f.action('background.daily');
      await session.send('Performance.enable');
      const sample = async () => {
        await session.send('HeapProfiler.collectGarbage');
        const metrics = Object.fromEntries((await session.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
        return { heap: metrics.JSHeapUsedSize, ...(await session.send('Memory.getDOMCounters')) };
      };
      const cycle = async rounds => f.page.evaluate(async rounds => {
        for (let i = 0; i < rounds; i++) {
          ShoreQA.look({ wall: ['misty', 'cove', 'forest'][i % 3], layout: i % 2 ? 'list' : 'dock', controls: ['icons', 'both', 'text'][i % 3], focus: i % 2 ? 'type' : 'glass' });
          // State commit can precede the displayed image's asynchronous load event,
          // even when its bytes were preloaded. Require the actual displayed photo too.
          await new Promise((resolve, reject) => { let tries = 0; function check() {
            const im = document.querySelector('img.photo');
            if (ShoreQA.ready() && im.complete && im.naturalWidth && im.src.includes(ShoreQA.state().wallpaper + '.jpg')) resolve();
            else if (++tries > 500) reject(Error('Appearance/displayed photo did not settle'));
            else setTimeout(check, 10);
          } check(); });
          const im = document.querySelector('img.photo');
          if (!im.complete || !im.naturalWidth || !im.src.includes(ShoreQA.state().wallpaper + '.jpg')) throw Error('Committed wallpaper is not decoded/visible: '+JSON.stringify({i,complete:im.complete,width:im.naturalWidth,src:im.src,state:ShoreQA.state()}));
        }
      }, rounds);
      await cycle(6); await f.page.waitForTimeout(250); const before = await sample();
      await cycle(60); await f.page.waitForTimeout(250); const after = await sample();
      const saved = await f.page.evaluate(() => JSON.stringify(ShoreQA.state().committed));
      assert(after.heap - before.heap < 1024 * 1024, JSON.stringify({ before, after }));
      assert(after.nodes - before.nodes < 50, JSON.stringify({ before, after }));
      assert.equal(after.jsEventListeners, before.jsEventListeners);
      await f.page.reload(); await f.ready(); assert.equal(await f.page.evaluate(() => JSON.stringify(ShoreQA.state().committed)), saved);
      assert.equal(f.errors.length, 0);
      results.push({ name: 'wallpaper/resource measurements', passed: true, cycles: 60, before, after });
    } finally { await session.detach(); await f.page.close(); }
  });
  await run('seeded daily-use transitions retain one focus and bounded resources', async () => {
    const f = await fixture({ virtualTime: true });
    const session = await f.page.context().newCDPSession(f.page);
    try {
      await f.ready(); await f.page.waitForTimeout(300); await session.send('Performance.enable');
      const sample = async () => {
        await session.send('HeapProfiler.collectGarbage');
        const metrics = Object.fromEntries((await session.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
        return { heap: metrics.JSHeapUsedSize, listeners: metrics.JSEventListeners, ...(await session.send('Memory.getDOMCounters')) };
      };
      // Warm every tested view/resource before looking for retained growth.
      for (const view of ['apps', 'settings', 'editor', 'appearance', 'home']) await f.page.evaluate(view => ShoreQA.scene(view), view);
      await f.page.waitForTimeout(300); const before = await sample();
      const seed = 0x60b2026;
      const trace = await f.page.evaluate(async seed => {
        let value = seed; const trace = [], keys = ['left', 'right', 'up', 'down', 'back'];
        const random = () => { value ^= value << 13; value ^= value >>> 17; value ^= value << 5; return value >>> 0; };
        for (let i = 0; i < 600; i++) {
          const step = random() % 12;
          if (step < 5) { trace.push(keys[step]); ShoreQA.nav(keys[step]); }
          else if (step < 9) { const view = ['home', 'apps', 'settings', 'editor'][step - 5]; trace.push(view); ShoreQA.scene(view); }
          else if (step === 9) { trace.push('appcontrol'); window.dispatchEvent(new Event('appcontrol')); }
          else if (step === 10) { trace.push('resume'); document.dispatchEvent(new Event('resume')); }
          else { trace.push('launch'); ShoreQA.scene('home'); ShoreQA.nav(['down', 'right', 'ok']); window.dispatchEvent(new Event('appcontrol')); }
          const where = ShoreQA.where(), s = ShoreQA.state();
          if (where.focusCount !== 1 || s.home.join(',') !== 'youtube,nuvio,spotify,moonlight') throw Error(JSON.stringify({ seed, firstFailingPrefix: trace, where }));
          if (i % 25 === 0) await new Promise(resolve => setTimeout(resolve, 0));
        }
        ShoreQA.scene('home'); return { seed, actions: trace.length, launches: window.__launches.length };
      }, seed);
      for (let hour = 0; hour < 26; hour++) {
        await f.page.clock.fastForward(3600000); await f.page.waitForTimeout(20);
      }
      await f.page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, value: true }); document.dispatchEvent(new Event('visibilitychange')); });
      const hiddenCalls = f.calls.length;
      await f.page.clock.fastForward(25 * 3600000); await f.page.waitForTimeout(100); assert.equal(f.calls.length, hiddenCalls, 'No hourly Bing work while hidden');
      f.control.name = 'AfterStandby';
      await f.page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, value: false }); document.dispatchEvent(new Event('visibilitychange')); });
      await f.page.waitForFunction(() => (document.querySelector('img.photo').getAttribute('data-live') || '').includes('AfterStandby'), null, { timeout: 3000 });
      await f.page.waitForTimeout(400); const after = await sample();
      assert(trace.launches > 20, 'App-launch boundary must really have been exercised');
      assert(after.heap - before.heap < 1024 * 1024, JSON.stringify({ before, after }));
      assert(after.nodes - before.nodes < 160, JSON.stringify({ before, after }));
      assert(after.jsEventListeners - before.jsEventListeners < 8, JSON.stringify({ before, after }));
      assert.equal(f.errors.length, 0);
      results.push({ name: 'stability measurements (accelerated clock, not elapsed days)', passed: true, trace, before, after, acceleratedHours: 51 });
    } finally { await session.detach(); await f.page.close(); }
  });
} finally { await preview.close(); }
fs.mkdirSync('.local/qa', { recursive: true });
fs.writeFileSync(process.env.RELIABILITY_REPORT || '.local/qa/reliability.json', JSON.stringify({ browser: process.env.CLEANHOME_CHROMIUM || 'Playwright bundled', scope: 'Isolated browser; no TV contacted', results }, null, 2) + '\n');
process.exitCode = results.some(r => !r.passed) ? 1 : 0;
