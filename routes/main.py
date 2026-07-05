from flask import Blueprint, render_template, request, jsonify, abort, current_app, url_for, flash, redirect
from extensions import db, cache
from models.article import Article
from config import Config
from sqlalchemy import or_, func
from utils.decorators import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    from datetime import datetime, timedelta

    country = request.args.get('country', '').strip()
    cutoff = datetime.utcnow() - timedelta(hours=24)

    base_q = Article.query
    if country:
        base_q = base_q.filter(Article.country == country)

    hero = (base_q
            .filter(Article.published_at >= cutoff)
            .order_by(Article.view_count.desc())
            .first())

    if not hero:
        hero = base_q.order_by(Article.published_at.desc()).first()

    trending = (base_q
                .order_by(Article.view_count.desc())
                .limit(5).all())

    articles_q = base_q.order_by(Article.published_at.desc())
    if hero:
        articles_q = articles_q.filter(Article.id != hero.id)
    articles = articles_q.limit(24).all()

    countries_raw = (db.session.query(Article.country, func.count(Article.id))
                     .group_by(Article.country)
                     .having(func.count(Article.id) > 0)
                     .all())
    country_list = sorted([c[0] for c in countries_raw if c[0] and c[0] != 'international'])

    # Separate, unfiltered pool for the homepage hotspot map's headline
    # matching — deliberately NOT scoped by country/limit(24) like `articles`
    # above, so the map has a wide enough set to actually find matches.
    hotspot_pool = (Article.query
                    .order_by(Article.published_at.desc())
                    .limit(150).all())

    return render_template('index.html',
                           hero=hero,
                           articles=articles,
                           trending=trending,
                           categories=Config.CATEGORIES,
                           category_colors=Config.CATEGORY_COLORS,
                           active_category='All',
                           selected_country=country,
                           country_list=country_list,
                           hotspot_pool=hotspot_pool)


@main_bp.route('/category/<cat>')
def category(cat):
    if cat not in Config.CATEGORIES:
        abort(404)

    page     = request.args.get('page', 1, type=int)
    articles = (Article.query
                .filter_by(category=cat)
                .order_by(Article.published_at.desc())
                .paginate(page=page, per_page=20, error_out=False))

    trending = (Article.query
                .filter_by(category=cat)
                .order_by(Article.view_count.desc())
                .limit(5).all())

    return render_template('category.html',
                           articles=articles,
                           trending=trending,
                           category=cat,
                           categories=Config.CATEGORIES,
                           category_colors=Config.CATEGORY_COLORS,
                           active_category=cat)


@main_bp.route('/article/<int:article_id>')
@login_required
def article(article_id):
    a = Article.query.get_or_404(article_id)
    a.view_count += 1
    db.session.commit()

    related = (Article.query
               .filter(Article.category == a.category, Article.id != a.id)
               .order_by(Article.published_at.desc())
               .limit(4).all())

    country = request.args.get('country', '').strip()
    back_url = url_for('main.index', country=country) if country else url_for('main.index')

    return render_template('article.html',
                           article=a,
                           related=related,
                           categories=Config.CATEGORIES,
                           category_colors=Config.CATEGORY_COLORS,
                           selected_country=country,
                           back_url=back_url)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    articles = []
    if q:
        articles = (Article.query
                    .filter(or_(
                        Article.title.ilike(f'%{q}%'),
                        Article.ai_summary.ilike(f'%{q}%'),
                        Article.source_name.ilike(f'%{q}%'),
                    ))
                    .order_by(Article.published_at.desc())
                    .limit(30).all())

    return render_template('search.html',
                           articles=articles,
                           query=q,
                           categories=Config.CATEGORIES,
                           category_colors=Config.CATEGORY_COLORS)


@main_bp.route('/bookmarks')
def bookmarks():
    return render_template('bookmarks.html',
                           categories=Config.CATEGORIES,
                           category_colors=Config.CATEGORY_COLORS)


@main_bp.route('/about')
def about():
    return render_template('about.html',
                           categories=Config.CATEGORIES)


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html',
                           categories=Config.CATEGORIES)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        from services.email_service import send_contact_message

        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or '@' not in email or not message:
            flash('Please fill in all fields with a valid email.', 'error')
            return redirect(url_for('main.contact'))

        sent = send_contact_message(name, email, message)
        if not sent:
            flash('Could not send your message. Please try again shortly.', 'error')
            return redirect(url_for('main.contact'))

        flash('Message sent — thanks for reaching out!', 'success')
        return redirect(url_for('main.index'))

    return render_template('contact.html',
                           categories=Config.CATEGORIES)


_COUNTRY_META = {
    'international': {'name': 'International', 'flag': '🌐'},
    'india':         {'name': 'India',         'flag': '🇮🇳'},
    'usa':           {'name': 'USA',           'flag': '🇺🇸'},
    'uk':            {'name': 'UK',            'flag': '🇬🇧'},
    'australia':     {'name': 'Australia',     'flag': '🇦🇺'},
}

def _country_meta(code):
    return _COUNTRY_META.get(code, {'name': code.title(), 'flag': '🏳️'})


@main_bp.route('/worldmap')
def worldmap():
    countries_raw = (db.session.query(Article.country, func.count(Article.id))
                     .group_by(Article.country)
                     .having(func.count(Article.id) > 0)
                     .order_by(func.count(Article.id).desc())
                     .all())

    country_data = [
        {'code': c[0], 'count': c[1], **_country_meta(c[0])}
        for c in countries_raw if c[0]
    ]

    return render_template('worldmap.html',
                           categories=Config.CATEGORIES,
                           country_data=country_data)


@main_bp.route('/api/country-news/<country>')
def api_country_news(country):
    articles = (Article.query
                .filter_by(country=country)
                .order_by(Article.published_at.desc())
                .limit(15).all())

    return jsonify([{
        'id': a.id,
        'title': a.title,
        'source': a.source_name,
        'thumbnail': a.thumbnail_url,
        'time_ago': a.time_ago(),
        'url': url_for('main.article', article_id=a.id, country=country),
    } for a in articles])


@main_bp.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404