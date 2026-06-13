"""
powerbi_dashboard.py - Fixed version
Developer-built: Full Power BI Dashboard. No hex+alpha colors. No div leaks.
"""

import logging
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import re

logger = logging.getLogger(__name__)

BG     = "#0f0e17"
PANEL  = "#1a1830"
CARD   = "#221f35"
BORDER = "#2d2a45"
TEXT   = "#e2e8f0"
SUB    = "#94a3b8"
DIM    = "#475569"
TEAL   = "#06b6d4"
PURPLE = "#a855f7"
PINK   = "#ec4899"
GREEN  = "#10b981"
ORANGE = "#f59e0b"
BLUE   = "#3b82f6"
RED    = "#ef4444"

PAL = [TEAL, PURPLE, PINK, GREEN, ORANGE, BLUE, RED,
       "#8b5cf6", "#14b8a6", "#f97316", "#6366f1", "#84cc16"]

BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=SUB, family="Inter,sans-serif", size=11),
    title_font=dict(color=TEXT, size=13),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)",
               zerolinecolor="rgba(255,255,255,0.05)",
               tickfont=dict(color=DIM, size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)",
               zerolinecolor="rgba(255,255,255,0.05)",
               tickfont=dict(color=DIM, size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=SUB, size=10)),
    margin=dict(l=10, r=10, t=45, b=10),
    hoverlabel=dict(bgcolor=CARD, font_color=TEXT),
)


# ── AUTO CONVERT STRING NUMBERS ───────────────────────────────────────────────
def _convert_nums(df):
    df = df.copy()
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(20).astype(str)
        cleaned = sample.str.replace(r'[\$£€₹¥,\[\]\(\)\+\s]', '', regex=True)
        num_count = cleaned.str.match(r'^-?\d+\.?\d*$').sum()
        if num_count >= len(sample) * 0.6 and len(sample) > 0:
            df[col] = (df[col].astype(str)
                       .str.replace(r'[\$£€₹¥,\[\]\(\)\+]', '', regex=True)
                       .str.strip()
                       .str.extract(r'(-?\d+\.?\d*)', expand=False))
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _nums(df):  return df.select_dtypes(include=[np.number]).columns.tolist()
def _cats(df):  return [c for c in df.select_dtypes(include=["object"]).columns if 2 <= df[c].nunique() <= 25]

def _best_num(df, prefer=None):
    cols = _nums(df)
    if not cols: return None
    p = prefer or ["revenue","price","profit","sales","value","amount","total","score"]
    for w in p:
        for c in cols:
            if w in c.lower(): return c
    return max(cols, key=lambda c: df[c].std() if df[c].std() > 0 else 0)

def _best_cat(df):
    cols = _cats(df)
    if not cols: return None
    p = ["industry","category","type","country","sector","name","company","region"]
    for w in p:
        for c in cols:
            if w in c.lower(): return c
    return max(cols, key=lambda c: -abs(df[c].nunique() - 8))

def _best_label(df):
    for w in ["name","title","company","symbol","label"]:
        for c in df.select_dtypes(include=["object"]).columns:
            if w in c.lower(): return c
    t = df.select_dtypes(include=["object"]).columns
    return max(t, key=lambda c: df[c].nunique()) if len(t) > 0 else None


# ── CHARTS ────────────────────────────────────────────────────────────────────

def _area_line(df):
    nums = _nums(df); cat = _best_cat(df) or _best_label(df)
    if not nums or not cat: return None
    agg = df.groupby(cat)[nums[:3]].sum().reset_index().sort_values(nums[0], ascending=False).head(20)
    fig = go.Figure()
    for i, col in enumerate(nums[:3]):
        c = PAL[i]
        fig.add_trace(go.Scatter(x=agg[cat], y=agg[col],
            name=col.replace("_"," ").title(), mode="lines+markers",
            line=dict(color=c, width=2.5, shape="spline"),
            fill="tozeroy", fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08)",
            marker=dict(size=5, color=c)))
    fig.update_layout(**BASE, height=280, title="Trend Overview")
    return fig

