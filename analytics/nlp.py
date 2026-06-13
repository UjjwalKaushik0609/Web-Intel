"""
nlp.py
------
Developer-built: NLP utilities — keyword extraction, word frequency,
named entity recognition, and topic detection.
No AI API needed — uses rule-based and statistical NLP.
"""

import re
import logging
from collections import Counter
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Common English stopwords to filter out
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "this", "that", "these", "those", "it", "its",
    "we", "you", "he", "she", "they", "i", "my", "your", "our", "their",
    "what", "which", "who", "when", "where", "how", "not", "no", "as", "if",
    "so", "than", "then", "more", "also", "about", "up", "out", "into",
    "can", "all", "one", "some", "any", "each", "s", "t", "re", "ll", "ve",
}


def extract_keywords(text: str, top_n: int = 20, min_length: int = 3) -> list:
    """
    Extract top keywords by frequency, excluding stopwords.

    Developer-built: tokenization, stopword filtering, frequency ranking.

    Args:
        text: Input text.
        top_n: Number of top keywords to return.
        min_length: Minimum word length to include.

    Returns:
        List of dicts with word and count.
    """
    if not text:
        return []

    # Tokenize — lowercase, letters only
    words = re.findall(r"\b[a-zA-Z]{%d,}\b" % min_length, text.lower())

    # Filter stopwords
    filtered = [w for w in words if w not in STOPWORDS]

    # Count frequency
    counter = Counter(filtered)
    top_words = counter.most_common(top_n)

    return [{"word": word, "count": count} for word, count in top_words]


def extract_bigrams(text: str, top_n: int = 10) -> list:
    """
    Extract most common two-word phrases (bigrams).

    Args:
        text: Input text.
        top_n: Number of top bigrams to return.

    Returns:
        List of dicts with phrase and count.
    """
    if not text:
        return []

    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]

    bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered) - 1)]
    counter = Counter(bigrams)

    return [{"phrase": phrase, "count": count} for phrase, count in counter.most_common(top_n)]


def extract_numbers(text: str) -> dict:
    """
    Extract all numbers, prices, and percentages from text.

    Args:
        text: Input text.

    Returns:
        Dict with prices, percentages, and plain numbers found.
    """
    prices = re.findall(r"[$£€¥₹]\s*[\d,]+\.?\d*", text)
    percentages = re.findall(r"\d+\.?\d*\s*%", text)
    plain_numbers = re.findall(r"\b\d+\.?\d*\b", text)

    return {
        "prices": prices[:20],
        "percentages": percentages[:20],
        "numbers": [float(n) for n in plain_numbers[:50] if float(n) < 1e9],
    }


def extract_named_entities(text: str) -> dict:
    """
    Simple rule-based named entity extraction.
    Detects: emails, URLs, phone numbers, dates, capitalized names.

    Developer-built: regex pattern matching — no ML needed.

    Args:
        text: Input text.

    Returns:
        Dict with detected entity lists.
    """
    entities = {}

    # Email addresses
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    if emails:
        entities["emails"] = list(set(emails))

    # URLs
    urls = re.findall(r"https?://[^\s<>\"{}|\\^`\[\]]+", text)
    if urls:
        entities["urls"] = list(set(urls))[:10]

    # Phone numbers (basic patterns)
    phones = re.findall(r"\b[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}\b", text)
    if phones:
        entities["phones"] = list(set(phones))

    # Dates (various formats)
    dates = re.findall(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
        text, re.IGNORECASE
    )
    if dates:
        entities["dates"] = list(set(dates))[:10]

    # Capitalized multi-word phrases (likely proper nouns/names)
    proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
    if proper_nouns:
        counter = Counter(proper_nouns)
        entities["proper_nouns"] = [
            {"name": name, "count": count}
            for name, count in counter.most_common(10)
        ]

    return entities


def word_frequency_dataframe(text: str, top_n: int = 30) -> pd.DataFrame:
    """
    Create a DataFrame of word frequencies for visualization.

    Args:
        text: Input text.
        top_n: Number of top words.

    Returns:
        DataFrame with 'word' and 'count' columns.
    """
    keywords = extract_keywords(text, top_n=top_n)
    if not keywords:
        return pd.DataFrame(columns=["word", "count"])
    return pd.DataFrame(keywords)


def detect_topics(text: str) -> list:
    """
    Simple topic detection using keyword matching.
    Detects common domains: tech, finance, health, sports, politics, etc.

    Developer-built: keyword-based topic classifier.

    Args:
        text: Input text.

    Returns:
        List of detected topics with confidence scores.
    """
    topic_keywords = {
        "Technology": ["software", "app", "data", "ai", "machine learning", "python",
                      "cloud", "api", "developer", "code", "digital", "tech", "internet"],
        "Finance": ["price", "cost", "revenue", "profit", "market", "stock", "investment",
                   "financial", "economy", "budget", "tax", "bank", "money"],
        "Health": ["health", "medical", "doctor", "treatment", "disease", "patient",
                  "hospital", "medicine", "therapy", "wellness", "diet", "fitness"],
        "E-Commerce": ["product", "buy", "sell", "shop", "cart", "checkout", "order",
                      "delivery", "shipping", "discount", "review", "rating"],
        "News": ["report", "government", "policy", "election", "president", "minister",
                "parliament", "law", "court", "crime", "international"],
        "Education": ["learn", "course", "student", "university", "school", "training",
                     "education", "skill", "certificate", "degree", "teacher"],
        "Travel": ["hotel", "flight", "destination", "travel", "trip", "tour",
                  "booking", "vacation", "resort", "airport", "visa"],
    }

    text_lower = text.lower()
    word_count = max(len(text_lower.split()), 1)
    scores = []

    for topic, keywords in topic_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        score = round(matches / len(keywords), 3)
        if score > 0:
            scores.append({"topic": topic, "confidence": score, "matches": matches})

    scores.sort(key=lambda x: x["confidence"], reverse=True)
    return scores[:5]
