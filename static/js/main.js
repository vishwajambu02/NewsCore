/* ══════════════════════════════════════════════════════════
   NewsCore — main.js
   Theme · Navbar · Search · Time-ago · Infinite scroll
   Share modal · Email digest · Toast
   ══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Theme ─────────────────────────────────────────────── */
  const html   = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const saved  = localStorage.getItem('nc-theme') || 'dark';
  html.setAttribute('data-theme', saved);

  toggle?.addEventListener('click', () => {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('nc-theme', next);
  });

  /* ── Navbar scroll shadow ───────────────────────────────── */
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar?.classList.toggle('scrolled', window.scrollY > 10);
  }, { passive: true });

  /* ── Search drawer ──────────────────────────────────────── */
  const searchToggle = document.getElementById('searchToggle');
  const searchDrawer = document.getElementById('searchDrawer');
  const searchInput  = document.getElementById('searchInput');

  searchToggle?.addEventListener('click', () => {
    searchDrawer?.classList.toggle('open');
    if (searchDrawer?.classList.contains('open')) searchInput?.focus();
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.nav-search-form')) {
      searchDrawer?.classList.remove('open');
    }
  });

  /* ── Mobile categories panel ─────────────────────────────
     nav-pills is hidden below 768px (no room for a horizontal
     pill row) — this hamburger + slide-down panel is the
     replacement so category navigation isn't just gone on mobile. */
  const catToggle   = document.getElementById('mobileCatToggle');
  const catPanel    = document.getElementById('mobileCatPanel');
  const catBackdrop = document.getElementById('mobileCatBackdrop');

  function closeCatPanel() {
    catPanel?.classList.remove('open');
    catBackdrop?.classList.remove('open');
    catToggle?.setAttribute('aria-expanded', 'false');
  }

  catToggle?.addEventListener('click', () => {
    const isOpen = catPanel?.classList.contains('open');
    if (isOpen) {
      closeCatPanel();
    } else {
      catPanel?.classList.add('open');
      catBackdrop?.classList.add('open');
      catToggle.setAttribute('aria-expanded', 'true');
      searchDrawer?.classList.remove('open');
    }
  });

  catBackdrop?.addEventListener('click', closeCatPanel);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeCatPanel();
  });

  /* ── Live time-ago updates ──────────────────────────────── */
  function timeAgoText(iso) {
    if (!iso) return '';
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 60)    return `${diff}s ago`;
    if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }

  function updateTimeAgo() {
    document.querySelectorAll('.time-ago[data-time]').forEach(el => {
      el.textContent = timeAgoText(el.dataset.time);
    });
  }

  updateTimeAgo();
  setInterval(updateTimeAgo, 30_000);

  /* ── Scroll-reveal (IntersectionObserver) ───────────────── */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        revealObserver.unobserve(e.target);
      }
    });
  }, { rootMargin: '0px 0px -60px 0px', threshold: 0.05 });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  /* ── Infinite scroll ────────────────────────────────────── */
  const sentinel = document.getElementById('scrollSentinel');
  const grid     = document.getElementById('articleGrid');
  const spinner  = document.getElementById('loadingSpinner');
  const noMore   = document.getElementById('noMore');
  let isFetching = false;

  if (sentinel && grid) {
    const observer = new IntersectionObserver(async (entries) => {
      if (!entries[0].isIntersecting || isFetching) return;

      const page     = parseInt(sentinel.dataset.page || '2');
      const category = sentinel.dataset.category || '';

      isFetching = true;
      if (spinner) spinner.style.display = 'flex';

      try {
        const params = new URLSearchParams({ page, limit: 12 });
        if (category) params.set('category', category);

        const res  = await fetch(`/api/articles?${params}`);
        const data = await res.json();

        if (!data.articles?.length || !data.has_next) {
          observer.disconnect();
          if (spinner) spinner.style.display = 'none';
          if (noMore)  noMore.style.display  = 'block';
          return;
        }

        // Hide skeleton loaders on first real fetch
        grid.querySelectorAll('.skeleton').forEach(s => s.remove());

        data.articles.forEach((a, i) => {
          const card = buildCard(a, i);
          grid.insertBefore(card, sentinel);
        });

        sentinel.dataset.page = page + 1;

      } catch (err) {
        console.error('[InfiniteScroll]', err);
      } finally {
        isFetching = false;
        if (spinner) spinner.style.display = 'none';
      }
    }, { rootMargin: '400px' });

    observer.observe(sentinel);
  }

  /* ── Build card (for infinite scroll) ──────────────────── */
  function buildCard(a, idx) {
    const card = document.createElement('article');
    card.className = 'article-card';
    card.dataset.id = a.id;
    card.style.animationDelay = `${idx * 0.05}s`;

    const sentClass = `sentiment-tag--${(a.sentiment || 'neutral').toLowerCase()}`;
    const catColor  = getCatColor(a.category);
    const timeAgo   = timeAgoText(a.published_at);
    const initial   = (a.category || 'N')[0];

    const imgHtml = a.thumbnail
      ? `<img src="${esc(a.thumbnail)}" alt="${esc(a.title)}" class="card-img" loading="lazy" />`
      : `<div class="card-img-placeholder"><span class="placeholder-cat">${initial}</span></div>`;

    const summaryHtml = a.summary
      ? `<p class="card-summary">${esc(a.summary)}</p>`
      : '';

    const verifiedHtml = a.is_verified
      ? '<span class="verified-badge verified-badge--sm">✓ Verified</span>'
      : '';

    card.innerHTML = `
      <div class="card-img-wrap">
        ${imgHtml}
        <span class="cat-badge cat-badge--corner" style="background:${catColor}">${esc(a.category)}</span>
      </div>
      <div class="card-body">
        <div class="card-meta">
          <span class="sentiment-tag ${sentClass}">${esc(a.sentiment || 'Neutral')}</span>
          ${verifiedHtml}
          <span class="time-ago" data-time="${a.published_at || ''}">${timeAgo}</span>
        </div>
        <h3 class="card-title">
          <a href="/article/${a.id}">${esc(a.title)}</a>
        </h3>
        ${summaryHtml}
        <div class="card-footer">
          <span class="source-label">${esc(a.source || a.source_name || '')}</span>
          <div class="card-actions">
            <button class="icon-btn-sm bookmark-btn" data-id="${a.id}" data-title="${esc(a.title)}" aria-label="Bookmark">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
            </button>
            <button class="icon-btn-sm listen-btn" data-text="${esc(a.summary || a.title)}" aria-label="Listen">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            </button>
            <button class="icon-btn-sm share-btn" data-url="${esc(a.url || a.original_url || '')}" data-title="${esc(a.title)}" aria-label="Share">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            </button>
          </div>
        </div>
      </div>`;

    return card;
  }

  /* ── Share modal ────────────────────────────────────────── */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.share-btn');
    if (!btn) return;
    openShareModal(
      btn.dataset.url   || window.location.href,
      btn.dataset.title || document.title
    );
  });

  function openShareModal(url, title) {
    document.getElementById('shareModal')?.remove();

    const modal = document.createElement('div');
    modal.id        = 'shareModal';
    modal.className = 'share-modal open';

    modal.innerHTML = `
      <div class="share-panel">
        <button class="share-close" id="shareClose">✕</button>
        <p class="share-title">Share this story</p>
        <div class="share-buttons">
          <a href="https://wa.me/?text=${encodeURIComponent(title + ' ' + url)}"
             target="_blank" class="share-btn-opt">WhatsApp</a>
          <a href="https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}"
             target="_blank" class="share-btn-opt">𝕏 (Twitter)</a>
        </div>
        <div class="share-copy-row">
          <input class="share-url-input" value="${esc(url)}" readonly />
          <button class="btn-read" id="copyLinkBtn">Copy</button>
        </div>
      </div>`;

    document.body.appendChild(modal);

    document.getElementById('shareClose').onclick = () => modal.remove();
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
    document.getElementById('copyLinkBtn').onclick = () => {
      navigator.clipboard.writeText(url).then(() => showToast('Link copied!'));
    };
  }

  /* ── Follow category ─────────────────────────────────────
     This button existed in the markup with zero JS behind it —
     that's why clicking did nothing. Wiring it up here, using
     localStorage so it works without needing user accounts. */
  const FOLLOW_KEY = 'nc-followed-categories';

  function getFollowed() {
    try { return JSON.parse(localStorage.getItem(FOLLOW_KEY)) || []; }
    catch { return []; }
  }

  function setFollowed(list) {
    localStorage.setItem(FOLLOW_KEY, JSON.stringify(list));
  }

  function paintFollowBtn(btn, isFollowing) {
    const cat   = btn.dataset.category;
    const color = btn.dataset.color || '';
    const icon  = btn.querySelector('.follow-btn-icon');
    const text  = btn.querySelector('.follow-btn-text');

    btn.classList.toggle('following', isFollowing);
    if (color) btn.style.setProperty('--follow-color', color);
    if (icon) icon.textContent = isFollowing ? '✓' : '+';
    if (text) text.textContent = isFollowing ? `Following ${cat}` : `Follow ${cat}`;
  }

  document.querySelectorAll('.follow-category-btn').forEach((btn) => {
    paintFollowBtn(btn, getFollowed().includes(btn.dataset.category));

    btn.addEventListener('click', () => {
      const cat = btn.dataset.category;
      const followed = getFollowed();
      const isFollowing = followed.includes(cat);
      const next = isFollowing
        ? followed.filter((c) => c !== cat)
        : [...followed, cat];

      setFollowed(next);
      paintFollowBtn(btn, !isFollowing);

      btn.classList.remove('just-toggled');
      requestAnimationFrame(() => btn.classList.add('just-toggled'));

      showToast(
        isFollowing ? `Unfollowed ${cat}` : `✓ Following ${cat} — you'll see more of this`
      );
    });
  });

  /* ── Email digest subscribe ─────────────────────────────── */
  document.getElementById('digestForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = e.target.querySelector('input[type="email"]');
    const email = input.value.trim();
    if (!email) return;

    try {
      const res  = await fetch('/api/subscribe', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ email, categories: ['World', 'Technology'] }),
      });
      const data = await res.json();
      showToast(data.message || 'Subscribed!');
      input.value = '';
    } catch {
      showToast('Something went wrong.', 'error');
    }
  });

  /* ── Toast ──────────────────────────────────────────────── */
  window.showToast = function (msg, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent   = msg;
    toast.style.borderColor = type === 'error' ? 'var(--signal)' : 'var(--border)';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  };

  /* ── Helpers ────────────────────────────────────────────── */
  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  const CAT_COLORS = {
    World:         '#E63946',
    Technology:    '#457B9D',
    Sports:        '#2DC653',
    Science:       '#7B2FBE',
    Business:      '#F4A261',
    Entertainment: '#E76F51',
    Health:        '#06D6A0',
  };

  function getCatColor(cat) {
    return CAT_COLORS[cat] || '#888';
  }

});