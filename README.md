🤖 Web Scraping AI Bot
An intelligent, production-ready web scraping system powered by Google Gemini 1.5 Flash, built with Python, Playwright, and Streamlit. Scrape any webpage — static or dynamic — and leverage AI to summarize content, extract structured data, analyze sentiment, and answer complex questions about it.

Features: Multi-page scraping • Automatic JavaScript detection • Real-time analytics • Sentiment analysis • Power BI integration • Horizontal Pod Autoscaling • CI/CD with GitHub Actions

✨ Key Features
Feature	Description
🌐 Smart Scraping	Auto-detect static vs. dynamic pages; dynamically switch between requests and Playwright
🤖 AI Summarization	Multi-chunk summarization with Google Gemini 1.5 Flash; handles large documents efficiently
📊 Data Extraction	Extract structured JSON data; ask free-form questions about any webpage
💾 Smart Caching	File-based TTL cache; avoid redundant API calls and scrapes
📈 Analytics Dashboard	Real-time metrics; sentiment analysis; data visualization with Plotly
📉 Power BI Integration	Export data directly to Power BI dashboards
🐳 Containerized	Multi-stage Docker build; runs on Kubernetes with auto-scaling
☸️ Production-Ready	AWS EKS deployment; Horizontal Pod Autoscaler; 99.9% uptime configuration
⚡ CI/CD Pipeline	Automated tests, builds, and deployments via GitHub Actions
🧪 Fully Tested	pytest coverage for scraper and pipeline layers
🏗️ Architecture Overview
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
          ▲                                  ▲
          │                                  │
          └──────────────┬───────────────────┘
                         │
          ┌──────────────▼───────────────────┐
          │  Analytics & Monitoring           │
          │  (analytics/ & monitor/)          │
          │                                   │
          │ • sentiment.py (TextBlob)        │
          │ • visualizer.py (Plotly)        │
          │ • eda.py (EDA on results)       │
          │ • tracker.py (metrics tracking)  │
          │ • reporter.py (report gen)       │
          └───────────────────────────────────┘
📁 Project Structure
web-scraping-ai-bot/
│
├── 🔧 Core Modules
│   │
│   ├── scraper/                      # Web Scraping Layer
│   │   ├── __init__.py
│   │   ├── base_scraper.py           # Static page scraper (requests + BeautifulSoup4)
│   │   ├── dynamic_scraper.py        # Dynamic page scraper (Playwright)
│   │   ├── detector.py               # Auto-detect JS-heavy pages
│   │   ├── cleaner.py                # HTML → clean text conversion
│   │   ├── chunker.py                # Token-safe text splitting for Gemini API
│   │   └── local_extractor.py        # Local data extraction utilities
│   │
│   ├── ai_engine/                    # AI & LLM Layer
│   │   ├── __init__.py
│   │   ├── client.py                 # Gemini API wrapper (google-generativeai)
│   │   ├── prompts.py                # System & user prompt templates
│   │   ├── summarizer.py             # Multi-chunk summarization engine
│   │   ├── extractor.py              # Structured JSON extraction & Q&A
│   │   └── [config] (API timeouts, retry logic)
│   │
│   ├── pipeline/                     # Orchestration Layer
│   │   ├── __init__.py
│   │   ├── pipeline.py               # Master orchestrator
│   │   ├── cache.py                  # File-based TTL cache (avoid re-scraping)
│   │   ├── deduplicator.py           # Remove duplicate records
│   │   └── exporter.py               # CSV & JSON export
│   │
│   ├── analytics/                    # Analytics & Insights Layer
│   │   ├── __init__.py
│   │   ├── agent.py                  # Multi-tool analytics agent
│   │   ├── sentiment.py              # Sentiment analysis (TextBlob)
│   │   ├── visualizer.py             # Plotly-based visualizations
│   │   ├── eda.py                    # Exploratory Data Analysis
│   │   ├── nlp.py                    # NLP utilities (tokenization, etc.)
│   │   ├── reporter.py               # Automated report generation
│   │   └── dashboard.py              # Analytics dashboard backend
│   │
│   └── monitor/                      # Monitoring & Tracking
│       └── tracker.py                # Metrics, performance tracking
│
├── 🎨 User Interface
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # Streamlit app (6 tabs)
│       └── powerbi_dashboard.py      # Power BI integration
│
├── ⚙️ Deployment & Infrastructure
│   │
│   ├── k8s/                          # Kubernetes Manifests
│   │   ├── deployment.yaml           # K8s Deployment (2 replicas)
│   │   ├── service.yaml              # LoadBalancer Service
│   │   ├── hpa.yaml                  # Horizontal Pod Autoscaler (2–5 pods)
│   │   └── secret.yaml               # API key Secret management
│   │
│   ├── .github/
│   │   └── workflows/
│   │       └── deploy.yml            # GitHub Actions CI/CD pipeline
│   │
│   ├── Dockerfile                    # Multi-stage Docker build
│   └── docker-compose.yml            # Local dev: single-service setup
│
├── 🧪 Testing
│   └── tests/
│       ├── __init__.py
│       ├── test_scraper.py           # Scraper layer unit tests
│       └── test_pipeline.py          # Pipeline layer unit tests
│
├── 📝 Configuration & Docs
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   ├── .gitignore                     # Git ignore rules
│   └── README.md                      # This file
│
└── 📊 Generated Files
    └── .cache/                        # TTL cache (auto-generated)
