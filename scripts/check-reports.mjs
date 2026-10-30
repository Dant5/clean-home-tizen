// Exercise the real help sheet and independently decode its locally generated QR.
import assert from 'node:assert/strict';
import {mkdirSync, writeFileSync} from 'node:fs';
import {openPreview, root} from './browser.mjs';
import {installOnboarding} from '../tests/fixtures/onboarding.mjs';

const widget = process.argv.includes('--widget');
const preview = await openPreview(widget ? {widgetPath: root + 'dist/CleanHome-Q60B-unsigned.wgt'} : {publicFonts: true});
const report = {engine: await preview.browser.version(), scope: widget ? 'Packaged widget' : 'Source preview', checks: [], errors: []};
const check = (name, value) => {assert.ok(value, name); report.checks.push(name);};
const folder = root + '.local/qa/reports-' + (process.env.CLEANHOME_CHROMIUM ? '85' : 'current') + (widget ? '-widget' : '');
mkdirSync(folder, {recursive: true});
async function open({unknown = false, failQR = false} = {}) {
  const page = await preview.browser.newPage({viewport: {width: 1920, height: 1080}});
  page.on('pageerror', e => report.errors.push(e.message));
  await page.route('https://**/*', route => route.abort());
  if (failQR) await page.route('**/assets/qr/qrcode.js', route => route.abort());
  await page.addInitScript(installOnboarding, {dailyBing: false});
  await page.addInitScript(unknown => {
    window.__sensitiveCalls = 0;
    window.webapis = {productinfo: {
      getRealModel() {if (unknown) throw Error('Denied'); return 'QE55Q70CATXXU';},
      getModel() {return '';}, getFirmware() {return unknown ? '' : 'T-TEST-1234.5';},
      getDuid() {window.__sensitiveCalls++; return 'never-share-this-value';}
    }};
    tizen.systeminfo = {getCapability() {return unknown ? null : '6.5';}};
  }, unknown);
  await page.goto(preview.baseURL);
  await page.waitForFunction(() => ShoreQA.ready() && ShoreQA.state().catalog.loaded);
  await page.evaluate(() => { CleanHomeConfig.reportEndpoint = ''; }); // Exercise optional phone fallback.
  return page;
}
const act = async (page, action) => {
  await page.waitForFunction(action => ShoreQA.actions().indexOf(action) >= 0, action);
  await page.evaluate(action => {if (!ShoreQA.activate(action)) throw Error('Missing action ' + action);}, action);
};
async function show(page) {
  await page.evaluate(() => ShoreQA.scene('settings'));
  await act(page, 'settings.group.samsung'); await act(page, 'samsung.diagnostics');
}
async function decode(page) {
  await page.waitForFunction(() => {const c = document.querySelector('.tv-report-qr canvas'); return c && !c.hidden;});
  if (!await page.evaluate(() => typeof window.jsQR === 'function')) await page.addScriptTag({path: root + 'node_modules/jsqr/dist/jsQR.js'});
  const clip = await page.$eval('.tv-report-qr canvas', e => {const r = e.getBoundingClientRect(); return {x:r.left,y:r.top,width:r.width,height:r.height};});
  const png = await page.screenshot({clip});
  return page.evaluate(base64 => new Promise((resolve, reject) => {
    const image = new Image(); image.onerror = reject;
    image.onload = () => {
      const canvas = document.createElement('canvas'); canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
      const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0);
      const result = jsQR(ctx.getImageData(0, 0, canvas.width, canvas.height).data, canvas.width, canvas.height);
      resolve(result && result.data);
    };
    image.src = 'data:image/png;base64,' + base64;
  }), png.toString('base64'));
}
try {
  let page = await open();
  const outgoing = []; page.on('request', r => {if (r.url().startsWith('https://')) outgoing.push(r.url());});
  const before = await page.evaluate(() => localStorage.getItem('cleanhome.home.v1'));
  check('QR library is not loaded at startup', await page.evaluate(() => !document.querySelector('script[src="assets/qr/qrcode.js"]') && typeof qrcode === 'undefined'));
  await show(page);
  check('Report begins with reviewable details and no QR', await page.evaluate(() => document.querySelector('.tv-report-data').textContent.includes('QE55Q70CATXXU') && document.querySelector('.tv-report-qr canvas').hidden));
  check('No request or app launch when opening report', outgoing.length === 0 && await page.evaluate(() => __launches.length === 0));
  await page.keyboard.press('Enter');
  const url = await decode(page), parsed = new URL(url), data = JSON.parse(parsed.searchParams.get('diagnostics'));
  check('Independent decoder reads a prefilled GitHub issue URL', parsed.origin === 'https://github.com' && parsed.pathname === '/Dant5/clean-home-tizen/issues/new' && parsed.searchParams.get('template') === 'tv-report.yml');
  check('Report includes actual model, firmware, OS and app versions', data.model === 'QE55Q70CATXXU' && data.firmware === 'T-TEST-1234.5' && data.tizen === '6.5' && data.cleanHome === '1.4.3');
  check('Report carries the selected success outcome', data.result === 'Works on my TV');
  check('No app list, unique identifier or account information in QR', !/AppOne|never-share|Alpha|account|applications|userAgent|Duid/i.test(JSON.stringify(data)) && await page.evaluate(() => __sensitiveCalls === 0));
  check('QR includes a four-module white quiet zone', await page.evaluate(() => {const c = document.querySelector('canvas'), ctx = c.getContext('2d'); return [0, c.width - 1].every(x => [0, c.height - 1].every(y => ctx.getImageData(x, y, 1, 1).data[0] === 255));}));
  for (const viewport of [{width: 1920, height: 1080}, {width: 1280, height: 720}]) {
    await page.setViewportSize(viewport); await page.waitForTimeout(150);
    check('Rendered QR still decodes at ' + viewport.width, await decode(page) === url);
    check('Exactly one focused control at ' + viewport.width, await page.evaluate(() => ShoreQA.where().focusCount === 1));
    const overflow = await page.evaluate(() => {
      const sr = document.getElementById('stage').getBoundingClientRect();
      return Array.from(document.querySelectorAll('.tv-report h2,.tv-report-intro,.tv-report-data,.tv-report-actions,.tv-report-note,.tv-report-qr')).map(e => {const r = e.getBoundingClientRect(); return {element: e.className || e.tagName, fits: r.left >= sr.left && r.right <= sr.right && r.top >= sr.top && r.bottom <= sr.bottom && e.scrollHeight <= e.clientHeight + 2, rect: {x:r.x,y:r.y,w:r.width,h:r.height}, scroll:e.scrollHeight,client:e.clientHeight};}).filter(e => !e.fits);
    });
    if (overflow.length) {report.overflow = overflow; await page.screenshot({path: folder + '/overflow.png'});}
    check('All report controls and content fit at ' + viewport.width + ': ' + JSON.stringify(overflow), overflow.length === 0);
  }
  await page.screenshot({path: folder + '/success-720.png'});
  await page.setViewportSize({width: 1920, height: 1080});
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('Enter');
  const problem = JSON.parse(new URL(await decode(page)).searchParams.get('diagnostics'));
  check('Changing outcome replaces the QR and result', problem.result === 'There is a problem');
  check('No report uploads and no app launches after both choices', outgoing.length === 0 && await page.evaluate(() => __launches.length === 0));
  check('Report preparation never changes saved preferences', await page.evaluate(() => localStorage.getItem('cleanhome.home.v1')) === before);
  await page.screenshot({path: folder + '/problem-1080.png'});
  await page.keyboard.press('Escape');
  check('Remote Back restores Samsung settings and focus', await page.evaluate(() => ShoreQA.where().settingsGroup === 'samsung' && ShoreQA.where().focusAction === 'samsung.diagnostics'));
  await page.evaluate(() => {
    tizen.application.launch = (id, ok, fail) => fail({name:'SecurityError', message:'private-api-message'});
    FrameDevice.launchApp('AppOne0001.Main', () => {});
  });
  await show(page); await act(page, 'report.1');
  const apiFailure = JSON.parse(new URL(await decode(page)).searchParams.get('diagnostics'));
  check('Real adapter failures reach the report as safe codes only', apiFailure.tvErrors === 1 && apiFailure.lastTVError === 'App launch: SecurityError' && !JSON.stringify(apiFailure).includes('private-api-message'));
  await page.keyboard.press('Escape');
  for (const bg of ['light', 'dark', 'photo']) {
    await page.evaluate(bg => {ShoreQA.scene('home'); ShoreQA.look({bg});}, bg); await page.waitForFunction(() => ShoreQA.ready());
    await show(page); await act(page, 'report.1');
    check(bg + ' report stays readable', await page.evaluate(() => getComputedStyle(document.getElementById('sheet')).backgroundColor === 'rgb(15, 20, 22)' && getComputedStyle(document.querySelector('.tv-report')).color === 'rgb(255, 255, 255)'));
    check(bg + ' report QR decodes', !!await decode(page)); await page.keyboard.press('Escape');
  }
  await page.close();
  page = await open();
  await page.evaluate(() => {
    webapis.productinfo.getRealModel = () => 'Q' + 'A'.repeat(39);
    webapis.productinfo.getFirmware = () => 'T-' + 'A'.repeat(62);
    for (let i = 0; i < 120; i++) FrameReport.recordTVError({name:'NotSupportedError'}, 'Could not read installed apps.');
  });
  await page.setViewportSize({width:1280,height:720}); await show(page); await act(page,'report.1');
  const longest = await decode(page);
  check('Longest accepted metadata and error code remain scannable at 720p', !!longest && JSON.parse(new URL(longest).searchParams.get('diagnostics')).tvErrors === 99);
  await page.close();
  page = await open({unknown: true}); await show(page); await act(page, 'report.1');
  const unknown = JSON.parse(new URL(await decode(page)).searchParams.get('diagnostics'));
  check('Missing/denied TV metadata offers a usable report', unknown.model === 'Not reported' && unknown.firmware === 'Not reported');
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('Enter');
  check('Back button restores previous sheet', await page.evaluate(() => ShoreQA.where().settingsGroup === 'samsung'));
  await page.close();
  page = await open();
  let releaseQR, requestedQR;
  const qrRequested = new Promise(resolve => {requestedQR = resolve;});
  await page.route('**/assets/qr/qrcode.js', async route => {
    requestedQR(); await new Promise(resolve => {releaseQR = resolve;}); await route.continue();
  });
  await show(page); await act(page, 'report.1'); await qrRequested; await page.keyboard.press('Escape');
  releaseQR(); await page.waitForTimeout(400);
  check('Late QR generation does not reopen a cancelled report', await page.evaluate(() => ShoreQA.where().settingsGroup === 'samsung' && !document.querySelector('.tv-report')));
  await page.close();
  page = await open({failQR: true}); await show(page); await act(page, 'report.1');
  await page.waitForFunction(() => document.querySelector('.tv-report-status').textContent.includes('Code unavailable'));
  check('Offline QR load failure gives manual reporting instructions', await page.evaluate(() => document.querySelector('.tv-report-status').textContent.includes('/issues') && document.querySelector('canvas').hidden));
  await page.keyboard.press('Escape');
  check('QR failure does not trap remote navigation', await page.evaluate(() => ShoreQA.where().settingsGroup === 'samsung'));
  await page.close();
  check('No uncaught runtime errors', report.errors.length === 0);
  console.log(JSON.stringify({engine: report.engine, scope: report.scope, checks: report.checks.length, errors: report.errors}));
} finally {
  writeFileSync(folder + '/report.json', JSON.stringify(report, null, 2) + '\n'); await preview.close();
}
