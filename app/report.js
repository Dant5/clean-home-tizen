/* Opt-in, local report preparation. No upload, identifiers, app list or raw logs. */
(function () {
  'use strict';
  var errors = 0, rejections = 0, tvErrors = 0, lastTVError = 'None', qrState = 'idle', qrWaiters = [];
  window.addEventListener('error', function () { errors = Math.min(99, errors + 1); });
  window.addEventListener('unhandledrejection', function () { rejections = Math.min(99, rejections + 1); });
  function read(object, method) {
    try { return object && typeof object[method] === 'function' ? object[method]() : ''; } catch (e) { return ''; }
  }
  function model(value) {
    return typeof value === 'string' && /^[A-Za-z][A-Za-z0-9_-]{2,39}$/.test(value) ? value : '';
  }
  function firmware(value) {
    return typeof value === 'string' && /^T-[A-Za-z0-9_.-]{1,62}$/.test(value) ? value : 'Not reported';
  }
  function number(value, max) { return typeof value === 'number' && isFinite(value) && value >= 0 && value <= max ? Math.round(value) : 0; }
  function recordTVError(error, title) {
    var names = ['SecurityError', 'NotFoundError', 'InvalidValuesError', 'InvalidStateError', 'NotSupportedError', 'UnknownError', 'TypeMismatchError', 'TimeoutError'];
    var name = error && names.indexOf(error.name) >= 0 ? error.name : title === 'The TV did not respond. Please try again.' ? 'TimeoutError' : 'TVError';
    var operation = title === 'Could not read installed apps.' ? 'App discovery' : title === 'Could not launch this app.' ? 'App launch' : title === 'Could not read TV inputs.' || title === 'Could not switch inputs.' ? 'TV input' : 'TV control';
    tvErrors = Math.min(99, tvErrors + 1); lastTVError = operation + ': ' + name;
  }
  function collect(state) {
    state = state || {};
    var p = window.webapis && window.webapis.productinfo, sys = window.tizen && window.tizen.systeminfo;
    var ua = String(navigator.userAgent || ''), tizenVersion = '', chrome = /(?:Chrome|Chromium)\/(\d{1,3})\./.exec(ua), match;
    try { if (sys && typeof sys.getCapability === 'function') tizenVersion = sys.getCapability('http://tizen.org/feature/platform.version'); } catch (e) {}
    if (typeof tizenVersion !== 'string' || !/^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$/.test(tizenVersion)) {
      match = /\bTizen[ /](\d{1,2}\.\d{1,2})(?:[; )]|$)/i.exec(ua);
      tizenVersion = match ? match[1] : 'Not reported';
    }
    var version = document.querySelector('meta[name="clean-home-version"]');
    var appVersion = version && version.getAttribute('content');
    return {
      schema: 1,
      cleanHome: /^\d+\.\d+\.\d+$/.test(appVersion || '') ? appVersion : 'Not reported',
      environment: window.tizen && window.tizen.application ? 'TV API present' : 'Browser preview',
      model: model(read(p, 'getRealModel')) || model(read(p, 'getModel')) || 'Not reported',
      firmware: firmware(read(p, 'getFirmware')),
      tizen: tizenVersion,
      chromium: chrome ? Number(chrome[1]) : 'Not reported',
      viewport: number(window.innerWidth, 16384) + 'x' + number(window.innerHeight, 16384),
      spacing: document.documentElement.className.indexOf('no-flex-gap') >= 0 ? 'Margin fallback' : 'Native gap',
      appDiscovery: state.catalogError ? 'Failed' : state.catalogLoaded ? 'Completed' : 'Pending',
      savedSettings: state.storageOk === true ? 'Available' : state.storageOk === false ? 'Unavailable' : 'Not checked',
      photo: state.photoReady === true ? 'Loaded' : 'Not loaded',
      errors: errors,
      rejections: rejections,
      tvErrors: tvErrors,
      lastTVError: lastTVError
    };
  }
  function prepare(report, outcome) {
    /* Rebuild from the allowlist. Never serialize a caller's extra properties. */
    var clean = {}, keys = ['schema', 'cleanHome', 'environment', 'model', 'firmware', 'tizen', 'chromium', 'viewport', 'spacing', 'appDiscovery', 'savedSettings', 'photo', 'errors', 'rejections', 'tvErrors', 'lastTVError'];
    keys.forEach(function (key) { clean[key] = report[key]; });
    clean.result = outcome === 'works' ? 'Works on my TV' : 'There is a problem';
    return { text: JSON.stringify(clean, null, 2), url: 'https://github.com/Dant5/clean-home-tizen/issues/new?template=tv-report.yml&title=' + encodeURIComponent('TV report: ' + clean.model + ' - ' + clean.result) + '&diagnostics=' + encodeURIComponent(JSON.stringify(clean)) };
  }
  function draw(canvas, url, done) {
    function paint(ok) {
      if (!ok) { done(false); return; }
      try {
        var qr = window.qrcode(0, 'M'), context = canvas.getContext('2d'), count, cell, size, row, column;
        qr.addData(url); qr.make(); count = qr.getModuleCount(); cell = Math.floor(600 / (count + 8));
        if (cell < 3) { done(false); return; }
        size = (count + 8) * cell; canvas.width = size; canvas.height = size;
        context.fillStyle = '#fff'; context.fillRect(0, 0, size, size); context.fillStyle = '#000';
        for (row = 0; row < count; row++) for (column = 0; column < count; column++) if (qr.isDark(row, column)) context.fillRect((column + 4) * cell, (row + 4) * cell, cell, cell);
        done(true);
      } catch (e) { done(false); }
    }
    if (qrState === 'ready') { paint(true); return; }
    if (qrState === 'failed') { paint(false); return; }
    qrWaiters.push(paint);
    if (qrState === 'loading') return;
    qrState = 'loading';
    var script = document.createElement('script'), timer;
    function finish(ok) {
      if (qrState !== 'loading') return;
      clearTimeout(timer); script.onload = script.onerror = null; qrState = ok ? 'ready' : 'failed';
      var waiters = qrWaiters; qrWaiters = []; waiters.forEach(function (callback) { callback(ok); });
    }
    script.src = 'assets/qr/qrcode.js';
    script.onload = function () { finish(typeof window.qrcode === 'function'); };
    script.onerror = function () { finish(false); };
    timer = setTimeout(function () { finish(false); }, 5000);
    document.head.appendChild(script);
  }
  window.FrameReport = { collect: collect, prepare: prepare, draw: draw, recordTVError: recordTVError };
}());
