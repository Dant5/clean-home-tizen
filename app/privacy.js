/* Local TV/soundbar DNS dashboard. No admin credentials, polling on Home or uploads. */
(function () {
  'use strict';
  function esc(value) { return String(value === null || value === undefined ? '' : value).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function config() {
    var c = window.CleanHomeConfig && window.CleanHomeConfig.dnsProtection;
    if (!c || typeof c.endpoint !== 'string' || !/^http:\/\/(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{4,5}$/.test(c.endpoint) || !/^[A-Za-z0-9_-]{32,128}$/.test(c.token || '')) return null;
    return c;
  }
  function request(path, action, done) {
    var c = config(), xhr, finished = false, timer;
    function finish(error, data) { if (finished) return; finished = true; clearTimeout(timer); done(error, data); }
    if (!c) { finish('Connect your TV-only resolver during setup.'); return function () {}; }
    try {
      xhr = new XMLHttpRequest(); xhr.open(action ? 'POST' : 'GET', c.endpoint + path, true); xhr.timeout = 30000; xhr.withCredentials = false;
      xhr.setRequestHeader('Authorization', 'Bearer ' + c.token);
      if (action) xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.onload = function () {
        var data;
        try { if (xhr.status === 200 && xhr.responseText.length < 65536) data = JSON.parse(xhr.responseText); } catch (e) {}
        if (data && (action ? data.accepted === true : data.schema === 1 && (path === '/v1/enforcement' ? typeof data.ruleStatus === 'string' : data.today && Array.isArray(data.days) && Array.isArray(data.top) && Array.isArray(data.recent)))) finish(null, data);
        else finish(action ? 'Change not confirmed. Refresh to check protection.' : 'Protection unavailable. Check the Dell resolver.');
      };
      xhr.onerror = xhr.ontimeout = function () { finish('Cannot reach the resolver. Protection is unknown.'); };
      timer = setTimeout(function () { finish('Resolver timed out. Protection is unknown.'); try { xhr.abort(); } catch (e) {} }, 31000);
      xhr.send(action ? JSON.stringify({ action: action }) : null);
    } catch (e) { finish('Cannot connect to the resolver.'); }
    return function () { if (finished) return; finished = true; clearTimeout(timer); if (xhr) { xhr.onload = xhr.onerror = xhr.ontimeout = null; try { xhr.abort(); } catch (e) {} } };
  }
  function time(value, zone, date) {
    try { var d = new Date(value); if (isNaN(d.getTime())) return 'Unknown time'; return d.toLocaleString('en-GB', { timeZone: zone, hour: '2-digit', minute: '2-digit', day: date ? '2-digit' : undefined, month: date ? 'short' : undefined }); } catch (e) { return 'Unknown time'; }
  }
  function count(value) {
    if (typeof value !== 'number' || !isFinite(value) || value < 0) return '\u2014';
    var n = Math.round(value), unit = 0, suffixes = ['', 'K', 'M', 'B', 'T'], rounded;
    while (n >= 1000 && unit < suffixes.length - 1) { n /= 1000; unit++; }
    rounded = Number(n.toFixed(unit && n < 100 ? 1 : 0));
    if (rounded >= 1000 && unit < suffixes.length - 1) { rounded /= 1000; unit++; }
    return String(rounded) + suffixes[unit];
  }
  function button(t, label, action, i) { return '<button type="button" tabindex="-1" class="btn' + (t.f.i === i ? ' is-focus' : '') + '" data-z="dns" data-i="' + i + '" data-action="dns.' + action + '">' + esc(label) + '</button>'; }
  function install(ctx) {
    var V = ctx.views, frames = ctx.frames, fills = ctx.fills, cancel = null, counterCancel = null, refreshTimer = null;
    function stop() { if (cancel) cancel(); if (counterCancel) counterCancel(); counterCancel = null; cancel = null; clearTimeout(refreshTimer); }
    function active(t) { return ctx.top() === t && !document.hidden; }
    function fetch(t, action) {
      stop(); t.enforcement = null; t.busy = true; t.error = ''; ctx.render();
      cancel = request(action ? '/v1/protection' : '/v1/status', action, function (error, data) {
        cancel = null;
        if (!active(t)) return;
        t.busy = false;
        if (error) { t.error = error; t.data = null; }
        else if (action) { fetch(t); return; }
        else {
          t.data = data;
          counterCancel = request('/v1/enforcement', null, function (counterError, counters) {
            counterCancel = null;
            if (!active(t)) return;
            t.enforcement = counterError ? null : counters;
            ctx.render();
          });
        }
        ctx.render();
        refreshTimer = setTimeout(function () { if (active(t)) fetch(t); }, 60000);
      });
    }
    function actions(t) {
      if (t.confirm) return ['confirm', 'cancel'];
      return ['back', 'refresh', 'device'].concat(t.data && !t.error ? [t.data.protectionEnabled ? 'disable' : 'enable', 'pause15', 'pause60'] : []);
    }
    function run(t, id) {
      if (id === 'back') { stop(); ctx.pop(); return; }
      if (id === 'device') { var scopes = ['all', 'tv', 'soundbar']; t.device = scopes[(scopes.indexOf(t.device || 'all') + 1) % scopes.length]; t.scroll = 0; return; }
      if (id === 'cancel') { t.confirm = false; t.f.i = 0; return; }
      if (t.busy) return;
      if (id === 'disable') { t.confirm = true; t.f.i = 1; return; }
      if (id === 'confirm') { t.confirm = false; t.f.i = 0; fetch(t, 'disable'); return; }
      fetch(t, id === 'refresh' ? null : id);
    }
    V.privacy = {
      sheet: true, norm: function (t) { t.f.i = Math.min(1, Math.max(0, t.f.i || 0)); },
      key: function (t, k) {
        if (k === 'back') ctx.pop();
        else if (k === 'up' || k === 'left') t.f.i = 0;
        else if (k === 'down' || k === 'right') t.f.i = 1;
        else if (k === 'ok') {
          if (t.f.i) ctx.pop();
          else { var next = { id: 'dns', f: { i: 0 }, data: null }; ctx.push(next); fetch(next); }
        }
      },
      point: function (t, z, i) { t.f.i = i; this.key(t, 'ok'); }
    };
    V.dns = {
      sheet: true, norm: function (t) { t.f.i = Math.min(actions(t).length - 1, Math.max(0, t.f.i || 0)); },
      key: function (t, k) {
        if (k === 'back') { if (t.confirm) { t.confirm = false; t.f.i = 0; } else { stop(); ctx.pop(); } }
        else if (k === 'left') t.f.i = Math.max(0, t.f.i - 1);
        else if (k === 'right') t.f.i = Math.min(actions(t).length - 1, t.f.i + 1);
        else if (k === 'down' || k === 'up') t.scroll = Math.max(0, Math.min(5000, (t.scroll || 0) + (k === 'down' ? 220 : -220)));
        else if (k === 'ok') run(t, actions(t)[t.f.i]);
      },
      point: function (t, z, i) { t.f.i = i; this.key(t, 'ok'); }
    };
    frames.privacy = function () { return '<div class="dns-page"><p class="dns-breadcrumb">Settings</p><h2>Privacy</h2><p class="dns-lead">Protection for your TV and soundbar, with your data kept at home.</p><div data-slot="body"></div></div>'; };
    fills.privacy = function (t, el) { el.body.innerHTML = '<div class="dns-menu">' + button(t, 'DNS Protection', 'open', 0) + button(t, 'Back', 'back', 1) + '</div><p class="dns-note">DNS filtering can block known ad and tracking domains for your TV and soundbar. It cannot remove every ad or replace Samsung\u2019s privacy settings.</p>'; };
    function shield() { return '<svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M14 3 24 7v7c0 5-5 9-10 11C9 23 4 19 4 14V7Z"/><path d="m9 14 3 3 7-7"/></svg>'; }
    frames.dns = function () {
      return '<div class="dns-overlay"><p class="dns-location">Settings / Privacy / DNS Protection</p><div class="dns-pill" data-slot="pill"></div>'
        + '<section class="dns-panel" aria-labelledby="dnsTitle"><h2 id="dnsTitle" class="dns-sr">DNS Protection</h2><div class="dns-scroll" data-slot="body" aria-live="polite"></div>'
        + '<div class="dns-footer"><div class="dns-toolbar" data-slot="actions"></div><p class="dns-hint">Left/Right: all-device controls · Up/Down: details · Back</p></div></section></div>';
    };
    fills.dns = function (t, el) {
      var labels = { device: 'View: ' + (t.device === 'tv' ? 'TV' : t.device === 'soundbar' ? 'Soundbar' : 'All devices'), back: 'Back', refresh: 'Refresh', enable: 'Enable', disable: 'Turn off', pause15: 'Pause 15 min', pause60: 'Pause 1 hour', confirm: 'Turn off protection', cancel: 'Keep protection' };
      el.actions.innerHTML = actions(t).map(function (id, i) { return button(t, labels[id], id, i); }).join('');
      el.actions.setAttribute('aria-busy', t.busy ? 'true' : 'false');
      /* Arrow keys change focus/scroll, not the data. Keep the static body intact. */
      if (t.paintNode === el.body && t.paintData === t.data && t.paintDevice === t.device && t.paintConfirm === t.confirm && t.paintBusy === t.busy && t.paintError === t.error && t.paintEnforcement === t.enforcement) {
        el.body.scrollTop = t.scroll || 0; t.scroll = el.body.scrollTop; return;
      }
      t.paintEnforcement = t.enforcement; t.paintNode = el.body; t.paintData = t.data; t.paintDevice = t.device; t.paintConfirm = t.confirm; t.paintBusy = t.busy; t.paintError = t.error;
      var d = t.data, html = '', max = 1, selected = null, combined = t.device !== 'tv' && t.device !== 'soundbar', notConfigured = false;
      if (d && !combined && Array.isArray(d.devices)) {
        d.devices.forEach(function (item) { if (item.id === t.device) selected = item; });
        if (selected && selected.configured) {
          var copy = {}; Object.keys(d).forEach(function (key) { copy[key] = d[key]; });
          Object.keys(selected).forEach(function (key) { copy[key] = selected[key]; }); d = copy;
        } else notConfigured = true;
      }
      var state = t.error || !d || notConfigured ? 'UNKNOWN' : d.protectionEnabled ? 'ENABLED' : d.pausedUntil ? 'PAUSED' : 'OFF';
      el.pill.innerHTML = shield() + '<span>' + esc(t.busy ? 'Checking DNS protection…' : state === 'ENABLED' ? 'DNS filtering · ' + count(d.today.blocked) + ' blocked today' : state === 'PAUSED' ? 'DNS filtering paused' : state === 'OFF' ? 'DNS filtering off' : 'DNS protection not verified') + '</span>';
      if (t.confirm) html += '<div class="dns-warning">Turn off DNS blocking for both configured devices until you enable it again? They will still use the Dell for DNS. Pause instead for automatic recovery.</div>';
      html += '<div class="dns-provider"><div class="dns-provider-mark">' + shield() + '</div><div><h3>AdGuard Home</h3><p>Local DNS · ' + (combined ? 'TV + soundbar' : t.device === 'tv' ? 'TV only' : 'Soundbar only') + '</p></div><span class="dns-badge' + (state === 'ENABLED' ? ' is-enabled' : '') + '">' + state + '</span></div>';
      if (notConfigured) {
        html += '<div class="dns-empty"><h3>Soundbar not connected to this filter</h3><p>Its own DNS routing must be configured and verified separately. No soundbar statistics are assumed from TV activity.</p></div>';
      } else if (t.error || !d) {
        html += '<div class="dns-empty"><h3>' + (t.busy ? 'Checking protection…' : config() ? 'Protection unknown' : 'Not connected') + '</h3><p>' + esc(t.error || (config() ? 'Reading the local resolver.' : 'Set up the dedicated resolver on your server before connecting this page.')) + '</p><p>Only real, attributed device traffic appears here.</p></div>';
      } else {
        var client = d.observedClientProtocols || {}, upstream = d.observedUpstreamTransport || {}, week = 0;
        html += '<div class="dns-intro"><h3>' + (state === 'ENABLED' ? count(d.today.blocked) + ' DNS requests blocked today.' : state === 'PAUSED' ? 'Protection is taking a break.' : 'DNS filtering is off.') + '</h3><p>'
          + (state === 'ENABLED' ? 'Blocks known ad and tracker domains. Alternate DNS paths are not verified.' : state === 'PAUSED' ? 'Blocking resumes at ' + esc(time(d.pausedUntil, d.timezone, true)) + '. You can enable it now.' : 'The devices still use this resolver, with blocking disabled. Choose Enable to resume filtering.') + '</p><span class="dns-sr">' + (state === 'ENABLED' ? 'DNS filtering enabled' : state === 'PAUSED' ? 'Protection paused' : 'Protection off') + '</span></div>';
        html += '<div class="dns-cards"><div class="dns-accent"><strong>' + count(d.today.blocked) + '</strong><span>Blocked today</span></div><div><strong>' + count(d.today.queries) + '</strong><span>Lookups today</span></div><div><strong>' + (d.lifetime ? count(d.lifetime.blocked) : '—') + '</strong><span>Lifetime blocked</span></div></div>';
        html += '<p class="dns-note">Lookups are DNS requests, including repeats, not a count of adverts.</p>' + (d.lifetime ? '<p class="dns-note">Lifetime since ' + esc(time(d.lifetime.since, d.timezone, true)) + '. ' + (d.lifetime.complete ? 'Recorded since this counter was enabled.' : 'Available history only; earlier records may be missing.') + '</p>' : '<p class="dns-note">Lifetime counter not connected yet. Earlier activity is not assumed.</p>');
        html += '<section class="dns-top"><h3>Most blocked · today</h3>';
        html += d.topToday && d.topToday.length ? d.topToday.slice(0, 3).map(function (r) { return '<div class="dns-domain"><i></i><span>' + esc(r.domain) + '</span><b>' + count(r.count) + '</b></div>'; }).join('') : '<p class="dns-note">No blocked requests in today’s available log.</p>';
        html += '</section><p class="dns-transport">' + (client[''] ? 'Device DNS: plain observed.' : Object.keys(client).length ? 'Device DNS: encrypted observed.' : 'Device DNS: not observed.') + ' Upstream: ' + (upstream.Encrypted && !upstream['Plain DNS'] ? 'encrypted observed.' : upstream['Plain DNS'] ? 'plain observed.' : 'not observed.') + '</p>';
        d.days.slice(0, 7).forEach(function (day) { max = Math.max(max, Number(day.blocked) || 0); week += Number(day.blocked) || 0; });
        html += '<section class="dns-week"><div class="dns-week-copy"><h3>This week</h3><p><strong>' + count(week) + '</strong> blocked</p><span>Top: ' + esc(d.top.length ? d.top[0].domain : 'None recorded') + '</span></div><div class="dns-chart" role="img" aria-label="Blocked requests by calendar day">';
        d.days.slice(0, 7).forEach(function (day, i) {
          var height = Math.round(100 * day.blocked / max), label = String(day.date).slice(5), date = new Date(String(day.date) + 'T12:00:00Z'), names = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
          html += '<div class="dns-day' + (i === d.days.length - 1 ? ' is-today' : '') + '" aria-label="' + esc(label) + ': ' + count(day.blocked) + ' blocked"><div class="dns-bar-track"><div class="dns-bar" style="height:' + Math.max(day.blocked > 0 ? 3 : 0, Math.min(100, height)) + '%"></div></div><small>' + esc(isNaN(date.getTime()) ? label : names[date.getUTCDay()]) + '</small></div>';
        });
        html += '</div></section><section class="dns-details"><h3>Device &amp; log details</h3>';
        if (combined && Array.isArray(d.devices)) html += '<p>' + d.devices.map(function (item) { return esc(item.label) + ': ' + (item.configured ? item.lastQueryAt ? 'DNS received' : 'waiting for DNS' : 'not connected to this filter'); }).join(' · ') + '</p>';
        html += '<p>' + esc(d.lastQueryAt ? 'Last device query: ' + time(d.lastQueryAt, d.timezone, true) : 'Waiting for device queries. Routing is not yet verified.') + '</p><p>Checked ' + esc(time(d.sampledAt, d.timezone)) + ' · Today in ' + esc(d.timezone) + '.</p><p>' + (d.complete ? 'Counts from available log records. ' : 'Partial log: totals are lower bounds. ') + esc(d.history) + '</p><p class="dns-control-scope">Controls apply to all configured devices. The View button only changes displayed statistics.</p></section>';
        html += '<section class="dns-requests"><h3>Recent blocked requests</h3>';
        html += d.recent.length ? d.recent.slice(0, 12).map(function (r) { return '<div class="dns-request"><div><strong>' + esc(r.domain) + '</strong><span>' + esc(time(r.time, d.timezone, true)) + ' · ' + esc(r.device || '') + '</span></div><p>' + esc(r.reason) + ' / ' + esc(r.source) + '</p></div>'; }).join('') : '<p>No blocked requests yet.</p>';
        var e = t.enforcement, eTime = e && new Date(e.sampledAt).getTime(), eValid = e && e.ruleStatus === 'present' && e.device === 'tv' && e.period === 'current-router-counters' && isFinite(eTime) && Date.now() - eTime >= -5000 && Date.now() - eTime <= 360000 && typeof e.udpPackets === 'number' && typeof e.tcpPackets === 'number' && isFinite(e.udpPackets) && isFinite(e.tcpPackets) && e.udpPackets >= 0 && e.tcpPackets >= 0;
        html += '</section><section class="dns-details dns-enforcement"><h3>External DNS packets blocked</h3><p>' + (t.device === 'soundbar' ? 'No soundbar enforcement is configured. These router rules apply only to the TV.' : eValid ? 'TV: ' + count(e.udpPackets) + ' UDP · ' + count(e.tcpPackets) + ' TCP. Router rules present; counters checked ' + esc(time(e.sampledAt, d.timezone)) + '.' : 'Unknown — no recent router counter reading.') + '</p><p>External plain DNS on port 53 only, across all resolver destinations. Counts include retries and test packets, reset after firewall/router restarts, and are separate from today’s DNS lookups. Encrypted DNS is outside these rules. Pause changes blocklists; it does not remove router rules.</p></section>';
        html += '<section class="dns-coverage"><h3>Connection &amp; coverage</h3><p>' + esc(d.resolver) + ' · ' + esc(d.scope) + '</p><p>' + esc(d.coverage) + '. Cached traffic, hardcoded addresses, other resolvers and encrypted DNS can bypass filtering.</p><p>Lists: ' + esc((d.filters || []).join(', ')) + '. Categories are not supplied for every domain. DNS filtering cannot reliably remove YouTube video ads.</p><h3>Soundbar microphone</h3><p>DNS protection does not mute the microphone. Use the soundbar’s supported Mic On/Off button; red indicates muted. Microphone and assistant state are not read by this dashboard. Mic-dependent features may be affected.</p></section>';
      }
      el.body.innerHTML = html;
      el.body.scrollTop = t.scroll || 0; t.scroll = el.body.scrollTop;
    };
    document.addEventListener('visibilitychange', function () {
      stop(); var t = ctx.top();
      if (!document.hidden && t.id === 'dns') fetch(t);
      else if (document.hidden && t.id === 'dns') { t.data = null; t.error = 'Refresh to check protection.'; t.busy = false; }
    });
    window.addEventListener('blur', function () { stop(); var t = ctx.top(); if (t.id === 'dns') t.busy = false; });
    window.addEventListener('focus', function () { var t = ctx.top(); if (t.id === 'dns' && !document.hidden) fetch(t); });
    return { open: function () { ctx.push({ id: 'privacy', f: { i: 0 } }); } };
  }
  window.FramePrivacy = { install: install };
})();
