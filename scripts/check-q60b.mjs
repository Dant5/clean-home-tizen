// Q60B-specific browser checks reuse upstream preview and ShoreQA, never contact a TV.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { openPreview, root } from './browser.mjs';
const preview = await openPreview({ publicFonts: true });
const report = { scope: 'Browser integration with mock Tizen APIs; no TV contacted', checks: [], errors: [], engine: await preview.browser.version() };
let page;
const check = (name, value) => { assert.ok(value, name); report.checks.push(name); };
try {
  page = await preview.browser.newPage({ viewport: { width: 1920, height: 1080 }, timezoneId: 'Australia/Perth' });
  page.on('pageerror', e => report.errors.push(e.message));
  await page.route('https://**/*', route => route.abort());
  await page.route('**/$WEBAPIS/webapis/webapis.js', route => route.fulfill({ body: '' }));
  await page.addInitScript(() => {
    window.__calls = []; window.__failLaunch = false;
    window.__catalog = [
      { id: 'ActualYT01.Video', name: 'YouTube', show: true },
      { id: 'MyLegacy01.Custom', name: 'Nuvio Legacy', show: true },
      { id: 'ActualSp01.Music', name: 'Spotify - Music and Podcasts', show: true },
      { id: 'MyMoonlight.Stream', name: 'Moonlight', show: true },
      { id: 'Any.Apps2SamsungID', packageId: 'CustomPkg1', name: 'Sideloaded app', show: true },
      { id: 'com.samsung.tv.csfs', name: 'Samsung Home', show: false },
      { id: 'org.tizen.menu', name: 'Settings', show: false }
    ];
    window.tizen = {
      application: {
        getAppsInfo(ok) {
          if (!sessionStorage.getItem('catalog-released')) window.__releaseCatalog = () => { sessionStorage.setItem('catalog-released', 'yes'); ok(window.__catalog); };
          else setTimeout(() => ok(window.__catalog), 0);
        },
        launch(id, ok, fail) { window.__calls.push(['launch', id]); setTimeout(() => window.__failLaunch ? fail({ message: 'Permission denied' }) : ok(), 40); },
        getCurrentApplication() { return { appInfo: { id: 'D5Q60BHome.CleanHome' }, hide() { window.__calls.push(['hide']); } }; }
      },
      systeminfo: { getPropertyValue(key, ok) { ok({ connected: [{ type: 'HDMI', number: 2 }], disconnected: [{ type: 'HDMI', number: 1 }] }); } },
      tvwindow: { setSource(source, ok) { window.__calls.push(['source', source.type, source.number]); ok(); } }
    };
    if (!sessionStorage.getItem('seeded')) {
      localStorage.setItem('cleanhome.home.v1', JSON.stringify({ home: ['youtube','nuvio','spotify','moonlight'], dailyBing: false })); sessionStorage.setItem('seeded', 'yes');
    }
  });
  const ready = () => page.waitForFunction(() => window.ShoreQA && ShoreQA.ready() && !ShoreQA.state().catalog.loading);
  const state = () => page.evaluate(() => ShoreQA.state());
  const act = action => page.evaluate(action => { if (!ShoreQA.activate(action)) throw Error('Missing action: ' + action); }, action);
  const scene = name => page.evaluate(name => ShoreQA.scene(name), name);
  const back = () => page.keyboard.press('Escape');
  const group = async name => { await scene('settings'); await act('settings.group.' + name); };
  await page.goto(preview.baseURL + '/home/');
  await page.waitForFunction(() => window.ShoreQA && ShoreQA.ready() && window.__releaseCatalog);
  await page.waitForFunction(() => ['youtube','nuvio','spotify','moonlight'].every(brand => {
    const tile = document.querySelector('[data-action="home.app.' + brand + '"]');
    return tile && tile.querySelector('.mark') && !tile.querySelector('.monogram') && Array.prototype.every.call(tile.querySelectorAll('img'), img => img.complete && img.naturalWidth > 0);
  }));
  check('Four finished bundled icons and usable Home precede the registry response', await page.evaluate(() => ShoreQA.state().catalog.loading));
  await page.evaluate(() => __releaseCatalog()); await ready();
  report.css = await page.evaluate(() => ({ inset: CSS.supports('inset', '0px'), flexGap: CSS.supports('gap', '12px'), mask: CSS.supports('-webkit-mask-image', 'url(x)') }));
  check('Dock content fills its existing tile on this engine', await page.$eval('.tile-content', el => { const a = el.getBoundingClientRect(), b = el.parentElement.getBoundingClientRect(); return Math.abs(a.width - b.width) < 1 && Math.abs(a.height - b.height) < 1; }));
  check('Only requested four favourites in the default order', JSON.stringify((await state()).dock) === JSON.stringify(['youtube', 'nuvio', 'spotify', 'moonlight']));
  check('Clean Home photo, dock and Manrope defaults retained', (await state()).look.bg === 'photo' && (await state()).look.layout === 'dock' && (await state()).look.font === 'manrope');
  check('No application is launched on boot', (await page.evaluate(() => __calls.length)) === 0);
  for (const [brand, id] of [['youtube', 'ActualYT01.Video'], ['nuvio', 'MyLegacy01.Custom'], ['spotify', 'ActualSp01.Music'], ['moonlight', 'MyMoonlight.Stream']]) {
    await act('home.app.' + brand); await page.waitForTimeout(90);
    check(brand + ' launches discovered ID', await page.evaluate(id => __calls[__calls.length - 1][1] === id, id));
  }
  await page.evaluate(() => { __failLaunch = true; });
  await act('home.app.youtube'); await page.waitForFunction(() => ShoreQA.state().view === 'message');
  check('Asynchronous launch errors are visible', /could not launch/i.test(await page.$eval('#stage', e => e.innerText)));
  await back(); await page.evaluate(() => { __failLaunch = false; });
  await act('util.apps'); await ready();
  check('Apps2Samsung custom ID is in All Apps', !!await page.$('[data-action="apps.open.Any.Apps2SamsungID"]'));
  await back(); await group('bindings'); await act('binding.nuvio');
  await page.keyboard.press('Control+A'); await page.keyboard.type('VerifiedOld.Nuvio');
  await page.keyboard.press('Enter'); await page.keyboard.press('Enter'); await ready();
  check('Remote ID editor saves verified ID', await page.evaluate(() => FrameDevice.getBinding('nuvio') === 'VerifiedOld.Nuvio'));
  await page.reload(); await ready(); await act('home.app.nuvio'); await page.waitForTimeout(90);
  check('Manual Nuvio ID survives reload and launches', await page.evaluate(() => __calls[__calls.length - 1][1] === 'VerifiedOld.Nuvio'));
  await group('bindings'); await act('binding.nuvio'); await page.keyboard.press('Control+A'); await page.keyboard.type('Unsaved.Target'); await back();
  check('Back cancels ID entry', await page.evaluate(() => FrameDevice.getBinding('nuvio') === 'VerifiedOld.Nuvio') && !await page.$('.id-entry'));
  await group('samsung');
  check('Samsung controls include Home, Settings and input selection', !!await page.$('[data-action="samsung.home"]') && !!await page.$('[data-action="samsung.settings"]') && !!await page.$('[data-action="samsung.inputs"]'));
  check('No Home takeover or System/root controls', !await page.$('[data-action="samsung.useAsHome"]') && !await page.$('[data-action="settings.group.system"]'));
  await act('samsung.inputs'); await page.waitForFunction(() => ShoreQA.state().view === 'devicepanel');
  check('Real input numbers and connection status shown', /HDMI 2.*Connected/.test(await page.$eval('#stage', e => e.innerText)));
  await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
  check('Remote selects HDMI 2 and hides launcher', await page.evaluate(() => __calls.some(c => c[0] === 'source' && c[2] === 2) && __calls.some(c => c[0] === 'hide')));
  await back(); await act('samsung.home'); await page.waitForTimeout(90);
  check('Samsung Home explicit escape uses installed ID', await page.evaluate(() => __calls[__calls.length - 1][1] === 'com.samsung.tv.csfs'));
  await act('samsung.settings'); await page.waitForTimeout(90);
  check('Samsung Settings explicit action uses installed ID', await page.evaluate(() => __calls[__calls.length - 1][1] === 'org.tizen.menu'));
  await scene('home'); await act('util.samsunghome'); await page.waitForTimeout(90);
  await page.keyboard.press('Escape');
  await page.keyboard.press('ArrowUp'); await page.waitForTimeout(100);
  const filters = await page.evaluate(() => Array.prototype.filter.call(document.querySelectorAll('#stage *'), e => e.getClientRects().length && (/blur/.test(getComputedStyle(e).filter) || (getComputedStyle(e).backdropFilter && getComputedStyle(e).backdropFilter !== 'none'))).length);
  check('Visible UI has no live blur', filters === 0);
  for (const viewport of [{ width: 1920, height: 1080 }, { width: 1280, height: 720 }]) {
    await page.setViewportSize(viewport); await page.waitForTimeout(100);
    check('Stage scales to ' + viewport.width, await page.$eval('#stage', (e, width) => Math.abs(e.getBoundingClientRect().width - width) < 2, viewport.width));
    check('Exactly one remote focus at ' + viewport.width, await page.evaluate(() => ShoreQA.where().focusCount === 1));
    await scene('home'); await page.keyboard.press('ArrowDown'); await page.waitForTimeout(180);
    await page.keyboard.press('ArrowRight'); await page.waitForTimeout(180);
    const rememberedApp = await page.evaluate(() => ShoreQA.where().focusAction);
    await page.keyboard.press('ArrowUp'); await page.waitForTimeout(180);
    check('Header focus clears the dock highlight at ' + viewport.width, await page.evaluate(() => ShoreQA.where().zone === 'util' && !document.querySelector('.dock .tile.is-focus, .dock .tile.is-sel') && Number(getComputedStyle(document.querySelector('.dock .plate')).opacity) === 0));
    await page.keyboard.press('ArrowDown'); await page.waitForTimeout(180);
    check('Returning from header restores the remembered app at ' + viewport.width, await page.evaluate(action => ShoreQA.where().focusAction === action && ShoreQA.where().focusCount === 1, rememberedApp));
    for (const name of ['background', 'layout', 'typography', 'focus', 'samsung', 'bindings']) {
      await group(name);
      check(name + ' panel geometry fits at ' + viewport.width, await page.evaluate(() => {
        const stage = document.getElementById('stage').getBoundingClientRect(), panel = document.getElementById('appearance').getBoundingClientRect();
        const buttons = Array.prototype.filter.call(document.querySelectorAll('.appearance [data-action]'), e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
        return Math.abs(panel.width - stage.width) < 2 && Math.abs(panel.height - stage.height) < 2 && buttons.every(e => { const r = e.getBoundingClientRect(); return r.left >= stage.left - 1 && r.top >= stage.top - 1 && r.right <= stage.right + 1 && r.bottom <= stage.bottom + 1; });
      }));
    }
    await scene('home');
  }
  await page.setViewportSize({ width: 1920, height: 1080 }); await scene('home'); await page.keyboard.press('ArrowDown'); await page.waitForTimeout(200);
  mkdirSync(root + 'dist', { recursive: true });
  await page.screenshot({ path: root + 'dist/CleanHome-Q60B-preview.png' });
  check('No unhandled JavaScript errors', report.errors.length === 0);
} catch (e) { report.failure = e.stack; throw e; }
finally {
  mkdirSync(root + '.local/qa', { recursive: true });
  writeFileSync(root + '.local/qa/' + (process.env.CLEANHOME_CHROMIUM ? 'q60b-chromium85.json' : 'q60b.json'), JSON.stringify(report, null, 2) + '\n');
  await preview.close();
  console.log(report.checks.length + ' Q60B integration checks passed in ' + report.engine);
}
