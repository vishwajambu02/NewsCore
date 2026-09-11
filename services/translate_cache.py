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
from services.gemini_service import translate_fields, translate_fields_batch

_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


def _content_hash(article):
    raw = f"{article.title}|{article.ai_summary}|{article.detailed_summary or ''}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:10]


def _cache_key(article, lang):
    return f"tr:{lang}:{article.id}:{_content_hash(article)}"


def _apply(article, translated):
    article.title = translated.get('title') or article.title
    article.ai_summary = translated.get('summary') or article.ai_summary
    article.detailed_summary = translated.get('detailed_summary') or article.detailed_summary
    return article


def translate_article(article, lang):
    """
    Mutates article.title / article.ai_summary / article.detailed_summary
    in place for display in `lang`. Display-only — never call
    db.session.commit() later in the same request after using this.
    """
    if not article or lang == 'en' or lang not in Config.LANGUAGE_NAMES_FOR_AI:
        return article

    key = _cache_key(article, lang)
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

    return _apply(article, cached)


def translate_articles(articles, lang):
    """
    Translates a list of articles for display in `lang`. Whatever is
    already cached is applied for free; everything else is translated in
    ONE batched Gemini call (instead of one call per article), so a page
    with 20-30 articles doesn't blow through the per-minute rate limit
    partway through and leave the rest untranslated.
    """
    if not articles or lang == 'en' or lang not in Config.LANGUAGE_NAMES_FOR_AI:
        return articles

    pending = []  # (article, cache_key) pairs not found in cache
    for a in articles:
        key = _cache_key(a, lang)
        cached = cache.get(key)
        if cached is not None:
            _apply(a, cached)
        else:
            pending.append((a, key))

    if not pending:
        return articles

    fields_list = [
        {
            'title': a.title or '',
            'summary': a.ai_summary or '',
            'detailed_summary': a.detailed_summary or '',
        }
        for a, _ in pending
    ]

    translated_list = translate_fields_batch(fields_list, Config.LANGUAGE_NAMES_FOR_AI[lang])

    for (a, key), translated in zip(pending, translated_list):
        cache.set(key, translated, timeout=_CACHE_TTL)
        _apply(a, translated)

    return articles
