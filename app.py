import os
import sys
from models.user import User
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, session
from extensions import db, cache
from config import Config
from models.article import Article, RSSSource


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Fix Neon PostgreSQL URL (postgres:// → postgresql://)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    # Init extensions
    db.init_app(app)
    cache.init_app(app)

    # Register blueprints
    from routes.main  import main_bp
    from routes.api   import api_bp
    from routes.admin import admin_bp
    from routes.auth  import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # Create tables + seed sources on first run
    with app.app_context():
        db.create_all()
        from services.rss_fetcher import seed_sources_from_config
        seed_sources_from_config(app, Config.RSS_SOURCES)

        # Trigger initial fetch if DB is empty
        if Article.query.count() == 0:
            print("[App] No articles found — triggering initial RSS fetch...")
            import threading
            from services.rss_fetcher import fetch_all_feeds
            threading.Thread(target=fetch_all_feeds, args=(app,), daemon=True).start()

    # Start background scheduler (not in debug reloader child process)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from services.scheduler import init_scheduler
        from services.rss_fetcher import fetch_all_feeds
        init_scheduler(app, fetch_all_feeds, Config.RSS_REFRESH_INTERVAL)

    # ── Site visit counter ──────────────────────────────────────────
    # Counts every real page view (skips static assets and admin pages,
    # so your own dashboard visits don't inflate the public visit count).

    @app.before_request
    def _count_visit():
        path = request.path
        if path.startswith('/static') or path.startswith('/admin'):
            return
        if request.method != 'GET':
            return
        from models.user import SiteStat
        try:
            SiteStat.increment()
        except Exception as e:
            # Never let visit counting break the actual page request
            print(f"[SiteStat] Failed to record visit: {e}")
            db.session.rollback()

    # ── Owner admin-link flag ────────────────────────────────────────
    # Exposes `is_site_admin` to every template. True only when the
    # logged-in site user's email matches ADMIN_USERNAME — shows a
    # shortcut icon to the admin dashboard in the navbar.

    @app.context_processor
    def inject_admin_flag():
        is_admin = False
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            print(f"[DEBUG] user_id={user_id} user_email={user.email if user else None} ADMIN_USERNAME={Config.ADMIN_USERNAME!r}")
            if user and user.email and user.email.lower() == Config.ADMIN_USERNAME.lower():
                is_admin = True
        else:
            print("[DEBUG] No user_id in session at all")
        return dict(is_site_admin=is_admin)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)