🛠️ Technology Stack
Layer	Technology	Purpose
Frontend	Streamlit	Web UI, real-time updates
Scraping	Requests, BeautifulSoup4, Playwright	Static & dynamic page scraping
AI/LLM	Google Gemini 1.5 Flash, google-genai	Content summarization, extraction, Q&A
Data Processing	pandas, NumPy, scipy	Data manipulation & analysis
Analytics	Plotly, TextBlob, scikit-learn	Visualization, sentiment analysis
Backend	Python 3.11+	Core logic
Caching	File-based TTL	Performance optimization
Testing	pytest, pytest-cov	Unit tests, coverage reports
Containerization	Docker, Docker Compose	Development & deployment
Orchestration	Kubernetes (AWS EKS)	Production scaling
CI/CD	GitHub Actions	Automated testing & deployment
Cloud	AWS (ECR, EKS, CloudWatch)	Production infrastructure
🚀 Quick Start
1. Prerequisites
Python 3.11+ (3.12 recommended)
Google Gemini API Key → Get one here
Git for version control
2. Clone & Setup Virtual Environment
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
3. Install Dependencies
# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (required for dynamic scraping)
playwright install chromium
4. Configure Environment Variables
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# On macOS/Linux:
nano .env

# On Windows (PowerShell):
notepad .env
Add your Google Gemini API key:

GEMINI_API_KEY=your_actual_gemini_api_key_here_do_not_share
5. Run the Application
# Start Streamlit app
streamlit run app/main.py
The app will open at http://localhost:8501 in your browser.

💻 Usage Guide
Tab 1: 📋 Summarize
Paste a URL or enter HTML content to get an AI-powered summary.

Input: URL or HTML
Output: Concise summary, key points
Features: Multi-chunk processing for large documents
Tab 2: 🔍 Extract Data
Extract structured JSON data from any webpage.

Input: URL, extraction schema (JSON template)
Output: Structured JSON data
Features: Smart field mapping, default value handling
Tab 3: ❓ Ask a Question
Ask any question about a webpage's content.

Input: URL, question
Output: AI-generated answer based on page content
Features: Context-aware responses, multi-source answers
Tab 4: 📊 Analytics Dashboard
View real-time metrics and insights.

