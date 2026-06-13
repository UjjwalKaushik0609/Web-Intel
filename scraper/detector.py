"""
detector.py
-----------
Developer-built: Heuristic engine to auto-detect whether a page is static or dynamic.
Determines whether to use requests (fast) or Playwright (slower, full JS).
AI does NOT run here — rule-based detection logic.
"""

import re
import logging
from typing import Literal
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# JS framework fingerprints found in HTML source
JS_FRAMEWORK_PATTERNS = [
    # React
    r"__NEXT_DATA__",
    r"react(?:dom)?[\./]",
    r"_reactFiber",
    r"data-reactroot",
    # Vue
    r"vue(?:\.min)?\.js",
    r"__vue_",
    # Angular
    r"ng-version",
    r"angular(?:\.min)?\.js",
    # General SPA indicators
    r"<div[^>]+id=['\"]app['\"]",
    r"<div[^>]+id=['\"]root['\"]",
    r"<div[^>]+id=['\"]main['\"]",
    r"window\.__STORE__",
    r"window\.__INITIAL_STATE__",
    r"window\.__PRELOADED_STATE__",
]

# Domains known to be JS-heavy (best served by Playwright)
KNOWN_DYNAMIC_DOMAINS = [
    "twitter.com", "x.com",
    "instagram.com",
    "facebook.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",
    "airbnb.com",
    "booking.com",
    "zillow.com",
]

# Domains known to be static-friendly
KNOWN_STATIC_DOMAINS = [
    "wikipedia.org",
    "en.wikipedia.org",
    "bbc.com",
    "bbc.co.uk",
    "reuters.com",
    "apnews.com",
    "github.com",
    "stackoverflow.com",
    "docs.python.org",
]


PageType = Literal["static", "dynamic"]


def _get_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        return domain.lstrip("www.")
    except Exception:
        return ""


def _quick_fetch_head(url: str, timeout: int = 5) -> dict:
    """
    Perform a HEAD request to get basic page info without downloading the body.
    Returns a dict with 'content_type' and 'status_code'.
    """
    try:
        resp = requests.head(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BotDetector/1.0)"},
            timeout=timeout,
            allow_redirects=True,
        )
        return {
            "content_type": resp.headers.get("Content-Type", "").lower(),
            "status_code": resp.status_code,
        }
    except Exception:
        return {"content_type": "", "status_code": 0}


def detect_page_type(url: str, sample_html: str = None) -> PageType:
    """
    Auto-detect whether a URL requires dynamic (Playwright) or static (requests) scraping.

    Detection strategy (in order of priority):
    1. Check known domain lists
    2. Check HTML for JS framework fingerprints (if sample provided)
    3. Check content-type from HEAD request
    4. Default to static (safer, faster)

    Args:
        url: URL to analyze.
        sample_html: Optional pre-fetched HTML to scan for JS frameworks.

    Returns:
        'static' or 'dynamic'
    """
    domain = _get_domain(url)

    # 1. Check known domain lists
    for known_domain in KNOWN_DYNAMIC_DOMAINS:
        if domain.endswith(known_domain):
            logger.info(f"[Detector] {url} → DYNAMIC (known dynamic domain: {known_domain})")
            return "dynamic"

    for known_domain in KNOWN_STATIC_DOMAINS:
        if domain.endswith(known_domain):
            logger.info(f"[Detector] {url} → STATIC (known static domain: {known_domain})")
            return "static"

    # 2. Scan HTML for JS framework fingerprints
    if sample_html:
        for pattern in JS_FRAMEWORK_PATTERNS:
            if re.search(pattern, sample_html, re.IGNORECASE):
                logger.info(f"[Detector] {url} → DYNAMIC (JS pattern: {pattern})")
                return "dynamic"

    # 3. HEAD request content-type check
    head_info = _quick_fetch_head(url)
    content_type = head_info.get("content_type", "")

    if "javascript" in content_type or "json" in content_type:
        logger.info(f"[Detector] {url} → DYNAMIC (JSON/JS content-type: {content_type})")
        return "dynamic"

    # 4. Default to static — faster and sufficient for most pages
    logger.info(f"[Detector] {url} → STATIC (default)")
    return "static"


def is_scraping_allowed(url: str) -> bool:
    """
    Lightweight robots.txt check.
    Returns True if scraping is likely allowed (no explicit disallow for all bots).
    NOTE: This is a basic check. For production, use the 'robotparser' stdlib module.
    """
    try:
        import urllib.robotparser
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        allowed = rp.can_fetch("*", url)
        logger.info(f"[Detector] Robots.txt check for {url}: {'allowed' if allowed else 'DISALLOWED'}")
        return allowed
    except Exception as e:
        logger.warning(f"[Detector] Could not check robots.txt for {url}: {e}")
        return True  # Fail open — user is responsible for compliance