def _bar_grouped(df):
    cat = _best_cat(df) or _best_label(df); nums = _nums(df)
    if not cat or not nums: return None
    agg = df.groupby(cat)[nums[:3]].sum().reset_index().sort_values(nums[0], ascending=False).head(12)
    fig = go.Figure()
    for i, col in enumerate(nums[:3]):
        fig.add_trace(go.Bar(name=col.replace("_"," ").title(),
            x=agg[cat], y=agg[col], marker=dict(color=PAL[i], opacity=0.9)))
    fig.update_layout(**BASE, barmode="group", height=280,
        title=f"Comparison by {cat.replace('_',' ').title()}", xaxis_tickangle=-30)
    return fig

def _donut(df, pinks=False):
    cat = _best_cat(df); num = _best_num(df)
    if not cat: return None
    cats = _cats(df)
    if pinks and len(cats) >= 2:
        cat = cats[1]
        colors = ["#ec4899","#f43f5e","#fb7185","#fda4af","#fecdd3","#ffe4e6"]
    else:
        colors = PAL
    if num and not pinks:
        agg = df.groupby(cat)[num].sum().reset_index().sort_values(num, ascending=False).head(8)
        labels, values = agg[cat], agg[num]
        title = f"{cat.replace('_',' ').title()} by {num.replace('_',' ').title()}"
    else:
        vc = df[cat].value_counts().head(8)
        labels, values = vc.index, vc.values
        title = f"{cat.replace('_',' ').title()} Breakdown"
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors[:len(labels)], line=dict(color=BG, width=3)),
        textfont=dict(color=TEXT, size=10), textposition="outside",
        hovertemplate="<b>%{label}</b><br>%{value:,.1f} (%{percent})<extra></extra>"))
    fig.update_layout(**BASE, title=title, height=300,
        annotations=[dict(text=f"<b>{len(labels)}</b><br><span style='font-size:10px'>items</span>",
            x=0.5, y=0.5, font=dict(size=14, color=TEXT), showarrow=False)])
    return fig

def _histogram(df):
    num = _best_num(df)
    if not num: return None
    series = df[num].dropna()
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=series, nbinsx=25,
        marker=dict(color=TEAL, opacity=0.8, line=dict(color=BG, width=1))))
    try:
        from numpy import linspace
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(series)
        xr = linspace(series.min(), series.max(), 200)
        fig.add_trace(go.Scatter(x=xr,
            y=kde(xr)*len(series)*(series.max()-series.min())/25,
            mode="lines", line=dict(color=PURPLE, width=2), name="KDE"))
    except Exception: pass
    mean_v, med_v = series.mean(), series.median()
    fig.add_vline(x=mean_v, line_dash="dash", line_color=PINK, line_width=1.5,
        annotation_text=f"Mean {mean_v:,.1f}", annotation_font_color=PINK, annotation_font_size=9)
    fig.add_vline(x=med_v, line_dash="dot", line_color=GREEN, line_width=1.5,
        annotation_text=f"Med {med_v:,.1f}", annotation_font_color=GREEN, annotation_font_size=9)
    fig.update_layout(**BASE, height=280,
        title=f"Distribution — {num.replace('_',' ').title()}", showlegend=False)
    return fig

def _scatter(df):
    nums = _nums(df)
    if len(nums) < 2: return None
    x = _best_num(df, prefer=["revenue","price","sales"])
    rem = [c for c in nums if c != x]; y = rem[0] if rem else nums[1]
    label = _best_label(df); cat = _best_cat(df)
    fig = px.scatter(df, x=x, y=y, size=x, size_max=40,
        color=cat if cat else None, text=label if label else None,
        color_discrete_sequence=PAL)
    fig.update_traces(textposition="top center", textfont=dict(color=DIM, size=8),
        marker=dict(line=dict(color=BG, width=1), opacity=0.85))
    fig.update_layout(**BASE, height=280,
        title=f"Bubble — {x.replace('_',' ').title()} vs {y.replace('_',' ').title()}")
    return fig

