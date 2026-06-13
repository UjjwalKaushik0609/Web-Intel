"""
extractor.py
------------
Developer-built: Universal extractor for ANY website.
Sends small focused chunks to Gemini for reliable extraction.
AI runs here — Gemini extracts the data.
"""

import json
import re
import logging
from typing import Optional, Union

from ai_engine.client import GeminiClient, get_client

logger = logging.getLogger(__name__)

BUILT_IN_SCHEMAS = {
    "article":  '{"title":"string","author":"string or null","published_date":"string or null","summary":"string","tags":["array"]}',
    "product":  '{"name":"string","price":"string","currency":"string or null","description":"string","rating":"string or null","availability":"string or null"}',
    "job":      '{"title":"string","company":"string","location":"string","salary":"string or null","description":"string"}',
    "event":    '{"name":"string","date":"string","location":"string","description":"string"}',
    "contact":  '{"name":"string","email":"string or null","phone":"string or null","address":"string or null"}',
}

# Keep well within free tier limits
MAX_CONTENT_CHARS = 4000


def _clean_json(raw: str) -> str:
    """Strip ALL markdown fences from Gemini response."""
    raw = raw.strip()
    # Remove ```json or ``` at start
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    # Remove ``` at end
    raw = re.sub(r'\s*```$', '', raw.strip())
    return raw.strip()


def _parse_json(text: str) -> Optional[Union[dict, list]]:
    """Parse JSON with multiple fallback strategies."""
    text = _clean_json(text)
    # Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find array
    try:
        m = re.search(r'\[[\s\S]*\]', text)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    # Find object
    try:
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    logger.error(f"[Extractor] JSON parse failed: {text[:200]}")
    return None


def _to_list(result) -> list:
    """Normalize any result to a list of dicts."""
    if result is None:
        return []
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if isinstance(result, dict):
        for key in ["data", "records", "results", "items", "extracted_data",
                    "products", "articles", "jobs", "events", "listings",
                    "entries", "coins", "companies", "quotes"]:
            if key in result and isinstance(result[key], list):
                return [r for r in result[key] if isinstance(r, dict)]
        return [result]
    return []


def _trim_content(content: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """
    Trim content to safe size for Gemini free tier.
    Takes first portion which has the most important data.
    Developer-built.
    """
    if len(content) <= max_chars:
        return content
    trimmed = content[:max_chars]
    last_newline = trimmed.rfind('\n')
    if last_newline > max_chars * 0.7:
        trimmed = trimmed[:last_newline]
    logger.info(f"[Extractor] Trimmed {len(content)} → {len(trimmed)} chars")
    return trimmed


def extract(
    content: str,
    schema: Optional[str] = None,
    content_type: Optional[str] = None,
    url: str = "",
    client: Optional[GeminiClient] = None,
) -> Union[list, dict, None]:
    """
    Universal extraction for ANY website.
    Trims content to 4000 chars for reliable Gemini response.
    AI runs here.
    """
    if not content or len(content.strip()) < 20:
        logger.warning("[Extractor] Content too short")
        return []

    client = client or get_client()

    # Trim to safe size
    content = _trim_content(content)
    logger.info(f"[Extractor] Extracting from {len(content)} chars")

    if schema:
        active_schema = schema
    elif content_type and content_type in BUILT_IN_SCHEMAS:
        active_schema = BUILT_IN_SCHEMAS[content_type]
    else:
        return _universal_extract(content, url, client)

    prompt = f"""Extract data from this web page as JSON.

SCHEMA: {active_schema}

RULES:
- Output ONLY JSON. No markdown. No explanation.
- Multiple items = JSON array [{{"field":"value"}}]
- Single item = JSON object {{"field":"value"}}
- Use real values. Never null if value exists.

URL: {url}
CONTENT: {content}

JSON:"""

    raw = client.generate(prompt)
    logger.info(f"[Extractor] Response: {raw[:200]}")
    result = _parse_json(raw)
    records = _to_list(result)
    logger.info(f"[Extractor] Got {len(records)} records")
    return records


def _universal_extract(content: str, url: str, client: GeminiClient) -> list:
    """
    Auto-detect content type and extract all data.
    Works for any website — Wikipedia, news, finance, products, jobs.
    AI runs here.
    """
    prompt = f"""Extract ALL structured data from this web page as a JSON array.

Auto-detect what type of data this is and extract everything.
Examples: facts, products, articles, quotes, jobs, companies, crypto stats.

RULES:
- Output ONLY a JSON array starting with [
- No markdown. No explanation. Just JSON.
- Each record needs at least 2 real fields
- Extract ALL records found
- Real values only

URL: {url}
CONTENT: {content}

JSON ARRAY:"""

    raw = client.generate(prompt)
    logger.info(f"[Extractor] Universal response: {raw[:300]}")
    result = _parse_json(raw)
    records = _to_list(result)
    logger.info(f"[Extractor] Universal got {len(records)} records")
    return records


def answer_question(
    content: str,
    question: str,
    url: str = "",
    client: Optional[GeminiClient] = None,
) -> str:
    """Answer any question about any web page. AI runs here."""
    from ai_engine.prompts import SYSTEM_QA_ASSISTANT, get_qa_prompt
    client = client or get_client()
    if not content:
        return "No content available."
    content = _trim_content(content, max_chars=6000)
    prompt = get_qa_prompt(content, question, url=url)
    return client.generate(prompt, system_instruction=SYSTEM_QA_ASSISTANT)