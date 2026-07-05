from flask import Blueprint, jsonify, request
from extensions import cache
from models.article import Article
from config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/articles')
@cache.cached(timeout=60, query_string=True)
def get_articles():
    """
    GET /api/articles?page=1&category=Technology&limit=12
    Used for infinite scroll.
    """
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 12, type=int)
    category = request.args.get('category', '')

    q = Article.query.order_by(Article.published_at.desc())
    if category and category in Config.CATEGORIES:
        q = q.filter_by(category=category)

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'articles':  [a.to_dict() for a in paginated.items],
        'page':      page,
        'has_next':  paginated.has_next,
        'total':     paginated.total,
    })


@api_bp.route('/articles/<int:article_id>')
def get_article(article_id):
    a = Article.query.get_or_404(article_id)
    return jsonify(a.to_dict())


@api_bp.route('/articles/bulk')
def bulk_articles():
    """
    GET /api/articles/bulk?ids=1,2,3,4
    Used to hydrate bookmarks from localStorage IDs.
    """
    ids_str = request.args.get('ids', '')
    if not ids_str:
        return jsonify({'articles': []})

    try:
        ids = [int(i) for i in ids_str.split(',') if i.strip().isdigit()]
    except ValueError:
        return jsonify({'error': 'Invalid ids'}), 400

    articles = Article.query.filter(Article.id.in_(ids)).all()
    return jsonify({'articles': [a.to_dict() for a in articles]})


@api_bp.route('/trending')
@cache.cached(timeout=300)
def trending():
    articles = (Article.query
                .order_by(Article.view_count.desc())
                .limit(10).all())
    return jsonify({'articles': [a.to_dict() for a in articles]})


@api_bp.route('/stats')
def stats():
    """Public stats for homepage live counters."""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)

    total    = Article.query.count()
    today    = Article.query.filter(Article.published_at >= cutoff).count()
    sources  = Article.query.with_entities(Article.source_name).distinct().count()
    cats     = {c: Article.query.filter_by(category=c).count() for c in Config.CATEGORIES}

    return jsonify({
        'total_articles': total,
        'articles_today': today,
        'sources':        sources,
        'by_category':    cats,
    })


@api_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Email digest subscription."""
    from extensions import db
    from models.user import EmailSubscriber
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    cats  = data.get('categories', ['World'])

    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400

    existing = EmailSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({'message': 'Already subscribed!'}), 200

    sub = EmailSubscriber(
        email      = email,
        categories = ','.join(cats) if isinstance(cats, list) else cats,
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({'message': 'Subscribed successfully!'}), 201