Displays: Request count, cache hit rate, average response time
Visualizations: Sentiment analysis, word clouds, topic distribution
Export: Download analytics as CSV/JSON
Tab 5: 🔴 Live Monitor
Real-time performance tracking and debugging.

Metrics: Active scrapes, queue depth, API usage
Logs: Real-time event stream
Alerts: Performance warnings
Tab 6: 📈 Power BI Dashboard
Export and visualize data in Microsoft Power BI.

Features: Direct Power BI integration
Export formats: .xlsx, .csv
Scheduling: Auto-export to Power BI workspaces
🐳 Docker
Quick Start with Docker
# Build the Docker image
docker build -t scraper-bot:latest .

# Run with environment file
docker run -p 8501:8501 \
  --env-file .env \
  --name scraper-bot-container \
  scraper-bot:latest
Access at http://localhost:8501

Docker Compose (Recommended for Development)
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Stop, remove, and clean volumes
docker-compose down -v
Dockerfile Overview
The provided Dockerfile is multi-stage for optimal image size:

Builder stage: Installs Python dependencies
Runtime stage: Copies only necessary files, installs Playwright Chromium
Security: Runs as non-root user, minimal attack surface
Resulting image: ~1.5GB (includes Chromium)

☸️ Kubernetes Deployment on AWS EKS
Prerequisites
AWS CLI installed and configured (aws configure)
kubectl installed and configured
eksctl (or existing EKS cluster)
IAM permissions: ECR, EKS, CloudWatch
Step 1: Create AWS EKS Cluster
# Create a new EKS cluster (takes 15–20 minutes)
eksctl create cluster \
  --name scraper-bot-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed \
  --enable-ssm
Or use an existing cluster:

# Update kubeconfig for existing cluster
aws eks update-kubeconfig \
  --name scraper-bot-cluster \
  --region us-east-1
Step 2: Create AWS ECR Repository
# Create private ECR repository
aws ecr create-repository \
  --repository-name scraper-bot \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=KMS
Step 3: Build and Push Docker Image to ECR
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
ECR_REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/scraper-bot"

# Authenticate Docker to ECR
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ECR_REPO

# Build and tag image
docker build -t scraper-bot:latest .
docker tag scraper-bot:latest $ECR_REPO:latest
docker tag scraper-bot:latest $ECR_REPO:$(git rev-parse --short HEAD)

# Push to ECR
docker push $ECR_REPO:latest
docker push $ECR_REPO:$(git rev-parse --short HEAD)
Step 4: Create Kubernetes Secret
# Create namespace
kubectl create namespace scraper-bot-prod

# Create secret for API key
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_actual_api_key_here" \
  -n scraper-bot-prod
Step 5: Update Kubernetes Manifests
Edit k8s/deployment.yaml:

image: YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-bot:latest
Then apply manifests:

# Apply deployment
kubectl apply -f k8s/deployment.yaml -n scraper-bot-prod

# Apply service (creates load balancer)
kubectl apply -f k8s/service.yaml -n scraper-bot-prod

# Apply autoscaler
kubectl apply -f k8s/hpa.yaml -n scraper-bot-prod

# Verify deployment
kubectl get pods -n scraper-bot-prod
kubectl get svc -n scraper-bot-prod
Step 6: Get Public Load Balancer URL
# Wait for EXTERNAL-IP to be assigned (may take 2–3 minutes)
kubectl get svc scraper-bot-service -n scraper-bot-prod --watch

# Output example:
# NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP
# scraper-bot-service     LoadBalancer   10.100.0.1      a1b2c3d4-123456789.us-east-1.elb.amazonaws.com
Visit: http://a1b2c3d4-123456789.us-east-1.elb.amazonaws.com:8501

🔄 Horizontal Pod Autoscaling (HPA)
The k8s/hpa.yaml automatically scales pods based on CPU utilization:

minReplicas: 2                    # Always run at least 2 pods
maxReplicas: 5                    # Never exceed 5 pods
targetCPUUtilizationPercentage: 70  # Scale up at 70% CPU
Monitor autoscaling:

