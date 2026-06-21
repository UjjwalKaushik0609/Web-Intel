"""
visualizer.py
-------------
Developer-built: Chart generation for the Analytics Agent tab.
FIX: All charts now use the SAME dark theme as the Power BI Dashboard
so text/labels are readable against the dark app background.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# ── DARK THEME (matches app/powerbi_dashboard.py) ─────────────────────────────
BG     = "#0f0e17"
CARD   = "#221f35"
BORDER = "#2d2a45"
TEXT   = "#e2e8f0"
SUB    = "#94a3b8"
DIM    = "#475569"
TEAL   = "#06b6d4"
PURPLE = "#a855f7"
PINK   = "#ec4899"
GREEN  = "#10b981"

PALETTE = [TEAL, PURPLE, PINK, GREEN, "#f59e0b", "#3b82f6", "#ef4444", "#8b5cf6"]

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=SUB, family="Inter, sans-serif", size=11),
    title_font=dict(color=TEXT, size=14),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)",
               tickfont=dict(color=DIM, size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)",
               tickfont=dict(color=DIM, size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=SUB, size=10)),
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor=CARD, font_color=TEXT, bordercolor=BORDER),
)


def plot_value_counts(df: pd.DataFrame, column: str, top_n: int = 15,
                      title: Optional[str] = None) -> go.Figure:
    try:
        counts = df[column].value_counts().head(top_n).reset_index()
        counts.columns = [column, "count"]
        fig = px.bar(counts, x=column, y="count",
            title=title or f"Top {top_n} — {column}",
            color="count",
            color_continuous_scale=[[0,TEAL],[1,PURPLE]],
            text="count")
        fig.update_traces(textposition="outside", textfont=dict(color=DIM))
        fig.update_layout(**DARK_LAYOUT, xaxis_tickangle=-45, showlegend=False)
        fig.update_coloraxes(showscale=False)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_value_counts: {e}")
        return go.Figure()


def plot_histogram(df: pd.DataFrame, column: str, bins: int = 20,
                   title: Optional[str] = None) -> go.Figure:
    try:
        fig = px.histogram(df, x=column, nbins=bins,
            title=title or f"Distribution of {column}",
            color_discrete_sequence=[TEAL], marginal="box")
        fig.update_layout(**DARK_LAYOUT, bargap=0.05)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_histogram: {e}")
        return go.Figure()


def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str,
                 color_col: Optional[str] = None, title: Optional[str] = None) -> go.Figure:
    try:
        # FIX: drop NaN and ensure no negative/invalid values before plotting
        plot_df = df[[c for c in [x_col, y_col, color_col] if c]].copy()
        plot_df = plot_df.dropna(subset=[x_col, y_col])
        if plot_df.empty:
            return go.Figure()

        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col,
            title=title or f"{x_col} vs {y_col}",
            color_discrete_sequence=PALETTE)
        fig.update_traces(marker=dict(line=dict(color=BG, width=1), opacity=0.85))
        fig.update_layout(**DARK_LAYOUT)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_scatter: {e}")
        return go.Figure()


def plot_pie(df: pd.DataFrame, column: str, top_n: int = 8,
            title: Optional[str] = None) -> go.Figure:
    try:
        counts = df[column].value_counts()
        if len(counts) > top_n:
            top = counts.head(top_n)
            top["Other"] = counts.iloc[top_n:].sum()
            counts = top
        fig = px.pie(values=counts.values, names=counts.index,
            title=title or f"Distribution of {column}",
            color_discrete_sequence=PALETTE, hole=0.45)
        fig.update_traces(textposition="outside", textfont=dict(color=TEXT, size=10),
            marker=dict(line=dict(color=BG, width=2)))
        fig.update_layout(**DARK_LAYOUT)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_pie: {e}")
        return go.Figure()


def plot_word_frequency(keywords: list, top_n: int = 20,
                        title: str = "Top Keywords") -> go.Figure:
    try:
        if not keywords: return go.Figure()
        df = pd.DataFrame(keywords[:top_n]).sort_values("count", ascending=True)
        fig = px.bar(df, x="count", y="word", orientation="h", title=title,
            color="count", color_continuous_scale=[[0,TEAL],[1,PURPLE]], text="count")
        fig.update_traces(textposition="outside", textfont=dict(color=DIM))
        # FIX: apply base layout first, then MERGE extra axis tweaks via
        # update_yaxes() instead of passing a second literal yaxis= kwarg
        # (passing yaxis twice — once inside **DARK_LAYOUT, once explicitly —
        # raised "got multiple values for keyword argument 'yaxis'", which
        # was silently caught and returned a blank chart)
        fig.update_layout(**DARK_LAYOUT, showlegend=False,
            height=max(400, len(df)*22))
        fig.update_yaxes(tickfont=dict(color=SUB, size=11))
        fig.update_coloraxes(showscale=False)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_word_frequency: {e}")
        return go.Figure()


def plot_sentiment_gauge(polarity: float, title: str = "Sentiment Score") -> go.Figure:
    try:
        bar_color = GREEN if polarity >= 0.1 else PINK if polarity <= -0.1 else "#f59e0b"
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=round(polarity, 3),
            title=dict(text=title, font=dict(color=TEXT, size=14)),
            number=dict(font=dict(color=bar_color, size=24)),
            delta=dict(reference=0, increasing=dict(color=GREEN), decreasing=dict(color=PINK)),
            gauge=dict(
                axis=dict(range=[-1,1], tickwidth=1, tickfont=dict(color=DIM)),
                bar=dict(color=bar_color),
                bgcolor=CARD, bordercolor=BORDER,
                threshold=dict(line=dict(color=TEXT, width=2), thickness=0.75, value=polarity),
            ),
        ))
        fig.update_layout(**DARK_LAYOUT, height=280)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_sentiment_gauge: {e}")
        return go.Figure()


def plot_correlation_heatmap(df: pd.DataFrame, title: str = "Correlation Matrix") -> go.Figure:
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2: return go.Figure()
        corr = numeric_df.corr()
        fig = px.imshow(corr, title=title,
            color_continuous_scale=[[0,PINK],[0.5,CARD],[1,TEAL]],
            zmin=-1, zmax=1, text_auto=".2f", aspect="auto")
        fig.update_traces(textfont=dict(color=TEXT, size=9))
        fig.update_layout(**DARK_LAYOUT)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_correlation_heatmap: {e}")
        return go.Figure()


def plot_missing_values(profile: dict, title: str = "Missing Values by Column") -> go.Figure:
    try:
        missing = profile.get("missing", {})
        if not missing: return go.Figure()
        data = [(c, m["percent"]) for c, m in missing.items() if m["percent"] > 0]
        if not data:
            fig = go.Figure()
            fig.update_layout(**DARK_LAYOUT, title="✅ No Missing Values Found")
            return fig
        data.sort(key=lambda x: x[1], reverse=True)
        cols, pcts = zip(*data)
        fig = px.bar(x=list(cols), y=list(pcts), title=title,
            labels={"x":"Column","y":"Missing %"},
            color=list(pcts), color_continuous_scale=[[0,GREEN],[1,PINK]],
            text=[f"{p:.1f}%" for p in pcts])
        fig.update_traces(textposition="outside", textfont=dict(color=DIM))
        fig.update_layout(**DARK_LAYOUT, showlegend=False)
        fig.update_coloraxes(showscale=False)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_missing_values: {e}")
        return go.Figure()


def plot_topic_distribution(topics: list, title: str = "Detected Topics") -> go.Figure:
    try:
        if not topics: return go.Figure()
        df = pd.DataFrame(topics).sort_values("confidence", ascending=True)
        fig = px.bar(df, x="confidence", y="topic", orientation="h", title=title,
            color="confidence", color_continuous_scale=[[0,TEAL],[1,PURPLE]],
            text=df["confidence"].apply(lambda x: f"{x:.1%}"))
        fig.update_traces(textposition="outside", textfont=dict(color=DIM))
        # FIX: same duplicate-key issue — 'xaxis' was passed both inside
        # **DARK_LAYOUT and again explicitly. Use update_xaxes() to merge.
        fig.update_layout(**DARK_LAYOUT, showlegend=False)
        fig.update_xaxes(tickformat=".0%")
        fig.update_coloraxes(showscale=False)
        return fig
    except Exception as e:
        logger.error(f"[Visualizer] plot_topic_distribution: {e}")
        return go.Figure()


def auto_visualize(df: pd.DataFrame) -> list:
    """Auto-select the most relevant charts — all dark-themed."""
    charts = []
    if df.empty: return charts

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.select_dtypes(include=["object"]).columns if df[c].nunique() <= 20]

    for col in numeric_cols[:3]:
        charts.append({"title": f"Distribution — {col}",
            "figure": plot_histogram(df, col), "type": "histogram"})

    for col in cat_cols[:2]:
        charts.append({"title": f"Top Values — {col}",
            "figure": plot_value_counts(df, col), "type": "bar"})

    if len(numeric_cols) >= 2:
        # FIX: drop NaN before scatter to avoid the marker-size crash
        valid_df = df[[numeric_cols[0], numeric_cols[1]]].dropna()
        if not valid_df.empty:
            charts.append({"title": f"Relationship — {numeric_cols[0]} vs {numeric_cols[1]}",
                "figure": plot_scatter(df, numeric_cols[0], numeric_cols[1]), "type": "scatter"})

    if len(numeric_cols) >= 3:
        charts.append({"title": "Correlation Matrix",
            "figure": plot_correlation_heatmap(df), "type": "heatmap"})

    if cat_cols:
        charts.append({"title": f"Composition — {cat_cols[0]}",
            "figure": plot_pie(df, cat_cols[0]), "type": "pie"})

    return charts