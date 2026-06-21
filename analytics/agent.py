"""
agent.py
--------
Developer-built: Autonomous Data Analytics & Data Science Agent.
SECURITY FIX: Accepts explicit api_key, passed through to a fresh
GeminiClient each time — no global state, no key leaking between sessions.
"""

import json
import logging
from typing import Optional

import pandas as pd

from analytics.eda import profile_dataframe, detect_data_types, compute_correlations
from analytics.sentiment import analyze_dataframe_sentiment, get_sentiment_summary, analyze_page_sentiment
from analytics.nlp import extract_keywords, extract_bigrams, extract_named_entities, detect_topics, word_frequency_dataframe
from analytics.visualizer import auto_visualize, plot_word_frequency, plot_sentiment_gauge, plot_missing_values, plot_topic_distribution

logger = logging.getLogger(__name__)


class DataAnalyticsAgent:
    """
    Autonomous agent — developer-built EDA/NLP/sentiment/charts,
    Gemini only used for the final narrative interpretation.
    """

    def __init__(self, gemini_client=None, api_key: Optional[str] = None):
        self._client = gemini_client
        self.api_key = api_key   # session-scoped, never global
        logger.info("[AnalyticsAgent] Initialized")

    def _get_client(self):
        if self._client is None:
            from ai_engine.client import get_client
            self._client = get_client(api_key=self.api_key)
        return self._client

    def analyze_dataframe(self, df: pd.DataFrame, url: str = "", content_type: str = "") -> dict:
        logger.info(f"[AnalyticsAgent] Analyzing {df.shape[0]} rows × {df.shape[1]} cols")
        result = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "profile": {}, "semantic_types": {}, "correlations": {},
            "charts": [], "ai_insights": "", "recommendations": "",
            "data_quality_score": 0,
        }
        profile = profile_dataframe(df)
        result["profile"] = profile
        result["semantic_types"] = detect_data_types(df)
        result["correlations"] = compute_correlations(df)
        result["data_quality_score"] = self._quality_score(profile)
        result["charts"] = auto_visualize(df)
        result["missing_chart"] = plot_missing_values(profile)
        result["ai_insights"] = self._ai_insights(profile, result["semantic_types"],
                                                   result["correlations"], url, content_type)
        result["recommendations"] = self._ai_recommendations(profile, df, content_type)
        return result

    def analyze_text_content(self, text: str, url: str = "") -> dict:
        result = {
            "text_length": len(text), "word_count": len(text.split()),
            "keywords": [], "bigrams": [], "entities": {}, "topics": [],
            "sentiment": {}, "charts": [], "ai_insights": "",
        }
        result["keywords"] = extract_keywords(text, top_n=25)
        result["bigrams"] = extract_bigrams(text, top_n=10)
        result["entities"] = extract_named_entities(text)
        result["topics"] = detect_topics(text)
        result["sentiment"] = analyze_page_sentiment(text)

        if result["keywords"]:
            result["charts"].append({"title":"Top Keywords",
                "figure": plot_word_frequency(result["keywords"], title="Top Keywords"),
                "type":"keywords"})
        if result["sentiment"].get("overall"):
            pol = result["sentiment"]["overall"].get("polarity", 0)
            result["charts"].append({"title":"Sentiment Score",
                "figure": plot_sentiment_gauge(pol), "type":"sentiment"})
        if result["topics"]:
            result["charts"].append({"title":"Detected Topics",
                "figure": plot_topic_distribution(result["topics"]), "type":"topics"})

        result["ai_insights"] = self._text_ai_insights(result, url)
        return result

    def _quality_score(self, profile):
        score = 100
        rows = profile.get("shape", {}).get("rows", 1)
        missing = profile.get("missing", {})
        if missing:
            avg_missing = sum(v["percent"] for v in missing.values()) / max(len(missing),1)
            score -= min(40, avg_missing * 1.5)
        dup_pct = (profile.get("duplicates",0) / max(rows,1)) * 100
        score -= min(30, dup_pct)
        return max(0, int(score))

    def _ai_insights(self, profile, semantic_types, correlations, url, content_type):
        try:
            summary = {
                "rows": profile.get("shape",{}).get("rows"),
                "columns": profile.get("shape",{}).get("columns"),
                "missing_summary": {c:f"{v['percent']}% missing" for c,v in profile.get("missing",{}).items() if v["percent"]>0},
                "numeric_stats": profile.get("numeric_stats",{}),
                "top_categories": {c:s.get("top_values",{}) for c,s in profile.get("categorical_stats",{}).items()},
                "duplicates": profile.get("duplicates",0),
            }
            prompt = f"""You are a senior data analyst. Analyze this dataset profile.

Source: {url or 'web scrape'} | Type: {content_type or 'general'}
Semantic types: {json.dumps(semantic_types, indent=2)}
Profile: {json.dumps(summary, indent=2)}
Correlations: {json.dumps(correlations.get('pairs',[])[:5], indent=2)}

Write a concise report:
1. Dataset Overview  2. Key Findings (3-5)  3. Data Quality Issues  4. Interesting Correlations
Under 300 words, reference real numbers."""
            return self._get_client().generate(prompt)
        except Exception as e:
            logger.error(f"[AnalyticsAgent] AI insights failed: {e}")
            return "AI insights unavailable."

    def _ai_recommendations(self, profile, df, content_type):
        try:
            prompt = f"""You are a data consultant. Based on this dataset, give 4 actionable recommendations.

Type: {content_type or 'general'} | Rows: {df.shape[0]} | Cols: {df.shape[1]}
Numeric: {list(profile.get('numeric_stats',{}).keys())}
Stats: {json.dumps(profile.get('numeric_stats',{}), indent=2)[:1000]}

1. How to use this data for business decisions
2. What additional data to collect
3. What analysis to run next
4. Data quality improvements needed
Be specific and practical."""
            return self._get_client().generate(prompt)
        except Exception as e:
            logger.error(f"[AnalyticsAgent] Recommendations failed: {e}")
            return "Recommendations unavailable."

    def _text_ai_insights(self, analysis, url):
        try:
            top_kw = [k["word"] for k in analysis.get("keywords",[])[:10]]
            topics = [t["topic"] for t in analysis.get("topics",[])[:3]]
            sent = analysis.get("sentiment",{}).get("overall",{})
            prompt = f"""Analyze NLP findings from a scraped page.
Source: {url} | Words: {analysis.get('word_count',0)}
Keywords: {', '.join(top_kw)} | Topics: {', '.join(topics)}
Sentiment: {sent.get('label','neutral')} ({sent.get('polarity',0)})

Write: 1. Content Summary 2. Tone & Sentiment 3. Key Themes 4. Notable Entities
Under 200 words."""
            return self._get_client().generate(prompt)
        except Exception as e:
            logger.error(f"[AnalyticsAgent] Text insights failed: {e}")
            return "Text insights unavailable."

    def quick_stats(self, df: pd.DataFrame) -> dict:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        stats = {
            "rows": len(df), "columns": len(df.columns),
            "numeric_cols": len(numeric_cols),
            "text_cols": len(df.select_dtypes(include=["object"]).columns),
            "missing_pct": round(df.isna().sum().sum() / max(df.size,1) * 100, 1),
            "duplicates": int(df.duplicated().sum()),
        }
        for col in numeric_cols[:3]:
            stats[f"{col}_mean"] = round(float(df[col].mean()), 2)
        return stats