# Watch HPA status
kubectl get hpa scraper-bot-hpa -n scraper-bot-prod --watch

# View HPA events
kubectl describe hpa scraper-bot-hpa -n scraper-bot-prod
⚙️ CI/CD with GitHub Actions
The pipeline (.github/workflows/deploy.yml) automatically:

Runs pytest tests on every push to main and PRs
Builds Docker image on push to main
Pushes to AWS ECR with git SHA tag
Deploys to AWS EKS using kubectl apply
Health checks verify deployment before marking as complete
Required GitHub Secrets
Go to Settings → Secrets → Actions and add:

Secret	Description
AWS_ACCESS_KEY_ID	IAM user access key ID
AWS_SECRET_ACCESS_KEY	IAM user secret key
AWS_REGION	AWS region (e.g., us-east-1)
AWS_ACCOUNT_ID	12-digit AWS account ID
ECR_REPOSITORY	ECR repo name (e.g., scraper-bot)
EKS_CLUSTER_NAME	EKS cluster name
GEMINI_API_KEY	Google Gemini API key
GitHub Actions Workflow
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:          # Run pytest
  build:         # Build Docker image
  deploy:        # Deploy to EKS (only on main)
☁️ AWS Services Architecture
┌────────────────────────────────────────────────────┐
│          AWS Cloud Infrastructure                   │
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  GitHub Actions (CI/CD)                  │    │
│  │  - Run tests                             │    │
│  │  - Build Docker image                    │    │
│  │  - Push to ECR                           │    │
│  │  - Deploy to EKS                         │    │
│  └──────────────────────────────────────────┘    │
│                    │                              │
│                    ▼                              │
│  ┌──────────────────────────────────────────┐    │
│  │  AWS ECR (Elastic Container Registry)    │    │
│  │  - Private Docker image storage          │    │
│  │  - Image scanning on push                │    │
│  │  - KMS encryption                        │    │
│  └──────────────────────────────────────────┘    │
│                    │                              │
│                    ▼                              │
│  ┌──────────────────────────────────────────┐    │
│  │  AWS EKS (Elastic Kubernetes Service)    │    │
│  │  - Managed Kubernetes cluster            │    │
│  │  - Auto-scaling with HPA                 │    │
│  │  - Load balancer                         │    │
│  └──────────────────────────────────────────┘    │
│       │                      │                    │
│       ▼                      ▼                    │
│  ┌─────────────┐      ┌──────────────┐          │
│  │  Pod 1      │      │   Pod 2–5    │          │
│  │  (Primary)  │      │  (Autoscaled)│          │
│  └─────────────┘      └──────────────┘          │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │  AWS CloudWatch                          │    │
│  │  - Container logs                        │    │
│  │  - CPU/memory metrics                    │    │
│  │  - Performance alarms                    │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │  AWS ELB (Elastic Load Balancer)         │    │
│  │  - Route traffic to pods                 │    │
│  │  - Health checks                         │    │
│  └──────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
AWS Services Reference
Service	Role	Cost Impact
ECR	Stores & versions Docker images	~$0.10 per GB/month
EKS	Managed Kubernetes control plane	~$0.10/hour (cluster)
EC2	Worker nodes (t3.medium)	~$0.03/hour per node
ELB	Load balancer	~$16/month + $0.006/GB
CloudWatch	Logs & monitoring	~$0.50/GB ingestion
IAM	Access control	Free tier, pay-per-policy
IAM Policy for CI/CD
Attach this to your GitHub Actions IAM user:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EKSAccess",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
📚 Core Modules Documentation
Scraper Module (scraper/)
detector.py — Page Type Detection
Automatically detects if a page requires Playwright (JS-heavy) or requests (static).

from scraper.detector import detect_page_type

