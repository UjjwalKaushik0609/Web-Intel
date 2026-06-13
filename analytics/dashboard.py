"""
dashboard.py
------------
Developer-built: Fully Automatic Power BI Style Dashboard.
Auto-detects best columns for each chart — zero manual config.
Dark theme matching Power BI. User selects which charts to show.
"""

import logging
from typing import Optional, List, Tuple

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

PBI_BG     = "#1a1a2e"
PBI_PANEL  = "#16213e"
PBI_BORDER = "#0f3460"
PBI_ACCENT = "#e94560"
PBI_BLUE   = "#533483"
PBI_TEAL   = "#05bfdb"
PBI_TEXT   = "#ffffff"
PBI_SUB    = "#a0a0b0"
PBI_GREEN  = "#00b09b"

PBI_COLORS = [
    "#05bfdb","#e94560","#7b2d8b","#00c9a7",
    "#f7971e","#2193b0","#c6426e","#6dd5fa",
    "#a8edea","#fed6e3","#f093fb","#4facfe",
]

DARK = dict(
    paper_bgcolor=PBI_PANEL, plot_bgcolor=PBI_PANEL,
    font=dict(color=PBI_TEXT, family="Segoe UI, Arial", size=11),
    title_font=dict(color=PBI_TEXT, size=13, family="Segoe UI Bold, Arial"),
    xaxis=dict(gridcolor="#2a2a4a", zerolinecolor="#2a2a4a",
               tickfont=dict(color=PBI_SUB, size=10)),
    yaxis=dict(gridcolor="#2a2a4a", zerolinecolor="#2a2a4a",
               tickfont=dict(color=PBI_SUB, size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=PBI_TEXT, size=10)),
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor=PBI_BORDER, font_color=PBI_TEXT),
)


def _best_numeric(df, prefer=None):
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric: return None
    prefer = prefer or ["revenue","price","profit","sales","value",
                        "amount","score","count","total","employees"]
    for p in prefer:
        for col in numeric:
            if p in col.lower(): return col
    return max(numeric, key=lambda c: df[c].std() if df[c].std()>0 else 0)


def _best_category(df, prefer=None, max_unique=30):
    cat_cols = [c for c in df.select_dtypes(include=["object"]).columns
                if 2 <= df[c].nunique() <= max_unique]
    if not cat_cols: return None
    prefer = prefer or ["industry","category","type","country","sector",
                        "name","company","region","status","author"]
    for p in prefer:
        for col in cat_cols:
            if p in col.lower(): return col
    return max(cat_cols, key=lambda c: -abs(df[c].nunique()-10))


def _best_label(df):
    for p in ["name","title","company","symbol","ticker","label"]:
        for col in df.select_dtypes(include=["object"]).columns:
            if p in col.lower(): return col
    text_cols = df.select_dtypes(include=["object"]).columns
    return max(text_cols, key=lambda c: df[c].nunique()) if len(text_cols)>0 else None


def _all_numeric(df): return df.select_dtypes(include=[np.number]).columns.tolist()
def _all_cat(df, mx=30):
    return [c for c in df.select_dtypes(include=["object"]).columns
            if df[c].nunique()<=mx]


def _bar_chart(df):
    cat = _best_category(df)
    num = _best_numeric(df)
    if not cat or not num: return go.Figure(), ""
    agg = df.groupby(cat)[num].sum().reset_index()
    agg = agg.sort_values(num, ascending=False).head(15)
    title = f"Top {len(agg)} — {num.replace('_',' ').title()} by {cat.replace('_',' ').title()}"
    fig = px.bar(agg, x=num, y=cat, orientation="h", title=title,
        color=num,
        color_continuous_scale=[[0,PBI_BLUE],[0.5,PBI_TEAL],[1,PBI_ACCENT]],
        text=num)
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside",
        textfont=dict(color=PBI_SUB, size=9))
    fig.update_layout(**DARK, height=max(320, len(agg)*28))
    fig.update_coloraxes(showscale=False)
    return fig, title


def _donut_chart(df):
    cat = _best_category(df)
    num = _best_numeric(df)
    if not cat: return go.Figure(), ""
    if num:
        agg = df.groupby(cat)[num].sum().reset_index()
        agg = agg.sort_values(num, ascending=False).head(10)
        labels, values = agg[cat], agg[num]
        title = f"{cat.replace('_',' ').title()} by {num.replace('_',' ').title()}"
    else:
        counts = df[cat].value_counts().head(10)
        labels, values = counts.index, counts.values
        title = f"{cat.replace('_',' ').title()} Distribution"
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=PBI_COLORS, line=dict(color=PBI_BG, width=2)),
        textfont=dict(color=PBI_TEXT, size=11),
        hovertemplate="<b>%{label}</b><br>%{value:,.1f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**DARK, title=title, height=360,
        annotations=[dict(text=f"<b>{len(labels)}</b><br>items",
            x=0.5, y=0.5, font=dict(size=14, color=PBI_TEXT), showarrow=False)])
    return fig, title


