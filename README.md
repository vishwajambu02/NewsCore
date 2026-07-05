<div align="center">

# 📰 NewsCore

### AI-Powered News Aggregator

*Real-time news from around the world, summarized and understood by AI.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini%20AI-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[Live Demo](#) · [Report Bug](../../issues) · [Request Feature](../../issues)

</div>

---

## 📖 About

**NewsCore** is a full-stack news aggregation platform that pulls stories from dozens of RSS feeds around the world and runs each one through **Google Gemini AI** to generate concise summaries, detailed explainers, sentiment analysis, and automatic categorization — so you get the story, not just the headline.

Built solo as a deep-dive into full-stack development: real-time data pipelines, AI integration, authentication systems, and production deployment.

---

## ✨ Features

### 🤖 AI-Powered
- **Smart summaries** — 2–3 line AI summary + a detailed, original explainer for every article
- **Sentiment analysis** — Positive / Negative / Neutral / Mixed tagging per story
- **Auto-categorization** — World, Technology, Sports, Science, Business, Entertainment, Health

### 📡 Live News Pipeline
- Aggregates from **verified RSS sources** (BBC, Reuters, Al Jazeera, NASA, and more)
- Scheduled background fetching with duplicate detection
- Graceful fallback handling so the feed never breaks, even under API rate limits

### 🔐 Authentication & Users
- Email + OTP verification flow (via Brevo)
- Secure admin panel with environment-based credentials
- Contact form with reply-to email support

### 🗺️ Rich Reading Experience
- Interactive **world map** highlighting global stories
- Category-based filtering with per-category accent colors
- **Follow** categories with persistent preferences
- Bookmarking, share, and text-to-speech "listen" support
- Fully responsive with a native-feeling **PWA** experience (splash screen, offline-ready)

### 🛠️ Admin Tools
- Manage RSS sources, articles, and subscribers
- Manual article edit and verification controls

---

## 🧱 Tech Stack

| Layer          | Technology                                   |
|----------------|-----------------------------------------------|
| **Backend**    | Flask, SQLAlchemy                             |
| **Database**   | PostgreSQL ([Neon](https://neon.tech))        |
| **AI**         | Google Gemini API (`google-genai`)            |
| **Email**      | Brevo (Transactional Email API)               |
| **Frontend**   | Jinja2, HTML/CSS, vanilla JS                  |
| **Feeds**      | `feedparser`                                  |
| **Maps**       | Leaflet.js                                    |
| **Deployment** | Render                                        |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Neon](https://neon.tech) PostgreSQL database (or any Postgres instance)
- A [Google Gemini API key](https://ai.google.dev/)
- A [Brevo](https://www.brevo.com/) account for transactional email

### Installation

```bash
# Clone the repo
git clone https://github.com/vishwajambu02/NewsCore.git
cd NewsCore

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
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
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

### Run Locally

```bash
python app.py
```

Visit **http://127.0.0.1:5000** 🎉

### Backfilling AI Summaries

If you're seeding the database from existing articles without summaries:

```bash
python backfill_summaries.py
```

---

## 📂 Project Structure

```
NewsCore/
├── models/          # SQLAlchemy models (Article, RSSSource, ...)
├── routes/          # Flask blueprints / view functions
├── services/        # Gemini AI service, RSS fetcher, email service
├── templates/        # Jinja2 templates
├── static/          # CSS, JS, images
├── utils/           # Decorators and helpers
├── migrations/      # Database migration scripts
├── app.py           # Application entry point
├── config.py        # App configuration
├── extensions.py    # Flask extension instances
└── backfill_summaries.py
```

---

## 🌐 Deployment

NewsCore is designed to deploy easily on **[Render](https://render.com)**:

1. Push your repo to GitHub
2. Create a new **Web Service** on Render, connected to your repo
3. Add your environment variables in the Render dashboard
4. Set the start command:
   ```
   gunicorn app:app
   ```
5. Deploy 🚀

---

## 🗺️ Roadmap

- [ ] AI news chatbot ("Ask NewsCore")
- [ ] Daily AI-generated email digest for subscribers
- [ ] Personalized "For You" feed
- [ ] AI-based related article recommendations

---

## 👤 Author

**Vishwa Jambucha**
B.Tech CSE, Parul University

- GitHub: [@vishwajambu02](https://github.com/vishwajambu02)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

If you found this project interesting, consider giving it a ⭐!

</div>
