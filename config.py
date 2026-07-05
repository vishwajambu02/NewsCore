import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    # Session settings — keeps users logged in for 30 days
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = False       # Set True when deployed on HTTPS (Render)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///newscore.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
    MAIL_FROM = os.environ.get('MAIL_FROM', 'vishwajambu66@gmail.com')

    # Gemini
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    # Admin
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 120))

    # RSS refresh interval in minutes
    RSS_REFRESH_INTERVAL = int(os.environ.get('RSS_REFRESH_INTERVAL', 30))

    # Mail
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    # RSS Sources — toggle active=True/False from admin
    RSS_SOURCES = [
        # International
        {"name": "BBC News",         "url": "http://feeds.bbci.co.uk/news/rss.xml",                          "category": "World",      "country": "international", "active": True},
        {"name": "BBC Technology",   "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",               "category": "Technology", "country": "international", "active": True},
        {"name": "Reuters",          "url": "https://feeds.reuters.com/reuters/topNews",                      "category": "World",      "country": "international", "active": True},
        {"name": "Al Jazeera",       "url": "https://www.aljazeera.com/xml/rss/all.xml",                      "category": "World",      "country": "international", "active": True},
        {"name": "TechCrunch",       "url": "https://techcrunch.com/feed/",                                   "category": "Technology", "country": "international", "active": True},
        {"name": "The Verge",        "url": "https://www.theverge.com/rss/index.xml",                         "category": "Technology", "country": "international", "active": True},
        {"name": "Wired",            "url": "https://www.wired.com/feed/rss",                                 "category": "Technology", "country": "international", "active": True},
        {"name": "Hacker News",      "url": "https://news.ycombinator.com/rss",                               "category": "Technology", "country": "international", "active": True},
        {"name": "NASA",             "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",                 "category": "Science",    "country": "international", "active": True},
        {"name": "ESPN",             "url": "https://www.espn.com/espn/rss/news",                             "category": "Sports",     "country": "international", "active": True},

        # India
        {"name": "NDTV Top Stories", "url": "https://feeds.feedburner.com/ndtvnews-top-stories",              "category": "World",      "country": "india", "active": True},
        {"name": "Times of India",   "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",     "category": "World",      "country": "india", "active": True},
        {"name": "The Hindu",        "url": "https://www.thehindu.com/feeder/default.rss",                    "category": "World",      "country": "india", "active": True},
        {"name": "India Today",      "url": "https://www.indiatoday.in/rss/home",                             "category": "World",      "country": "india", "active": True},

        # USA
        {"name": "CNN",              "url": "http://rss.cnn.com/rss/edition.rss",                             "category": "World",      "country": "usa", "active": True},
        {"name": "NYT World",        "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",         "category": "World",      "country": "usa", "active": True},
        {"name": "NPR News",         "url": "https://feeds.npr.org/1001/rss.xml",                             "category": "World",      "country": "usa", "active": True},

        # UK
        {"name": "The Guardian UK",  "url": "https://www.theguardian.com/uk/rss",                             "category": "World",      "country": "uk", "active": True},
        {"name": "Sky News",         "url": "https://feeds.skynews.com/feeds/rss/home.xml",                   "category": "World",      "country": "uk", "active": True},

        # Australia
        {"name": "ABC Australia",    "url": "https://www.abc.net.au/news/feed/51120/rss.xml",                 "category": "World",      "country": "australia", "active": True},
    ]

    CATEGORIES = ["World", "Technology", "Sports", "Science", "Business", "Entertainment", "Health"]

    CATEGORY_COLORS = {
        "World":         "#E63946",
        "Technology":    "#457B9D",
        "Sports":        "#2DC653",
        "Science":       "#7B2FBE",
        "Business":      "#F4A261",
        "Entertainment": "#E76F51",
        "Health":        "#06D6A0",
    }