# 🤖 Web Scraping AI Bot

An intelligent, production-ready web scraping system powered by **Google Gemini 1.5 Flash**, built with Python, Playwright, and Streamlit. Scrape any webpage — static or dynamic — and leverage AI to summarize content, extract structured data, analyze sentiment, and answer complex questions about it.

**Features:** Multi-page scraping • Automatic JavaScript detection • Real-time analytics • Sentiment analysis • Power BI integration • Horizontal Pod Autoscaling • CI/CD with GitHub Actions

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🌐 Smart Scraping** | Auto-detect static vs. dynamic pages; dynamically switch between `requests` and Playwright |
| **🤖 AI Summarization** | Multi-chunk summarization with Google Gemini 1.5 Flash; handles large documents efficiently |
| **📊 Data Extraction** | Extract structured JSON data; ask free-form questions about any webpage |
| **💾 Smart Caching** | File-based TTL cache; avoid redundant API calls and scrapes |
| **📈 Analytics Dashboard** | Real-time metrics; sentiment analysis; data visualization with Plotly |
| **📉 Power BI Integration** | Export data directly to Power BI dashboards |
| **🐳 Containerized** | Multi-stage Docker build; runs on Kubernetes with auto-scaling |
| **☸️ Production-Ready** | AWS EKS deployment; Horizontal Pod Autoscaler; 99.9% uptime configuration |
| **⚡ CI/CD Pipeline** | Automated tests, builds, and deployments via GitHub Actions |
| **🧪 Fully Tested** | pytest coverage for scraper and pipeline layers |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  User Interface Layer (app/)                  │
│  Streamlit Web UI: 6 Tabs                                    │
│  ├─ Summarize │ Extract │ Q&A │ Analytics │ Monitor │ Power BI│
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼───────────────────────────────────┐
│            Pipeline Orchestrator Layer (pipeline/)            │
│  detect → scrape → clean → chunk → AI → dedupe → cache → export
└──────┬──────────────────────────────────────┬────────────────┘
       │                                      │
┌──────▼─────────────────┐      ┌────────────▼─────────────────┐
│  Scraper Layer         │      │    AI Engine Layer            │
│  (scraper/)            │      │    (ai_engine/)               │
│                        │      │                               │
│ • base_scraper.py      │      │ • client.py                   │
│   (requests + retry)   │      │   (Gemini API wrapper)        │
│ • dynamic_scraper.py   │      │ • prompts.py                  │
│   (Playwright)         │      │   (system & user prompts)     │
│ • detector.py          │      │ • summarizer.py               │
│   (JS detection)       │      │   (multi-chunk summarization) │
│ • cleaner.py           │      │ • extractor.py                │
│   (HTML → text)        │      │   (structured extraction)     │
│ • chunker.py           │      │                               │
│   (token-safe split)   │      │                               │
└────────────────────────┘      └───────────────────────────────┘
                                   │
                 ┌─────────────────┴──────────────────┐
                 │                                    │
     ┌───────────▼──────────────┐     ┌──────────────▼────────────┐
     │  Analytics Layer         │     │  Monitor Layer             │
     │  (analytics/)            │     │  (monitor/)                │
     │                          │     │                            │
     │ • agent.py               │     │ • tracker.py               │
     │   (Analytics agent)      │     │   (Performance tracking)   │
     │ • dashboard.py           │     │                            │
     │   (Analytics dashboard)  │     │                            │
     │ • nlp.py                 │     │                            │
     │   (NLP analysis)         │     │                            │
     │ • sentiment.py           │     │                            │
     │   (Sentiment analysis)   │     │                            │
     │ • visualizer.py          │     │                            │
     │   (Data visualization)   │     │                            │
     │ • eda.py & reporter.py   │     │                            │
     │   (Exploratory & reports)│     │                            │
     └──────────────────────────┘     └────────────────────────────┘
