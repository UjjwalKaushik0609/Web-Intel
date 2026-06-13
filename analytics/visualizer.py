"""
visualizer.py
-------------
Developer-built: Chart generation using Plotly for interactive visualizations.
Creates bar charts, histograms, scatter plots, pie charts, word frequency charts.
All charts are returned as Plotly figures ready for Streamlit's st.plotly_chart().
No AI involved — pure data visualization logic.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# Consistent color palette across all charts
COLOR_PALETTE = px.colors.qualitative.Set2
PRIMARY_COLOR = "#667eea"
SECONDARY_COLOR = "#764ba2"


def plot_value_counts(
    df: pd.DataFrame,
    column: str,
    top_n: int = 15,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Bar chart of top N value counts for a categorical column.

    Args:
        df: Input DataFrame.
        column: Column name to plot.
        top_n: Number of top categories to show.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        counts = df[column].value_counts().head(top_n).reset_index()
        counts.columns = [column, "count"]

        fig = px.bar(
            counts,
            x=column,
            y="count",
            title=title or f"Top {top_n} Values — {column}",
            color="count",
            color_continuous_scale=["#667eea", "#764ba2"],
            text="count",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12),
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_value_counts failed: {e}")
        return go.Figure()


def plot_histogram(
    df: pd.DataFrame,
    column: str,
    bins: int = 20,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Histogram for a numeric column showing distribution.

    Args:
        df: Input DataFrame.
        column: Numeric column to plot.
        bins: Number of histogram bins.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        fig = px.histogram(
            df,
            x=column,
            nbins=bins,
            title=title or f"Distribution of {column}",
            color_discrete_sequence=[PRIMARY_COLOR],
            marginal="box",  # Add box plot on top
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            bargap=0.05,
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_histogram failed: {e}")
        return go.Figure()


def plot_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Scatter plot to show relationship between two numeric columns.

    Args:
        df: Input DataFrame.
        x_col: X-axis column.
        y_col: Y-axis column.
        color_col: Optional column to color points by.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title or f"{x_col} vs {y_col}",
            trendline="ols",  # Add regression line
            color_discrete_sequence=COLOR_PALETTE,
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_scatter failed: {e}")
        return go.Figure()


def plot_pie(
    df: pd.DataFrame,
    column: str,
    top_n: int = 8,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Pie chart for categorical distribution.

    Args:
        df: Input DataFrame.
        column: Categorical column.
        top_n: Max slices (others grouped as 'Other').
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        counts = df[column].value_counts()
        if len(counts) > top_n:
            top = counts.head(top_n)
            other_count = counts.iloc[top_n:].sum()
            top["Other"] = other_count
            counts = top

        fig = px.pie(
            values=counts.values,
            names=counts.index,
            title=title or f"Distribution of {column}",
            color_discrete_sequence=COLOR_PALETTE,
            hole=0.3,  # Donut style
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(paper_bgcolor="white")
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_pie failed: {e}")
        return go.Figure()


def plot_word_frequency(keywords: list, top_n: int = 20, title: str = "Top Keywords") -> go.Figure:
    """
    Horizontal bar chart for word frequency / keywords.

    Args:
        keywords: List of dicts with 'word' and 'count' keys.
        top_n: Number of keywords to show.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        if not keywords:
            return go.Figure()

        df = pd.DataFrame(keywords[:top_n])
        df = df.sort_values("count", ascending=True)

        fig = px.bar(
            df,
            x="count",
            y="word",
            orientation="h",
            title=title,
            color="count",
            color_continuous_scale=["#667eea", "#764ba2"],
            text="count",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(tickfont=dict(size=11)),
            height=max(400, len(df) * 22),
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_word_frequency failed: {e}")
        return go.Figure()


def plot_sentiment_gauge(polarity: float, title: str = "Sentiment Score") -> go.Figure:
    """
    Gauge chart showing sentiment polarity (-1 to 1).

    Args:
        polarity: Sentiment polarity score (-1 to 1).
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        # Map -1..1 to 0..100 for gauge
        gauge_value = (polarity + 1) * 50

        if polarity >= 0.1:
            bar_color = "#2ecc71"
        elif polarity <= -0.1:
            bar_color = "#e74c3c"
        else:
            bar_color = "#f39c12"

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=round(polarity, 3),
            title={"text": title, "font": {"size": 16}},
            delta={"reference": 0, "increasing": {"color": "#2ecc71"}},
            gauge={
                "axis": {"range": [-1, 1], "tickwidth": 1},
                "bar": {"color": bar_color},
                "steps": [
                    {"range": [-1, -0.1], "color": "#fadbd8"},
                    {"range": [-0.1, 0.1], "color": "#fef9e7"},
                    {"range": [0.1, 1], "color": "#d5f5e3"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 2},
                    "thickness": 0.75,
                    "value": polarity,
                },
            },
        ))
        fig.update_layout(
            paper_bgcolor="white",
            height=300,
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_sentiment_gauge failed: {e}")
        return go.Figure()


def plot_correlation_heatmap(df: pd.DataFrame, title: str = "Correlation Matrix") -> go.Figure:
    """
    Heatmap of correlations between numeric columns.

    Args:
        df: Input DataFrame.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return go.Figure()

        corr = numeric_df.corr()

        fig = px.imshow(
            corr,
            title=title,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            text_auto=".2f",
            aspect="auto",
        )
        fig.update_layout(
            paper_bgcolor="white",
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_correlation_heatmap failed: {e}")
        return go.Figure()


def plot_missing_values(profile: dict, title: str = "Missing Values by Column") -> go.Figure:
    """
    Bar chart showing missing value percentage per column.

    Args:
        profile: EDA profile dict from eda.profile_dataframe().
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        missing = profile.get("missing", {})
        if not missing:
            return go.Figure()

        cols = list(missing.keys())
        percents = [missing[c]["percent"] for c in cols]

        # Only show columns with missing values
        data = [(c, p) for c, p in zip(cols, percents) if p > 0]
        if not data:
            fig = go.Figure()
            fig.update_layout(
                title="✅ No Missing Values Found",
                paper_bgcolor="white",
            )
            return fig

        data.sort(key=lambda x: x[1], reverse=True)
        cols_filtered, percents_filtered = zip(*data)

        fig = px.bar(
            x=list(cols_filtered),
            y=list(percents_filtered),
            title=title,
            labels={"x": "Column", "y": "Missing %"},
            color=list(percents_filtered),
            color_continuous_scale=["#2ecc71", "#e74c3c"],
            text=[f"{p:.1f}%" for p in percents_filtered],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_missing_values failed: {e}")
        return go.Figure()


def plot_topic_distribution(topics: list, title: str = "Detected Topics") -> go.Figure:
    """
    Horizontal bar chart for detected topics and their confidence scores.

    Args:
        topics: List of dicts with 'topic' and 'confidence' keys.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    try:
        if not topics:
            return go.Figure()

        df = pd.DataFrame(topics)
        df = df.sort_values("confidence", ascending=True)

        fig = px.bar(
            df,
            x="confidence",
            y="topic",
            orientation="h",
            title=title,
            color="confidence",
            color_continuous_scale=["#667eea", "#764ba2"],
            text=df["confidence"].apply(lambda x: f"{x:.1%}"),
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            xaxis=dict(tickformat=".0%"),
        )
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_topic_distribution failed: {e}")
        return go.Figure()


def auto_visualize(df: pd.DataFrame) -> list:
    """
    Automatically generate the most relevant charts for any DataFrame.
    Developer-built: smart chart selection based on column types and cardinality.

    Args:
        df: Input DataFrame.

    Returns:
        List of dicts with 'title' and 'figure' keys.
    """
    charts = []
    if df.empty:
        return charts

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [
        col for col in df.select_dtypes(include=["object"]).columns
        if df[col].nunique() <= 20  # Only low-cardinality categoricals
    ]

    # Chart 1: Distribution for each numeric column
    for col in numeric_cols[:3]:
        charts.append({
            "title": f"Distribution — {col}",
            "figure": plot_histogram(df, col),
            "type": "histogram",
        })

    # Chart 2: Value counts for categorical columns
    for col in cat_cols[:2]:
        charts.append({
            "title": f"Top Values — {col}",
            "figure": plot_value_counts(df, col),
            "type": "bar",
        })

    # Chart 3: Scatter for first two numeric columns
    if len(numeric_cols) >= 2:
        charts.append({
            "title": f"Relationship — {numeric_cols[0]} vs {numeric_cols[1]}",
            "figure": plot_scatter(df, numeric_cols[0], numeric_cols[1]),
            "type": "scatter",
        })

    # Chart 4: Correlation heatmap if 3+ numeric columns
    if len(numeric_cols) >= 3:
        charts.append({
            "title": "Correlation Matrix",
            "figure": plot_correlation_heatmap(df),
            "type": "heatmap",
        })

    # Chart 5: Pie for first categorical
    if cat_cols:
        charts.append({
            "title": f"Composition — {cat_cols[0]}",
            "figure": plot_pie(df, cat_cols[0]),
            "type": "pie",
        })

    return charts
