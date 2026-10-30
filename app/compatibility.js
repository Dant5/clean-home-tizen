/* Detect actual flex spacing; CSS.supports('gap') also matches older grid-only implementations. */
(function () {
  'use strict';
  var probe = document.createElement('div'), first = document.createElement('div'), second = document.createElement('div');
  probe.style.cssText = 'position:absolute;visibility:hidden;display:flex;flex-direction:column;row-gap:1px;top:-100px;left:0;width:1px;padding:0;border:0';
  first.style.cssText = second.style.cssText = 'height:1px;min-height:1px;padding:0;border:0';
  probe.appendChild(first); probe.appendChild(second);
  document.documentElement.appendChild(probe);
  var gap = probe.scrollHeight === 3;
  probe.parentNode.removeChild(probe);
  if (!gap) document.documentElement.className += ' no-flex-gap';
}());