def _treemap(df):
    cat = _best_cat(df) or _best_label(df); num = _best_num(df)
    if not cat or not num: return None
    plot_df = df[[cat, num]].dropna(); plot_df = plot_df[plot_df[num] > 0]
    if plot_df.empty: return None
    fig = px.treemap(plot_df, path=[cat], values=num, color=num,
        color_continuous_scale=[[0,"#7c3aed"],[0.5,TEAL],[1,PINK]])
    fig.update_traces(textfont=dict(color=TEXT, size=11),
        marker=dict(line=dict(color=BG, width=2)))
    fig.update_layout(**BASE, height=280,
        title=f"Treemap — {num.replace('_',' ').title()}")
    fig.update_coloraxes(showscale=False)
    return fig

def _heatmap(df):
    nd = df.select_dtypes(include=[np.number])
    if nd.shape[1] < 2: return None
    corr = nd.corr()
    lbls = [c.replace("_"," ").title() for c in corr.columns]
    fig = go.Figure(go.Heatmap(z=corr.values, x=lbls, y=lbls,
        colorscale=[[0,PINK],[0.5,CARD],[1,TEAL]], zmid=0,
        text=corr.values.round(2), texttemplate="%{text}",
        textfont=dict(color=TEXT, size=9),
        hovertemplate="%{x} × %{y}<br>r = %{z:.3f}<extra></extra>"))
    fig.update_layout(**BASE, title="Correlation Heatmap", height=280)
    return fig

def _waterfall(df):
    cat = _best_label(df) or _best_cat(df); num = _best_num(df)
    if not cat or not num: return None
    plot_df = df[[cat,num]].dropna().sort_values(num, ascending=False).head(10)
    fig = go.Figure(go.Waterfall(x=plot_df[cat].astype(str), y=plot_df[num],
        measure=["relative"]*len(plot_df),
        connector=dict(line=dict(color=BORDER, width=1)),
        increasing=dict(marker=dict(color=TEAL)),
        decreasing=dict(marker=dict(color=PINK)),
        text=[f"{v:,.0f}" for v in plot_df[num]],
        textposition="outside", textfont=dict(color=DIM, size=9)))
    fig.update_layout(**BASE, height=280,
        title=f"Waterfall — Top {num.replace('_',' ').title()}", xaxis_tickangle=-30)
    return fig

def _box(df):
    cat = _best_cat(df); num = _best_num(df)
    if not cat or not num: return None
    fig = px.box(df, x=cat, y=num, color=cat,
        color_discrete_sequence=PAL, points="outliers")
    fig.update_layout(**BASE, height=280, showlegend=False, xaxis_tickangle=-30,
        title=f"Box — {num.replace('_',' ').title()}")
    return fig

def _stacked(df):
    cat = _best_cat(df); nums = _nums(df)[:4]
    if not cat or len(nums) < 2: return None
    agg = df.groupby(cat)[nums].sum().reset_index()
    top = agg.assign(t=agg[nums].sum(axis=1)).sort_values("t", ascending=False).head(10)
    fig = go.Figure()
    for i, col in enumerate(nums):
        fig.add_trace(go.Bar(name=col.replace("_"," ").title(),
            x=top[cat], y=top[col], marker_color=PAL[i]))
    fig.update_layout(**BASE, barmode="stack", height=280,
        title=f"Stacked by {cat.replace('_',' ').title()}", xaxis_tickangle=-30)
    return fig

def _funnel(df):
    num = _best_num(df); label = _best_label(df) or _best_cat(df)
    if not num or not label: return None
    plot_df = df[[label,num]].dropna().sort_values(num, ascending=False).head(8)
    fig = go.Figure(go.Funnel(y=plot_df[label].astype(str), x=plot_df[num],
        textinfo="value+percent total",
        marker=dict(color=PAL[:len(plot_df)], line=dict(color=BG, width=1)),
        textfont=dict(color=TEXT, size=10),
        connector=dict(line=dict(color=BORDER, width=1))))
    fig.update_layout(**BASE, height=280, title=f"Funnel — {num.replace('_',' ').title()}")
    return fig

