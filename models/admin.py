from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from functools import wraps
from extensions import db
from models.article import Article, RSSSource
from models.user import AdminLog, EmailSubscriber, LoginLog, SiteStat, User
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


def log_action(action, detail=''):
    log = AdminLog(action=action, detail=detail)
    db.session.add(log)
    db.session.commit()


# ── Login ────────────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)

    total_articles = Article.query.count()
    articles_today = Article.query.filter(Article.published_at >= cutoff).count()
    total_sources  = RSSSource.query.count()
    active_sources = RSSSource.query.filter_by(active=True).count()
    subscribers    = EmailSubscriber.query.count()
    total_visits   = SiteStat.get_total()
    total_users    = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()

    # Category breakdown for chart
    cat_data = []
    for cat in Config.CATEGORIES:
        count = Article.query.filter_by(category=cat).count()
        cat_data.append({'category': cat, 'count': count, 'color': Config.CATEGORY_COLORS.get(cat, '#888')})

    # Sentiment breakdown
    sent_data = {}
    for s in ['Positive', 'Neutral', 'Negative']:
        sent_data[s] = Article.query.filter_by(sentiment=s).count()

    # Recent logs
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(10).all()

    # Recent login activity — who signed in/up, with which method, success or not
    login_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(20).all()

    return render_template('admin/dashboard.html',
                           total_articles=total_articles,
                           articles_today=articles_today,
                           total_sources=total_sources,
                           active_sources=active_sources,
                           subscribers=subscribers,
                           total_visits=total_visits,
                           total_users=total_users,
                           verified_users=verified_users,
                           cat_data=cat_data,
                           sent_data=sent_data,
                           logs=logs,
                           login_logs=login_logs)


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()

    query = User.query
    if q:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{q}%'),
                User.name.ilike(f'%{q}%'),
                User.phone.ilike(f'%{q}%'),
            )
        )

    users_page = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()

    return render_template('admin/users.html',
                           users=users_page,
                           query=q,
                           total_users=total_users,
                           verified_users=verified_users)


# ── Subscribers ────────────────────────────────────────────────────────────────

@admin_bp.route('/subscribers')
@admin_required
def subscribers():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()

    query = EmailSubscriber.query
    if q:
        query = query.filter(EmailSubscriber.email.ilike(f'%{q}%'))

    subs_page = query.order_by(EmailSubscriber.subscribed_at.desc()).paginate(page=page, per_page=25, error_out=False)
    total_subs = EmailSubscriber.query.count()
    active_subs = EmailSubscriber.query.filter_by(active=True).count()

    return render_template('admin/subscribers.html',
                           subscribers=subs_page,
                           query=q,
                           total_subs=total_subs,
                           active_subs=active_subs)


@admin_bp.route('/subscribers/<int:sub_id>/toggle', methods=['POST'])
@admin_required
def toggle_subscriber(sub_id):
    s = EmailSubscriber.query.get_or_404(sub_id)
    s.active = not s.active
    db.session.commit()
    state = 'activated' if s.active else 'deactivated'
    log_action('toggle_subscriber', f'{state}: {s.email}')
    return jsonify({'active': s.active, 'message': f'{s.email} {state}.'})


@admin_bp.route('/subscribers/<int:sub_id>/delete', methods=['POST'])
@admin_required
def delete_subscriber(sub_id):
    s = EmailSubscriber.query.get_or_404(sub_id)
    email = s.email
    db.session.delete(s)
    db.session.commit()
    log_action('delete_subscriber', f'Deleted: {email}')
    flash(f'Removed subscriber "{email}".', 'success')
    return redirect(url_for('admin.subscribers'))


# ── Articles ──────────────────────────────────────────────────────────────────

@admin_bp.route('/articles')
@admin_required
def articles():
    page     = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    q        = request.args.get('q', '')

    query = Article.query
    if category:
        query = query.filter_by(category=category)
    if q:
        query = query.filter(Article.title.ilike(f'%{q}%'))

    articles = query.order_by(Article.published_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('admin/articles.html',
                           articles=articles,
                           categories=Config.CATEGORIES,
                           active_category=category,
                           query=q)


@admin_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    a = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        a.title      = request.form.get('title', a.title)
        a.ai_summary = request.form.get('summary', a.ai_summary)
        a.category   = request.form.get('category', a.category)
        a.sentiment  = request.form.get('sentiment', a.sentiment)
        a.admin_edited = True
        db.session.commit()
        log_action('edit_article', f'Edited article #{article_id}: {a.title[:60]}')
        flash('Article updated.', 'success')
        return redirect(url_for('admin.articles'))
    return render_template('admin/edit_article.html',
                           article=a,
                           categories=Config.CATEGORIES)


@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@admin_required
def delete_article(article_id):
    a = Article.query.get_or_404(article_id)
    title = a.title
    db.session.delete(a)
    db.session.commit()
    log_action('delete_article', f'Deleted article #{article_id}: {title[:60]}')
    flash('Article deleted.', 'success')
    return redirect(url_for('admin.articles'))


# ── Sources ───────────────────────────────────────────────────────────────────

@admin_bp.route('/sources')
@admin_required
def sources():
    sources = RSSSource.query.order_by(RSSSource.name).all()
    return render_template('admin/sources.html', sources=sources)


@admin_bp.route('/sources/<int:source_id>/toggle', methods=['POST'])
@admin_required
def toggle_source(source_id):
    s = RSSSource.query.get_or_404(source_id)
    s.active = not s.active
    db.session.commit()
    state = 'enabled' if s.active else 'disabled'
    log_action('toggle_source', f'{state} source: {s.name}')
    return jsonify({'active': s.active, 'message': f'{s.name} {state}.'})


@admin_bp.route('/sources/add', methods=['POST'])
@admin_required
def add_source():
    name     = request.form.get('name', '').strip()
    url      = request.form.get('url', '').strip()
    category = request.form.get('category', 'World')

    if not name or not url:
        flash('Name and URL are required.', 'error')
        return redirect(url_for('admin.sources'))

    if RSSSource.query.filter_by(url=url).first():
        flash('Source URL already exists.', 'error')
        return redirect(url_for('admin.sources'))

    src = RSSSource(name=name, url=url, category=category)
    db.session.add(src)
    db.session.commit()
    log_action('add_source', f'Added source: {name}')
    flash(f'Source "{name}" added.', 'success')
    return redirect(url_for('admin.sources'))


# ── Manual Fetch ──────────────────────────────────────────────────────────────

@admin_bp.route('/fetch-now', methods=['POST'])
@admin_required
def fetch_now():
    from services.rss_fetcher import fetch_all_feeds
    from flask import current_app
    import threading
    threading.Thread(target=fetch_all_feeds, args=(current_app._get_current_object(),), daemon=True).start()
    log_action('manual_fetch', 'Admin triggered manual RSS fetch.')
    flash('RSS fetch started in background.', 'success')
    return redirect(url_for('admin.dashboard'))