/* ══════════════════════════════════════════════════════════
   NewsCore — speech.js
   Text-to-speech via Web Speech API.
   Handles .listen-btn clicks on cards and hero.
   ══════════════════════════════════════════════════════════ */

(function () {
  if (!('speechSynthesis' in window)) return;  // unsupported — silently exit

  const synth     = window.speechSynthesis;
  let   activeBtn = null;
  let   utterance = null;

  function stopSpeech() {
    synth.cancel();
    if (activeBtn) {
      activeBtn.classList.remove('listening');
      activeBtn.setAttribute('aria-label', 'Listen');
      activeBtn.setAttribute('aria-pressed', 'false');
    }
    activeBtn  = null;
    utterance  = null;
  }

  function startSpeech(btn, text) {
    stopSpeech();   // stop any existing

    utterance = new SpeechSynthesisUtterance(text);
    utterance.lang  = 'en-US';
    utterance.rate  = 0.95;
    utterance.pitch = 1.0;

    utterance.onend = utterance.onerror = () => {
      btn.classList.remove('listening');
      btn.setAttribute('aria-label', 'Listen');
      btn.setAttribute('aria-pressed', 'false');
      if (activeBtn === btn) activeBtn = null;
    };

    activeBtn = btn;
    btn.classList.add('listening');
    btn.setAttribute('aria-label', 'Stop reading');
    btn.setAttribute('aria-pressed', 'true');

    synth.speak(utterance);
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.listen-btn');
    if (!btn) return;

    const text = btn.dataset.text?.trim();
    if (!text) return;

    // Toggle: if this button is already active, stop it
    if (activeBtn === btn && synth.speaking) {
      stopSpeech();
    } else {
      startSpeech(btn, text);
    }
  });

  // Stop speech when navigating away
  window.addEventListener('pagehide', stopSpeech);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopSpeech();
  });
})();