
"""
local_extractor.py
------------------
Developer-built: 100% LOCAL data extraction — zero AI, zero API key needed.
Uses regex, BeautifulSoup, and pattern matching to extract structured data
from any website WITHOUT calling Gemini.
 
This makes the bot work even when:
- No API key available
- Quota exhausted
- Offline mode needed
"""
 
import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
 
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)
 
 
def extract_tables(html: str) -> List[Dict[str, Any]]:
    """
    Extract all HTML tables as list of records.
    Works for Wikipedia tables, finance tables, comparison tables.
    Developer-built — no AI needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    all_records = []
 
    for table in soup.find_all("table"):
        try:
            # Get headers
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [
                    th.get_text(strip=True)
                    for th in header_row.find_all(["th", "td"])
                    if th.get_text(strip=True)
                ]
 
            if not headers:
                continue
 
            # Get data rows
            rows = table.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                values = [c.get_text(strip=True) for c in cells]
                if len(values) >= 2 and any(v for v in values):
                    record = {}
                    for i, header in enumerate(headers):
                        if i < len(values) and values[i]:
                            # Clean header name
                            key = re.sub(r'[^a-zA-Z0-9_]', '_', header.lower()).strip('_')
                            record[key] = values[i]
                    if record:
                        all_records.append(record)
 
        except Exception as e:
            logger.debug(f"[LocalExtractor] Table error: {e}")
 
    logger.info(f"[LocalExtractor] Extracted {len(all_records)} table records")
    return all_records
 
 
def extract_lists(html: str) -> List[Dict[str, Any]]:
    """
    Extract structured list items from HTML.
    Works for product listings, news headlines, job listings.
    Developer-built — no AI needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    records = []
 
    # Remove noise
    for tag in ["script", "style", "nav", "footer", "header"]:
        for el in soup.find_all(tag):
            el.decompose()
 
    # Find product-like items
    product_containers = soup.find_all(
        class_=re.compile(r"(product|item|card|listing|result|article|post|job)", re.I)
    )
 
    for container in product_containers[:50]:
        record = {}
 
        # Title/name
        title = (
            container.find(["h1", "h2", "h3", "h4"]) or
            container.find(class_=re.compile(r"(title|name|heading)", re.I))
        )
        if title:
            record["title"] = title.get_text(strip=True)
 
        # Price
        price = container.find(class_=re.compile(r"(price|cost|amount)", re.I))
        if not price:
            price_text = re.search(
                r'[£$€₹¥]\s*[\d,]+\.?\d*',
                container.get_text()
            )
            if price_text:
                record["price"] = price_text.group()
        else:
            record["price"] = price.get_text(strip=True)
 
        # Rating
        rating = container.find(class_=re.compile(r"(rating|star|score)", re.I))
        if rating:
            record["rating"] = rating.get_text(strip=True)
 
        # Description
        desc = container.find("p")
        if desc:
            record["description"] = desc.get_text(strip=True)[:200]
 
        # Link
        link = container.find("a")
        if link and link.get("href"):
            record["url"] = link.get("href")
 
        if len(record) >= 2:
            records.append(record)
 
    logger.info(f"[LocalExtractor] Extracted {len(records)} list records")
    return records
 
 
def extract_key_values(text: str) -> Dict[str, Any]:
    """
    Extract key-value pairs from plain text using regex patterns.
    Works for Wikipedia infoboxes, specification pages, data sheets.
    Developer-built — no AI needed.
    """
    result = {}
 
    # Price patterns
    prices = re.findall(r'[£$€₹¥]\s*[\d,]+\.?\d*', text)
    if prices:
        result["prices_found"] = prices[:5]
 
    # Date patterns
    dates = re.findall(
        r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|'
        r'(?:January|February|March|April|May|June|July|August|September|'
        r'October|November|December)\s+\d{1,2},?\s+\d{4})\b',
        text
    )
    if dates:
        result["dates_found"] = list(set(dates))[:5]
 
    # Email patterns
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if emails:
        result["emails"] = list(set(emails))
 
    # Phone patterns
    phones = re.findall(r'\b[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}\b', text)
    if phones:
        result["phones"] = list(set(phones))[:5]
 
    # Numbers with labels (e.g., "Revenue: $500 billion")
    labeled_numbers = re.findall(
        r'([A-Za-z][A-Za-z\s]{2,20}):\s*([£$€₹¥]?\s*[\d,\.]+\s*(?:billion|million|trillion|%)?)',
        text
    )
    for label, value in labeled_numbers[:10]:
        key = re.sub(r'\s+', '_', label.strip().lower())
        result[key] = value.strip()
 
    # URLs
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    if urls:
        result["urls_found"] = list(set(urls))[:5]
 
    return result
 
 
def extract_wikipedia_infobox(html: str) -> Dict[str, Any]:
    """
    Extract Wikipedia infobox data as key-value pairs.
    Works for any Wikipedia page — companies, people, places, things.
    Developer-built — no AI needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {}
 
    # Find infobox table
    infobox = soup.find("table", class_=re.compile(r"infobox", re.I))
    if not infobox:
        return result
 
    for row in infobox.find_all("tr"):
        try:
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if key and value and len(key) < 50:
                    clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key.lower()).strip('_')
                    result[clean_key] = value[:200]
        except Exception:
            pass
 
    logger.info(f"[LocalExtractor] Infobox extracted {len(result)} fields")
    return result
 
 
def smart_local_extract(html: str, url: str = "") -> List[Dict[str, Any]]:
    """
    Master local extraction — tries multiple strategies.
    Returns best results without any API calls.
 
    Strategy priority:
    1. Wikipedia infobox (for Wikipedia pages)
    2. HTML tables (for data-heavy pages)
    3. Structured list items (for listings/products)
 
    Developer-built — 100% local, zero API needed.
    """
    records = []
 
    # Strategy 1: Wikipedia infobox
    if "wikipedia.org" in url:
        infobox = extract_wikipedia_infobox(html)
        if infobox:
            records.append(infobox)
            logger.info(f"[LocalExtractor] Used infobox strategy: {len(records)} records")
            return records
 
    # Strategy 2: HTML tables
    table_records = extract_tables(html)
    if table_records:
        logger.info(f"[LocalExtractor] Used table strategy: {len(table_records)} records")
        return table_records
 
    # Strategy 3: Structured lists
    list_records = extract_lists(html)
    if list_records:
        logger.info(f"[LocalExtractor] Used list strategy: {len(list_records)} records")
        return list_records
 
    logger.info("[LocalExtractor] No structured data found")
    return []