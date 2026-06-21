# 🤖 Web Intel

An autonomous web scraping platform powered by **Gemini 2.5 Flash** — scrape any website, summarize it, extract structured data, ask questions about it, run full data-science analytics, monitor it live, and visualize everything on a Power BI–style dashboard. **No coding required.**

Built by **Ujjwal Kaushik**.

---

## ✨ Features

| Tab | What It Does |
|---|---|
| 📝 **Summarize & Ask** | Scrape any page, get an AI summary, then ask unlimited follow-up questions — all reusing the same cached scrape (no re-fetching) |
| 📊 **Extract Data** | Pull structured JSON/CSV from any website — works with AI (Gemini) or 100% locally with zero API key |
| 🔬 **Analytics Agent** | Auto EDA, sentiment analysis, NLP keyword/topic extraction, charts, and AI-written insights & recommendations |
| 📡 **Live Monitor** | Tracks a URL snapshot-to-snapshot, shows what changed (🟢 up / 🔴 down), with custom alert rules |
| 📈 **Power BI Dashboard** | Fully automatic dark-themed dashboard — KPI cards, gauges, bar/donut/scatter/treemap/heatmap/waterfall/funnel charts, all auto-generated from whatever data you scraped |

---

## 🔒 Security & Privacy — Read This First

This app is designed so that **your Gemini API key can never be exposed to other people**, even when the app is deployed publicly.

### How your key is protected

| Layer | Protection |
|---|---|
| **In the app** | Your key lives only in `st.session_state` — Streamlit's **per-browser-tab** memory. It is never written to a global variable, never written to disk, and is wiped the moment you close the tab or click "Clear Key." |
| **Across visitors** | If you share your live app URL, every visitor gets their own **isolated session**. They must paste their own key in the sidebar — they will never see or use yours. |
| **In the Gemini client** | `get_client()` builds a **brand-new** client object on every single call — there is no shared/cached client that could leak one user's key into another user's request. |
| **In Docker** | `.dockerignore` blocks `.env` and `.env.*` from ever entering the build context. The built image contains **zero** copies of any API key, anywhere in any layer. |
| **In Git** | `.gitignore` blocks `.env` from being committed. Only `.env.example` (a safe placeholder template) is tracked. |

### What you should still do
- Never commit a real key to `.env.example` or anywhere in the repo.
- Never bake a key into `docker-compose.yml`'s `env_file` line for a *public* deployment (it's commented out by default for exactly this reason).
- For local/private single-user use, it's fine to keep a real key in your local `.env` — that file never leaves your machine.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Streamlit UI (app/main.py)               │
│   Summarize & Ask │ Extract │ Analytics │ Monitor │ Dash  │
└──────────────────────┬─────────────────────────────────────┘
                        │  (session-scoped API key only)
┌──────────────────────▼─────────────────────────────────────┐
│            Pipeline Orchestrator (pipeline/)               │
│  detect → fetch (memoized) → clean → AI/local → cache       │
└──────┬──────────────────────────────────────┬───────────────┘
       │                                      │
┌──────▼──────────┐                ┌──────────▼──────────┐
│  Scraper Layer  │                │    AI Engine Layer   │
│  (scraper/)     │                │    (ai_engine/)      │
│ requests        │                │ Gemini 2.5 Flash     │
│ Playwright      │                │ fresh client/request │
│ local_extractor │                │ prompts/summarizer   │
└─────────────────┘                └──────────────────────┘
       │
┌──────▼──────────────────┐   ┌─────────────────────────┐
│  Analytics (analytics/) │   │  Monitor (monitor/)     │
│  EDA · NLP · sentiment  │   │  Snapshot diff engine   │
│  Dark-theme charts      │   │  Alert rules            │
└──────────────────────────┘  └─────────────────────────┘
       │
