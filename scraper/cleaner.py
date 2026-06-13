"""
cleaner.py
----------
Developer-built: HTML-to-clean-text conversion pipeline.
Strips scripts, styles, ads, navigation boilerplate; preserves meaningful content.
AI does NOT run here — purely rule-based text cleaning.
"""

import re
import logging
import copy
from typing import Optional

from bs4 import BeautifulSoup, Comment, Tag

logger = logging.getLogger(__name__)

REMOVE_TAGS = [
    "script", "style", "noscript", "iframe", "embed", "object", "svg", "canvas",
]

SOFT_REMOVE_TAGS = [
    "nav", "header", "footer", "aside", "form", "button",
]

NOISE_PATTERNS = re.compile(
    r"(^|[\s_-])(nav|navbar|navigation|menu|advertisement|"
    r"cookie|popup|modal|banner|social|share|subscribe|newsletter|"
    r"sponsored|promo|widget)($|[\s_-])",
    re.IGNORECASE,
)


def _remove_noise_elements(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove scripts, styles, and noisy elements safely."""
    for tag_name in REMOVE_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag_name in SOFT_REMOVE_TAGS:
        for element in soup.find_all(tag_name):
            if not isinstance(element, Tag):
                continue
            classes = " ".join(element.get("class") or [])
            element_id = element.get("id") or ""
            if NOISE_PATTERNS.search(classes) or NOISE_PATTERNS.search(element_id):
                element.decompose()

    return soup


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple newlines/spaces."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def html_to_text(html: str) -> str:
    """Convert raw HTML to clean plain text."""
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
        soup = _remove_noise_elements(soup)
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id=re.compile(r"(main|content|article|post|body)", re.I))
            or soup.find(class_=re.compile(r"(main|content|article|post|body)", re.I))
        )
        target = main_content if main_content else soup
        text = target.get_text(separator="\n", strip=True)
        return _normalize_whitespace(text)
    except Exception as e:
        logger.error(f"[Cleaner] Error cleaning HTML: {e}")
        return ""


def soup_to_text(soup: BeautifulSoup) -> str:
    """Convert a BeautifulSoup object directly to clean text."""
    try:
        soup_copy = copy.copy(soup)
        soup_copy = _remove_noise_elements(soup_copy)
        text = soup_copy.get_text(separator="\n", strip=True)
        return _normalize_whitespace(text)
    except Exception as e:
        logger.error(f"[Cleaner] Error converting soup to text: {e}")
        try:
            return _normalize_whitespace(soup.get_text(separator="\n", strip=True))
        except Exception:
            return ""


def extract_metadata(soup: BeautifulSoup) -> dict:
    """Extract page metadata: title, description, keywords, canonical URL."""
    metadata = {
        "title": "", "description": "", "keywords": "",
        "canonical_url": "", "og_title": "", "og_description": "",
    }
    try:
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        for meta in soup.find_all("meta"):
            if not isinstance(meta, Tag):
                continue
            name = (meta.get("name") or "").lower()
            prop = (meta.get("property") or "").lower()
            content = meta.get("content") or ""

            if name == "description":
                metadata["description"] = content
            elif name == "keywords":
                metadata["keywords"] = content
            elif prop == "og:title":
                metadata["og_title"] = content
            elif prop == "og:description":
                metadata["og_description"] = content

        canonical = soup.find("link", rel="canonical")
        if canonical and isinstance(canonical, Tag):
            metadata["canonical_url"] = canonical.get("href") or ""
    except Exception as e:
        logger.error(f"[Cleaner] Error extracting metadata: {e}")
    return metadata
