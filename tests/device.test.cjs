/* Adapter contract tests: only the public Tizen boundary is mocked. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function harness({ list = [], store = {}, verified = {}, launch, info, infoError = false, sourceError = false, writeError = false, initialNow = 1000000 } = {}) {
  const timers = new Map(), calls = []; let timerId = 0, now = initialNow, infoCalls = 0;
  const app = {
    getAppsInfo(ok, fail) { infoCalls++; if (info) info(ok, fail); else infoError ? fail({ name: 'SecurityError' }) : ok(list); },
    launch(id, ok, fail) { calls.push(['launch', id]); if (launch) launch(id, ok, fail); else ok(); },
    getCurrentApplication() { return { hide() { calls.push(['hide']); } }; }
  };
  const context = { console, navigator: { userAgent: 'Chromium/85 QA' },
    Date: { now: () => now },
    setTimeout(fn, delay) { timers.set(++timerId, { fn, at: now + delay }); return timerId; }, clearTimeout(id) { timers.delete(id); },
    localStorage: { getItem(key) { return store[key] || null; }, setItem(key, value) { if (writeError) throw Error('QuotaExceeded'); store[key] = value; } },
    CleanHomeConfig: { timeoutMs: 8000, verifiedAppIds: verified }, tizen: { application: app,
      systeminfo: { getPropertyValue(key, ok, fail) { assert.equal(key, 'VIDEOSOURCE'); if (sourceError) return fail({ name: 'SecurityError' }); ok({ connected: [{ type: 'HDMI', number: 2 }], disconnected: [{ type: 'HDMI', number: 1 }, { type: 'TV', number: 1 }] }); } },
      tvwindow: { setSource(source, ok) { calls.push(['source', source.type, source.number]); ok(); } } } };
  context.window = context;
  vm.runInNewContext(fs.readFileSync('app/device.js', 'utf8'), context);
  return { device: context.FrameDevice, calls, store, context, get infoCalls() { return infoCalls; },
    advance(ms) { now += ms; for (const [id, timer] of [...timers]) if (timer.at <= now) { timers.delete(id); timer.fn(); } },
    expire() { for (const timer of [...timers.values()]) timer.fn(); } };
}
const inventory = [
  { id: 'OtherYT001.Video', name: 'YouTube', show: true },
  { id: 'MyLegacy42.Launch', name: 'Nuvio Legacy', show: true },
  { id: 'SpotifyXYZ.Audio', name: 'Spotify - Music and Podcasts', show: true },
  { id: 'MyMoon123.Stream', name: 'Moonlight', show: true },
  { id: 'custom.length.id', packageId: 'CustomPkg1', name: 'Apps2Samsung Player', show: true },
  { id: 'D5Q60BHome.CleanHome', name: 'Clean Home', show: true },
  { id: 'Hidden.Worker', name: 'Background service', show: true }
];
test('actual inventory IDs resolve all four favourites, including custom sideload IDs', () => {
  const h = harness({ list: inventory }); let entries;
  h.device.apps((e, result) => { assert.equal(e, null); entries = result; });
  assert.deepEqual(Array.from(entries, a => a.brand), ['youtube', 'nuvio', 'spotify', 'moonlight', '']);
  for (const brand of ['youtube', 'nuvio', 'spotify', 'moonlight']) h.device.launch(brand, e => assert.equal(e, null));
  assert.deepEqual(h.calls.map(c => c[1]), inventory.slice(0, 4).map(a => a.id));
  assert(entries.some(a => a.appId === 'custom.length.id'));
});
test('missing favourite never falls back to someone else’s hard-coded ID', () => {
  const h = harness(); let error; h.device.launch('nuvio', e => error = e);
  assert.match(error.message, /missing|ambiguous/); assert.equal(h.calls.length, 0);
});
test('ambiguous names require an explicit manual ID', () => {
  const h = harness({ list: inventory.concat({ id: 'SecondYT01.Video', name: 'YouTube', show: true }) });
  let error; h.device.launch('youtube', e => error = e); assert.match(error.message, /ambiguous/);
  assert.equal(h.device.setBinding('youtube', 'SecondYT01.Video'), null);
  h.device.launch('youtube', e => assert.equal(e, null)); assert.equal(h.calls[0][1], 'SecondYT01.Video');
});
test('Nuvio and Nuvio Legacy are not confused', () => {
  const h = harness({ list: [{ id: 'ModernNuvio.App', name: 'Nuvio', show: true }] });
  let error; h.device.launch('nuvio', e => error = e); assert.match(error.message, /missing/); assert.equal(h.calls.length, 0);
});
test('manual hidden/omitted sideload IDs persist and appear in catalogue', () => {
  const h = harness(); assert.equal(h.device.setBinding('nuvio', 'VerifiedLegacy.Custom'), null);
  let entries; h.device.apps((e, result) => entries = result); assert(entries.some(a => a.manual && a.brand === 'nuvio'));
  const again = harness({ store: h.store }); again.device.launch('nuvio', e => assert.equal(e, null));
  assert.equal(again.calls[0][1], 'VerifiedLegacy.Custom');
});
test('invalid IDs and storage failures keep prior binding', () => {
  const store = { 'cleanhome.q60b.bindings.v1': JSON.stringify({ nuvio: 'OldTarget.App' }) };
  const h = harness({ store, writeError: true });
  assert(h.device.setBinding('nuvio', 'Bad; shell'));
  assert(h.device.setBinding('nuvio', 'NewTarget.App'));
  assert.equal(h.device.getBinding('nuvio'), 'OldTarget.App');
});
test('launch error, synchronous exception and timeout are real errors; late callbacks ignored', () => {
  for (const launch of [(id, ok, fail) => fail({ message: 'Denied' }), () => { throw Error('Threw'); }]) {
    const h = harness({ launch }); let error; h.device.launchApp('Target.App', e => error = e); assert(error);
  }
  let late, count = 0, result;
  const h = harness({ launch(id, ok) { late = ok; } });
  h.device.launchApp('Target.App', e => { count++; result = e; }); assert.equal(count, 0);
  h.expire(); assert.match(result.message, /did not respond/); late(); assert.equal(count, 1);
});
test('successful launch callback is awaited', () => {
  let pending, count = 0; const h = harness({ launch(id, ok) { pending = ok; } });
  h.device.launchApp('Target.App', e => { assert.equal(e, null); count++; }); assert.equal(count, 0); pending(); assert.equal(count, 1);
});
test('discovery denial and missing Tizen surface honest errors', () => {
  const h = harness({ infoError: true }); let e; h.device.apps(error => e = error); assert.match(e.message, /read installed/);
  delete h.context.tizen; h.device.launchApp('Target.App', error => e = error); assert.match(e.message, /on the TV/);
});
test('Samsung screen only uses installed or owner-verified targets', () => {
  const h = harness({ list: [{ id: 'com.samsung.tv.csfs', name: 'Home', show: false }] });
  h.device.home(e => assert.equal(e, null)); assert.equal(h.calls[0][1], 'com.samsung.tv.csfs');
  const noHome = harness(); let error; noHome.device.home(e => error = e); assert.match(error.message, /remote Home/); assert.equal(noHome.calls.length, 0);
});
test('source selection enumerates actual ports, switches exact port and hides only this launcher', () => {
  const h = harness(); let list; h.device.sources((e, result) => { assert.equal(e, null); list = result; }); assert.equal(list.length, 3);
  h.device.openSource('HDMI', 2, e => assert.equal(e, null)); assert.deepEqual(h.calls, [['source', 'HDMI', 2], ['hide']]);
  let error; h.device.openSource('HDMI', 9, e => error = e); assert.match(error.message, /no longer available/); assert.equal(h.calls.length, 2);
});
test('source privilege failure does not switch inputs', () => {
  const h = harness({ sourceError: true }); let error; h.device.openSource('HDMI', 2, e => error = e); assert(error); assert.equal(h.calls.length, 0);
});
test('inventory-verified package profile resolves a hidden native app without using modern Nuvio', () => {
  const h = harness({ list: [{ id: 'NuvioTV001.NuvioTV', name: 'Nuvio TV', show: true }] });
  h.context.CleanHomeConfig.verifiedAppIds = { nuvio: 'NuvioTV002.Nuvio' };
  vm.runInNewContext(fs.readFileSync('app/device.js', 'utf8'), h.context);
  h.context.FrameDevice.launch('nuvio', e => assert.equal(e, null));
  assert.equal(h.calls[0][1], 'NuvioTV002.Nuvio');
});

test('clearing a packaged ID restores discovery across restarts', () => {
  const verified = { moonlight: 'Old.Stream' };
  const h = harness({ verified });
  assert.equal(h.device.setBinding('moonlight', ''), null);
  const again = harness({ verified, store: h.store, list: [{ id: 'New.Stream', name: 'Moonlight', show: true }] });
  again.device.launch('moonlight', e => assert.equal(e, null));
  assert.equal(again.calls[0][1], 'New.Stream');
});


test('Samsung show=true utilities stay out while native favourites and custom packages remain', () => {
  const h = harness({ list: inventory.concat([
    { id: 'org.tizen.rm-network-status', name: 'Network status widget', show: true },
    { id: 'com.samsung.App', name: 'App', show: true },
    { id: 'AgingApp', name: 'AgingApp', show: true },
    { id: '2022ePop01.SmartTV', name: '2022.SmartTV.Pontus', show: true },
    { id: 'org.tizen.browser', name: 'Internet', show: false }
  ]) });
  let result; h.device.apps((e, value) => { assert.equal(e, null); result = value; });
  assert.equal(result.length, 6);
  assert(result.some(a => a.appId === 'org.tizen.browser'));
  for (const brand of ['youtube', 'nuvio', 'spotify', 'moonlight']) assert(result.some(a => a.brand === brand));
  assert(!result.some(a => /widget|AgingApp|Pontus|^App$/.test(a.name)));
});

test('fresh catalogue survives reload, explicit refresh bypasses it, and expiry bounds staleness', () => {
  const list = inventory.slice(), h = harness({ list });
  h.device.apps(e => assert.equal(e, null)); assert.equal(h.infoCalls, 1);
  list.push({ id: 'OtherPkg01.NewApp', name: 'New app', show: true });
  let result; h.device.apps((e, value) => { assert.equal(e, null); result = value; });
  assert.equal(h.infoCalls, 1); assert(!result.some(a => a.name === 'New app'));
  const again = harness({ list, store: h.store });
  again.device.apps((e, value) => result = value); assert.equal(again.infoCalls, 0);
  again.device.apps((e, value) => result = value, true);
  assert.equal(again.infoCalls, 1); assert(result.some(a => a.name === 'New app'));
  again.advance(5 * 60 * 1000);
  assert(again.device.cachedApps().some(a => a.name === 'New app'));
  again.device.apps(e => assert.equal(e, null)); assert.equal(again.infoCalls, 2);
});

test('concurrent catalogue requests share one Samsung call', () => {
  let finish, count = 0;
  const h = harness({ info(ok) { finish = ok; } });
  h.device.apps(e => { assert.equal(e, null); count++; });
  h.device.apps(e => { assert.equal(e, null); count++; }, true);
  assert.equal(h.infoCalls, 1); assert.equal(count, 0);
  finish(inventory); assert.equal(count, 2);
});

test('slow inventory succeeds beyond launch timeout; timed-out late results cannot overwrite cache', () => {
  let finish, count = 0, error;
  const h = harness({ info(ok) { finish = ok; } });
  h.device.apps(e => { error = e; count++; });
  h.advance(9000); assert.equal(count, 0);
  finish(inventory); assert.equal(count, 1); assert.equal(error, null);
  h.device.apps(e => { error = e; count++; }, true);
  h.advance(21000); assert.equal(count, 2); assert(error);
  const cache = h.store['cleanhome.q60b.catalog.v1'];
  finish([]); assert.equal(count, 2); assert.equal(h.store['cleanhome.q60b.catalog.v1'], cache);
});

test('malformed asynchronous enumeration reports an error and permits retry', () => {
  let deliver, calls = 0, error;
  const h = harness({ info(ok) { deliver = ok; } });
  h.device.apps(e => { error = e; calls++; });
  assert.doesNotThrow(() => deliver({ unexpected: true }));
  assert(error); assert.equal(calls, 1);
  h.device.apps(e => { error = e; calls++; });
  deliver(inventory); assert.equal(error, null); assert.equal(calls, 2);
});

test('expired catalogue remains visible during refresh including a persisted reload', () => {
  const h = harness({ list: inventory }); h.device.apps(e => assert.equal(e, null));
  h.advance(6 * 60000);
  const stale = h.device.cachedApps(); assert(stale.some(a => a.brand === 'nuvio'));
  let deliver, completed = false;
  const again = harness({ store: h.store, initialNow: 1600000, info(ok) { deliver = ok; } });
  assert(again.device.cachedApps().some(a => a.brand === 'nuvio'));
  again.device.apps(e => { assert.equal(e, null); completed = true; }, true);
  assert.equal(completed, false); assert.equal(again.infoCalls, 1);
  assert(again.device.cachedApps().some(a => a.brand === 'nuvio'));
  deliver(inventory.filter(a => a.name !== 'Nuvio Legacy'));
  assert.equal(completed, true); assert(!again.device.cachedApps().some(a => a.brand === 'nuvio'));
});

test('malformed asynchronous video-source response is bounded without changing inputs', () => {
  const h = harness(); let deliver, error;
  h.context.tizen.systeminfo.getPropertyValue = (key, ok) => { deliver = ok; };
  h.device.sources(e => { error = e; });
  assert.doesNotThrow(() => deliver({ connected: {} })); assert(error); assert.equal(h.calls.length, 0);
});
