"""
pipeline.py
-----------
Developer-built: Universal pipeline for ANY website.
FIX 1: Accepts explicit api_key (session-scoped, no global leak).
FIX 2: Caches raw HTML per URL so it's fetched ONCE and reused by
       both fetch_content() (for AI/summarize/Q&A) and local extraction
       (for tables) — no more double-scraping the same page.
"""

import re
import logging
from typing import Optional, Dict, Any

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

from scraper.detector import detect_page_type
from scraper.cleaner import extract_metadata
from pipeline.cache import get_cache
from pipeline.deduplicator import deduplicate
from pipeline.exporter import export_to_json, export_to_csv, export_to_dataframe

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class ScrapingPipeline:

    def __init__(
        self,
        use_cache: bool = True,
        cache_ttl: int = 3600,
        force_static: bool = False,
        force_dynamic: bool = False,
        api_key: Optional[str] = None,
    ):
        self.use_cache = use_cache
        self.cache = get_cache(ttl=cache_ttl) if use_cache else None
        self.force_static = force_static
        self.force_dynamic = force_dynamic
        self.api_key = api_key          # session-scoped key, never global
        self._ai_client = None
        # In-memory per-instance HTML cache — guarantees a URL is only
        # ever fetched once within a single pipeline's lifetime (one tab run)
        self._html_memo: Dict[str, str] = {}

    def _get_ai_client(self):
        """Always builds a fresh client scoped to THIS pipeline's api_key."""
        from ai_engine.client import get_client
        if self._ai_client is None:
            self._ai_client = get_client(api_key=self.api_key)
        return self._ai_client

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch raw HTML — checks in-memory memo AND the TTL file cache
        BEFORE making a network request, so the same URL is never
        scraped twice (fixes Tab 4 double-fetch bug).
        """
        # 1) In-memory memo (fastest, same pipeline instance / same run)
        if url in self._html_memo:
            logger.info(f"[Pipeline] HTML memo-hit: {url}")
            return self._html_memo[url]

        # 2) Persistent TTL cache (survives across reruns / tabs)
        cache_key = f"raw_html:{url}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[Pipeline] HTML cache-hit: {url}")
                self._html_memo[url] = cached
                return cached

        # 3) Actually fetch over the network
        import random
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        html = None
        try:
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.raise_for_status()
            html = resp.content.decode("utf-8", errors="replace")
            logger.info(f"[Pipeline] Fetched {len(html)} chars from {url}")
        except Exception as e:
            logger.error(f"[Pipeline] requests fetch failed: {url} — {e}")
            try:
                from scraper.dynamic_scraper import scrape_dynamic
                html = scrape_dynamic(url)
            except Exception as e2:
                logger.error(f"[Pipeline] Playwright fallback failed: {e2}")
                return None

        if html:
            self._html_memo[url] = html
            if self.use_cache and self.cache:
                self.cache.set(cache_key, html)

        return html

    def _extract_text(self, html: str, url: str = "") -> str:
        """Extract clean main-content text from any website."""
        if not html:
            return ""
        try:
            soup = BeautifulSoup(html, "html.parser")

            if "wikipedia.org" in url:
                content_div = soup.find(id="mw-content-text")
                if content_div:
                    noise_classes = ["toc","navbox","navbox-inner","navbox-subgroup",
                        "reflist","refbegin","mbox","ambox","tmbox","hatnote",
                        "navigation-not-searchable","noprint","mw-editsection",
                        "reference","portal","sistersitebox","metadata","catlinks"]
                    for cls in noise_classes:
                        for el in content_div.find_all(class_=cls):
                            try: el.decompose()
                            except Exception: pass
                    text = content_div.get_text(separator="\n", strip=True)
                    text = re.sub(r'\n{4,}', '\n\n\n', text)
                    text = re.sub(r'\[[\d]+\]', '', text)
                    return text.strip()

            for tag in ["script","style","noscript","iframe","svg","canvas",
                        "head","footer","nav"]:
                for el in soup.find_all(tag):
                    try: el.decompose()
                    except Exception: pass

            noise_re = re.compile(
                r"(sidebar|navbar|breadcrumb|cookie|popup|modal|advertisement|"
                r"social|share|reflist|navbox|noprint|hatnote|mbox|portal|"
                r"toc|catlinks|header|footer)", re.I)
            for el in soup.find_all(True):
                try:
                    el_id = str(el.get("id") or "")
                    el_class = " ".join(list(el.get("class") or []))
                    if noise_re.search(el_id) or noise_re.search(el_class):
                        el.decompose()
                except Exception: pass

            main = (soup.find("main") or soup.find("article") or
                soup.find(id=re.compile(r"^(content|main|primary|article|post|body)$", re.I)) or
                soup.find(class_=re.compile(r"(article.body|post.content|main.content|entry.content|product.detail)", re.I)))

            if main:
                text = main.get_text(separator="\n", strip=True)
                if len(text) > 500:
                    return re.sub(r'\n{4,}', '\n\n\n', text).strip()

            best, best_len = None, 0
            for el in soup.find_all(["div","section"]):
                try:
                    t = el.get_text(strip=True)
                    if len(t) > best_len:
                        best_len, best = len(t), el
                except Exception: pass

            target = best if best and best_len > 200 else (soup.find("body") or soup)
            text = target.get_text(separator="\n", strip=True)
            return re.sub(r'\n{4,}', '\n\n\n', text).strip()

        except Exception as e:
            logger.error(f"[Pipeline] Text extraction error: {e}")
            try:
                return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
            except Exception:
                return ""

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch clean text content — reuses cached HTML if already fetched."""
        cache_key = f"content:{url}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        html = self._fetch_html(url)   # reuses memo/cache — no duplicate request
        if not html:
            return None

        content = self._extract_text(html, url=url)
        if not content or len(content) < 50:
            try:
                soup = BeautifulSoup(html, "html.parser")
                for tag in ["script","style","noscript"]:
                    for el in soup.find_all(tag): el.decompose()
                content = soup.get_text(separator="\n", strip=True)
            except Exception:
                return None

        if content and self.use_cache and self.cache:
            self.cache.set(cache_key, content)

        return content or None

    def fetch_metadata(self, url: str) -> dict:
        try:
            html = self._fetch_html(url)   # reuses memo — no duplicate request
            if html:
                return extract_metadata(BeautifulSoup(html, "html.parser"))
        except Exception as e:
            logger.error(f"[Pipeline] Metadata error: {e}")
        return {}

    def run_summarize(self, url: str, style: str = "concise") -> Dict[str, Any]:
        content = self.fetch_content(url)
        if not content:
            return {"url": url, "summary": "Failed to fetch page content.", "error": True}

        metadata = self.fetch_metadata(url)
        from ai_engine.summarizer import summarize
        summary = summarize(content, url=url, style=style, client=self._get_ai_client())

        return {"url": url, "summary": summary, "metadata": metadata,
                "content_length": len(content), "style": style}

    def run_extract(self, url: str, schema: Optional[str] = None,
                    content_type: Optional[str] = None) -> Dict[str, Any]:
        content = self.fetch_content(url)   # reuses cached HTML
        if not content:
            return {"url": url, "data": [], "error": "Failed to fetch page content."}

        from ai_engine.extractor import extract
        extracted = extract(content, schema=schema, content_type=content_type,
                            url=url, client=self._get_ai_client())

        if isinstance(extracted, list):
            records = deduplicate([r for r in extracted if isinstance(r, dict)])
        elif isinstance(extracted, dict) and "error" not in extracted:
            records = [extracted]
        else:
            records = []

        return {"url": url, "data": records, "record_count": len(records),
                "content_type": content_type or "auto-detected"}

    def run_qa(self, url: str, question: str) -> Dict[str, Any]:
        content = self.fetch_content(url)   # reuses cached HTML
        if not content:
            return {"url": url, "question": question,
                    "answer": "Failed to fetch page content."}
        from ai_engine.extractor import answer_question
        answer = answer_question(content, question=question, url=url,
                                 client=self._get_ai_client())
        return {"url": url, "question": question, "answer": answer}

    def export_data(self, data, format: str = "json", filename=None) -> str:
        if format == "csv":
            return export_to_csv(data if isinstance(data, list) else [data], filename=filename)
        return export_to_json(data, filename=filename)

    def data_to_dataframe(self, data) -> pd.DataFrame:
        return export_to_dataframe(data if isinstance(data, list) else [data])