def _histogram_chart(df):
    num = _best_numeric(df)
    if not num: return go.Figure(), ""
    series = df[num].dropna()
    title = f"Distribution of {num.replace('_',' ').title()}"
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=series, nbinsx=25,
        marker=dict(color=PBI_TEAL, opacity=0.85, line=dict(color=PBI_BG, width=1)),
        hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>"))
    mean_v, med_v = series.mean(), series.median()
    fig.add_vline(x=mean_v, line_dash="dash", line_color=PBI_ACCENT, line_width=2,
        annotation_text=f"Mean: {mean_v:,.1f}",
        annotation_font_color=PBI_ACCENT, annotation_font_size=10)
    fig.add_vline(x=med_v, line_dash="dot", line_color=PBI_GREEN, line_width=2,
        annotation_text=f"Median: {med_v:,.1f}",
        annotation_font_color=PBI_GREEN, annotation_font_size=10)
    fig.update_layout(**DARK, title=title, height=320, showlegend=False)
    return fig, title


def _scatter_chart(df):
    nums = _all_numeric(df)
    if len(nums) < 2: return go.Figure(), ""
    x_col = _best_numeric(df, prefer=["revenue","price","sales","profit"])
    remaining = [c for c in nums if c!=x_col]
    y_col = _best_numeric(pd.DataFrame(df[remaining]),
        prefer=["profit","employees","score"]) if remaining else nums[1]
    label = _best_label(df)
    cat = _best_category(df)
    title = f"{x_col.replace('_',' ').title()} vs {y_col.replace('_',' ').title()}"
    fig = px.scatter(df, x=x_col, y=y_col, text=label if label else None,
        color=cat if cat else None, size=x_col, size_max=35, title=title,
        color_discrete_sequence=PBI_COLORS,
        hover_data=[label] if label else None)
    fig.update_traces(textposition="top center",
        textfont=dict(color=PBI_SUB, size=8),
        marker=dict(line=dict(color=PBI_BG, width=1), opacity=0.85))
    fig.update_layout(**DARK, height=400)
    return fig, title


def _treemap_chart(df):
    cat = _best_category(df)
    num = _best_numeric(df)
    if not cat or not num: return go.Figure(), ""
    plot_df = df[[cat,num]].dropna()
    plot_df = plot_df[plot_df[num]>0]
    title = f"{num.replace('_',' ').title()} Treemap by {cat.replace('_',' ').title()}"
    fig = px.treemap(plot_df, path=[cat], values=num, title=title,
        color=num,
        color_continuous_scale=[[0,PBI_BLUE],[0.5,PBI_TEAL],[1,PBI_ACCENT]])
    fig.update_traces(textfont=dict(color=PBI_TEXT, size=11),
        marker=dict(line=dict(color=PBI_BG, width=2)),
        hovertemplate="<b>%{label}</b><br>%{value:,.1f}<extra></extra>")
    fig.update_layout(**DARK, height=380)
    fig.update_coloraxes(showscale=False)
    return fig, title


def _heatmap_chart(df):
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2: return go.Figure(), ""
    corr = numeric_df.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=[c.replace('_',' ').title() for c in corr.columns],
        y=[c.replace('_',' ').title() for c in corr.columns],
        colorscale=[[0,PBI_ACCENT],[0.5,PBI_PANEL],[1,PBI_TEAL]],
        zmid=0, text=corr.values.round(2), texttemplate="%{text}",
        textfont=dict(color=PBI_TEXT, size=10),
        hovertemplate="%{x} × %{y}<br>r = %{z:.3f}<extra></extra>"))
    fig.update_layout(**DARK, title="Correlation Heatmap", height=380)
    return fig, "Correlation Heatmap"


