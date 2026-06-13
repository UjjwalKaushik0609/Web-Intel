"""
base_scraper.py
---------------
Developer-built: HTTP scraping with proper decompression handling.
Fixes gzip/binary response issue on Windows.
SSL verification disabled for Windows certificate compatibility.
"""
 
import time
import random
import logging
import urllib3
from typing import Optional
 
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
logger = logging.getLogger(__name__)
 
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]
 
 
def _build_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
 
 
def _get_random_headers() -> dict:
    """Headers that tell server to send plain text, not compressed."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        # Do NOT include Accept-Encoding — this prevents gzip compression issues
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
    }
 
 
def scrape_static(
    url: str,
    timeout: int = 20,
    delay: float = 1.0,
    max_retries: int = 3,
) -> Optional[BeautifulSoup]:
    """
    Scrape a static HTML page.
    Properly handles encoding and decompression for any website.
    """
    session = _build_session(retries=max_retries)
    time.sleep(delay + random.uniform(0, 0.5))
 
    try:
        logger.info(f"[BaseScraper] Fetching: {url}")
        response = session.get(
            url,
            headers=_get_random_headers(),
            timeout=timeout,
            verify=False,       # SSL fix for Windows
        )
        response.raise_for_status()
 
        # Force proper text decoding — fixes binary/garbled content
        # Try detected encoding first, then utf-8, then latin-1 as fallback
        if response.encoding and response.encoding.lower() not in ['utf-8', 'utf8']:
            try:
                text = response.content.decode('utf-8', errors='replace')
            except Exception:
                text = response.content.decode('latin-1', errors='replace')
        else:
            text = response.content.decode('utf-8', errors='replace')
 
        soup = BeautifulSoup(text, "html.parser")
        logger.info(f"[BaseScraper] OK — {url} ({len(text)} chars)")
        return soup
 
    except requests.exceptions.Timeout:
        logger.error(f"[BaseScraper] Timeout: {url}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[BaseScraper] Connection error: {url} — {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[BaseScraper] HTTP error: {url} — {e}")
    except Exception as e:
        logger.error(f"[BaseScraper] Error: {url} — {e}")
 
    return None
 
 
def get_raw_html(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch raw HTML string with proper encoding handling."""
    session = _build_session()
    try:
        response = session.get(
            url,
            headers=_get_random_headers(),
            timeout=timeout,
            verify=False,
        )
        response.raise_for_status()
        # Decode bytes directly to avoid encoding issues
        text = response.content.decode('utf-8', errors='replace')
        return text
    except Exception as e:
        logger.error(f"[BaseScraper] get_raw_html failed: {url} — {e}")
        return None
