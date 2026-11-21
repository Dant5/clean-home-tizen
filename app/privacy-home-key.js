/* Q60B-only, foreground Privacy-page Home handling. No native settings writes. */
(function () {
  'use strict';
  var wanted = false, registered = false, blurred = false, checked = false, common = null;
  function supported() {
    if (checked) return common;
    checked = true;
    try {
      var w = window.webapis, p = w && w.productinfo, a = w && w.appcommon;
      if (!p || p.getRealModel() !== 'QA55Q60BAWXXY' || p.getFirmware() !== 'T-NKLBUABC-1720.7') return null;
      if (!a || typeof a.registerKey !== 'function' || typeof a.unregisterKey !== 'function' || typeof a.getSpecialSupportedKeys !== 'function') return null;
      var keys = a.getSpecialSupportedKeys();
      if (!Array.isArray(keys) || !keys.some(function (key) { return key.name === 'SmartHub' && key.code === 10071; })) return null;
      common = a;
    } catch (e) { common = null; }
    return common;
  }
  function sync() {
    var enable = wanted && !blurred && !document.hidden;
    if (enable === registered) return;
    try {
      if (enable) { if (!supported()) return; common.registerKey(['SmartHub']); registered = true; }
      else { common.unregisterKey(['SmartHub']); registered = false; }
    } catch (e) { /* Leave Back/native launch handling usable; a later transition can retry cleanup. */ }
  }
  window.addEventListener('blur', function () { blurred = true; sync(); });
  window.addEventListener('focus', function () { blurred = false; sync(); });
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('pagehide', function () { wanted = false; sync(); });
  window.FramePrivacyHomeKey = {
    setEnabled: function (enable) { wanted = !!enable; sync(); },
    active: function () { return registered; }
  };
}());
