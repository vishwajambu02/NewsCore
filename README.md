<div align="center">

# 🧠 NewsCore

### AI-Summarized News. Real-Time Sentiment. Verified Publishers.

**A full-stack, AI-powered news aggregation platform that reads the internet so you don't have to.**

[![Live Demo](https://img.shields.io/badge/🔴_LIVE-newscore--tejh.onrender.com-0a0a0f?style=for-the-badge)](https://newscore-tejh.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Blueprints-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev)

[**🚀 View Live App**](https://newscore-tejh.onrender.com/) · [**🐛 Report Bug**](../../issues) · [**✨ Request Feature**](../../issues)

</div>

---

## 🌍 What is NewsCore?

NewsCore is a **live, production-deployed news intelligence platform** that ingests articles from trusted global publishers, runs them through **Google Gemini AI** for summarization and sentiment analysis, and serves them through a sleek, dark-themed reading experience — complete with a **live geopolitical hotspot map**, country-level filtering across **195 countries**, and a full authentication system built from the ground up.

This isn't a tutorial clone. It's a real system solving real engineering problems: scheduled scraping pipelines, AI rate-limit management, database persistence across ephemeral deployments, and secure multi-flow authentication — all running live on Render.

> 📌 **Built solo** by [@vishwajambu02](https://github.com/vishwajambu02) as a full-stack engineering deep-dive — from raw HTML scraping to AI pipelines to production auth systems.

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 🤖 AI-Powered Intelligence
- **Gemini-generated summaries** for every article, plus deep-dive `detailed_summary` expansions
- **Automated sentiment tagging** — Positive, Negative, Neutral, Mixed — per story
- **Scheduled ingestion** via APScheduler, continuously refreshing content

### 🗺️ Live World Monitor
- Interactive **geopolitical hotspot map** with Red / Yellow / Green alert tiers
- Real-time country-level conflict & development tracking

### 🌐 Global Coverage
- **195-country** grouped filtering dropdown
- Category-based browsing: World, Technology, Sports, Science, Business, Entertainment, Health

</td>
<td width="50%" valign="top">

### 🔐 Rock-Solid Auth System
- Hybrid **OTP signup + password login** flow via Brevo transactional email
- Full **password lifecycle**: change, forgot, and reset flows
- Hardened against legacy account edge cases (e.g. missing password hashes)

### 📊 Admin Command Center
- Live dashboard with site stats & login analytics (`LoginLog`, `SiteStat`)
- Full visibility into platform health and user activity

### 📱 Built for Every Screen
- Fully responsive, mobile-first layout
- Persistent Neon PostgreSQL storage — zero data loss across deploys

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NewsCore Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│   Sources ──▶ APScheduler ──▶ Gemini AI ──▶ Neon PostgreSQL  │
│  (Publishers)  (Ingestion)   (Summarize +    (Persistence)   │
│                                Sentiment)                     │
│                                    │                          │
│                                    ▼                          │
│              Flask (Blueprints) ──▶ Gunicorn ──▶ Render      │
│                    │                                          │
│         ┌──────────┼───────────┐                             │
│         ▼          ▼           ▼                             │
│    Auth System  Admin Panel  World Monitor                   │
│  (Brevo OTP +   (Dashboard,   (Iframe hotspot                │
│   Password)      Stats)        map)                          │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask (Blueprint architecture) |
| **Database** | Neon PostgreSQL |
| **AI Engine** | Google Gemini API |
| **Scheduling** | APScheduler |
| **Email / OTP** | Brevo (Sendinblue) |
| **Server** | Gunicorn |
| **Hosting** | Render (auto-deploy on `git push`) |
| **Frontend** | Server-rendered Jinja2 + responsive CSS |

---

## 🚀 Live Demo

<div align="center">

### 👉 [newscore-tejh.onrender.com](https://newscore-tejh.onrender.com/) 👈

*Real-time AI-summarized headlines, updated continuously.*

</div>

---

## ⚙️ Getting Started

```bash
# Clone the repository
git clone https://github.com/vishwajambu02/NewsCore.git
cd NewsCore

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (see below)
cp .env.example .env

# Run locally
flask run
```

### 🔑 Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API access |
| `BREVO_API_KEY` | Transactional email for OTP flows |
| `SECRET_KEY` | Flask session signing |

> ⚠️ Without `DATABASE_URL` set, the app will silently fall back to local SQLite — always verify your `.env` is loaded in production.

---

## 📸 Preview

> *World hotspot map, country filtering, AI sentiment tags, and the full reading experience — all live at the demo link above.*

---

## 🗺️ Roadmap

- [ ] **SvachhSpots** integration — civic-tech sanitation discovery platform (planned)
- [ ] Multi-language summaries (previously scoped, paused on Gemini free-tier limits)
- [ ] Personalized news feed based on reading history
- [ ] Push notifications for breaking Red Alert events

---

## 👤 Author

**Vishwa Jambu**
B.Tech CSE, Parul University · Full-Stack Developer

[![GitHub](https://img.shields.io/badge/GitHub-vishwajambu02-181717?style=flat-square&logo=github)](https://github.com/vishwajambu02)

---

<div align="center">

### ⭐ If NewsCore impressed you, consider starring the repo!

*Built with Flask, Gemini AI, and a lot of debugging at 2 AM.*

</div>
