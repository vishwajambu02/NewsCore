/* ══════════════════════════════════════════════════════════
   NewsCore — splash.js
   Plays the boot animation once per browser session, then
   tears itself out of the DOM. The head-inline snippet in
   base.html already prevents any flash on repeat page loads.

   Includes a hard failsafe: no matter what goes wrong (slow
   network, cold-start delay, a thrown error), the splash is
   guaranteed to be removed within HARD_FAILSAFE_MS.
   ══════════════════════════════════════════════════════════ */
(function () {
  const splash = document.getElementById('splashScreen');
  if (!splash) return;

  const HARD_FAILSAFE_MS = 4000; // absolute upper bound, no matter what

  function forceRemove() {
    if (!splash.isConnected) return; // already removed
    splash.remove();
    document.body.classList.remove('splash-lock');
    try { sessionStorage.setItem('nc-splash-shown', '1'); } catch (e) { /* ignore */ }
  }

  // Hard failsafe — fires regardless of any error below.
  const failsafeTimer = setTimeout(forceRemove, HARD_FAILSAFE_MS);

  try {
    // Already shown this session (html.no-splash) → nothing to do.
    if (document.documentElement.classList.contains('no-splash')) {
      clearTimeout(failsafeTimer);
      forceRemove();
      return;
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      clearTimeout(failsafeTimer);
      forceRemove();
      return;
    }

    document.body.classList.add('splash-lock');

    const TOTAL_HOLD = 2350;   // ms — full timeline before exit begins
    const EXIT_DURATION = 600; // ms — matches the CSS exit animation

    // Animate the percentage counter alongside the CSS progress-bar fill.
    const pctEl = document.getElementById('splashPct');
    const PROGRESS_START = 1350; // matches .splash-progress-fill animation-delay
    const PROGRESS_DURATION = 1250;

    if (pctEl) {
      const startTime = performance.now() + PROGRESS_START;
      function tick() {
        try {
          const elapsed = performance.now() - startTime;
          const pct = Math.min(100, Math.max(0, Math.round((elapsed / PROGRESS_DURATION) * 100)));
          pctEl.textContent = pct + '%';
          if (pct < 100) requestAnimationFrame(tick);
        } catch (e) {
          // If the counter breaks, the failsafe timer will still clean up.
        }
      }
      requestAnimationFrame(tick);
    }

    setTimeout(() => {
      try {
        splash.classList.add('splash-exit');
        setTimeout(() => {
          clearTimeout(failsafeTimer);
          forceRemove();
        }, EXIT_DURATION);
      } catch (e) {
        clearTimeout(failsafeTimer);
        forceRemove();
      }
    }, TOTAL_HOLD);

  } catch (e) {
    // Any unexpected error → let the failsafe (already scheduled) handle it,
    // but no need to wait the full 4s if we already know something broke.
    clearTimeout(failsafeTimer);
    forceRemove();
  }
})();
