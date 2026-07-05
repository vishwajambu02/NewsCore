/* ══════════════════════════════════════════════════════════
   NewsCore — bookmarks.js
   Saves/removes article bookmarks in localStorage.
   Works on every page (article cards + hero).
   ══════════════════════════════════════════════════════════ */

(function () {
  const KEY = 'nc-bookmarks';

  /* ── Storage helpers ──────────────────────────────────── */
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch { return {}; }
  }

  function save(bookmarks) {
    localStorage.setItem(KEY, JSON.stringify(bookmarks));
  }

  function isBookmarked(id) {
    return !!load()[id];
  }

  function toggle(id, title) {
    const bookmarks = load();
    if (bookmarks[id]) {
      delete bookmarks[id];
      save(bookmarks);
      return false;  // removed
    } else {
      bookmarks[id] = { id, title, savedAt: Date.now() };
      save(bookmarks);
      return true;   // added
    }
  }

  /* ── Badge counter in navbar ──────────────────────────── */
  function updateBadge() {
    const badge = document.getElementById('bookmarkBadge');
    if (!badge) return;
    const count = Object.keys(load()).length;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'grid' : 'none';
  }

  /* ── Sync button visual state ─────────────────────────── */
  function syncBtn(btn, bookmarked) {
    const svg = btn.querySelector('svg');
    btn.classList.toggle('bookmarked', bookmarked);
    btn.setAttribute('aria-label', bookmarked ? 'Remove bookmark' : 'Bookmark');
    if (svg) {
      svg.setAttribute('fill', bookmarked ? 'currentColor' : 'none');
    }
  }

  function syncAllBtns() {
    const bookmarks = load();
    document.querySelectorAll('.bookmark-btn[data-id]').forEach(btn => {
      syncBtn(btn, !!bookmarks[btn.dataset.id]);
    });
  }

  /* ── Click handler (event delegation) ────────────────── */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.bookmark-btn');
    if (!btn) return;

    const id    = btn.dataset.id;
    const title = btn.dataset.title || '';
    if (!id) return;

    const added = toggle(id, title);
    syncBtn(btn, added);
    updateBadge();

    if (typeof window.showToast === 'function') {
      window.showToast(added ? 'Bookmarked!' : 'Bookmark removed');
    }
  });

  /* ── Bookmarks page rendering ─────────────────────────── */
  function renderBookmarksPage() {
    const container = document.getElementById('bookmarksContainer');
    if (!container) return;

    const bookmarks = load();
    const entries   = Object.values(bookmarks).sort((a, b) => b.savedAt - a.savedAt);

    if (entries.length === 0) {
      container.innerHTML = `
        <div class="bookmarks-empty">
          <div class="bookmarks-empty-icon">🔖</div>
          <p class="bookmarks-empty-text">No bookmarks yet.<br>Hit the bookmark icon on any article.</p>
        </div>`;
      return;
    }

    container.innerHTML = entries.map(b => `
      <div class="bookmark-item" data-id="${b.id}">
        <div class="bookmark-info">
          <p class="bookmark-title">${escHtml(b.title)}</p>
          <span class="bookmark-date">${new Date(b.savedAt).toLocaleDateString()}</span>
        </div>
        <button class="icon-btn-sm bookmark-remove" data-id="${b.id}" aria-label="Remove">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6"/><path d="M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
      </div>`).join('');

    // Remove individual bookmarks
    container.querySelectorAll('.bookmark-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const bookmarks = load();
        delete bookmarks[id];
        save(bookmarks);
        renderBookmarksPage();
        syncAllBtns();
        updateBadge();
      });
    });
  }

  function escHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /* ── Init ─────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    syncAllBtns();
    updateBadge();
    renderBookmarksPage();
  });

  // Re-sync after infinite scroll adds new cards
  const gridEl = document.getElementById('articleGrid');
  if (gridEl) {
    new MutationObserver(syncAllBtns).observe(gridEl, { childList: true });
  }
})();