```

---

## 📁 Project Structure

```
web-scraping-ai-bot/
├── scraper/                      # Web Scraping Layer
│   ├── base_scraper.py           # Static page scraper (requests + BeautifulSoup4)
│   ├── dynamic_scraper.py        # Dynamic page scraper (Playwright)
│   ├── detector.py               # Auto-detect JS-heavy pages
│   ├── cleaner.py                # HTML → clean text conversion
│   ├── chunker.py                # Token-safe text splitting
│   └── local_extractor.py        # Local data extraction
│
├── ai_engine/                    # AI & LLM Layer
│   ├── client.py                 # Gemini API wrapper
│   ├── prompts.py                # Prompt templates
│   ├── summarizer.py             # Multi-chunk summarization
│   └── extractor.py              # Structured extraction
│
├── pipeline/                     # Orchestration Layer
│   ├── pipeline.py               # Master orchestrator
│   ├── cache.py                  # TTL-based caching
│   ├── deduplicator.py           # Duplicate removal
│   └── exporter.py               # CSV & JSON export
│
├── analytics/                    # Analytics Layer
│   ├── agent.py                  # Analytics agent
│   ├── dashboard.py              # Analytics dashboard
│   ├── eda.py                    # Exploratory analysis
│   ├── nlp.py                    # NLP analysis
│   ├── reporter.py               # Report generation
│   ├── sentiment.py              # Sentiment analysis
│   └── visualizer.py             # Data visualization
│
├── monitor/                      # Monitoring Layer
│   └── tracker.py                # Performance tracking
│
├── app/                          # Frontend UI
│   ├── main.py                   # Streamlit app (6 tabs)
│   └── powerbi_dashboard.py      # Power BI integration
│
├── k8s/                          # Kubernetes Manifests
│   ├── deployment.yaml           # K8s Deployment
│   ├── service.yaml              # LoadBalancer Service
│   ├── hpa.yaml                  # Autoscaler config
│   └── secret.yaml               # Secrets management
│
├── tests/                        # Unit Tests
│   ├── test_scraper.py           # Scraper tests
│   └── test_pipeline.py          # Pipeline tests
│
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local dev setup
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Web UI, real-time updates |
| **Scraping** | Requests, BeautifulSoup4, Playwright | Static & dynamic page scraping |
| **AI/LLM** | Google Gemini 1.5 Flash, google-genai | Content summarization, extraction, Q&A |
| **Data Processing** | pandas, NumPy, scipy | Data manipulation & analysis |
| **Analytics** | Plotly, TextBlob | Visualization, sentiment analysis |
| **Backend** | Python 3.11+ | Core logic |
| **Testing** | pytest, pytest-cov | Unit tests, coverage reports |
| **Containerization** | Docker, Docker Compose | Development & deployment |
| **Orchestration** | Kubernetes (AWS EKS) | Production scaling |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Cloud** | AWS (ECR, EKS, CloudWatch) | Production infrastructure |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Google Gemini API Key** → [Get one here](https://makersuite.google.com/app/apikey)
- **Git** for version control

### 2. Clone & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/web-scraping-ai-bot.git
cd web-scraping-ai-bot

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (cmd):
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (required for dynamic scraping)
playwright install chromium
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Add your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here_do_not_share
```

### 5. Run the Application

```bash
# Start Streamlit app
streamlit run app/main.py
```

The app will open at **http://localhost:8501** in your browser.

---

## 💻 Usage Guide

### Tab 1: 📋 Summarize
Paste a URL or enter HTML content to get an AI-powered summary.

### Tab 2: 🔍 Extract Data
Extract structured JSON data from any webpage.

### Tab 3: ❓ Ask a Question
Ask any question about a webpage's content.

### Tab 4: 📊 Analytics Dashboard
View real-time metrics and insights.

### Tab 5: 🔴 Live Monitor
Real-time performance tracking and debugging.

### Tab 6: 📈 Power BI Dashboard
Export and visualize data in Microsoft Power BI.

---

## 🐳 Docker

### Quick Start with Docker

```bash
# Build the Docker image
docker build -t scraper-bot:latest .

# Run with environment file
docker run -p 8501:8501 \
  --env-file .env \
  --name scraper-bot-container \
  scraper-bot:latest
```

### Docker Compose (Recommended for Development)

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down
```

---

## ☸️ Kubernetes Deployment on AWS EKS

### Prerequisites

- **AWS CLI** installed and configured
- **kubectl** installed and configured
- **eksctl** for cluster management
- **IAM permissions** for ECR, EKS, CloudWatch

### Step 1: Create AWS EKS Cluster

```bash
eksctl create cluster \
  --name scraper-bot-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### Step 2: Create AWS ECR Repository

```bash
aws ecr create-repository \
  --repository-name scraper-bot \
  --region us-east-1
```

### Step 3: Build and Push Docker Image

```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
ECR_REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/scraper-bot"

# Authenticate Docker to ECR
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ECR_REPO

# Build and push image
docker build -t scraper-bot:latest .
docker tag scraper-bot:latest $ECR_REPO:latest
docker push $ECR_REPO:latest
```

### Step 4: Create Kubernetes Secret

```bash
kubectl create namespace scraper-bot-prod

kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_actual_api_key_here" \
  -n scraper-bot-prod
```

### Step 5: Apply Kubernetes Manifests

Edit `k8s/deployment.yaml` with your ECR image URI, then:

```bash
kubectl apply -f k8s/deployment.yaml -n scraper-bot-prod
kubectl apply -f k8s/service.yaml -n scraper-bot-prod
kubectl apply -f k8s/hpa.yaml -n scraper-bot-prod
```

### Step 6: Get Public URL

```bash
kubectl get svc scraper-bot-service -n scraper-bot-prod

# Copy the EXTERNAL-IP and access at http://EXTERNAL-IP:8501
```

---

## 🔄 Horizontal Pod Autoscaling

The `k8s/hpa.yaml` automatically scales pods based on CPU utilization:

```yaml
minReplicas: 2
maxReplicas: 5
targetCPUUtilizationPercentage: 70
```

Monitor with:
```bash
kubectl get hpa scraper-bot-hpa -n scraper-bot-prod --watch
```

---

## ⚙️ CI/CD with GitHub Actions

The pipeline automatically:
1. Runs pytest tests on every push and PR
2. Builds Docker image on push to `main`
3. Pushes to AWS ECR
4. Deploys to AWS EKS

### Required GitHub Secrets

Go to **Settings → Secrets → Actions** and add:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g., us-east-1) |
| `AWS_ACCOUNT_ID` | 12-digit AWS account ID |
| `ECR_REPOSITORY` | ECR repo name |
| `EKS_CLUSTER_NAME` | EKS cluster name |
| `GEMINI_API_KEY` | Google Gemini API key |

---

## ☁️ AWS Services Architecture

| Service | Role | Cost |
|---------|------|------|
| **ECR** | Docker image storage | ~$0.10/GB/month |
| **EKS** | Kubernetes cluster | ~$0.10/hour |
| **EC2** | Worker nodes (t3.medium) | ~$0.03/hour per node |
| **ELB** | Load balancer | ~$16/month |
| **CloudWatch** | Logs & monitoring | ~$0.50/GB |

---

## 📚 Core Modules

### Scraper Module

```python
from scraper.detector import detect_page_type
from scraper.base_scraper import BasicScraper

# Detect page type
page_type = detect_page_type("https://example.com")

# Scrape static page
scraper = BasicScraper(timeout=10, retries=3)
html = scraper.scrape("https://example.com")
```

### AI Engine Module

```python
from ai_engine.client import GeminiClient
from ai_engine.summarizer import Summarizer

client = GeminiClient(api_key="your_key")
summarizer = Summarizer(client=client)
summary = summarizer.summarize(text, style="concise")
```

### Pipeline Module

```python
from pipeline.pipeline import ScrapingPipeline

pipeline = ScrapingPipeline(use_cache=True)
result = pipeline.run(
    url="https://example.com",
    task="summarize"
)
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
GEMINI_API_KEY=your_api_key_here
SCRAPER_TIMEOUT=10
SCRAPER_RETRIES=3
CACHE_TTL_SECONDS=3600
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
```

### Kubernetes Secrets

```bash
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_key" \
  -n scraper-bot-prod
```

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest --cov=scraper,ai_engine,pipeline --cov-report=html

# Run specific test file
pytest tests/test_scraper.py -v

# Run with parallel execution
pytest -n auto
```

Coverage target: **≥ 80%**

---

## 🐛 Troubleshooting

### Issue: "Playwright executable not found"
```bash
playwright install chromium
```

### Issue: "GEMINI_API_KEY not found"
```bash
cp .env.example .env
# Edit .env with your key
nano .env
```

### Issue: "Connection timeout" on Kubernetes
```bash
kubectl logs <pod-name> -n scraper-bot-prod
kubectl get pods -n scraper-bot-prod
kubectl describe pod <pod-name> -n scraper-bot-prod
```

### Issue: "Out of memory"
Edit `k8s/deployment.yaml`:
```yaml
resources:
  requests:
    memory: "1Gi"
  limits:
    memory: "2Gi"
```

---

## 📈 Performance Tips

1. Enable caching: `use_cache=True`
2. Batch multiple URLs for parallel processing
3. Adjust `max_tokens` for Gemini API limits
4. Monitor HPA with `kubectl top nodes`
5. Check CloudWatch logs for API duration metrics

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run tests: `pytest --cov`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

- Follow **PEP 8**
- Use **type hints** for functions
- Add **docstrings** to classes and functions
- Write **unit tests** for new features

---

## 📜 License

This project is licensed under the **MIT License** — see LICENSE file for details.

---

## 💬 Support & Community

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/web-scraping-ai-bot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/web-scraping-ai-bot/discussions)
- **Email:** your.email@example.com

---

## 🙏 Acknowledgments

- **Google Gemini** for providing the powerful LLM API
- **Streamlit** for the beautiful web UI framework
- **Playwright** for robust browser automation
- **BeautifulSoup4** for HTML parsing
- **AWS** for cloud infrastructure

---

**Made with ❤️ by [Your Name/Team]**
