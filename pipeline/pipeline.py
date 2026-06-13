"""
pipeline.py
-----------
Developer-built: Universal pipeline for ANY website.
Directly targets mw-content-text for Wikipedia.
Uses biggest-block strategy for all other sites.
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
    ):
        self.use_cache = use_cache
        self.cache = get_cache(ttl=cache_ttl) if use_cache else None
        self.force_static = force_static
        self.force_dynamic = force_dynamic
        self._ai_client = None

    def _get_ai_client(self):
        if self._ai_client is None:
            from ai_engine.client import get_client
            self._ai_client = get_client()
        return self._ai_client

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch raw HTML directly using requests.
        Bypasses scraper module to keep the original HTML structure intact.
        This is critical — converting BeautifulSoup to string loses some IDs.
        """
        import random
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.raise_for_status()
            html = resp.content.decode("utf-8", errors="replace")
            logger.info(f"[Pipeline] Fetched {len(html)} chars from {url}")
            return html
        except Exception as e:
            logger.error(f"[Pipeline] Fetch failed: {url} — {e}")
            # Fallback to playwright for JS-heavy pages
            try:
                from scraper.dynamic_scraper import scrape_dynamic
                return scrape_dynamic(url)
            except Exception:
                return None

    def _extract_text(self, html: str, url: str = "") -> str:
        """
        Extract clean main content text from any website.

        For Wikipedia: uses mw-content-text directly (68k chars of article).
        For others: finds the largest text block on the page.
        Developer-built — no AI.
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, "html.parser")

            # ── Wikipedia-specific extraction ──────────────────────────
            if "wikipedia.org" in url:
                content_div = soup.find(id="mw-content-text")
                if content_div:
                    # Remove Wikipedia internal noise
                    noise_classes = [
                        "toc", "navbox", "navbox-inner", "navbox-subgroup",
                        "reflist", "refbegin", "mbox", "ambox", "tmbox",
                        "hatnote", "navigation-not-searchable", "noprint",
                        "mw-editsection", "reference", "portal",
                        "sistersitebox", "metadata", "catlinks",
                    ]
                    for cls in noise_classes:
                        for el in content_div.find_all(class_=cls):
                            try:
                                el.decompose()
                            except Exception:
                                pass

                    # Remove all [edit] links
                    for el in content_div.find_all("span", class_="mw-editsection"):
                        try:
                            el.decompose()
                        except Exception:
                            pass

                    text = content_div.get_text(separator="\n", strip=True)
                    text = re.sub(r'\n{4,}', '\n\n\n', text)
                    text = re.sub(r'\[[\d]+\]', '', text)  # Remove citation numbers [1][2]
                    text = text.strip()
                    logger.info(f"[Pipeline] Wikipedia extracted {len(text)} chars")
                    return text

            # ── General website extraction ─────────────────────────────
            # Remove noise tags
            for tag in ["script", "style", "noscript", "iframe",
                        "svg", "canvas", "head", "footer", "nav"]:
                for el in soup.find_all(tag):
                    try:
                        el.decompose()
                    except Exception:
                        pass

            # Remove noisy elements by class/id
            noise_re = re.compile(
                r"(sidebar|navbar|breadcrumb|cookie|popup|modal|"
                r"advertisement|social|share|reflist|navbox|noprint|"
                r"hatnote|mbox|portal|toc|catlinks|header|footer)", re.I
            )
            for el in soup.find_all(True):
                try:
                    el_id = str(el.get("id") or "")
                    el_class = " ".join(list(el.get("class") or []))
                    if noise_re.search(el_id) or noise_re.search(el_class):
                        el.decompose()
                except Exception:
                    pass

            # Try known content containers first
            main = (
                soup.find("main") or
                soup.find("article") or
                soup.find(id=re.compile(r"^(content|main|primary|article|post|body)$", re.I)) or
                soup.find(class_=re.compile(r"(article.body|post.content|main.content|entry.content|product.detail)", re.I))
            )

            if main:
                text = main.get_text(separator="\n", strip=True)
                if len(text) > 500:
                    text = re.sub(r'\n{4,}', '\n\n\n', text)
                    logger.info(f"[Pipeline] Main block: {len(text)} chars")
                    return text.strip()

            # Fallback: find biggest div
            best = None
            best_len = 0
            for el in soup.find_all(["div", "section"]):
                try:
                    t = el.get_text(strip=True)
                    if len(t) > best_len:
                        best_len = len(t)
                        best = el
                except Exception:
                    pass

            target = best if best and best_len > 200 else (soup.find("body") or soup)
            text = target.get_text(separator="\n", strip=True)
            text = re.sub(r'\n{4,}', '\n\n\n', text)
            logger.info(f"[Pipeline] Fallback block: {len(text)} chars")
            return text.strip()

        except Exception as e:
            logger.error(f"[Pipeline] Text extraction error: {e}")
            try:
                return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
            except Exception:
                return ""

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch clean content from ANY URL."""
        cache_key = f"content_v7:{url}"

        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[Pipeline] Cache hit: {url}")
                return cached

        html = self._fetch_html(url)
        if not html:
            logger.error(f"[Pipeline] No HTML for: {url}")
            return None

        content = self._extract_text(html, url=url)

        if not content or len(content) < 50:
            logger.error(f"[Pipeline] Content too short: {len(content) if content else 0}")
            return None

        if self.use_cache and self.cache:
            self.cache.set(cache_key, content)

        return content

    def fetch_metadata(self, url: str) -> dict:
        """Fetch page metadata."""
        try:
            html = self._fetch_html(url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                return extract_metadata(soup)
        except Exception as e:
            logger.error(f"[Pipeline] Metadata error: {e}")
        return {}

    def run_summarize(self, url: str, style: str = "concise") -> Dict[str, Any]:
        """Summarize any web page."""
        cache_key = f"summary_v4:{style}:{url}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        content = self.fetch_content(url)
        if not content:
            return {"url": url, "summary": "Failed to fetch page content.", "error": True}

        metadata = self.fetch_metadata(url)

        from ai_engine.summarizer import summarize
        summary = summarize(content, url=url, style=style, client=self._get_ai_client())

        result = {
            "url": url, "summary": summary,
            "metadata": metadata,
            "content_length": len(content),
            "style": style,
        }
        if self.use_cache and self.cache:
            self.cache.set(cache_key, result)
        return result

    def run_extract(
        self,
        url: str,
        schema: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract structured data from ANY website."""
        cache_key = f"extract_v7:{content_type or 'auto'}:{url}"
        if self.use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        content = self.fetch_content(url)
        if not content:
            return {"url": url, "data": [], "error": "Failed to fetch page content."}

        logger.info(f"[Pipeline] Sending {len(content)} chars to Gemini")

        from ai_engine.extractor import extract
        extracted = extract(
            content, schema=schema, content_type=content_type,
            url=url, client=self._get_ai_client(),
        )

        if isinstance(extracted, list):
            records = [r for r in extracted if isinstance(r, dict)]
            records = deduplicate(records)
        elif isinstance(extracted, dict) and "error" not in extracted:
            records = [extracted]
        else:
            records = []

        result = {
            "url": url, "data": records,
            "record_count": len(records),
            "content_type": content_type or "auto-detected",
        }
        if records and self.use_cache and self.cache:
            self.cache.set(cache_key, result)
        return result

    def run_qa(self, url: str, question: str) -> Dict[str, Any]:
        """Answer questions about any web page."""
        content = self.fetch_content(url)
        if not content:
            return {"url": url, "question": question,
                    "answer": "Failed to fetch page content."}

        from ai_engine.extractor import answer_question
        answer = answer_question(content, question=question,
                                 url=url, client=self._get_ai_client())
        return {"url": url, "question": question, "answer": answer}

    def export_data(self, data, format: str = "json", filename=None) -> str:
        if format == "csv":
            records = data if isinstance(data, list) else [data]
            return export_to_csv(records, filename=filename)
        return export_to_json(data, filename=filename)

    def data_to_dataframe(self, data) -> pd.DataFrame:
        records = data if isinstance(data, list) else [data]
        return export_to_dataframe(records)