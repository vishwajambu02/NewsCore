def translate_fields_batch(items: list, target_language: str):
    """
    Translate MANY articles' fields in a SINGLE Gemini call instead of one
    call per article.

    Returns (merged_list, translated_indices) — translated_indices is the
    set of positions that were actually translated, so the caller can avoid
    caching English fallbacks as if they were real translations.
    """
    clients = _get_clients()
    if not clients or not items:
        return items, set()

    payload = {}
    for i, item in enumerate(items):
        non_empty = {k: v for k, v in item.items() if v}
        if non_empty:
            payload[str(i)] = non_empty

    if not payload:
        return items, set()

    system = (
        f"You are a professional news translator. You will receive a JSON "
        f"object where each key is an article index and each value is an "
        f"object of text fields for that article. Translate every text "
        f"value into {target_language}. Keep meaning accurate and natural "
        f"for a news reader — do not summarise or shorten. Keep numbers, "
        f"dates and proper nouns intact. Return ONLY a valid JSON object "
        f"with the EXACT same structure (same indices as keys, same field "
        f"names inside each), no markdown, no extra text."
    )
    user_text = json.dumps(payload, ensure_ascii=False)

    try:
        raw = _call_gemini(user_text, system, max_output_tokens=8192,
                            temperature=0.2, allow_retry=False)
        result = _parse_json_response(raw)
        merged = [dict(item) for item in items]
        translated_indices = set()
        if isinstance(result, dict):
            for idx_str, translated in result.items():
                try:
                    idx = int(idx_str)
                except (TypeError, ValueError):
                    continue
                if 0 <= idx < len(merged) and isinstance(translated, dict):
                    merged[idx].update(
                        {k: v for k, v in translated.items() if k in merged[idx] and v}
                    )
                    translated_indices.add(idx)
        return merged, translated_indices
    except Exception as exc:
        if _is_quota_error(exc):
            logger.warning("[Gemini] translate_fields_batch quota hit, serving English fallback")
        else:
            logger.error("[Gemini] translate_fields_batch failed: %s", exc)
        return items, set()
