"""
eda.py
------
Developer-built: Autonomous Exploratory Data Analysis engine.
Automatically profiles any dataset extracted by the scraper.
Detects data types, missing values, distributions, outliers, correlations.
AI (Gemini) then interprets the findings and writes a human-readable report.
"""

import logging
import json
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def _safe_json(obj):
    """Convert numpy types to Python native for JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    return obj


def profile_dataframe(df: pd.DataFrame) -> dict:
    """
    Auto-profile a DataFrame — shape, types, missing values,
    numeric stats, categorical stats, and duplicate count.

    Args:
        df: Input DataFrame from extracted scraper data.

    Returns:
        Profile dict with all stats.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}

    profile = {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "missing": {},
        "numeric_stats": {},
        "categorical_stats": {},
        "duplicates": int(df.duplicated().sum()),
        "sample_rows": df.head(3).to_dict(orient="records"),
    }

    # Missing value analysis
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        profile["missing"][col] = {
            "count": missing_count,
            "percent": round(missing_count / len(df) * 100, 2),
        }

    # Numeric column statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        profile["numeric_stats"][col] = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "q25": round(float(series.quantile(0.25)), 4),
            "q75": round(float(series.quantile(0.75)), 4),
            "skewness": round(float(series.skew()), 4),
            "outliers_iqr": int(_count_outliers_iqr(series)),
        }

    # Categorical column statistics
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        value_counts = series.value_counts()
        profile["categorical_stats"][col] = {
            "unique_count": int(series.nunique()),
            "top_values": {
                str(k): int(v)
                for k, v in value_counts.head(5).items()
            },
            "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
        }

    return profile


def _count_outliers_iqr(series: pd.Series) -> int:
    """Count outliers using the IQR method."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return int(((series < lower) | (series > upper)).sum())


def detect_data_types(df: pd.DataFrame) -> dict:
    """
    Intelligently detect semantic data types beyond pandas dtype.
    Detects: price, rating, date, URL, email, percentage, count.

    Args:
        df: Input DataFrame.

    Returns:
        Dict mapping column names to detected semantic types.
    """
    import re
    semantic_types = {}

    price_pattern = re.compile(r"price|cost|fee|amount|salary|wage", re.I)
    rating_pattern = re.compile(r"rating|score|stars|grade|rank", re.I)
    date_pattern = re.compile(r"date|time|posted|created|updated|published", re.I)
    url_pattern = re.compile(r"url|link|href|website", re.I)
    count_pattern = re.compile(r"count|number|qty|quantity|total|num_", re.I)
    name_pattern = re.compile(r"name|title|label|description|summary", re.I)

    for col in df.columns:
        col_lower = col.lower()
        if price_pattern.search(col_lower):
            semantic_types[col] = "price"
        elif rating_pattern.search(col_lower):
            semantic_types[col] = "rating"
        elif date_pattern.search(col_lower):
            semantic_types[col] = "date"
        elif url_pattern.search(col_lower):
            semantic_types[col] = "url"
        elif count_pattern.search(col_lower):
            semantic_types[col] = "count"
        elif name_pattern.search(col_lower):
            semantic_types[col] = "text"
        else:
            dtype = str(df[col].dtype)
            if "float" in dtype or "int" in dtype:
                semantic_types[col] = "numeric"
            else:
                semantic_types[col] = "categorical"

    return semantic_types


def compute_correlations(df: pd.DataFrame) -> dict:
    """
    Compute correlation matrix for numeric columns.

    Args:
        df: Input DataFrame.

    Returns:
        Dict with correlation pairs and strength labels.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {}

    corr_matrix = numeric_df.corr()
    correlations = []

    cols = corr_matrix.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if pd.isna(val):
                continue
            abs_val = abs(val)
            if abs_val >= 0.7:
                strength = "strong"
            elif abs_val >= 0.4:
                strength = "moderate"
            else:
                strength = "weak"

            correlations.append({
                "col1": cols[i],
                "col2": cols[j],
                "correlation": round(float(val), 4),
                "strength": strength,
                "direction": "positive" if val > 0 else "negative",
            })

    # Sort by absolute correlation descending
    correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return {"pairs": correlations}