┌──────▼──────────────────────┐
│  Power BI Dashboard          │
│  (app/powerbi_dashboard.py)  │
│  Auto chart selection         │
└───────────────────────────────┘
```

---

## 📁 Project Structure

```
web-scraping-ai-bot/
├── scraper/
│   ├── base_scraper.py      # requests + retry + UA rotation
│   ├── dynamic_scraper.py   # Playwright for JS-heavy pages
│   ├── local_extractor.py   # Zero-API table/infobox extraction
│   ├── cleaner.py           # HTML → clean text
│   ├── chunker.py           # Token-safe text splitting
│   └── detector.py          # Static vs dynamic detection
│
├── ai_engine/
│   ├── client.py            # Gemini wrapper — session-scoped, no global state
│   ├── prompts.py
│   ├── summarizer.py
│   └── extractor.py
│
├── pipeline/
│   ├── pipeline.py          # Orchestrator — memoized single-fetch per URL
│   ├── cache.py             # TTL file cache
│   ├── deduplicator.py      # Dedup + auto-clean (drops empty cols, fills N/A)
│   └── exporter.py          # CSV/JSON/Excel export
│
├── analytics/
│   ├── agent.py             # Autonomous analytics agent
│   ├── eda.py / nlp.py / sentiment.py
│   └── visualizer.py        # Dark-theme charts for the Analytics tab
│
├── monitor/
│   └── tracker.py           # Snapshot diff + alert engine
│
├── app/
│   ├── main.py               # Streamlit UI — 5 tabs, session-scoped key
│   └── powerbi_dashboard.py  # Fully automatic dark Power BI dashboard
│
├── tests/
├── k8s/                      # Kubernetes manifests
├── .github/workflows/        # CI/CD pipeline
├── Dockerfile                # Multi-stage, non-root, no secrets baked in
├── docker-compose.yml        # No env_file by default (public-safe)
├── .dockerignore             # Blocks .env from the build context
├── .gitignore                # Blocks .env from version control
├── .env.example
└── requirements.txt
```

---

## 🚀 Quick Start (Local)

### 1. Clone & install
```bash
git clone https://github.com/YOUR_USERNAME/web-scraping-ai-bot.git
cd web-scraping-ai-bot

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
playwright install chromium
```

### 2. Run
```bash
streamlit run app/main.py
```
Open **http://localhost:8501**, paste your Gemini API key in the sidebar (get a free one at [aistudio.google.com](https://aistudio.google.com/app/apikey)).

> Your key stays in that browser tab only — it is never saved anywhere.

---

## 🐳 Docker

### Build
```bash
docker build -t web-scraping-ai-bot:latest .
```

### Verify no key is baked in (optional sanity check)
```bash
docker run --rm web-scraping-ai-bot:latest ls -la
# .env should NOT appear — only .env.example
```

### Run
```bash
docker run -p 8501:8501 web-scraping-ai-bot:latest
```
Each visitor enters their own key in the sidebar — nothing is pre-loaded.

### Or with Docker Compose
```bash
docker-compose up --build
```

---

## ☸️ Kubernetes & CI/CD

Kubernetes manifests are in `k8s/` (Deployment, Service, HPA, Secret template). The GitHub Actions pipeline in `.github/workflows/deploy.yml` runs tests, builds the image, pushes to ECR, and deploys to EKS on every push to `main`. See inline comments in those files for the exact `kubectl`/AWS CLI commands.

---

## 🧪 Tests
```bash
pytest tests/ -v --cov=scraper --cov=pipeline --cov=ai_engine
```

---

## 🛡️ Ethical Use

- Respect each site's `robots.txt` and Terms of Service.
- The built-in polite delay and caching are there to minimize load on target servers.
- Don't scrape personal/private data without consent.

---

## 📜 License

This project is licensed under the **MIT License** — see LICENSE file for details.

---

## 💬 Support & Community

- **Issues:** [GitHub Issues](https://github.com/UjjwalKaushik0609/Web-Intel/issues)
- **Discussions:** [GitHub Discussions](https://github.com/UjjwalKaushik0609/Web-Intel/discussions)
- **Email:** ujjwalkaushik0609@gmail.com

---

## 🙏 Acknowledgments

- **Google Gemini** for providing the powerful LLM API
- **Streamlit** for the beautiful web UI framework
- **Playwright** for robust browser automation
- **BeautifulSoup4** for HTML parsing
- **AWS** for cloud infrastructure

---

**Made with ❤️ by [Ujjwal kaushik]