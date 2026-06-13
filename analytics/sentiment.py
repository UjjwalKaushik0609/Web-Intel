"""
sentiment.py
------------
Developer-built: Sentiment analysis on scraped text content.
Uses TextBlob for fast rule-based sentiment scoring (no API needed).
AI (Gemini) provides deeper qualitative sentiment interpretation.
"""

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _get_textblob():
    """Lazy import TextBlob."""
    try:
        from textblob import TextBlob
        return TextBlob
    except ImportError:
        logger.error("TextBlob not installed. Run: pip install textblob")
        return None


def analyze_text_sentiment(text: str) -> dict:
    """
    Analyze sentiment of a single text string.

    Returns polarity (-1 to 1) and subjectivity (0 to 1).
    Developer-built: scoring logic and label mapping.

    Args:
        text: Input text string.

    Returns:
        Dict with polarity, subjectivity, label, and emoji.
    """
    TextBlob = _get_textblob()
    if not TextBlob or not text:
        return {"polarity": 0, "subjectivity": 0, "label": "neutral", "emoji": "😐"}

    try:
        blob = TextBlob(str(text))
        polarity = round(blob.sentiment.polarity, 4)
        subjectivity = round(blob.sentiment.subjectivity, 4)

        # Map polarity score to human-readable label
        if polarity >= 0.5:
            label, emoji = "very positive", "😄"
        elif polarity >= 0.1:
            label, emoji = "positive", "🙂"
        elif polarity <= -0.5:
            label, emoji = "very negative", "😠"
        elif polarity <= -0.1:
            label, emoji = "negative", "😞"
        else:
            label, emoji = "neutral", "😐"

        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "label": label,
            "emoji": emoji,
        }
    except Exception as e:
        logger.error(f"[Sentiment] Error analyzing text: {e}")
        return {"polarity": 0, "subjectivity": 0, "label": "neutral", "emoji": "😐"}


def analyze_dataframe_sentiment(
    df: pd.DataFrame,
    text_columns: Optional[list] = None,
) -> pd.DataFrame:
    """
    Add sentiment columns to a DataFrame for all text fields.

    Automatically detects text columns if not specified.
    Developer-built: column detection and batch processing.

    Args:
        df: Input DataFrame.
        text_columns: List of column names to analyze. Auto-detected if None.

    Returns:
        DataFrame with added sentiment columns.
    """
    if df.empty:
        return df

    result_df = df.copy()

    # Auto-detect text columns
    if text_columns is None:
        text_columns = [
            col for col in df.columns
            if df[col].dtype == object
            and df[col].str.len().mean() > 20  # Only columns with meaningful text length
        ]

    if not text_columns:
        logger.info("[Sentiment] No text columns found for sentiment analysis")
        return result_df

    for col in text_columns:
        logger.info(f"[Sentiment] Analyzing column: {col}")
        sentiments = df[col].fillna("").apply(
            lambda x: analyze_text_sentiment(str(x))
        )

        result_df[f"{col}_polarity"] = sentiments.apply(lambda x: x["polarity"])
        result_df[f"{col}_sentiment"] = sentiments.apply(lambda x: x["label"])

    return result_df


def get_sentiment_summary(df: pd.DataFrame) -> dict:
    """
    Compute overall sentiment distribution across all sentiment columns.

    Args:
        df: DataFrame with sentiment columns added by analyze_dataframe_sentiment.

    Returns:
        Summary dict with counts and percentages per sentiment label.
    """
    sentiment_cols = [col for col in df.columns if col.endswith("_sentiment")]

    if not sentiment_cols:
        return {}

    summary = {}
    for col in sentiment_cols:
        counts = df[col].value_counts().to_dict()
        total = len(df)
        summary[col] = {
            label: {
                "count": int(count),
                "percent": round(count / total * 100, 1)
            }
            for label, count in counts.items()
        }

    return summary


def analyze_page_sentiment(page_text: str) -> dict:
    """
    Full sentiment analysis of a scraped page.
    Splits text into sentences and scores each.

    Args:
        page_text: Full page text content.

    Returns:
        Dict with overall score, sentence breakdown, and key phrases.
    """
    TextBlob = _get_textblob()
    if not TextBlob or not page_text:
        return {}

    try:
        blob = TextBlob(page_text[:5000])  # Limit to first 5000 chars

        # Overall sentiment
        overall = analyze_text_sentiment(page_text[:5000])

        # Sentence-level breakdown — find most positive and negative
        sentence_scores = []
        for sentence in blob.sentences[:50]:  # Max 50 sentences
            score = sentence.sentiment.polarity
            sentence_scores.append({
                "text": str(sentence)[:100],
                "polarity": round(score, 3),
            })

        # Sort to find extremes
        sorted_sentences = sorted(sentence_scores, key=lambda x: x["polarity"])
        most_negative = sorted_sentences[:3] if sorted_sentences else []
        most_positive = sorted_sentences[-3:][::-1] if sorted_sentences else []

        return {
            "overall": overall,
            "sentence_count": len(sentence_scores),
            "most_positive_sentences": most_positive,
            "most_negative_sentences": most_negative,
            "average_polarity": round(
                sum(s["polarity"] for s in sentence_scores) / max(len(sentence_scores), 1), 4
            ),
        }

    except Exception as e:
        logger.error(f"[Sentiment] Page sentiment failed: {e}")
        return {}
