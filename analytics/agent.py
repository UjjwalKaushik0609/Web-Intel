"""
agent.py
--------
Developer-built: Autonomous Data Analytics & Data Science Agent.
Orchestrates EDA, sentiment, NLP, visualization, and AI interpretation.
This is the brain — it decides what analysis to run and in what order.
AI (Gemini) provides interpretation, insights, and recommendations.
Developer code does: profiling, stats, charts, NLP, sentiment scoring.
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
    Autonomous agent that:
    1. Profiles extracted data (developer-built EDA)
    2. Runs NLP analysis (developer-built)
    3. Scores sentiment (developer-built)
    4. Generates charts (developer-built)
    5. Asks Gemini to interpret everything (AI step)
    6. Produces a final actionable report (AI step)

    Think of this as: Developer = the analyst doing the work,
    Gemini = the senior consultant writing the executive summary.
    """

    def __init__(self, gemini_client=None):
        """
        Initialize the agent.

        Args:
            gemini_client: Optional GeminiClient. Lazy-loaded if not provided.
        """
        self._client = gemini_client
        logger.info("[AnalyticsAgent] Initialized")

    def _get_client(self):
        """Lazy-load Gemini client."""
        if self._client is None:
            from ai_engine.client import get_client
            self._client = get_client()
        return self._client

    def analyze_dataframe(self, df: pd.DataFrame, url: str = "", content_type: str = "") -> dict:
        """
        Full autonomous analysis of an extracted DataFrame.

        Pipeline:
        1. EDA profile (developer)
        2. Data type detection (developer)
        3. Correlation analysis (developer)
        4. Auto chart generation (developer)
        5. AI interpretation of all findings (Gemini)

        Args:
            df: Extracted data as DataFrame.
            url: Source URL for context.
            content_type: Type of data (product, job, article, etc.)

        Returns:
            Full analysis result dict with profile, charts, and AI insights.
        """
        logger.info(f"[AnalyticsAgent] Starting DataFrame analysis ({df.shape[0]} rows × {df.shape[1]} cols)")

        result = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "profile": {},
            "semantic_types": {},
            "correlations": {},
            "charts": [],
            "ai_insights": "",
            "recommendations": "",
            "data_quality_score": 0,
        }

        # Step 1: EDA Profile — developer built
        logger.info("[AnalyticsAgent] Step 1: Running EDA profile...")
        profile = profile_dataframe(df)
        result["profile"] = profile

        # Step 2: Semantic type detection — developer built
        logger.info("[AnalyticsAgent] Step 2: Detecting semantic types...")
        result["semantic_types"] = detect_data_types(df)

        # Step 3: Correlations — developer built
        logger.info("[AnalyticsAgent] Step 3: Computing correlations...")
        result["correlations"] = compute_correlations(df)

        # Step 4: Data quality score — developer built
        result["data_quality_score"] = self._compute_quality_score(profile)

        # Step 5: Auto charts — developer built
        logger.info("[AnalyticsAgent] Step 4: Generating charts...")
        result["charts"] = auto_visualize(df)

        # Step 6: Missing value chart
        result["missing_chart"] = plot_missing_values(profile)

        # Step 7: AI interprets the findings — Gemini runs here
        logger.info("[AnalyticsAgent] Step 5: Asking Gemini to interpret findings...")
        result["ai_insights"] = self._get_ai_insights(profile, result["semantic_types"],
                                                       result["correlations"], url, content_type)

        # Step 8: AI recommendations — Gemini runs here
        result["recommendations"] = self._get_ai_recommendations(profile, df, content_type)

        logger.info("[AnalyticsAgent] DataFrame analysis complete")
        return result

    def analyze_text_content(self, text: str, url: str = "") -> dict:
        """
        Full autonomous analysis of scraped page text.

        Pipeline:
        1. Keyword extraction (developer)
        2. Bigram extraction (developer)
        3. Named entity recognition (developer)
        4. Topic detection (developer)
        5. Sentiment analysis (developer)
        6. Charts (developer)
        7. AI interpretation (Gemini)

        Args:
            text: Cleaned page text content.
            url: Source URL.

        Returns:
            Full text analysis result dict.
        """
        logger.info(f"[AnalyticsAgent] Starting text analysis ({len(text)} chars)")

        result = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "keywords": [],
            "bigrams": [],
            "entities": {},
            "topics": [],
            "sentiment": {},
            "charts": [],
            "ai_insights": "",
        }

        # Step 1: Keywords — developer built
        result["keywords"] = extract_keywords(text, top_n=25)

        # Step 2: Bigrams — developer built
        result["bigrams"] = extract_bigrams(text, top_n=10)

        # Step 3: Named entities — developer built
        result["entities"] = extract_named_entities(text)

        # Step 4: Topics — developer built
        result["topics"] = detect_topics(text)

        # Step 5: Sentiment — developer built
        result["sentiment"] = analyze_page_sentiment(text)

        # Step 6: Charts — developer built
        if result["keywords"]:
            result["charts"].append({
                "title": "Top Keywords",
                "figure": plot_word_frequency(result["keywords"], title="Top Keywords"),
                "type": "keywords",
            })

        if result["sentiment"] and result["sentiment"].get("overall"):
            polarity = result["sentiment"]["overall"].get("polarity", 0)
            result["charts"].append({
                "title": "Sentiment Score",
                "figure": plot_sentiment_gauge(polarity),
                "type": "sentiment",
            })

        if result["topics"]:
            result["charts"].append({
                "title": "Detected Topics",
                "figure": plot_topic_distribution(result["topics"]),
                "type": "topics",
            })

        # Step 7: AI interprets everything — Gemini runs here
        result["ai_insights"] = self._get_text_ai_insights(result, url)

        logger.info("[AnalyticsAgent] Text analysis complete")
        return result

    def _compute_quality_score(self, profile: dict) -> int:
        """
        Compute a 0-100 data quality score based on:
        - Missing value percentage
        - Duplicate count
        - Number of columns with data

        Developer-built: scoring algorithm.
        """
        score = 100
        rows = profile.get("shape", {}).get("rows", 1)

        # Penalize for missing values
        missing = profile.get("missing", {})
        if missing:
            avg_missing = sum(v["percent"] for v in missing.values()) / max(len(missing), 1)
            score -= min(40, avg_missing * 1.5)

        # Penalize for duplicates
        duplicates = profile.get("duplicates", 0)
        dup_pct = (duplicates / max(rows, 1)) * 100
        score -= min(30, dup_pct)

        return max(0, int(score))

    def _get_ai_insights(self, profile: dict, semantic_types: dict,
                          correlations: dict, url: str, content_type: str) -> str:
        """
        Ask Gemini to interpret EDA findings.
        AI runs here — Gemini reads stats and writes human insights.
        """
        try:
            profile_summary = {
                "rows": profile.get("shape", {}).get("rows"),
                "columns": profile.get("shape", {}).get("columns"),
                "missing_summary": {
                    col: f"{v['percent']}% missing"
                    for col, v in profile.get("missing", {}).items()
                    if v["percent"] > 0
                },
                "numeric_stats": profile.get("numeric_stats", {}),
                "top_categories": {
                    col: stats.get("top_values", {})
                    for col, stats in profile.get("categorical_stats", {}).items()
                },
                "duplicates": profile.get("duplicates", 0),
            }

            prompt = f"""You are a senior data analyst. Analyze this dataset profile and provide insights.

Data Source: {url or 'web scrape'}
Content Type: {content_type or 'general'}
Semantic Column Types: {json.dumps(semantic_types, indent=2)}

Dataset Profile:
{json.dumps(profile_summary, indent=2)}

Correlations found:
{json.dumps(correlations.get('pairs', [])[:5], indent=2)}

Write a concise data analysis report with:
1. **Dataset Overview** — what kind of data is this, key characteristics
2. **Key Findings** — 3-5 most interesting patterns or insights from the stats
3. **Data Quality Issues** — any missing values, anomalies, or concerns
4. **Interesting Correlations** — explain any significant relationships found

Keep it under 300 words. Be specific, reference actual numbers from the profile."""

            return self._get_client().generate(prompt)

        except Exception as e:
            logger.error(f"[AnalyticsAgent] AI insights failed: {e}")
            return "AI insights unavailable. Check your Gemini API key."

    def _get_ai_recommendations(self, profile: dict, df: pd.DataFrame, content_type: str) -> str:
        """
        Ask Gemini for actionable recommendations based on the data.
        AI runs here — Gemini generates business recommendations.
        """
        try:
            numeric_stats = profile.get("numeric_stats", {})
            categorical_stats = profile.get("categorical_stats", {})

            prompt = f"""You are a data science consultant. Based on this scraped dataset analysis,
provide actionable business recommendations.

Content Type: {content_type or 'general web data'}
Rows: {df.shape[0]}, Columns: {df.shape[1]}
Numeric columns: {list(numeric_stats.keys())}
Categorical columns: {list(categorical_stats.keys())}

Key stats:
{json.dumps(numeric_stats, indent=2)[:1000]}

Provide exactly 4 specific, actionable recommendations for:
1. How to use this data for business decisions
2. What additional data to collect
3. What analysis to run next
4. Any data quality improvements needed

Format as a numbered list. Be specific and practical."""

            return self._get_client().generate(prompt)

        except Exception as e:
            logger.error(f"[AnalyticsAgent] AI recommendations failed: {e}")
            return "Recommendations unavailable."

    def _get_text_ai_insights(self, analysis: dict, url: str) -> str:
        """
        Ask Gemini to interpret NLP and sentiment findings.
        AI runs here — Gemini synthesizes text analytics into narrative.
        """
        try:
            top_keywords = [k["word"] for k in analysis.get("keywords", [])[:10]]
            topics = [t["topic"] for t in analysis.get("topics", [])[:3]]
            sentiment = analysis.get("sentiment", {}).get("overall", {})
            entities = analysis.get("entities", {})
            bigrams = [b["phrase"] for b in analysis.get("bigrams", [])[:5]]

            prompt = f"""You are a content analyst. Analyze these NLP findings from a scraped web page.

Source: {url or 'web page'}
Word count: {analysis.get('word_count', 0)}

Top keywords: {', '.join(top_keywords)}
Top phrases: {', '.join(bigrams)}
Detected topics: {', '.join(topics)}
Overall sentiment: {sentiment.get('label', 'neutral')} (polarity: {sentiment.get('polarity', 0)})
Named entities found: {json.dumps({k: len(v) if isinstance(v, list) else v for k, v in entities.items()}, indent=2)}

Write a brief content analysis report covering:
1. **Content Summary** — what is this page mainly about
2. **Tone & Sentiment** — how does the content feel, who is the audience
3. **Key Themes** — main topics and themes detected
4. **Notable Entities** — important names, dates, or data points found

Keep it under 200 words. Be insightful and specific."""

            return self._get_client().generate(prompt)

        except Exception as e:
            logger.error(f"[AnalyticsAgent] Text AI insights failed: {e}")
            return "Text insights unavailable."

    def quick_stats(self, df: pd.DataFrame) -> dict:
        """
        Fast stats summary without AI — for instant display while AI loads.
        Entirely developer-built — no API calls.

        Args:
            df: Input DataFrame.

        Returns:
            Quick stats dict.
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_cols": len(numeric_cols),
            "text_cols": len(df.select_dtypes(include=["object"]).columns),
            "missing_pct": round(df.isna().sum().sum() / max(df.size, 1) * 100, 1),
            "duplicates": int(df.duplicated().sum()),
        }

        for col in numeric_cols[:3]:
            stats[f"{col}_mean"] = round(float(df[col].mean()), 2)
            stats[f"{col}_min"] = round(float(df[col].min()), 2)
            stats[f"{col}_max"] = round(float(df[col].max()), 2)

        return stats