def _gauges(df):
    nums = _nums(df)[:4]
    if not nums: return None
    specs = [[{"type": "indicator"}] * len(nums)]
    fig = make_subplots(rows=1, cols=len(nums), specs=specs)
    for i, col in enumerate(nums):
        val = float(df[col].mean())
        mx  = float(df[col].max())
        # Use only valid hex colors — NO alpha suffix
        bar_colors = [TEAL, PURPLE, PINK, GREEN]
        clr = bar_colors[i % len(bar_colors)]
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            title=dict(text=col.replace("_"," ").title(),
                       font=dict(color=SUB, size=10)),
            number=dict(font=dict(color=clr, size=18), valueformat=",.1f"),
            gauge=dict(
                axis=dict(range=[0, mx], tickfont=dict(color=DIM, size=8)),
                bar=dict(color=clr, thickness=0.7),
                bgcolor=CARD,
                bordercolor=BORDER,
                # NO steps with alpha colors — removed to fix error
            ),
        ), row=1, col=i+1)
    fig.update_layout(**BASE, height=200, title="Average Metrics")
    return fig


# ── PANEL HELPERS ─────────────────────────────────────────────────────────────
def _phdr(title, badge):
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER};'
        f'border-radius:14px 14px 0 0;padding:.6rem 1rem;'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="color:{TEXT};font-size:.9rem;font-weight:600;">{title}</span>'
        f'<span style="background:rgba(124,58,237,.2);color:{PURPLE};'
        f'font-size:.7rem;padding:2px 8px;border-radius:10px;">{badge}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

def _pbody(fig, key):
    if fig and fig.data:
        st.markdown(
            f'<div style="background:{CARD};border:1px solid {BORDER};'
            f'border-top:none;border-radius:0 0 14px 14px;padding:.3rem;">',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig, use_container_width=True, key=key)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{CARD};border:1px solid {BORDER};'
            f'border-top:none;border-radius:0 0 14px 14px;padding:.8rem;'
            f'text-align:center;color:{DIM};font-size:.8rem;">'
            f'⚠️ Not enough data for this chart</div>',
            unsafe_allow_html=True
        )


# ── KPI CARDS ─────────────────────────────────────────────────────────────────
def _kpis(df):
    nums = _nums(df); cats = _cats(df)
    items = [("📋", "Total Records",  f"{len(df):,}",       TEAL,   ""),
             ("📊", "Columns",        str(len(df.columns)), PURPLE, "")]
    for col in nums[:4]:
        total = df[col].sum(); avg = df[col].mean(); mx = df[col].max()
        is_m = any(p in col.lower() for p in ["revenue","price","profit","sales","amount"])
        items.append(("💰" if is_m else "📈",
                      col.replace("_"," ").title(),
                      f"{total:,.0f}",
                      PINK if is_m else TEAL,
                      f"Avg {avg:,.1f}"))
    for col in cats[:1]:
        items.append(("🏷️", f"Unique {col.replace('_',' ').title()}",
                      str(df[col].nunique()), GREEN, ""))
    items = items[:8]
    cols = st.columns(len(items))
    for i, (icon, label, val, color, sub) in enumerate(items):
        with cols[i]:
            st.markdown(
                f'<div style="background:{CARD};border:1px solid {BORDER};'
                f'border-radius:14px;padding:.9rem 1rem;text-align:center;">'
                f'<div style="font-size:1.4rem;">{icon}</div>'
                f'<div style="font-size:1.7rem;font-weight:700;color:{color};line-height:1.1;">{val}</div>'
                f'<div style="font-size:.7rem;color:{DIM};text-transform:uppercase;'
                f'letter-spacing:.06em;margin-top:4px;">{label}</div>'
                f'<div style="font-size:.7rem;color:{PURPLE};margin-top:2px;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# ── SUMMARY TABLE ─────────────────────────────────────────────────────────────
def _table(df, n=10):
    nums = _nums(df); cat = _best_cat(df) or _best_label(df)
    if not cat: return
    if nums:
        agg = df.groupby(cat)[nums[:4]].sum().reset_index()
        agg = agg.sort_values(nums[0], ascending=False).head(n)
        cols = [cat] + nums[:4]
    else:
        agg = df.head(n); cols = df.columns[:5].tolist()

    th = "".join(
        f'<th style="background:{PANEL};color:{SUB};padding:.4rem .7rem;'
        f'font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;'
        f'border-bottom:1px solid {BORDER};">{c.replace("_"," ").title()}</th>'
        for c in cols
    )
    rows_html = ""
    for _, row in agg.iterrows():
        tds = ""
        for col in cols:
            val = row[col]
            try:    tds += f'<td style="padding:.4rem .7rem;font-size:.82rem;color:{TEXT};border-bottom:1px solid rgba(255,255,255,.03);">{float(val):,.1f}</td>'
            except: tds += f'<td style="padding:.4rem .7rem;font-size:.82rem;color:{TEXT};border-bottom:1px solid rgba(255,255,255,.03);">{val}</td>'
        rows_html += f"<tr>{tds}</tr>"

    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True
    )


