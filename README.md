# 🤖 Web Scraping AI Bot

An intelligent web scraping system powered by **Google Gemini 1.5 Flash**, built with Python, Playwright, and Streamlit. Scrape any webpage — static or dynamic — and use AI to summarize content, extract structured data, or answer questions about it.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app/)                   │
│          Summarize │ Extract Data │ Ask a Question       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Pipeline Orchestrator (pipeline/)           │
│    detect → scrape → clean → AI process → cache → export│
└──────┬──────────────────────────────────────┬───────────┘
       │                                      │
┌──────▼──────────┐                ┌──────────▼──────────┐
│  Scraper Layer  │                │    AI Engine Layer   │
│  (scraper/)     │                │    (ai_engine/)      │
│                 │                │                      │
│ • base_scraper  │                │ • client.py          │
│   (requests)    │                │   (Gemini API)       │
│ • dynamic_scraper│               │ • prompts.py         │
│   (Playwright)  │                │ • summarizer.py      │
│ • cleaner.py    │                │ • extractor.py       │
│ • chunker.py    │                │                      │
│ • detector.py   │                └──────────────────────┘
└─────────────────┘
```

---

## 📁 Project Structure

```
web-scraping-ai-bot/
├── scraper/
│   ├── base_scraper.py      # requests + BeautifulSoup4, retry + user-agent rotation
│   ├── dynamic_scraper.py   # Playwright for JS-heavy pages
│   ├── cleaner.py           # HTML → clean text conversion
│   ├── chunker.py           # Token-safe text splitting for Gemini
│   └── detector.py          # Auto-detect static vs dynamic pages
│
├── ai_engine/
│   ├── client.py            # Gemini API wrapper (google-generativeai)
│   ├── prompts.py           # All prompt templates
│   ├── summarizer.py        # Multi-chunk summarization
│   └── extractor.py         # Structured JSON extraction + Q&A
│
├── pipeline/
│   ├── pipeline.py          # Master orchestrator
│   ├── cache.py             # File-based TTL cache
│   ├── deduplicator.py      # Remove duplicate records
│   └── exporter.py          # CSV and JSON export
│
├── app/
│   └── main.py              # Streamlit UI (3 tabs)
│
├── tests/
│   ├── test_scraper.py      # Unit tests for scraper layer
│   └── test_pipeline.py     # Unit tests for pipeline layer
│
├── k8s/
│   ├── deployment.yaml      # Kubernetes Deployment (2 replicas)
│   ├── service.yaml         # LoadBalancer Service
│   ├── secret.yaml          # API key Secret
│   └── hpa.yaml             # Horizontal Pod Autoscaler (2–5 pods)
│
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions CI/CD pipeline
│
├── Dockerfile               # Multi-stage, non-root, Playwright + Chromium
├── docker-compose.yml       # Local development single-service setup
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- A Google Gemini API key → [Get one here](https://makersuite.google.com/app/apikey)

### 2. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/web-scraping-ai-bot.git
cd web-scraping-ai-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the App

```bash
streamlit run app/main.py
```

Open your browser at **http://localhost:8501**

---

## 🐳 Docker

### Build & Run with Docker

```bash
# Build the image
docker build -t scraper-bot .

# Run with your API key
docker run -p 8501:8501 --env-file .env scraper-bot
```

### Run with Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

App available at **http://localhost:8501**

---

## ☸️ Kubernetes Deployment on AWS EKS

### Prerequisites

- AWS CLI configured (`aws configure`)
- `kubectl` installed and configured
- `eksctl` or an existing EKS cluster
- AWS ECR repository created

### Step 1 — Create EKS Cluster (if needed)

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

### Step 2 — Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name scraper-bot \
  --region us-east-1
```

### Step 3 — Build & Push to ECR

```bash
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
```

### Step 4 — Create Kubernetes Secret

```bash
kubectl create secret generic scraper-bot-secrets \
  --from-literal=GEMINI_API_KEY="your_actual_api_key"
```

### Step 5 — Update & Apply Manifests

Edit `k8s/deployment.yaml` and replace the image URI:
```yaml
image: YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/scraper-bot:latest
```

Then apply:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### Step 6 — Get the Public URL

```bash
kubectl get service scraper-bot-service
# Look for EXTERNAL-IP — this is your app's public URL
```

---

## ⚙️ CI/CD with GitHub Actions

The pipeline in `.github/workflows/deploy.yml` automatically:

1. **Runs pytest tests** on every push
2. **Builds the Docker image** on push to `main`
3. **Pushes to AWS ECR**
4. **Deploys to AWS EKS** with zero-downtime rolling update

### Required GitHub Secrets

Go to **Settings → Secrets → Actions** and add:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | e.g., `us-east-1` |
| `AWS_ACCOUNT_ID` | 12-digit AWS account ID |
| `ECR_REPOSITORY` | ECR repo name, e.g., `scraper-bot` |
| `EKS_CLUSTER_NAME` | Your EKS cluster name |
| `GEMINI_API_KEY` | Your Gemini API key |

---

## ☁️ AWS Services Used

| Service | Role |
|---|---|
| **AWS ECR** (Elastic Container Registry) | Stores Docker images securely. Images are tagged with git commit SHA for traceability. |
| **AWS EKS** (Elastic Kubernetes Service) | Runs the Kubernetes cluster. Manages pod scheduling, networking, and scaling. |
| **AWS IAM** (Identity & Access Management) | Controls permissions. The CI/CD IAM user needs ECR push access and EKS deploy access. |
| **AWS CloudWatch** | Monitors container logs, CPU/memory metrics, and sets up alarms. EKS integrates with CloudWatch Container Insights. |
| **AWS ELB** (Elastic Load Balancer) | Automatically created by the Kubernetes LoadBalancer Service to route traffic to pods. |

### IAM Policy for CI/CD User

Attach this policy to your CI/CD IAM user:

```json
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
```

### Enable CloudWatch Container Insights on EKS

```bash
aws eks update-addon \
  --cluster-name scraper-bot-cluster \
  --addon-name amazon-cloudwatch-observability \
  --region us-east-1
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scraper --cov=pipeline --cov=ai_engine --cov-report=term-missing

# Run specific test file
pytest tests/test_scraper.py -v
pytest tests/test_pipeline.py -v
```

---

## 🔧 Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | **Required** | Google Gemini API key |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |
| `CACHE_DIR` | `.cache` | Cache file directory |
| `EXPORT_DIR` | `exports` | Export file directory |
| `LOG_LEVEL` | `INFO` | Python log level |

---

## 🤖 AI Features

### What Gemini 1.5 Flash Does

| Feature | How AI is Used |
|---|---|
| **Summarize** | Reads cleaned page text, produces concise/detailed/bullet summaries |
| **Extract Data** | Given a JSON schema, extracts structured records (products, articles, jobs, etc.) |
| **Auto-Extract** | Detects content type automatically and extracts relevant structured data |
| **Ask a Question** | Answers any question grounded strictly in the page content |

### What the Developer Code Does

| Component | Role |
|---|---|
| `base_scraper.py` | HTTP requests with retry + user-agent rotation |
| `dynamic_scraper.py` | Playwright browser automation for JS pages |
| `cleaner.py` | Rule-based HTML noise removal |
| `chunker.py` | Splits long pages into token-safe pieces for Gemini |
| `detector.py` | Heuristic detection: static vs dynamic |
| `cache.py` | File-based TTL cache to save API costs |
| `deduplicator.py` | MD5-fingerprint deduplication of extracted records |
| `exporter.py` | CSV/JSON file generation via pandas |

---

## 📝 Example Usage (Python API)

```python
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
```

---

## 🛡️ Ethical Scraping

This tool is built for legitimate use cases. Always:

- ✅ Respect `robots.txt` (use `detector.is_scraping_allowed()`)
- ✅ Add polite delays between requests (built-in)
- ✅ Follow each site's Terms of Service
- ✅ Don't scrape personal data without consent
- ✅ Cache aggressively to minimize server load

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