page_type = detect_page_type(url)
# Returns: "static" or "dynamic"
base_scraper.py — Static Page Scraper
Scrapes static HTML using requests and BeautifulSoup4.

from scraper.base_scraper import BasicScraper

scraper = BasicScraper(
    timeout=10,
    retries=3,
    user_agent_rotation=True
)
html = scraper.scrape("https://example.com")
dynamic_scraper.py — Dynamic Page Scraper
Scrapes JS-heavy pages using Playwright.

from scraper.dynamic_scraper import DynamicScraper

scraper = DynamicScraper(
    headless=True,
    timeout=15,
    wait_selector=".content"
)
html = await scraper.scrape("https://example.com")
cleaner.py — HTML to Text Conversion
Converts messy HTML to clean, readable text.

from scraper.cleaner import clean_html

clean_text = clean_html(html_content)
chunker.py — Token-Safe Text Splitting
Splits large texts into Gemini-compatible chunks.

from scraper.chunker import ChunkProcessor

chunker = ChunkProcessor(max_tokens=30000)
chunks = chunker.split_text(large_text)
AI Engine Module (ai_engine/)
client.py — Gemini API Wrapper
Wrapper around google-generativeai for easier access.

from ai_engine.client import GeminiClient

client = GeminiClient(api_key="your_key")
response = client.generate(prompt="Summarize this text: ...")
summarizer.py — Multi-Chunk Summarization
Summarizes large documents across multiple API calls.

from ai_engine.summarizer import Summarizer

summarizer = Summarizer(client=client)
summary = summarizer.summarize(text, style="concise")
extractor.py — Structured Data Extraction
Extracts JSON data according to provided schema.

from ai_engine.extractor import DataExtractor

extractor = DataExtractor(client=client)
data = extractor.extract_json(
    text=html_content,
    schema={"products": ["name", "price", "url"]}
)
Pipeline Module (pipeline/)
pipeline.py — Master Orchestrator
Orchestrates the full scrape → clean → AI workflow.

from pipeline.pipeline import ScrapingPipeline

pipeline = ScrapingPipeline()
result = pipeline.run(
    url="https://example.com",
    task="summarize",
    use_cache=True
)
cache.py — TTL-Based Caching
File-based caching to avoid redundant scrapes.

from pipeline.cache import Cache

cache = Cache(ttl_seconds=3600)
cached_result = cache.get("https://example.com")
cache.set("https://example.com", result)
Analytics Module (analytics/)
sentiment.py — Sentiment Analysis
Analyzes sentiment of scraped content.

from analytics.sentiment import SentimentAnalyzer

analyzer = SentimentAnalyzer()
sentiment = analyzer.analyze(text)
# Returns: {"polarity": 0.5, "subjectivity": 0.3, "label": "positive"}
visualizer.py — Data Visualization
Creates interactive Plotly visualizations.

from analytics.visualizer import Visualizer

viz = Visualizer()
fig = viz.create_word_cloud(text)
fig.show()
🔧 Configuration
Environment Variables (.env)
# ── Google Gemini API ──
GEMINI_API_KEY=your_api_key_here

# ── Scraping Settings (Optional) ──
SCRAPER_TIMEOUT=10                    # Request timeout in seconds
SCRAPER_RETRIES=3                     # Retry failed requests
BROWSER_HEADLESS=true                 # Run Playwright headless

# ── Cache Settings (Optional) ──
CACHE_TTL_SECONDS=3600                # Cache expiry time
CACHE_DIR=.cache                      # Cache directory

# ── Streamlit Settings (Optional) ──
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
Kubernetes Secrets
# Create secret
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_key" \
  -n scraper-bot-prod

# View secret
kubectl get secret scraper-bot-secrets -n scraper-bot-prod -o yaml

# Update secret
kubectl delete secret scraper-bot-secrets -n scraper-bot-prod
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="new_key" \
  -n scraper-bot-prod
