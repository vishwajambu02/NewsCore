"""
backfill_summaries.py
One-time script: finds all existing articles with a blank ai_summary
(usually because Gemini failed silently before this fix) and regenerates
summary / detailed_summary / sentiment / category for them.

Tries real Gemini AI summaries first (with model fallback chain).
Once every model's daily quota is exhausted, automatically switches to an
offline (no-API) fallback summary for all remaining articles, so nothing
is left blank. Re-run this script again tomorrow (after quota resets) —
see the note at the bottom for how to redo the offline ones with real AI.

Run from project root:
    python backfill_summaries.py
"""

import time
from app import create_app
from extensions import db
from models.article import Article
from services.gemini_service import summarize_article, offline_fallback_summary, QuotaExhaustedError

app = create_app()

with app.app_context():
    blank_articles = Article.query.filter(
        (Article.ai_summary == None) | (Article.ai_summary == '')
    ).all()

    print(f"[Backfill] Found {len(blank_articles)} articles with blank summaries.")

    fixed = 0
    fixed_offline = 0
    gemini_exhausted = False

    for i, article in enumerate(blank_articles, 1):
        print(f"[Backfill] ({i}/{len(blank_articles)}) {article.title[:70]}")

        if gemini_exhausted:
            # All Gemini models are done for today — skip straight to offline
            # fallback so we don't waste time hitting a dead API.
            ai_data = offline_fallback_summary(article.title)
            fixed_offline += 1
        else:
            try:
                ai_data = summarize_article(article.title, article.title)
            except QuotaExhaustedError:
                print("[Backfill] All Gemini models exhausted for today. "
                      "Switching to offline fallback summaries for the rest of this run "
                      "(no more waiting — these can be upgraded to real AI summaries later).")
                gemini_exhausted = True
                ai_data = offline_fallback_summary(article.title)
                fixed_offline += 1
            except Exception as e:
                print(f"[Backfill] Skipped (error): {e}")
                continue

        if ai_data.get('summary'):
            article.ai_summary = ai_data.get('summary', '')
            article.detailed_summary = ai_data.get('detailed_summary', '')
            article.sentiment = ai_data.get('sentiment', article.sentiment)
            db.session.commit()
            fixed += 1
        else:
            print(f"[Backfill] Still empty after retry, skipping: {article.title[:70]}")

        # Only need the delay while we're still hitting the real API.
        if not gemini_exhausted:
            time.sleep(7)

    print(f"[Backfill] Done. Fixed {fixed}/{len(blank_articles)} articles "
          f"({fixed_offline} via offline fallback, {fixed - fixed_offline} via real AI).")
    if fixed_offline:
        print("[Backfill] NOTE: offline-fallback articles have simple placeholder summaries. "
              "Once Gemini quota resets, you can re-run a real backfill on just those by "
              "checking for the phrase 'This story is developing' in ai_summary.")