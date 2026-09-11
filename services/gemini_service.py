def translate_fields(fields: dict, target_language: str) -> dict:
    """
    Translate a dict of text fields (e.g. {'title':..., 'summary':...}) into
    target_language (e.g. 'Hindi') in a SINGLE Gemini call — batching keeps
    quota usage down since we're translating per-article, per-language.

    Falls back to the original values on any failure (quota, parse error,
    no client) so a translation hiccup never blanks out the UI.
    """
    client = _get_client()
    if client is None or not fields:
        return fields

    non_empty = {k: v for k, v in fields.items() if v}
    if not non_empty:
        return fields

    system = (
        f"You are a professional news translator. Translate the values in the "
        f"given JSON object into {target_language}. Keep the meaning accurate "
        f"and natural for a news reader — do not summarise or shorten. Keep "
        f"numbers, dates and proper nouns intact. Return ONLY a valid JSON "
        f"object with the exact same keys as the input, no markdown, no extra text."
    )
    user_text = json.dumps(non_empty, ensure_ascii=False)

    try:
        raw = _call_gemini(user_text, system, max_output_tokens=2048, temperature=0.2)
        result = _parse_json_response(raw)
        if isinstance(result, dict):
            merged = dict(fields)
            merged.update({k: v for k, v in result.items() if k in fields and v})
            return merged
        return fields
    except Exception as exc:
        if _is_quota_error(exc):
            logger.warning("[Gemini] translate_fields quota hit, serving English fallback")
        else:
            logger.error("[Gemini] translate_fields failed: %s", exc)
        return fields
