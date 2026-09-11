"""
services/translate_cache.py
Wraps gemini_service.translate_fields with a cache so the same
article+language pair is only ever translated once (Gemini quota is
precious). Cache key includes a content hash, so an admin-edited
article automatically gets re-translated instead of serving stale text.
"""
import hashlib
from extensions import cache
from config import Config
from services.gemini_service import translate_fields

_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


def _content_hash(article):
    raw = f"{article.title}|{article.ai_summary}|{article.detailed_summary or ''}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:10]


def translate_article(article, lang):
    """
    Mutates article.title / article.ai_summary / article.detailed_summary
    in place for display in `lang`. Display-only — never call
    db.session.commit() later in the same request after using this.
    """
    if not article or lang == 'en' or lang not in Config.LANGUAGE_NAMES_FOR_AI:
        return article

    key = f"tr:{lang}:{article.id}:{_content_hash(article)}"
    cached = cache.get(key)

    if cached is None:
        cached = translate_fields(
            {
                'title': article.title or '',
                'summary': article.ai_summary or '',
                'detailed_summary': article.detailed_summary or '',
            },
            Config.LANGUAGE_NAMES_FOR_AI[lang],
        )
        cache.set(key, cached, timeout=_CACHE_TTL)

    article.title = cached.get('title') or article.title
    article.ai_summary = cached.get('summary') or article.ai_summary
    article.detailed_summary = cached.get('detailed_summary') or article.detailed_summary
    return article


def translate_articles(articles, lang):
    for a in articles:
        translate_article(a, lang)
    return articles
