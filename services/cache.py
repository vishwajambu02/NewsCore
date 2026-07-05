"""
services/cache.py
─────────────────
Thin helpers around Flask-Caching.
Import `cache` from extensions, use these helpers for manual cache ops
(e.g. busting homepage cache after an RSS fetch, or caching heavy queries).
"""

from extensions import cache


# ── Key constants ────────────────────────────────────────────
HOMEPAGE_KEY   = 'homepage'
TRENDING_KEY   = 'trending'
STATS_KEY      = 'view::stats'
CAT_KEY_PREFIX = 'category::'     # e.g. "category::Technology"
API_KEY_PREFIX = 'api::articles::' # e.g. "api::articles::page1"


# ── Manual get / set / delete ─────────────────────────────────

def get(key: str):
    """Retrieve a value from cache. Returns None on miss."""
    return cache.get(key)


def set(key: str, value, timeout: int = 120):
    """Store a value in cache with optional timeout (seconds)."""
    cache.set(key, value, timeout=timeout)


def delete(key: str):
    """Delete a single key from cache."""
    cache.delete(key)


def clear_all():
    """Wipe the entire cache (use after bulk RSS fetch)."""
    cache.clear()


# ── Convenience busters ───────────────────────────────────────

def bust_homepage():
    """Call this after new articles are saved to invalidate homepage cache."""
    cache.delete(HOMEPAGE_KEY)


def bust_category(category: str):
    """Invalidate a specific category page cache."""
    cache.delete(f"{CAT_KEY_PREFIX}{category}")


def bust_after_fetch():
    """
    Called automatically by rss_fetcher after a successful fetch run.
    Clears homepage + trending so fresh articles appear immediately.
    """
    bust_homepage()
    cache.delete(TRENDING_KEY)
    cache.delete(STATS_KEY)


# ── Cached query helpers ──────────────────────────────────────

def get_or_set(key: str, fn, timeout: int = 120):
    """
    Cache-aside pattern.
    Returns cached value if present, otherwise calls fn(), caches + returns result.

    Usage:
        articles = get_or_set('latest_articles', lambda: Article.query...all(), timeout=60)
    """
    value = cache.get(key)
    if value is None:
        value = fn()
        cache.set(key, value, timeout=timeout)
    return value