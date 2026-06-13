# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Web Scraping AI Bot
# Multi-stage build for smaller final image.
# Stage 1 (builder): Install Python dependencies
# Stage 2 (runtime): Copy only what's needed + install Playwright Chromium
# ─────────────────────────────────────────────────────────────────────────────

# ── STAGE 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── STAGE 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Labels for image metadata
LABEL maintainer="Web Scraping AI Bot"
LABEL description="AI-powered web scraper using Gemini 1.5 Flash"
LABEL version="1.0.0"

# Install runtime system dependencies required by Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium dependencies
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install Playwright and download Chromium browser
RUN playwright install chromium \
    && playwright install-deps chromium

# ── Security: Run as non-root user ────────────────────────────────────────────
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /root/.cache/ms-playwright 2>/dev/null || true

# Switch to non-root user
USER appuser

# Create necessary directories
RUN mkdir -p .cache exports

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8501/_stcore/health || exit 1

# Start the Streamlit application
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
