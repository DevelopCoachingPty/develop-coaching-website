/* booking-tracking.js - FlowBuild booking completion -> existing Google tag
 * Vanilla browser IIFE. No tag loader, cookie changes, storage or personal data.
 *
 * LIMITATION: dedup is per-document, in-memory, and cleared on bfcache
 * restore. It is NOT appointment-level durable deduplication. A full page
 * reload, a new document, or a bfcache restore can allow another event.
 */
(function () {
  "use strict";

  var PROD_HOSTS = ["develop-coaching.com", "www.develop-coaching.com"];
  var ORIGIN = "https://link.flow-build.com";
  var PATHNAME = "/widget/booking/zXUkPVoGKzRyirwYa0Ck";
  var EVENT_NAME = "msgsndr-booking-complete";
  var CALENDAR_ID = "zXUkPVoGKzRyirwYa0Ck";
  var DL_EVENT = "scale_session_booked";
  var DL_PROVIDER = "FlowBuild";

  if (window.__flowBuildBookingTrackingInstalled) return;
  window.__flowBuildBookingTrackingInstalled = true;

  if (PROD_HOSTS.indexOf(window.location.hostname) === -1) return;

  var booked = false;

  function isPlainObject(v) {
    if (v === null || typeof v !== "object") return false;
    if (Array.isArray(v)) return false;
    var proto = Object.getPrototypeOf(v);
    return proto === Object.prototype || proto === null;
  }

  function pathMatches(pathname) {
    if (pathname === PATHNAME) return true;
    if (pathname === PATHNAME + "/") return true;
    return false;
  }

  function isTrustedIframeSource(source) {
    if (!source || typeof source !== "object") return false;
    var frames = document.querySelectorAll("iframe");
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      if (f.contentWindow !== source) continue;
      if (!f.isConnected) continue;
      var src = f.getAttribute("src");
      if (!src) continue;
      var url;
      try {
        url = new URL(src, document.baseURI);
      } catch (e) {
        continue;
      }
      if (url.protocol !== "https:") continue;
      if (url.origin !== ORIGIN) continue;
      if (!pathMatches(url.pathname)) continue;
      return true;
    }
    return false;
  }

  function pushBooked() {
    // Use the data layer that already owns the site's Google tag and consent.
    // Do not create a second config, client ID, session ID or attribution source.
    var dl = window.dataLayer;
    if (!dl || typeof dl.push !== "function") return false;
    if (window['ga-disable-G-PXT2VCVFLW']) return false;
    if (window.navigator && (window.navigator.globalPrivacyControl || window.navigator.doNotTrack === '1')) return false;
    function googleEvent() { dl.push(arguments); }
    googleEvent('event', DL_EVENT, {
      send_to: 'G-PXT2VCVFLW',
      transport_type: 'beacon',
      scheduler_provider: DL_PROVIDER,
      booking_calendar_id: CALENDAR_ID
    });
    return true;
  }

  function onMessage(event) {
    if (event.origin !== ORIGIN) return;
    if (!isTrustedIframeSource(event.source)) return;

    var data = event.data;
    if (!Array.isArray(data)) return;
    if (data.length !== 2) return;
    if (data[0] !== EVENT_NAME) return;

    var payload = data[1];
    if (!isPlainObject(payload)) return;
    if (payload.calendarId !== CALENDAR_ID) return;

    if (booked) return;
    booked = pushBooked();
  }

  window.addEventListener("message", onMessage);

  window.addEventListener("pageshow", function (e) {
    if (e && e.persisted) booked = false;
  });
})();