🧪 Testing
Run Tests Locally
# Run all tests with coverage
pytest --cov=scraper,ai_engine,pipeline --cov-report=html

# Run specific test file
pytest tests/test_scraper.py -v

# Run specific test function
pytest tests/test_scraper.py::test_basic_scraper -v

# Run tests in parallel
pytest -n auto
Test Coverage
Scraper layer: URL validation, HTML parsing, error handling
Pipeline layer: Cache logic, deduplication, export formats
Current coverage target: ≥ 80%

🐛 Troubleshooting
Issue: "Playwright executable not found"
Solution:

playwright install chromium
Issue: "GEMINI_API_KEY not found"
Solution:

# Make sure .env file exists and is in the correct directory
cp .env.example .env
# Edit with your key
nano .env
Issue: "Connection timeout" on Kubernetes
Solution:

# Check pod logs
kubectl logs <pod-name> -n scraper-bot-prod

# Check if pods are running
kubectl get pods -n scraper-bot-prod

# Describe pod for events
kubectl describe pod <pod-name> -n scraper-bot-prod
Issue: "Out of memory" with large documents
Solution: Increase container memory in k8s/deployment.yaml:

resources:
  requests:
    memory: "1Gi"
  limits:
    memory: "2Gi"
📈 Performance Tips
Enable Caching: Set use_cache=True in pipeline calls
Batch Requests: Process multiple URLs in parallel
Optimize Chunking: Adjust max_tokens based on Gemini rate limits
Monitor HPA: Watch kubectl top nodes for resource utilization
CloudWatch Logs: Check DURATION and BILLED_DURATION metrics
🤝 Contributing
Fork the repository
Create a feature branch: git checkout -b feature/amazing-feature
Make your changes and add tests
Run tests locally: pytest --cov
Commit: git commit -m 'Add amazing feature'
Push: git push origin feature/amazing-feature
Open a Pull Request
Code Style
Follow PEP 8
Use type hints for all functions
Add docstrings to all classes and functions
Write unit tests for new features
📜 License
This project is licensed under the MIT License — see the LICENSE file for details.

💬 Support & Community
Issues: GitHub Issues
Discussions: GitHub Discussions
Email: your.email@example.com
🙏 Acknowledgments
Google Gemini for providing the powerful LLM API
Streamlit for the beautiful web UI framework
Playwright for robust browser automation
BeautifulSoup4 for HTML parsing
AWS for cloud infrastructure
Made with ❤️ by [Your Name/Team]

🐳 Docker
Build & Run with Docker
# Build the image
docker build -t scraper-bot .

# Run with your API key
docker run -p 8501:8501 --env-file .env scraper-bot
Run with Docker Compose
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
App available at http://localhost:8501

☸️ Kubernetes Deployment on AWS EKS
Prerequisites
AWS CLI configured (aws configure)
kubectl installed and configured
eksctl or an existing EKS cluster
AWS ECR repository created
Step 1 — Create EKS Cluster (if needed)
eksctl create cluster \
  --name scraper-bot-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
Step 2 — Create ECR Repository
aws ecr create-repository \
  --repository-name scraper-bot \
  --region us-east-1
Step 3 — Build & Push to ECR
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t scraper-bot .
docker tag scraper-bot:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-bot:latest
docker push \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-bot:latest
Step 4 — Create Kubernetes Secret
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_actual_api_key"
Step 5 — Update & Apply Manifests
Edit k8s/deployment.yaml and replace the image URI:

image: YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-bot:latest
Then apply:

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
Step 6 — Get the Public URL
kubectl get service scraper-bot-service
# Look for EXTERNAL-IP — this is your app's public URL
⚙️ CI/CD with GitHub Actions
The pipeline in .github/workflows/deploy.yml automatically:

Runs pytest tests on every push
Builds the Docker image on push to main
Pushes to AWS ECR
Deploys to AWS EKS with zero-downtime rolling update
Required GitHub Secrets
Go to Settings → Secrets → Actions and add:

