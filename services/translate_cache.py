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


def _cache_key(article, lang, include_detailed):
    variant = 'full' if include_detailed else 'brief'
    return f"tr:{lang}:{variant}:{article.id}:{_content_hash(article)}"


def _apply(article, translated):
    article.title = translated.get('title') or article.title
    article.ai_summary = translated.get('summary') or article.ai_summary
    if 'detailed_summary' in translated:
        article.detailed_summary = translated.get('detailed_summary') or article.detailed_summary
    return article


def translate_article(article, lang, include_detailed=True):
    """
    Mutates article.title / article.ai_summary (and detailed_summary when
    include_detailed=True) in place for display in `lang`. Display-only —
    never call db.session.commit() later in the same request after using
    this.

    include_detailed should only be True on the single-article page, where
    detailed_summary is actually shown — sending it for every card on a
    list page bloats the translation payload for no visual benefit.
    """
    if not article or lang == 'en' or lang not in Config.LANGUAGE_NAMES_FOR_AI:
        return article

    key = _cache_key(article, lang, include_detailed)
    cached = cache.get(key)

    if cached is None:
        fields = {
            'title': article.title or '',
            'summary': article.ai_summary or '',
        }
        if include_detailed:
            fields['detailed_summary'] = article.detailed_summary or ''

        cached = translate_fields(fields, Config.LANGUAGE_NAMES_FOR_AI[lang])
        cache.set(key, cached, timeout=_CACHE_TTL)

    return _apply(article, cached)


def translate_articles(articles, lang, include_detailed=False):
    """
    Translates a list of articles for display in `lang`. Whatever is
    already cached is applied for free; everything else is translated in
    ONE batched Gemini call (instead of one call per article), so a page
    with 20-30 articles doesn't blow through the per-minute rate limit or
    the output-token limit partway through and leave the rest untranslated.

    include_detailed defaults to False because list/card views (homepage,
    category, trending, search) never render detailed_summary — including
    it here would roughly triple the batch payload for zero visible gain
    and risks the model's JSON response getting truncated/malformed.
    """
    if not articles or lang == 'en' or lang not in Config.LANGUAGE_NAMES_FOR_AI:
        return articles

    pending = []  # (article, cache_key) pairs not found in cache
    for a in articles:
        key = _cache_key(a, lang, include_detailed)
        cached = cache.get(key)
        if cached is not None:
            _apply(a, cached)
        else:
            pending.append((a, key))

    if not pending:
        return articles

    fields_list = []
    for a, _ in pending:
        fields = {
            'title': a.title or '',
            'summary': a.ai_summary or '',
        }
        if include_detailed:
            fields['detailed_summary'] = a.detailed_summary or ''
        fields_list.append(fields)

    translated_list = translate_fields_batch(fields_list, Config.LANGUAGE_NAMES_FOR_AI[lang])

    for (a, key), translated in zip(pending, translated_list):
        cache.set(key, translated, timeout=_CACHE_TTL)
        _apply(a, translated)

    return articles
