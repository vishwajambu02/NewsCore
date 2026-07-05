"""
services/gemini_service.py
Gemini AI integration for NewsCore.
Provides: article summarization, sentiment analysis, category classification.
Uses google-genai SDK (new) — pip install google-genai
"""

import os
import json
import re
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QuotaExhaustedError(Exception):
    """Raised when the Gemini API reports quota/rate-limit exhaustion."""
    pass


# ── SDK initialisation ──────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    _SDK = "genai"
except ImportError:
    try:
        import google.generativeai as genai_old
        _SDK = "generativeai"
    except ImportError:
        genai = None
        genai_old = None
        _SDK = None

_client = None

# Multiple free-tier models, tried in order. Each model has its OWN separate
# daily quota bucket on Google's side — so when one model's daily limit is
# exhausted, we fall back to the next one instead of stopping entirely.
# This roughly multiplies total free daily capacity across models.
_MODEL_FALLBACK_CHAIN = [
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]
_model_name = _MODEL_FALLBACK_CHAIN[0]
_warned = False

# Retry settings for transient server-side errors (503 UNAVAILABLE, high demand)
_MAX_RETRIES = 3
_RETRY_DELAYS = [5, 10, 20]  # seconds, increasing backoff


def _get_client():
    """Lazily initialise the Gemini client."""
    global _client, _warned
    if _client is not None:
        return _client

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        if not _warned:
            print("[Gemini] GEMINI_API_KEY not set — AI features disabled. "
                  "Set GEMINI_API_KEY in your .env file to enable summaries.")
            _warned = True
        return None

    if _SDK == "genai":
        _client = genai.Client(api_key=api_key)
    elif _SDK == "generativeai":
        genai_old.configure(api_key=api_key)
        _client = genai_old.GenerativeModel(_model_name)
    else:
        logger.warning("[Gemini] No Gemini SDK found. Install: pip install google-genai")
        print("[Gemini] No SDK found — run: pip install google-genai")
        _client = None

    return _client


# ── Public API ──────────────────────────────────────────────────────────────

CATEGORIES = ["World", "Technology", "Sports", "Science", "Business", "Entertainment", "Health"]

_SYSTEM_PROMPT = """You are a professional news editor AI. Given a news article's title and short RSS description, return ONLY a valid JSON object with these exact fields:

{
  "summary": "A 2-3 sentence plain-English summary for card/preview display. 40-80 words.",
  "detailed_summary": "A longer, ORIGINAL explainer in your own words, 4-6 short paragraphs (roughly 250-400 words total). Cover: what happened, key context/background the reader needs, who is involved, and why it matters. Do NOT copy or closely paraphrase sentence-by-sentence from the source text — write it as your own fresh explainer article based on the facts given. Use \\n\\n between paragraphs.",
  "sentiment": "Positive" | "Negative" | "Neutral" | "Mixed",
  "category": "World" | "Technology" | "Sports" | "Science" | "Business" | "Entertainment" | "Health"
}

Rules:
- summary must be 40-80 words, factual, no bullet points
- detailed_summary must be original writing, not a copy of the source, and should read like a standalone news explainer
- If the source description is too short to support a full explainer, write what you can and stay factual — do not invent specific quotes, numbers, or named details that aren't in the input
- sentiment reflects the overall tone and implication of the story
- category is ONE of the exact values listed above
- Return ONLY the JSON object, no markdown, no explanation, no preamble
"""


def _is_quota_error(exc: Exception) -> bool:
    """Detect quota/rate-limit errors from either SDK's exception message/status."""
    msg = str(exc).lower()
    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status_code in (429,):
        return True
    quota_markers = ("quota", "rate limit", "resource_exhausted", "429", "too many requests")
    return any(marker in msg for marker in quota_markers)


def _is_overload_error(exc: Exception) -> bool:
    """Detect transient server-side overload errors (503 UNAVAILABLE) — worth retrying."""
    msg = str(exc).lower()
    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status_code in (503,):
        return True
    overload_markers = ("503", "unavailable", "high demand", "overloaded")
    return any(marker in msg for marker in overload_markers)


