import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime

from extensions import db
from models.article import Article, RSSSource
from services.gemini_service import summarize_article, offline_fallback_summary, QuotaExhaustedError
VERIFIED_SOURCES = {
    "BBC News", "BBC Technology", "Reuters Top News",
    "Al Jazeera", "NASA Breaking News"
}

def fetch_all_feeds(app):
    """Fetch all active RSS sources and store new articles."""
    with app.app_context():
        sources = RSSSource.query.filter_by(active=True).all()
        total_new = 0
        # Shared across all sources in this run — once Gemini quota is
        # exhausted, stop calling it for the rest of this fetch cycle
        # instead of retrying (and logging) for every single article.
        gemini_state = {"quota_exhausted": False}

        for source in sources:
            count = _fetch_source(source, gemini_state)
            total_new += count
        print(f"[RSS] Fetched {total_new} new articles from {len(sources)} sources.")
        return total_new


def _fetch_source(source: RSSSource, gemini_state: dict) -> int:
    """Fetch a single RSS source. Returns count of new articles added."""
    source_name = source.name
    source_category = source.category
    source_country = source.country

    try:
        feed = feedparser.parse(source.url)
    except Exception as e:
        print(f"[RSS] Error parsing feed for {source_name}: {e}")
        return 0

    new_count = 0

    for entry in feed.entries[:15]:
        try:
            new_count += _process_entry(entry, source_name, source_category, source_country, gemini_state)
        except Exception as entry_err:
            # Any failure on this one article (DB blip, parsing issue, etc.)
            # should not take down the rest of the batch or this source's
            # remaining entries.
            db.session.rollback()
            print(f"[RSS] Skipped one article from {source_name} (error): {entry_err}")

    return new_count


def _process_entry(entry, source_name, source_category, source_country, gemini_state) -> int:
    """Process a single feed entry. Returns 1 if a new article was added, else 0."""
    url = entry.get('link', '')
    if not url:
        return 0

    # Duplicate check — this was previously unprotected and a transient
    # DB connection error here would crash the entire scheduled job.
    if Article.query.filter_by(original_url=url).first():
        return 0

    title    = entry.get('title', 'Untitled')
    content  = _extract_content(entry)
    pub_date = _parse_date(entry)
    thumb    = _extract_thumbnail(entry)

    if gemini_state["quota_exhausted"]:
        # All Gemini models are done for today — use offline fallback so new
        # articles still get a non-blank summary instead of nothing at all.
        ai_data = offline_fallback_summary(title)
    else:
        try:
            ai_data = summarize_article(title, content)
        except QuotaExhaustedError:
            gemini_state["quota_exhausted"] = True
            print("[Gemini] Quota exhausted — switching to offline fallback for the rest of this fetch cycle.")
            ai_data = offline_fallback_summary(title)
        except Exception as gemini_err:
            print(f"[Gemini] summarize_article failed unexpectedly: {gemini_err}")
            ai_data = offline_fallback_summary(title)

    article = Article(
        title             = title,
        original_url      = url,
        source_name       = source_name,
        category          = ai_data.get('category', source_category),
        country           = source_country or 'international',
        thumbnail_url     = thumb,
        published_at      = pub_date,
        ai_summary        = ai_data.get('summary', ''),
        detailed_summary  = ai_data.get('detailed_summary', ''),
        sentiment         = ai_data.get('sentiment', 'Neutral'),
        is_verified       = source_name in VERIFIED_SOURCES,
    )

    db.session.add(article)
    db.session.commit()
    return 1


def _extract_content(entry) -> str:
    """Extract best available text content from feed entry."""
    if hasattr(entry, 'content') and entry.content:
        return entry.content[0].get('value', '')
    if hasattr(entry, 'summary'):
        return entry.summary
    if hasattr(entry, 'description'):
        return entry.description
    return entry.get('title', '')


def _extract_thumbnail(entry) -> str:
    """Try to get a thumbnail image URL from the feed entry."""
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if m.get('medium') == 'image':
                return m.get('url', '')
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href', '')
    return ''


def _parse_date(entry) -> datetime:
    """Parse published date from feed entry."""
    for field in ('published', 'updated', 'created'):
        val = entry.get(field, '')
        if val:
            try:
                return parsedate_to_datetime(val).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.utcnow()


def seed_sources_from_config(app, config_sources):
    with app.app_context():
        for s in config_sources:
            existing = RSSSource.query.filter_by(url=s['url']).first()
            if not existing:
                src = RSSSource(
                    name     = s['name'],
                    url      = s['url'],
                    category = s['category'],
                    country  = s.get('country', 'international'),
                    active   = s['active'],
                )
                db.session.add(src)
            else:
                existing.country = s.get('country', 'international')
        db.session.commit()
        print("[DB] RSS sources seeded.")