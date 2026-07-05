from datetime import datetime
from extensions import db


class Article(db.Model):
    __tablename__ = 'articles'

    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(500), nullable=False)
    original_url  = db.Column(db.String(1000), unique=True, nullable=False)
    source_name   = db.Column(db.String(200))
    category      = db.Column(db.String(100), default='World')
    country       = db.Column(db.String(50), nullable=True, default='international')
    thumbnail_url = db.Column(db.String(1000))
    published_at  = db.Column(db.DateTime, default=datetime.utcnow)
    fetched_at    = db.Column(db.DateTime, default=datetime.utcnow)

    ai_summary       = db.Column(db.Text)
    detailed_summary = db.Column(db.Text)   # NEW: longer AI-written explainer for the article page
    sentiment         = db.Column(db.String(20), default='Neutral')
    is_verified       = db.Column(db.Boolean, default=False)
    view_count         = db.Column(db.Integer, default=0)
    admin_edited        = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':                self.id,
            'title':             self.title,
            'url':               self.original_url,
            'source':            self.source_name,
            'category':          self.category,
            'thumbnail':         self.thumbnail_url,
            'published_at':      self.published_at.isoformat() if self.published_at else None,
            'summary':           self.ai_summary,
            'detailed_summary':  self.detailed_summary,
            'sentiment':         self.sentiment,
            'is_verified':       self.is_verified,
            'views':             self.view_count,
        }

    def time_ago(self):
        now = datetime.utcnow()
        diff = now - (self.published_at or self.fetched_at)
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"

    def __repr__(self):
        return f'<Article {self.id}: {self.title[:60]}>'


class RSSSource(db.Model):
    __tablename__ = 'rss_sources'

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(200), nullable=False)
    url      = db.Column(db.String(1000), nullable=False, unique=True)
    category = db.Column(db.String(100), default='World')
    country  = db.Column(db.String(50), default='international')
    active   = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def time_ago(self):
        now = datetime.utcnow()
        diff = now - self.added_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"

    def __repr__(self):
        return f'<RSSSource {self.name}>'