def _generate_with_model(model_name: str, user_text: str, system_prompt: str,
                          max_output_tokens: int, temperature: float, client) -> str:
    """Single attempt against a specific model. Raises on any error."""
    if _SDK == "genai":
        response = client.models.generate_content(
            model=model_name,
            contents=user_text,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
        return response.text.strip()

    elif _SDK == "generativeai":
        prompt = system_prompt + "\n\n" + user_text
        response = client.generate_content(
            prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens},
        )
        return response.text.strip()

    else:
        raise RuntimeError("No Gemini SDK available")


def _call_gemini(user_text: str, system_prompt: str, max_output_tokens: int, temperature: float) -> str:
    """
    Makes a call to the Gemini API and returns raw text.

    - Retries the SAME model on transient 503/overload errors, with increasing backoff.
    - On a daily-quota (429) error, moves on to the NEXT model in the fallback chain
      instead of giving up — each model has its own separate daily quota bucket.
    - Only raises QuotaExhaustedError once EVERY model in the chain is exhausted.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError("Gemini client not available")

    last_exc = None

    for model_name in _MODEL_FALLBACK_CHAIN:
        for attempt in range(_MAX_RETRIES):
            try:
                return _generate_with_model(
                    model_name, user_text, system_prompt, max_output_tokens, temperature, client
                )

            except Exception as exc:
                last_exc = exc

                if _is_quota_error(exc):
                    # This model's daily/minute quota is done — try the next model.
                    print(f"[Gemini] '{model_name}' quota exhausted, "
                          f"falling back to next model in chain...")
                    break  # break retry loop, move to next model

                if _is_overload_error(exc) and attempt < _MAX_RETRIES - 1:
                    delay = _RETRY_DELAYS[attempt]
                    print(f"[Gemini] '{model_name}' overloaded (503), retrying in {delay}s... "
                          f"(attempt {attempt + 1}/{_MAX_RETRIES})")
                    time.sleep(delay)
                    continue

                # Not a quota error, not an overload error (or retries exhausted on this model).
                raise

    # Every model in the chain has been tried and exhausted.
    raise last_exc


def summarize_article(title: str, content: str) -> dict:
    """
    Summarise a news article with Gemini AI.

    Returns a dict with keys: summary, detailed_summary, sentiment, category.
    Falls back to safe defaults if AI is unavailable or fails.
    Raises QuotaExhaustedError if the failure is specifically a quota/rate-limit issue,
    so the caller can stop retrying for the rest of the fetch cycle.
    """
    fallback = {
        "summary": "",
        "detailed_summary": "",
        "sentiment": "Neutral",
        "category": _guess_category(title),
    }

    client = _get_client()
    if client is None:
        return fallback

    body = (content or "").strip()
    if len(body) > 4000:
        body = body[:4000] + "…"

    user_text = f"Title: {title}\n\nSource description:\n{body}"

    try:
        raw = _call_gemini(user_text, _SYSTEM_PROMPT, max_output_tokens=1536, temperature=0.4)

        result = _parse_json_response(raw)
        validated = _validate_result(result, fallback)

        if not validated["summary"]:
            print(f"[Gemini] WARNING: empty summary returned for '{title[:60]}'. "
                  f"Raw response (first 300 chars): {raw[:300]!r}")

        return validated

    except Exception as exc:
        if _is_quota_error(exc):
            logger.error("[Gemini] Quota/rate-limit hit: %s", exc)
            print(f"[Gemini] Quota/rate-limit error: {exc}")
            raise QuotaExhaustedError(str(exc)) from exc

        logger.error("[Gemini] summarize_article failed for '%s': %s", title[:60], exc)
        print(f"[Gemini] summarize_article FAILED for '{title[:60]}': {type(exc).__name__}: {exc}")
        return fallback


def generate_digest(articles: list[dict]) -> str:
    client = _get_client()
    if client is None or not articles:
        return ""

    bullet_list = "\n".join(
        f"- [{a.get('category','News')}] {a.get('title','')} — {a.get('summary','')}"
        for a in articles[:10]
    )

    prompt = (
        "You are a witty, concise news editor. Given today's top stories below, "
        "write a 4-5 sentence daily digest paragraph that a reader would want to "
        "open in their email. Be informative, engaging, never sensationalist.\n\n"
        f"Stories:\n{bullet_list}\n\nWrite the digest paragraph:"
    )

    try:
        return _call_gemini(prompt, "", max_output_tokens=300, temperature=0.7)
    except Exception as exc:
        logger.error("[Gemini] generate_digest failed: %s", exc)
        print(f"[Gemini] generate_digest FAILED: {exc}")

    return ""


def chat_with_news(question: str, context_articles: list[dict]) -> str:
    client = _get_client()
    if client is None:
        return "AI features are currently unavailable."

    context = "\n\n".join(
        f"[{a.get('category','')}] {a.get('title','')}: {a.get('summary','')}"
        for a in context_articles[:15]
    )

    system = (
        "You are a helpful news assistant. Answer the user's question based only on "
        "the news articles provided. If the answer isn't in the articles, say so honestly. "
        "Be concise (2-4 sentences)."
    )

    user_text = f"Today's articles:\n{context}\n\nQuestion: {question}"

    try:
        return _call_gemini(user_text, system, max_output_tokens=300, temperature=0.4)
    except Exception as exc:
        logger.error("[Gemini] chat_with_news failed: %s", exc)
        print(f"[Gemini] chat_with_news FAILED: {exc}")

    return "Sorry, I couldn't process that question right now."


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    logger.warning(
        "[Gemini] Full JSON parse failed, attempting field-level recovery. Raw (first 400 chars): %s",
        cleaned[:400],
    )
    print(f"[Gemini] JSON parse failed, salvaging fields. Raw (first 400 chars): {cleaned[:400]!r}")
    return _extract_fields_regex(cleaned)


def _extract_fields_regex(text: str) -> dict:
    """Best-effort salvage of individual fields from a broken/truncated JSON blob."""
    result = {}
    for field in ("summary", "detailed_summary", "sentiment", "category"):
        m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if m:
            result[field] = m.group(1).replace('\\n', '\n').replace('\\"', '"')
    if result:
        logger.warning("[Gemini] Recovered fields via regex: %s", list(result.keys()))
    return result


def _validate_result(result: dict, fallback: dict) -> dict:
    valid_sentiments = {"Positive", "Negative", "Neutral", "Mixed"}

    summary           = str(result.get("summary", fallback["summary"])).strip()
    detailed_summary  = str(result.get("detailed_summary", fallback["detailed_summary"])).strip()
    sentiment          = result.get("sentiment", fallback["sentiment"])
    category           = result.get("category", fallback["category"])

    if sentiment not in valid_sentiments:
        sentiment = "Neutral"
    if category not in CATEGORIES:
        category = fallback["category"]

    return {
        "summary":          summary,
        "detailed_summary": detailed_summary,
        "sentiment":        sentiment,
        "category":         category,
    }


def _guess_category(title: str) -> str:
    title_lower = title.lower()
    rules = [
        (["tech", "ai", "software", "app", "cyber", "robot", "computer", "code", "data", "startup"], "Technology"),
        (["sport", "football", "cricket", "tennis", "nba", "nfl", "match", "game", "player", "league"], "Sports"),
        (["science", "research", "nasa", "space", "climate", "study", "discovery", "universe"], "Science"),
        (["business", "market", "stock", "economy", "trade", "finance", "gdp", "bank", "invest"], "Business"),
        (["health", "covid", "vaccine", "hospital", "disease", "cancer", "mental", "medical"], "Health"),
        (["movie", "music", "celebrity", "award", "film", "netflix", "oscar", "pop", "actor"], "Entertainment"),
    ]
    for keywords, cat in rules:
        if any(kw in title_lower for kw in keywords):
            return cat
    return "World"


def offline_fallback_summary(title: str) -> dict:
    """
    No-API fallback used when every model in the Gemini fallback chain has
    exhausted its daily quota. Produces a non-blank, reasonably presentable
    summary/detailed_summary from the title alone, so the UI never shows an
    empty card while waiting for the real AI quota to reset.

    This is intentionally simple (no external calls) — it exists purely so
    nothing is left blank under a deadline. Re-run the real backfill later
    (once quota resets) to replace these with genuine AI summaries.
    """
    clean_title = title.strip().rstrip('.')
    category = _guess_category(title)

    summary = f"{clean_title}. This story is developing — more details are being tracked as they emerge."

    detailed_summary = (
        f"{clean_title}.\n\n"
        f"This report is centered on the headline above. As with many fast-moving "
        f"news stories, full context and further developments may still be emerging "
        f"at the time of publication.\n\n"
        f"Check the original source for the complete and most up-to-date account of "
        f"this story."
    )

    return {
        "summary": summary,
        "detailed_summary": detailed_summary,
        "sentiment": "Neutral",
        "category": category,
    }