Secret	Description
AWS_ACCESS_KEY_ID	IAM user access key
AWS_SECRET_ACCESS_KEY	IAM user secret key
AWS_REGION	e.g., us-east-1
AWS_ACCOUNT_ID	12-digit AWS account ID
ECR_REPOSITORY	ECR repo name, e.g., scraper-bot
EKS_CLUSTER_NAME	Your EKS cluster name
GEMINI_API_KEY	Your Gemini API key
☁️ AWS Services Used
Service	Role
AWS ECR (Elastic Container Registry)	Stores Docker images securely. Images are tagged with git commit SHA for traceability.
AWS EKS (Elastic Kubernetes Service)	Runs the Kubernetes cluster. Manages pod scheduling, networking, and scaling.
AWS IAM (Identity & Access Management)	Controls permissions. The CI/CD IAM user needs ECR push access and EKS deploy access.
AWS CloudWatch	Monitors container logs, CPU/memory metrics, and sets up alarms. EKS integrates with CloudWatch Container Insights.
AWS ELB (Elastic Load Balancer)	Automatically created by the Kubernetes LoadBalancer Service to route traffic to pods.
IAM Policy for CI/CD User
Attach this policy to your CI/CD IAM user:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    }
  ]
}
Enable CloudWatch Container Insights on EKS
aws eks update-addon \
  --cluster-name scraper-bot-cluster \
  --addon-name amazon-cloudwatch-observability \
  --region us-east-1
🧪 Running Tests
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scraper --cov=pipeline --cov=ai_engine --cov-report=term-missing

# Run specific test file
pytest tests/test_scraper.py -v
pytest tests/test_pipeline.py -v
🔧 Configuration Reference
Variable	Default	Description
GEMINI_API_KEY	Required	Google Gemini API key
CACHE_TTL	3600	Cache TTL in seconds
CACHE_DIR	.cache	Cache file directory
EXPORT_DIR	exports	Export file directory
LOG_LEVEL	INFO	Python log level
🤖 AI Features
What Gemini 1.5 Flash Does
Feature	How AI is Used
Summarize	Reads cleaned page text, produces concise/detailed/bullet summaries
Extract Data	Given a JSON schema, extracts structured records (products, articles, jobs, etc.)
Auto-Extract	Detects content type automatically and extracts relevant structured data
Ask a Question	Answers any question grounded strictly in the page content
What the Developer Code Does
Component	Role
base_scraper.py	HTTP requests with retry + user-agent rotation
dynamic_scraper.py	Playwright browser automation for JS pages
cleaner.py	Rule-based HTML noise removal
chunker.py	Splits long pages into token-safe pieces for Gemini
detector.py	Heuristic detection: static vs dynamic
cache.py	File-based TTL cache to save API costs
deduplicator.py	MD5-fingerprint deduplication of extracted records
exporter.py	CSV/JSON file generation via pandas
📝 Example Usage (Python API)
from pipeline.pipeline import ScrapingPipeline

pipeline = ScrapingPipeline(use_cache=True)

# Summarize a page
result = pipeline.run_summarize("https://example.com/article", style="bullets")
print(result["summary"])

# Extract structured data
result = pipeline.run_extract("https://example.com/jobs", content_type="job")
print(result["data"])  # List of job record dicts

# Ask a question
result = pipeline.run_qa("https://example.com/pricing", "What is the Pro plan price?")
print(result["answer"])

# Export to CSV
pipeline.export_data(result["data"], format="csv", filename="jobs.csv")
🛡️ Ethical Scraping
This tool is built for legitimate use cases. Always:

✅ Respect robots.txt (use detector.is_scraping_allowed())
✅ Add polite delays between requests (built-in)
✅ Follow each site's Terms of Service
✅ Don't scrape personal data without consent
✅ Cache aggressively to minimize server load
📄 License
MIT License — see LICENSE for details.
