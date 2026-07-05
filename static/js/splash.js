/* ══════════════════════════════════════════════════════════
   NewsCore — splash.js
   Plays the boot animation once per browser session, then
   tears itself out of the DOM. The head-inline snippet in
   base.html already prevents any flash on repeat page loads.
   ══════════════════════════════════════════════════════════ */

(function () {
  const splash = document.getElementById('splashScreen');
  if (!splash) return;

  // Already shown this session (html.no-splash) → nothing to do.
  if (document.documentElement.classList.contains('no-splash')) {
    splash.remove();
    return;
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (reduceMotion) {
    splash.remove();
    sessionStorage.setItem('nc-splash-shown', '1');
    return;
  }

  document.body.classList.add('splash-lock');

  const TOTAL_HOLD = 2350;  // ms — full timeline before exit begins
  const EXIT_DURATION = 600; // ms — matches the CSS exit animation

  // Animate the percentage counter alongside the CSS progress-bar fill.
  const pctEl = document.getElementById('splashPct');
  const PROGRESS_START = 1350; // matches .splash-progress-fill animation-delay
  const PROGRESS_DURATION = 1250;

  if (pctEl) {
    const startTime = performance.now() + PROGRESS_START;
    function tick() {
      const elapsed = performance.now() - startTime;
      const pct = Math.min(100, Math.max(0, Math.round((elapsed / PROGRESS_DURATION) * 100)));
      pctEl.textContent = pct + '%';
      if (pct < 100) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  setTimeout(() => {
    splash.classList.add('splash-exit');

    setTimeout(() => {
      splash.remove();
      document.body.classList.remove('splash-lock');
      sessionStorage.setItem('nc-splash-shown', '1');
    }, EXIT_DURATION);

  }, TOTAL_HOLD);
})();