def _waterfall_chart(df):
    cat = _best_label(df) or _best_category(df)
    num = _best_numeric(df)
    if not cat or not num: return go.Figure(), ""
    plot_df = df[[cat,num]].dropna().sort_values(num,ascending=False).head(10)
    title = f"Top {len(plot_df)} {cat.replace('_',' ').title()} by {num.replace('_',' ').title()}"
    fig = go.Figure(go.Waterfall(
        x=plot_df[cat].astype(str), y=plot_df[num],
        measure=["relative"]*len(plot_df),
        connector=dict(line=dict(color=PBI_BORDER, width=1)),
        increasing=dict(marker=dict(color=PBI_TEAL)),
        decreasing=dict(marker=dict(color=PBI_ACCENT)),
        text=[f"{v:,.0f}" for v in plot_df[num]],
        textposition="outside", textfont=dict(color=PBI_SUB, size=9)))
    fig.update_layout(**DARK, title=title, height=360, xaxis_tickangle=-30)
    return fig, title


def _stacked_bar_chart(df):
    cat = _best_category(df)
    nums = _all_numeric(df)[:4]
    if not cat or len(nums)<2: return go.Figure(), ""
    agg = df.groupby(cat)[nums].sum().reset_index()
    top = agg.assign(total=agg[nums].sum(axis=1))\
              .sort_values("total",ascending=False).head(12)
    fig = go.Figure()
    for i,num in enumerate(nums):
        fig.add_trace(go.Bar(name=num.replace("_"," ").title(),
            x=top[cat], y=top[num], marker_color=PBI_COLORS[i]))
    fig.update_layout(**DARK,
        title=f"Multi-Metric by {cat.replace('_',' ').title()}",
        barmode="stack", height=360, xaxis_tickangle=-35)
    return fig, f"Multi-Metric by {cat}"


def _box_plot(df):
    cat = _best_category(df)
    num = _best_numeric(df)
    if not cat or not num: return go.Figure(), ""
    title = f"{num.replace('_',' ').title()} by {cat.replace('_',' ').title()}"
    fig = px.box(df, x=cat, y=num, title=title, color=cat,
        color_discrete_sequence=PBI_COLORS, points="outliers")
    fig.update_layout(**DARK, height=360, showlegend=False, xaxis_tickangle=-35)
    return fig, title


AVAILABLE_CHARTS = {
    "📊 Bar Chart":           ("bar",       _bar_chart),
    "🍩 Donut Chart":         ("donut",     _donut_chart),
    "📉 Histogram":           ("histogram", _histogram_chart),
    "🔵 Scatter / Bubble":    ("scatter",   _scatter_chart),
    "🌳 Treemap":             ("treemap",   _treemap_chart),
    "🌡️ Correlation Heatmap": ("heatmap",   _heatmap_chart),
    "🌊 Waterfall Chart":     ("waterfall", _waterfall_chart),
    "📦 Stacked Bar":         ("stacked",   _stacked_bar_chart),
    "🎻 Box Plot":            ("box",       _box_plot),
}


def compute_kpis(df):
    kpis = []
    numeric_cols = _all_numeric(df)
    cat_cols = _all_cat(df)

    kpis.append({"label":"Total Records","value":f"{len(df):,}",
        "color":PBI_TEAL,"icon":"📋","sub":""})
    kpis.append({"label":"Data Columns","value":str(len(df.columns)),
        "color":PBI_BLUE,"icon":"📊","sub":""})

    for col in numeric_cols[:3]:
        total = df[col].sum()
        avg   = df[col].mean()
        is_money = any(p in col.lower() for p in ["revenue","price","profit","sales"])
        kpis.append({
            "label": f"Total {col.replace('_',' ').title()}",
            "value": f"{total:,.1f}",
            "sub":   f"Avg: {avg:,.1f}",
            "color": PBI_ACCENT if is_money else PBI_TEAL,
            "icon":  "💰" if is_money else "📈",
        })

    for col in cat_cols[:1]:
        kpis.append({"label":f"Unique {col.replace('_',' ').title()}",
            "value":str(df[col].nunique()),"color":PBI_GREEN,
            "icon":"🏷️","sub":""})

    return kpis[:6]


def auto_build_dashboard(df, selected_labels):
    """
    Build charts automatically — zero manual config.
    Each chart function auto-detects the best columns.
    """
    charts = []
    for label in selected_labels:
        if label not in AVAILABLE_CHARTS: continue
        chart_type, build_fn = AVAILABLE_CHARTS[label]
        try:
            fig, title = build_fn(df)
            if fig and fig.data:
                charts.append({"label":label,"title":title,
                    "figure":fig,"type":chart_type})
                logger.info(f"[Dashboard] Built: {label}")
            else:
                logger.warning(f"[Dashboard] Skipped {label} — no suitable columns")
        except Exception as e:
            logger.error(f"[Dashboard] Failed {label}: {e}")
    return charts


# Backward compat
def build_dashboard(df, selected_charts, chart_configs=None):
    return auto_build_dashboard(df, selected_charts)