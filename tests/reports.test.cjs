/* Privacy-boundary tests use synthetic metadata; never read a real device. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
function open({product = {}, ua = 'Tizen 6.5; Chrome/85.0.4182.0 private-ua-value', platform = '6.5', denied = false} = {}) {
  const events = {}, calls = [];
  const context = {navigator: {userAgent: ua}, innerWidth: 1920, innerHeight: 1080,
    document: {documentElement: {className: ''}, querySelector: () => ({getAttribute: () => '1.4.2'})},
    addEventListener: (name, fn) => {events[name] = fn;},
    webapis: {productinfo: Object.fromEntries(Object.entries(product).map(([key, value]) => [key, () => {calls.push(key); if (value instanceof Error) throw value; return value;}]))},
    tizen: {application: {}, systeminfo: {getCapability(key) {calls.push(key); if (denied) throw Error('Denied'); return platform;}}}};
  context.window = context; vm.runInNewContext(readFileSync('app/report.js', 'utf8'), context);
  return {report: context.FrameReport, events, calls, context};
}
test('only non-unique documented model/firmware getters are used; failures are isolated', () => {
  const h = open({product: {getRealModel: Error('Denied'), getModel: 'QE55Q70CATXXU', getFirmware: 'T-TEST-1234.5', getDuid: 'private-device-value', getSerial: 'private-serial-value'}});
  const r = h.report.collect({catalogLoaded: true, storageOk: true, photoReady: true});
  assert.equal(r.model, 'QE55Q70CATXXU'); assert.equal(r.firmware, 'T-TEST-1234.5'); assert.equal(r.tizen, '6.5'); assert.equal(r.chromium, 85);
  assert.equal(r.appDiscovery, 'Completed'); assert.equal(r.savedSettings, 'Available'); assert.equal(r.photo, 'Loaded');
  assert(!h.calls.some(x => /Duid|Serial/.test(x)));
});
test('report never includes arbitrary state, app lists, addresses, raw UA or error contents', () => {
  const h = open(); h.events.error({message: 'private-error-value', filename: 'private-url-value'}); h.events.unhandledrejection({reason: 'private-rejection-value'});
  h.report.recordTVError({name:'SecurityError', message:'private-api-value'}, 'Could not launch this app.');
  const r = h.report.collect({applications: ['private-app-value'], account: 'private-account-value', address: 'private-address-value'});
  const prepared = h.report.prepare({...r, extra: 'private-extra-value'}, 'problem');
  assert(!prepared.text.includes('private-')); assert(!prepared.url.includes('private-'));
  assert.equal(r.errors, 1); assert.equal(r.rejections, 1);
  assert.equal(r.tvErrors, 1); assert.equal(r.lastTVError, 'App launch: SecurityError');
  for (let i = 0; i < 200; i++) h.events.error({}); assert.equal(h.report.collect().errors, 99);
});
test('TV error diagnostics accept only fixed operation names and error codes', () => {
  const h = open();
  h.report.recordTVError({name: 'private-error-value'}, 'private-title-value');
  assert.equal(h.report.collect().lastTVError, 'TV control: TVError');
  h.report.recordTVError(null, 'The TV did not respond. Please try again.');
  assert.equal(h.report.collect().lastTVError, 'TV control: TimeoutError');
});
test('unknown or malformed getter data is omitted, with no serial/network fallback', () => {
  const h = open({product: {getRealModel: 'a@private.invalid', getModel: '192.0.2.20', getFirmware: 'https://private.invalid/?token=secret'}, platform: 'unexpected-value', ua: 'no-version private-ua-value'});
  const r = h.report.collect(); assert.equal(r.model, 'Not reported'); assert.equal(r.firmware, 'Not reported'); assert.equal(r.tizen, 'Not reported'); assert.equal(r.chromium, 'Not reported');
  assert(!JSON.stringify(r).includes('private')); assert(!JSON.stringify(r).includes('192.0.2'));
});
test('Tizen version comes from reported OS, not a guessed engine mapping', () => {
  const h = open({platform: '9.0', ua: 'Tizen 6.5; Chrome/120.0.6099.109'});
  assert.equal(h.report.collect().tizen, '9.0');
  const fallback = open({denied: true, ua: 'Mozilla/5.0 (SMART-TV; Tizen 10.0) Chrome/130.0.6723.116'});
  assert.equal(fallback.report.collect().tizen, '10.0');
});
test('documented OEM build suffixes preserve the reported OS instead of falling back to an older UA', () => {
  for (const platform of [['9','0','0','1'].join('.'), '9.0.0.vendor_build']) {
    const h = open({platform, ua:'Tizen 6.5; Chrome/120.0.6099.109'});
    assert.equal(h.report.collect().tizen, '9.0.0');
  }
  const h = open({denied:true, ua:'Mozilla/5.0 (SMART-TV; Tizen '+['10','0','0','1'].join('.')+') Chrome/130.0.6723.116'});
  assert.equal(h.report.collect().tizen, '10.0.0');
});
test('plain browser and missing APIs are honest and harmless', () => {
  const h = open(); delete h.context.tizen; delete h.context.webapis;
  const r = h.report.collect({catalogError: true, storageOk: false});
  assert.equal(r.environment, 'Browser preview'); assert.equal(r.model, 'Not reported'); assert.equal(r.appDiscovery, 'Failed'); assert.equal(r.savedSettings, 'Unavailable');
});
test('QR destination is a GitHub draft with structured reviewable data, not a submission endpoint', () => {
  const h = open({product: {getRealModel: 'QE55Q70CATXXU'}}), r = h.report.collect();
  for (const outcome of ['works', 'problem']) {
    const p = h.report.prepare(r, outcome), url = new URL(p.url), details = JSON.parse(url.searchParams.get('diagnostics'));
    assert.equal(url.origin, 'https://github.com'); assert.equal(url.pathname, '/Dant5/clean-home-tizen/issues/new'); assert.equal(url.searchParams.get('template'), 'tv-report.yml');
    assert.equal(details.result, outcome === 'works' ? 'Works on my TV' : 'There is a problem'); assert.equal(details.model, r.model); assert.equal(p.text, JSON.stringify(details, null, 2));
    assert(p.url.length < 1800);
  }
});
