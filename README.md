<div align="center">

# 📰 NewsCore

### AI-Powered News Aggregator

*Real-time news from around the world, summarized and understood by AI.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini%20AI-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[Live Demo](https://newscore-tejh.onrender.com/) · [Report Bug](../../issues) · [Request Feature](../../issues)

</div>

---

## 📖 About

**NewsCore** is a full-stack news aggregation platform that pulls stories from RSS feeds around the world and runs each one through **Google Gemini AI** to generate concise summaries, detailed explainers, sentiment analysis, and automatic categorization — so you get the story, not just the headline.

Built solo as a deep-dive into full-stack development: real-time data pipelines, AI integration, passwordless authentication, and production deployment.

---

## ✨ Features

### 🤖 AI-Powered
- **Smart summaries** — a short `ai_summary` for cards/lists, plus a longer, multi-paragraph `detailed_summary` for the full article page
- **Sentiment analysis** — sentiment tagging per story
- **Auto-categorization** — World, Technology, Sports, Science, Business, Entertainment, Health

### 📡 Live News Pipeline
- Aggregates from **verified RSS sources** (BBC, Reuters, Al Jazeera, NASA, and more)
- Scheduled background fetching via **APScheduler**, with duplicate detection
- Graceful fallback handling so the feed never breaks, even under API rate limits

### 🔐 Passwordless Authentication
- **No passwords, anywhere** — fully OTP-based email login via Brevo
- **Sign in with Email** — instantly creates a bare user profile
- **Create Your Own Account** — collects name, phone, and email for a fuller profile
- Optional **Remember Me** for 30-day persistent sessions
- Contact form with reply-to email support

### 🗺️ Rich Reading Experience
- Interactive **world map** with geopolitical hotspot tracking across ~12 countries, tiered by severity
- Category-based filtering with per-category accent colors
- **Follow** categories with persistent preferences
- Bookmarking, share, and text-to-speech "listen" support
- Trending Now — live, view-count-based ranking of top stories
- Infinite scroll for continuous browsing
- Fully responsive, dark-themed UI with a coral (`#ff6b35`) accent

### 🛠️ Admin Tools
- Separate, secured admin session (independent from user login)
- Admin shortcut in navbar, visible only to the configured owner account
- User and subscriber management
- Dashboard analytics — site visits and login activity
- Manual RSS fetch trigger for on-demand content refresh

---

## 🧱 Tech Stack

| Layer          | Technology                                   |
|----------------|-----------------------------------------------|
| **Backend**    | Flask (Blueprint architecture), SQLAlchemy    |
| **Database**   | PostgreSQL ([Neon](https://neon.tech))        |
| **AI**         | Google Gemini API (`google-genai`)            |
| **Email / OTP**| Brevo (Transactional Email API)               |
| **Scheduling** | APScheduler                                   |
| **Frontend**   | Jinja2, HTML/CSS, vanilla JS                  |
| **Feeds**      | `feedparser`                                  |
| **Maps**       | Leaflet.js / worldmonitor.app embed           |
| **Deployment** | Render                                        |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Neon](https://neon.tech) PostgreSQL database (or any Postgres instance)
- A [Google Gemini API key](https://ai.google.dev/)
- A [Brevo](https://www.brevo.com/) account for transactional email (OTP delivery)

### Installation

```bash
# Clone the repo
git clone https://github.com/vishwajambu02/NewsCore.git
cd NewsCore

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows (PowerShell)
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

```env
DATABASE_URL=your_neon_postgres_connection_string
GEMINI_API_KEY=your_gemini_api_key
BREVO_API_KEY=your_brevo_api_key
SECRET_KEY=your_flask_secret_key
ADMIN_USERNAME=your_admin_email@example.com
```

> ⚠️ Without a `.env` file present, the app silently falls back to SQLite instead of connecting to Neon — always confirm this file exists before running or debugging locally.
> ⚠️ `ADMIN_USERNAME` must be a real email address — it's matched against the logged-in user's email to reveal the admin shortcut in the navbar.

### Run Locally

```bash
python Run.py
```

Visit **http://127.0.0.1:5000** 🎉

*(Tested in Microsoft Edge — some in-browser dev environments don't persist session cookies correctly.)*

### Backfilling AI Summaries

If you're seeding the database with older articles missing `detailed_summary`:

```bash
python backfill_summaries.py
```

---

## 📂 Project Structure

```
NewsCore/
├── models/          # SQLAlchemy models (Article, User, SiteStat, LoginLog, ...)
├── routes/          # Flask blueprints / view functions (auth, admin, articles)
├── services/        # Gemini AI service, RSS fetcher, email/OTP service
├── templates/       # Jinja2 templates
├── static/
│   ├── css/
│   ├── js/          # main.js — infinite scroll, UI interactions
│   └── images/
├── utils/           # Decorators and helpers
├── migrations/      # Database migration scripts
├── Run.py           # Application entry point
├── config.py        # App configuration
├── extensions.py    # Flask extension instances
└── backfill_summaries.py
```

> Adjust this tree to match your actual repository layout before publishing.

---

## 🌐 Deployment

NewsCore is designed to deploy easily on **[Render](https://render.com)**:

1. Push your repo to GitHub
2. Create a new **Web Service** on Render, connected to your repo
3. Add your environment variables in the Render dashboard
4. Make sure `psycopg2-binary` is listed in `requirements.txt` so the Neon PostgreSQL connection works in production
5. If using Brevo, authorize Render's outbound IPs in Brevo's security settings
6. Set the start command, e.g.:
   ```
   gunicorn Run:app
   ```
7. Deploy 🚀

---

## 🐛 Common Issues

| Symptom | Cause |
|---|---|
| App silently uses SQLite instead of Postgres | Missing `.env` file |
| All AI summaries are empty | `GEMINI_API_KEY` not loading, or Gemini quota/billing issue |
| `psycopg2` import errors on deploy | Missing `psycopg2-binary` in `requirements.txt` |
| OTP emails not sending | Brevo IP authorization needs updating in security settings |
| Session doesn't persist locally | Testing in an environment that doesn't retain cookies — use a real browser like Edge |

---

## 🗺️ Roadmap

- [ ] AI news chatbot ("Ask NewsCore")
- [ ] Daily AI-generated email digest for subscribers
- [ ] Personalized "For You" feed
- [ ] AI-based related article recommendations
- [ ] Backfill remaining `detailed_summary` fields for older articles

---

## 👤 Author

**Vishwa Jambu**
B.Tech CSE, Parul University

- GitHub: [@vishwajambu02](https://github.com/vishwajambu02)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

If you found this project interesting, consider giving it a ⭐!

</div>
