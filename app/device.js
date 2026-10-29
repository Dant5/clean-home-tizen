/* Public Tizen APIs for an independently signed Q60B application. */
(function () {
  'use strict';
  var SELF = 'D5Q60BHome.CleanHome', KEY = 'cleanhome.q60b.bindings.v1';
  var BRANDS = ['youtube', 'nuvio', 'spotify', 'moonlight'], cache = [], raw = [], bindings = {};
  var CATALOG_KEY = 'cleanhome.q60b.catalog.v1', cacheAt = 0, pending = null;
  var CACHE_MS = 5 * 60 * 1000;
  var NAMES = { youtube: 'YouTube', nuvio: 'Nuvio', spotify: 'Spotify', moonlight: 'Moonlight', home: 'Samsung Home', settings: 'TV settings' };
  /* These are compatibility candidates for Samsung screens, never favourite IDs.
     Only an installed candidate (or an owner-verified ID) is attempted. */
  var SYSTEM = { home: ['com.samsung.tv.csfs', 'com.samsung.tv.coba.newhome', 'com.samsung.tv.coba.edenview'],
    settings: ['org.tizen.menu', 'com.samsung.tv.quickpanel', 'com.samsung.tv.coba.setting'] };
  /* Samsung's show flag includes internal utilities. Consumer-shape filtering follows
     arn0-tv's Tizen 6.5 findings; explicit favourite IDs always remain available.
     See assets/licenses/arn0-tv-MIT.txt and THIRD_PARTY_NOTICES.md. */
  var STORE_ID = /^[A-Za-z0-9]{10}\.[A-Za-z0-9_-]+$/, STORE_PACKAGE = /^[A-Za-z0-9]{10}$/, NUMERIC_ID = /^\d{9,13}$/;
  var PRELOADED = ['org.tizen.netflix-app', 'org.tizen.primevideo', 'org.tizen.apple.apple-music', 'org.tizen.browser', 'com.samsung.tv.aria-video'];
  var INTERNAL = /(?:^ep[ ._-]|adplayer|account|privacy|factory|daemon|background|service|worker|plugin|preview|promotion|launcher|dummy|agent|e-?manual|security|widget)/i;
  var HIDDEN = ['2022ePop01.SmartTV', 'w2VwCK465D.OTApp', 'WykOS4t4F0.cmsWebApp'];
  function api() { return window.tizen && window.tizen.application; }
  function valid(id) { return typeof id === 'string' && /^[A-Za-z0-9][A-Za-z0-9._-]{0,160}$/.test(id) && ['constructor', 'prototype', '__proto__'].indexOf(id) < 0; }
  function failure(err, title) { return { message: title || 'The TV could not open this screen.', detail: err && (err.message || err.name) || 'Try again, or use the remote Home button.' }; }
  function unavailable(done) { done(failure(null, 'Open Clean Home on the TV to use this control.')); }
  function bounded(done, timeout) {
    var ended = false, timer = setTimeout(function () { finish(failure(null, 'The TV did not respond. Please try again.')); }, timeout || window.CleanHomeConfig.timeoutMs || 8000);
    function finish(err, value) { if (ended) return; ended = true; clearTimeout(timer); done(err, value); }
    return finish;
  }
  var verified = window.CleanHomeConfig.verifiedAppIds || {};
  Object.keys(NAMES).forEach(function (key) { if (valid(verified[key])) bindings[key] = verified[key]; });
  try { var saved = JSON.parse(localStorage.getItem(KEY) || '{}'); Object.keys(NAMES).forEach(function (key) { if (valid(saved[key]) || saved[key] === '') bindings[key] = saved[key]; }); } catch (e) {}
  function setBinding(brand, id) {
    if (!Object.prototype.hasOwnProperty.call(NAMES, brand) || (id && !valid(id))) return failure(null, 'Enter a valid application ID.');
    var next = {}; Object.keys(bindings).forEach(function (key) { next[key] = bindings[key]; });
    next[brand] = id || ''; // An explicit blank survives reload and restores discovery over packaged defaults.
    try { localStorage.setItem(KEY, JSON.stringify(next)); } catch (e) { return failure(e, 'Could not save application ID. Previous ID kept.'); }
    bindings = next; cache = catalogue(raw); return null;
  }
  function identify(a) {
    var name = (a.name || '').toLowerCase().replace(/[ _-]+/g, ' ').trim();
    if (name === 'youtube') return 'youtube';
    if (name === 'nuvio legacy') return 'nuvio';
    if (name === 'spotify' || name === 'spotify music and podcasts') return 'spotify';
    if (name === 'moonlight') return 'moonlight';
    return '';
  }
  function consumer(a) {
    if (PRELOADED.indexOf(a.appId) >= 0) return true;
    if (!a.show || HIDDEN.indexOf(a.appId) >= 0 || INTERNAL.test(a.name + ' ' + a.appId)) return false;
    return STORE_ID.test(a.appId) || STORE_PACKAGE.test(a.packageId || '') || NUMERIC_ID.test(a.appId) || !!identify(a);
  }
  function catalogue(list) {
      var seen = {}, result = [];
      list.forEach(function (a) {
        var explicit = BRANDS.some(function (b) { return bindings[b] === a.appId; });
        if (!valid(a.appId) || a.appId === SELF || seen[a.appId] || !a.name || (!explicit && !consumer(a))) return;
        seen[a.appId] = true;
        result.push({ appId: a.appId, name: a.name, icon: a.icon || '', brand: '', rank: 30 });
      });
      BRANDS.forEach(function (brand) {
        var matches = result.filter(function (a) { return bindings[brand] ? a.appId === bindings[brand] : identify(a) === brand; });
        // Ambiguous matches remain unbound until the owner selects the actual ID.
        if (matches.length === 1) { matches[0].brand = brand; matches[0].rank = BRANDS.indexOf(brand); }
        if (bindings[brand] && !matches.length) result.push({ appId: bindings[brand], name: NAMES[brand], brand: brand, icon: '', rank: BRANDS.indexOf(brand), manual: true });
      });
      return result;
  }
  function fresh() { var age = Date.now() - cacheAt; return cacheAt > 0 && age >= 0 && age < CACHE_MS; }
  // A stale snapshot keeps All Apps usable while apps() refreshes it once in the background.
  function cachedApps() { return catalogue(raw); }
  function record(a) {
    return { appId: a.id, name: String(a.name || '').slice(0, 160), show: !!a.show, icon: String(a.iconPath || '').slice(0, 2048), packageId: String(a.packageId || '').slice(0, 161), version: String(a.version || '').slice(0, 80) };
  }
  try {
    var stored = JSON.parse(localStorage.getItem(CATALOG_KEY) || 'null');
    if (stored && stored.version === 1 && Array.isArray(stored.items) && stored.items.length <= 1000 && typeof stored.at === 'number') {
      cacheAt = stored.at;
      raw = stored.items.filter(function (a) { return a && valid(a.appId) && typeof a.name === 'string' && a.name.length <= 160 && typeof a.show === 'boolean' && typeof a.icon === 'string' && a.icon.length <= 2048 && typeof a.packageId === 'string' && a.packageId.length <= 161; });
    }
  } catch (eCache) { cacheAt = 0; }
  cache = catalogue(raw);
  function apps(done, force) {
    if (!api()) { unavailable(done); return; }
    if (!force && fresh()) { cache = catalogue(raw); done(null, cache.slice()); return; }
    if (pending) { pending.push(done); return; }
    var waiters = pending = [done];
    var finish = bounded(function (err) {
      if (pending !== waiters) return;
      pending = null;
      waiters.forEach(function (callback) { callback(err, err ? undefined : cache.slice()); });
    }, window.CleanHomeConfig.catalogTimeoutMs || 20000);
    try { api().getAppsInfo(function (list) {
      if (pending !== waiters) return;
      if (!Array.isArray(list)) { finish(failure(null, 'Could not read installed apps. Unexpected TV response.')); return; }
      raw = list.filter(function (a) { return a && valid(a.id); }).slice(0, 1000).map(record);
      cache = catalogue(raw); cacheAt = Date.now();
      try {
        var value = JSON.stringify({ version: 1, at: cacheAt, items: raw });
        if (value.length < 512000) localStorage.setItem(CATALOG_KEY, value);
      } catch (eWrite) { /* Enumeration remains usable if persistence is unavailable. */ }
      finish(null);
    }, function (err) { finish(failure(err, 'Could not read installed apps.')); }); } catch (err) { finish(failure(err)); }
  }
  function resolve(brand) {
    if (bindings[brand]) return bindings[brand];
    var matches = cache.filter(function (a) { return a.brand === brand; });
    return matches.length === 1 ? matches[0].appId : '';
  }
  function launchApp(id, done) {
    if (!api()) { unavailable(done); return; }
    if (!valid(id) || id === SELF) { done(failure(null, 'No verified launch target. Check Settings > Application IDs.')); return; }
    var finish = bounded(done);
    try { api().launch(id, function () { finish(null); }, function (err) { finish(failure(err, 'Could not launch this app.')); }); }
    catch (err) { finish(failure(err)); }
  }
  function launch(brand, done) {
    var id = resolve(brand);
    if (id) { launchApp(id, done); return; }
    apps(function (err) {
      var found = resolve(brand);
      if (err || !found) done(err || failure(null, NAMES[brand] + ' is missing or ambiguous. Check Settings > Application IDs.'));
      else launchApp(found, done);
    });
  }
  function systemScreen(kind, done) {
    if (!api()) { unavailable(done); return; }
    if (bindings[kind]) { launchApp(bindings[kind], done); return; }
    apps(function (err) {
      if (err) { done(err); return; }
      var ids = SYSTEM[kind].filter(function (id) { return raw.some(function (a) { return a.appId === id; }); });
      function next() {
        if (!ids.length) { done(failure(null, 'Use the remote Home / Settings button, or enter a verified ID in Application IDs.')); return; }
        launchApp(ids.shift(), function (error) { if (error && /did not respond/.test(error.message)) done(error); else if (error) next(); else done(null); });
      }
      next();
    });
  }
  function sources(done) {
    if (!window.tizen || !tizen.systeminfo || !tizen.tvwindow) { unavailable(done); return; }
    var finish = bounded(done);
    try { tizen.systeminfo.getPropertyValue('VIDEOSOURCE', function (info) {
      if (!info || ['connected', 'disconnected'].some(function (key) { return info[key] != null && !Array.isArray(info[key]); })) {
        finish(failure(null, 'Could not read TV inputs. Unexpected TV response.')); return;
      }
      var result = [], seen = {};
      ['connected', 'disconnected'].forEach(function (status) {
        (info[status] || []).forEach(function (source) {
          if (!source || typeof source.number !== 'number' || !isFinite(source.number) || source.number < 0 || Math.floor(source.number) !== source.number) return;
          var key = source.type + ':' + source.number;
          if (!/^(HDMI|TV|AV|COMP)$/.test(source.type) || seen[key]) return;
          seen[key] = true;
          result.push({ type: source.type, number: source.number, connected: status === 'connected', name: source.type === 'TV' ? 'TV' : source.type + ' ' + source.number });
        });
      });
      result.sort(function (a, b) { return a.type.localeCompare(b.type) || a.number - b.number; });
      finish(null, result);
    }, function (err) { finish(failure(err, 'Could not read TV inputs.')); }); } catch (err) { finish(failure(err)); }
  }
  function openSource(type, number, done) {
    sources(function (err, list) {
      if (err) { done(err); return; }
      var source = list.filter(function (a) { return a.type === type && a.number === number; })[0];
      if (!source) { done(failure(null, 'This input is no longer available.')); return; }
      var finish = bounded(done);
      try { tizen.tvwindow.setSource({ type: source.type, number: source.number }, function () {
        /* Hide only this launcher so the selected native input is visible. No persistent TV window. */
        try { api().getCurrentApplication().hide(); finish(null); }
        catch (e) { finish(failure(e, 'Input selected; use the remote Source button to display it.')); }
      }, function (e) { finish(failure(e, 'Could not switch inputs.')); }, 'MAIN'); } catch (e) { finish(failure(e)); }
    });
  }
  function diagnostics() {
    var model = '', firmware = '';
    try { if (window.webapis && webapis.productinfo) { model = webapis.productinfo.getModel(); firmware = webapis.productinfo.getFirmware(); } } catch (e) {}
    return { appId: SELF, userAgent: navigator.userAgent, model: model, firmware: firmware, applications: raw.slice(), favourites: BRANDS.map(function (brand) { return { name: NAMES[brand], appId: resolve(brand), manual: !!bindings[brand] }; }), capabilities: { application: !!api(), sources: !!(window.tizen && tizen.systeminfo && tizen.tvwindow) } };
  }
  window.FrameDevice = { apps: apps, cachedApps: cachedApps, launch: launch, launchApp: launchApp, home: function (done) { systemScreen('home', done); }, settings: function (done) { systemScreen('settings', done); },
    sources: sources, openSource: openSource, diagnostics: diagnostics, setBinding: setBinding,
    getBinding: function (brand) { return bindings[brand] || resolve(brand); } };
}());
