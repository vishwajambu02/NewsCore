/* ══════════════════════════════════════════════════════════
   NewsCore — notifications.js
   Requests browser push notification permission after a
   delay, and handles incoming push events via Service Worker.
   Gracefully no-ops if the browser doesn't support it.
   ══════════════════════════════════════════════════════════ */

(function () {
  if (!('Notification' in window)) return;  // not supported

  /* ── Ask for permission (once, after 45s dwell) ───────── */
  const ASKED_KEY = 'nc-notif-asked';

  function shouldAsk() {
    return (
      Notification.permission === 'default' &&
      !localStorage.getItem(ASKED_KEY)
    );
  }

  function requestPermission() {
    if (!shouldAsk()) return;
    localStorage.setItem(ASKED_KEY, '1');

    Notification.requestPermission().then(perm => {
      if (perm === 'granted') {
        showLocalNotification(
          '🗞️ NewsCore notifications on',
          'You\'ll get breaking news alerts as they happen.'
        );
      }
    });
  }

  // Ask after 45 seconds of dwell time — not immediately
  setTimeout(requestPermission, 45_000);

  /* ── Show a local notification ────────────────────────── */
  function showLocalNotification(title, body, url) {
    if (Notification.permission !== 'granted') return;

    const n = new Notification(title, {
      body,
      icon:   '/static/images/icon-192.png',
      badge:  '/static/images/icon-72.png',
      tag:    'newscore-alert',
      silent: false,
    });

    if (url) {
      n.onclick = () => { window.open(url, '_blank'); n.close(); };
    }

    // Auto-close after 8 seconds
    setTimeout(() => n.close(), 8000);
  }

  /* ── Register service worker ──────────────────────────── */
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => {
        console.log('[SW] Registered:', reg.scope);
      })
      .catch(err => {
        // SW missing is fine — notifications still work as local
        console.debug('[SW] Registration skipped:', err.message);
      });
  }

  /* ── Listen for push messages from SW ────────────────── */
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
      const { type, title, body, url } = event.data || {};
      if (type === 'PUSH_NEWS') {
        showLocalNotification(title || 'Breaking News', body || '', url);
      }
    });
  }

  /* ── Expose for manual use (e.g. from admin) ─────────── */
  window.NCNotify = { show: showLocalNotification };
})();