# ── MAIN RENDER ───────────────────────────────────────────────────────────────
def render_dashboard(df: pd.DataFrame, source_url: str = ""):
    """Full Power BI dashboard — auto-detects all chart types."""
    df   = _convert_nums(df)
    nums = _nums(df)
    cats = _cats(df)

    # Top bar — NO nested divs, single clean string
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{PANEL},{CARD});'
        f'border:1px solid {BORDER};border-radius:14px;padding:1rem 1.5rem;'
        f'margin-bottom:1.2rem;display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<div style="color:{TEXT};font-size:1.2rem;font-weight:700;">📈 Analytics Dashboard</div>'
        f'<div style="color:{DIM};font-size:.8rem;margin-top:2px;">'
        f'{len(df):,} records · {len(df.columns)} columns · '
        f'{len(nums)} numeric · {len(cats)} categorical</div>'
        f'</div>'
        f'<span style="background:rgba(16,185,129,.15);color:#10b981;'
        f'padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:600;">'
        f'🟢 LIVE DATA</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # KPI cards
    _kpis(df)
    st.markdown("<br>", unsafe_allow_html=True)

    # Gauges
    if len(nums) >= 2:
        _phdr("⏱️ Average Metrics Overview", "Gauges")
        _pbody(_gauges(df), "gauges")
        st.markdown("<br>", unsafe_allow_html=True)

    # Row 1
    c1, c2 = st.columns([2, 1])
    with c1: _phdr("📈 Trend Overview", "Area Line"); _pbody(_area_line(df), "area")
    with c2: _phdr("🍩 Composition", "Donut");        _pbody(_donut(df), "donut1")
    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2
    c1, c2, c3 = st.columns([1.5, 1.2, 1])
    with c1: _phdr("📊 Grouped Comparison", "Bar");       _pbody(_bar_grouped(df), "bar")
    with c2: _phdr("📉 Distribution", "Histogram");       _pbody(_histogram(df), "hist")
    with c3: _phdr("🍩 Breakdown", "Donut");              _pbody(_donut(df, pinks=True), "donut2")
    st.markdown("<br>", unsafe_allow_html=True)

    # Row 3
    c1, c2 = st.columns(2)
    with c1: _phdr("🔵 Bubble Analysis", "Scatter");  _pbody(_scatter(df), "scatter")
    with c2: _phdr("🌳 Treemap", "Hierarchy");         _pbody(_treemap(df), "treemap")
    st.markdown("<br>", unsafe_allow_html=True)

    # Row 4
    if len(nums) >= 2:
        c1, c2 = st.columns(2)
        with c1: _phdr("🌡️ Correlations", "Heatmap");   _pbody(_heatmap(df), "heat")
        with c2: _phdr("🌊 Waterfall", "Contribution");  _pbody(_waterfall(df), "wfall")
        st.markdown("<br>", unsafe_allow_html=True)

    # Row 5
    c1, c2, c3 = st.columns(3)
    with c1: _phdr("🎻 Distribution", "Box Plot");  _pbody(_box(df), "box")
    with c2: _phdr("📦 Stacked", "100% Bar");       _pbody(_stacked(df), "stacked")
    with c3: _phdr("🔻 Funnel", "Top Values");      _pbody(_funnel(df), "funnel")
    st.markdown("<br>", unsafe_allow_html=True)

    # Summary table
    _phdr("📋 Top Records Summary", "Table")
    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER};'
        f'border-top:none;border-radius:0 0 14px 14px;padding:.8rem;">',
        unsafe_allow_html=True
    )
    _table(df)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Downloads
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name="dashboard_data.csv", mime="text/csv")
    with d2:
        st.download_button("⬇️ Download JSON",
            data=df.to_json(orient="records", indent=2),
            file_name="dashboard_data.json", mime="application/json")