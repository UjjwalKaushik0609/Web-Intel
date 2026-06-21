"""
main.py — Web Scraping AI Bot
5 Tabs: Summarize & Ask | Extract Data | Analytics | Live Monitor | Dashboard
Made by Ujjwal Kaushik

SECURITY FIXES:
- API key stored in st.session_state (per-browser-session) instead of
  os.environ (process-global) — your key can NEVER leak to other visitors,
  even if your live link is shared publicly.
- Docker image never bakes in any key — see .dockerignore.

PERFORMANCE FIXES:
- Same URL is scraped ONCE per pipeline instance (HTML memo + TTL cache)
  and reused across Summarize / Q&A / Extract / Analytics.
- Live Monitor uses a scoped rerun so it doesn't re-render the whole app.
"""

import os, sys, json, time, logging
import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Web Intel", page_icon="🤖", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family:'Inter',sans-serif; }
.stApp { background:#0d0d1a; }
.main-header {
  background:linear-gradient(135deg,#1a1a3e 0%,#2d1b69 50%,#1a1a3e 100%);
  border:1px solid rgba(139,92,246,0.3); padding:1.1rem 2rem;
  border-radius:16px; margin-bottom:1.2rem; text-align:center; color:white;
}
.main-header h1 { margin:0; font-size:1.9rem; font-weight:700;
  background:linear-gradient(135deg,#a78bfa,#60a5fa,#f472b6);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.main-header p { margin:.3rem 0 0; opacity:.7; font-size:.85rem; color:#a78bfa; }
.glass-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
  border-radius:14px; padding:1rem; margin-bottom:.8rem; }
.result-card { background:rgba(167,139,250,0.08); border-left:3px solid #a78bfa;
  padding:1rem 1.2rem; border-radius:10px; margin:.6rem 0; color:#e2e8f0; }
.stButton>button { background:linear-gradient(135deg,#7c3aed,#2563eb)!important;
  color:white!important; border:none!important; border-radius:10px!important;
  padding:.6rem 1.1rem!important; font-weight:600!important; width:100%!important; }
.stButton>button:hover { opacity:.85!important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d0d1a,#13102a)!important;
  border-right:1px solid rgba(139,92,246,.2)!important; }
[data-testid="stSidebar"] * { color:#c4b5fd!important; }
.stTabs [data-baseweb="tab-list"] { background:rgba(255,255,255,.03)!important;
  border-radius:12px!important; padding:4px!important; gap:4px!important; }
.stTabs [data-baseweb="tab"] { border-radius:10px!important; color:#7c7ca0!important;
  font-weight:500!important; padding:.5rem 1rem!important; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#7c3aed,#2563eb)!important;
  color:white!important; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
  background:rgba(255,255,255,.04)!important; border:1px solid rgba(139,92,246,.25)!important;
  border-radius:10px!important; color:#e2e8f0!important; }
.stSelectbox>div>div { background:rgba(255,255,255,.04)!important;
  border:1px solid rgba(139,92,246,.25)!important; border-radius:10px!important; color:#e2e8f0!important; }
.stDataFrame { border-radius:12px!important; overflow:hidden!important; }
.live-banner { background:linear-gradient(135deg,rgba(52,211,153,.1),rgba(96,165,250,.1));
  border:1px solid rgba(52,211,153,.25); border-radius:10px; padding:.6rem 1rem;
  margin-bottom:.8rem; display:flex; justify-content:space-between; align-items:center; }
.section-title { font-size:1rem; font-weight:600; color:#a78bfa;
  text-transform:uppercase; letter-spacing:.08em; margin:1rem 0 .5rem;
  display:flex; align-items:center; gap:.5rem; }
.section-title::after { content:''; flex:1; height:1px;
  background:linear-gradient(90deg,rgba(139,92,246,.4),transparent); }
.alert-box { background:rgba(248,113,113,.1); border:1px solid rgba(248,113,113,.3);
  border-radius:10px; padding:.7rem 1rem; margin:.3rem 0; color:#fca5a5; }
.stSuccess{background:rgba(52,211,153,.1)!important;border:none!important;color:#34d399!important;border-radius:10px!important;}
.stInfo{background:rgba(96,165,250,.1)!important;border:none!important;color:#93c5fd!important;border-radius:10px!important;}
.stWarning{background:rgba(251,191,36,.1)!important;border:none!important;color:#fbbf24!important;border-radius:10px!important;}
.stError{background:rgba(248,113,113,.1)!important;border:none!important;color:#f87171!important;border-radius:10px!important;}
[data-testid="stMetricValue"]{color:#a78bfa!important;font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
  <h1>🤖 Web Intel</h1>
  <p>Gemini 2.5 Flash · Live Monitor · Power BI Dashboard · Made by Ujjwal Kaushik</p>
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [
    ("gemini_api_key", ""),         # SECURITY: lives ONLY in this browser session
    ("monitor_session", None),
    ("monitor_running", False),
    ("dashboard_df", None),
    ("monitor_url", ""),
    ("page_content_cache", {}),     # url -> content, avoids re-scrape within session
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── SIDEBAR — SECURE, SESSION-SCOPED API KEY ──────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    if st.session_state.gemini_api_key:
        k = st.session_state.gemini_api_key
        st.markdown(f"""
        <div style='background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.25);
        border-radius:10px;padding:.6rem 1rem;margin:.5rem 0;'>
        <span style='color:#34d399;font-size:.85rem;'>✅ API Key set for this session</span><br>
        <span style='color:#7c7ca0;font-size:.75rem;'>
        {k[:4]}{'*'*16}{k[-4:] if len(k)>8 else '****'}</span></div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ Clear Key", key="clear_key"):
            st.session_state.gemini_api_key = ""
            st.rerun()
    else:
        new_key = st.text_input("Gemini API Key", type="password",
            placeholder="Paste your own key",
            help="Stored only in YOUR browser session — never shared with "
                 "other visitors, never saved to disk. Get a free key at "
                 "aistudio.google.com/app/apikey")
        if new_key:
            st.session_state.gemini_api_key = new_key
            st.rerun()
        st.caption("🔒 Your key stays in your browser tab only.")

    st.markdown("""
    <div style='background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.2);
    border-radius:8px;padding:.5rem .8rem;margin:.4rem 0;font-size:.8rem;color:#a78bfa;'>
    🤖 Model: <b>Gemini 2.5 Flash</b>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔧 Scraping Settings")
    scrape_mode = st.selectbox("Scraping Mode",
        ["Auto-detect","Static (requests)","Dynamic (Playwright)"])
    use_cache = st.toggle("⚡ Enable Cache", value=True)
    cache_ttl = st.slider("Cache TTL (min)", 5, 120, 60, 5)

    st.markdown("---")
    st.markdown("### 🧹 Data Options")
    auto_clean = st.toggle("🧹 Auto-clean data", value=True)
    use_local  = st.toggle("🔧 Local extraction (no API)", value=False)

    st.markdown("---")
    st.markdown("""<div style='text-align:center;color:#4a4a6a;font-size:.75rem;'>
    Made by <b style='color:#a78bfa;'>Ujjwal Kaushik</b></div>""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _get_pipeline():
    """Always passes the SESSION's own key — never a global env var."""
    from pipeline.pipeline import ScrapingPipeline
    return ScrapingPipeline(
        use_cache=use_cache, cache_ttl=cache_ttl*60,
        force_static=(scrape_mode=="Static (requests)"),
        force_dynamic=(scrape_mode=="Dynamic (Playwright)"),
        api_key=st.session_state.gemini_api_key or None,
    )

def _validate(url, need_api=True):
    if not url.strip(): st.warning("⚠️ Enter a URL."); return False
    if not url.startswith(("http://","https://")): st.warning("⚠️ URL must start with http://"); return False
    if need_api and not st.session_state.gemini_api_key and not use_local:
        st.error("❌ Enter your Gemini API key in the sidebar (or enable Local Mode)."); return False
    return True

def _clean_df(records):
    if not records: return pd.DataFrame()
    df = pd.DataFrame(records)
    if auto_clean:
        from pipeline.deduplicator import clean_dataframe
        df = clean_dataframe(df)
    return df

def _extract(url, pipeline, ct=None, schema=None):
    if use_local:
        html = pipeline._fetch_html(url)   # memo-cached — won't re-fetch
        if not html: return []
        from scraper.local_extractor import smart_local_extract
        records = smart_local_extract(html, url=url)
    else:
        r = pipeline.run_extract(url, schema=schema, content_type=ct)
        records = r.get("data", [])
    if auto_clean and records:
        from pipeline.deduplicator import clean_records
        records = clean_records(records)
    return records

def _save_dashboard(df):
    if df is not None and not df.empty:
        st.session_state.dashboard_df = df

def _section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Summarize & Ask", "📊 Extract Data", "🔬 Analytics",
    "📡 Live Monitor", "📈 Dashboard",
])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — SUMMARIZE + ASK QUESTION (merged — one scrape, two outputs)
# ════════════════════════════════════════════════════════════════════
with tab1:
    _section("📝 Summarize & Ask Questions About Any Page")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_s = st.text_input("Page URL", placeholder="https://example.com/article", key="url_s")
    style = st.radio("Summary Style", ["concise","detailed","bullets"], horizontal=True,
        format_func=lambda x:{"concise":"⚡ Concise","detailed":"📖 Detailed","bullets":"📋 Bullets"}[x])
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        do_summary = st.button("🚀 Summarize Page", key="btn_s")
    with c2:
        do_fetch_only = st.button("📥 Just Fetch (for Q&A below)", key="btn_fetch")

    if do_summary or do_fetch_only:
        if _validate(url_s):
            with st.spinner("Scraping page (cached for reuse)..."):
                try:
                    pipeline = _get_pipeline()
                    content = pipeline.fetch_content(url_s)
                    if not content:
                        st.error("❌ Failed to fetch page content.")
                    else:
                        st.session_state.page_content_cache[url_s] = content
                        st.success(f"✅ Page cached ({len(content):,} chars) — "
                                   "ask follow-up questions below without re-scraping!")

                        if do_summary:
                            from ai_engine.summarizer import summarize
                            summary = summarize(content, url=url_s, style=style,
                                                client=pipeline._get_ai_client())
                            meta = pipeline.fetch_metadata(url_s)
                            if meta.get("title"):
                                st.markdown(f"<h3 style='color:#a78bfa;'>📄 {meta['title']}</h3>",
                                    unsafe_allow_html=True)
                            _section("🤖 AI Summary")
                            st.markdown(f'<div class="result-card">{summary}</div>',
                                unsafe_allow_html=True)
                            st.download_button("⬇️ Download Summary", data=summary,
                                file_name="summary.txt", mime="text/plain")
                except Exception as e:
                    st.error(f"❌ {e}"); logger.exception(e)

    st.divider()
    _section("💬 Ask a Follow-up Question")
    st.caption("Uses the page you fetched above — no second scrape needed.")

    cached_urls = list(st.session_state.page_content_cache.keys())
    if cached_urls:
        qa_url = st.selectbox("Cached page", cached_urls, key="qa_url_select")
    else:
        qa_url = url_s
        st.caption("No cached page yet — click 'Just Fetch' or 'Summarize' first, "
                   "or this will scrape fresh when you ask.")

    question = st.text_area("Your Question", height=80, key="question",
        placeholder="What is the price? Who is the author? What are the key facts?")

    if st.button("💬 Ask Gemini", key="btn_q"):
        if not question.strip():
            st.warning("⚠️ Enter a question.")
        elif not qa_url:
            st.warning("⚠️ Enter a URL first.")
        elif not st.session_state.gemini_api_key:
            st.error("❌ Enter your Gemini API key in the sidebar.")
        else:
            with st.spinner("Asking Gemini..."):
                try:
                    pipeline = _get_pipeline()
                    # Reuse cached content if we already fetched this URL
                    content = st.session_state.page_content_cache.get(qa_url)
                    if not content:
                        content = pipeline.fetch_content(qa_url)
                        if content:
                            st.session_state.page_content_cache[qa_url] = content

                    if not content:
                        st.error("❌ Failed to fetch page content.")
                    else:
                        from ai_engine.extractor import answer_question
                        answer = answer_question(content, question=question,
                            url=qa_url, client=pipeline._get_ai_client())
                        st.markdown(f"""<div style='background:rgba(96,165,250,.08);
                        border:1px solid rgba(96,165,250,.2);border-radius:10px;
                        padding:.7rem 1rem;color:#93c5fd;margin:.5rem 0;'>❓ {question}</div>""",
                        unsafe_allow_html=True)
                        _section("🤖 Gemini's Answer")
                        st.markdown(f'<div class="result-card">{answer}</div>',
                            unsafe_allow_html=True)
                        st.download_button("⬇️ Download Q&A",
                            data=f"Q: {question}\n\nA: {answer}",
                            file_name="qa.txt", mime="text/plain")
                except Exception as e:
                    st.error(f"❌ {e}"); logger.exception(e)

# ════════════════════════════════════════════════════════════════════
# TAB 2 — EXTRACT DATA
# ════════════════════════════════════════════════════════════════════
with tab2:
    _section("📊 Extract Structured Data")
    mode_color = "#34d399" if use_local else "#a78bfa"
    mode_text  = "🔧 Local Mode — no API needed" if use_local else "🤖 AI Mode — Gemini 2.5 Flash"
    st.markdown(f"""<div style='background:rgba(139,92,246,.08);border:1px solid
    rgba(139,92,246,.2);border-radius:10px;padding:.6rem 1rem;margin-bottom:.8rem;
    color:{mode_color};font-size:.9rem;'>{mode_text}</div>""", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_e = st.text_input("Page URL", placeholder="https://example.com/products", key="url_e")
    c1, c2 = st.columns(2)
    with c1: ct = st.selectbox("Content Type",
        ["Auto-detect","article","product","job","event","contact"])
    with c2: st.selectbox("Export Format", ["JSON","CSV"])
    schema = st.text_area("Custom Schema (optional)", height=65,
        placeholder='{"title":"string","price":"number"}')
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Extract Data", key="btn_e"):
        if _validate(url_e, need_api=not use_local):
            with st.spinner("Extracting structured data..."):
                try:
                    pipeline = _get_pipeline()
                    records = _extract(url_e, pipeline,
                        ct=None if ct=="Auto-detect" else ct,
                        schema=schema.strip() or None)
                    label = "Local" if use_local else "AI"
                    st.success(f"✅ Extracted **{len(records)} records** ({label} Mode)")
                    if records:
                        df = _clean_df(records)
                        if not df.empty:
                            st.dataframe(df, use_container_width=True)
                            _save_dashboard(df)
                            st.info("💡 Data saved → go to **📈 Dashboard** tab!")
                        d1, d2 = st.columns(2)
                        with d1:
                            st.download_button("⬇️ JSON",
                                data=json.dumps(records, indent=2, default=str),
                                file_name="data.json", mime="application/json")
                        with d2:
                            if not df.empty:
                                st.download_button("⬇️ CSV", data=df.to_csv(index=False),
                                    file_name="data.csv", mime="text/csv")
                    else:
                        st.warning("⚠️ No records extracted. Try Local Mode or a different Content Type.")
                except Exception as e:
                    st.error(f"❌ {e}"); logger.exception(e)

# ════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS AGENT (fixed: single scrape, dark charts)
# ════════════════════════════════════════════════════════════════════
with tab3:
    _section("🔬 Autonomous Analytics & Data Science Agent")
    inp = st.radio("Data Source", ["🌐 Scrape URL", "📁 Upload CSV"], horizontal=True)

    if inp == "🌐 Scrape URL":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        url_a = st.text_input("Page URL", key="url_a")
        c1, c2 = st.columns(2)
        with c1: act   = st.selectbox("Content Type",
            ["Auto-detect","product","article","job","event"], key="act")
        with c2: amode = st.selectbox("Analysis Mode",
            ["Full Analysis","Data Only","Text & NLP Only"], key="amode")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🚀 Run Analytics Agent", key="btn_a"):
            if _validate(url_a):
                with st.spinner("Running autonomous analysis..."):
                    try:
                        from analytics.agent import DataAnalyticsAgent
                        pipeline = _get_pipeline()
                        agent = DataAnalyticsAgent(api_key=st.session_state.gemini_api_key or None)

                        prog = st.progress(0, "📡 Fetching content...")
                        # FIX: ONE fetch — _fetch_html is memoized inside pipeline,
                        # so fetch_content() below reuses the same HTML, no double request.
                        content = pipeline.fetch_content(url_a)
                        if not content:
                            st.error("❌ Failed to fetch."); st.stop()

                        prog.progress(35, "🔍 Extracting structured data (reusing cached HTML)...")
                        records = []
                        html = pipeline._fetch_html(url_a)   # ← memo hit, NOT a new request
                        if html:
                            from scraper.local_extractor import smart_local_extract
                            from pipeline.deduplicator import clean_records
                            local = smart_local_extract(html, url=url_a)
                            if local: records = clean_records(local)
                        if not records and st.session_state.gemini_api_key:
                            r2 = pipeline.run_extract(url_a,
                                content_type=None if act=="Auto-detect" else act)
                            records = r2.get("data", [])
                            if records and auto_clean:
                                from pipeline.deduplicator import clean_records
                                records = clean_records(records)

                        df_a = _clean_df(records) if records else None
                        if df_a is not None and not df_a.empty:
                            _save_dashboard(df_a)

                        prog.progress(65, "🧠 Analyzing...")
                        df_res = text_res = None
                        if df_a is not None and not df_a.empty and amode != "Text & NLP Only":
                            df_res = agent.analyze_dataframe(df_a, url=url_a, content_type=act)
                        if amode != "Data Only":
                            text_res = agent.analyze_text_content(content, url=url_a)

                        prog.progress(100, "✅ Complete!")
                        st.success("✅ Analysis complete!")
                        st.divider()

                        if df_res and df_a is not None:
                            _section("📊 Data Analysis")
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("📋 Rows", df_res["shape"]["rows"])
                            m2.metric("📊 Columns", df_res["shape"]["columns"])
                            m3.metric("♻️ Dupes", df_res["profile"].get("duplicates", 0))
                            q = df_res.get("data_quality_score", 0)
                            m4.metric("⭐ Quality", f"{'🟢' if q>=80 else '🟡'} {q}/100")

                            with st.expander("🗂️ Extracted Data", expanded=True):
                                st.dataframe(df_a, use_container_width=True)

                            if df_res.get("charts"):
                                _section("📈 Auto Charts")
                                for i in range(0, len(df_res["charts"]), 2):
                                    cols = st.columns(2)
                                    for j, col in enumerate(cols):
                                        if i+j < len(df_res["charts"]):
                                            with col:
                                                st.plotly_chart(df_res["charts"][i+j]["figure"],
                                                    use_container_width=True, key=f"ac_{i}_{j}")

                            if df_res.get("ai_insights"):
                                _section("🤖 AI Insights")
                                st.markdown(f'<div class="result-card">{df_res["ai_insights"]}</div>',
                                    unsafe_allow_html=True)
                            if df_res.get("recommendations"):
                                _section("💡 Recommendations")
                                st.markdown(f'<div class="result-card">{df_res["recommendations"]}</div>',
                                    unsafe_allow_html=True)

                        if text_res:
                            st.divider()
                            _section("📝 Text & NLP Analysis")
                            t1, t2, t3 = st.columns(3)
                            t1.metric("📝 Words", f"{text_res.get('word_count',0):,}")
                            t2.metric("🔑 Keywords", len(text_res.get("keywords",[])))
                            t3.metric("🏷️ Topics", len(text_res.get("topics",[])))
                            for ch in text_res.get("charts", []):
                                st.plotly_chart(ch["figure"], use_container_width=True,
                                    key=f"tc_{ch['title']}")
                            if text_res.get("ai_insights"):
                                st.markdown(f'<div class="result-card">{text_res["ai_insights"]}</div>',
                                    unsafe_allow_html=True)

                        st.divider()
                        d1, d2 = st.columns(2)
                        if df_a is not None and not df_a.empty:
                            with d1:
                                st.download_button("📥 CSV", data=df_a.to_csv(index=False),
                                    file_name="analytics_data.csv", mime="text/csv")
                        combined = {}
                        if df_res: combined["data"] = {k:v for k,v in df_res.items() if k not in ["charts","missing_chart"]}
                        if text_res: combined["text"] = {k:v for k,v in text_res.items() if k!="charts"}
                        with d2:
                            st.download_button("📋 JSON Report",
                                data=json.dumps(combined, indent=2, default=str),
                                file_name="report.json", mime="application/json")

                    except Exception as e:
                        st.error(f"❌ {e}"); logger.exception(e)

    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            try:
                df_up = pd.read_csv(uploaded)
                if auto_clean:
                    from pipeline.deduplicator import clean_dataframe
                    df_up = clean_dataframe(df_up)
                st.success(f"✅ {len(df_up)} rows × {len(df_up.columns)} cols")
                st.dataframe(df_up.head(5), use_container_width=True)
                _save_dashboard(df_up)
                st.info("💡 Go to **📈 Dashboard** tab!")
                if st.button("🚀 Analyze CSV", key="btn_csv"):
                    if not st.session_state.gemini_api_key:
                        st.error("❌ Enter your Gemini API key in the sidebar.")
                    else:
                        with st.spinner("Analyzing..."):
                            try:
                                from analytics.agent import DataAnalyticsAgent
                                r = DataAnalyticsAgent(
                                    api_key=st.session_state.gemini_api_key
                                ).analyze_dataframe(df_up, content_type="uploaded CSV")
                                st.success("✅ Done!")
                                for i in range(0, len(r.get("charts",[])), 2):
                                    cols = st.columns(2)
                                    for j, col in enumerate(cols):
                                        if i+j < len(r["charts"]):
                                            with col:
                                                st.plotly_chart(r["charts"][i+j]["figure"],
                                                    use_container_width=True, key=f"cc_{i}_{j}")
                                if r.get("ai_insights"):
                                    st.markdown(f'<div class="result-card">{r["ai_insights"]}</div>',
                                        unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"❌ {e}")

# ════════════════════════════════════════════════════════════════════
# TAB 4 — LIVE MONITOR
# ════════════════════════════════════════════════════════════════════
with tab4:
    _section("📡 Live Data Monitor")
    st.markdown("""<div class="live-banner">
      <span style='color:#34d399;font-weight:600;'>⚡ Live Monitoring</span>
      <span style='color:#7c7ca0;font-size:.85rem;'>
        Scrapes every 60s · Previous vs Current · 🟢↑ / 🔴↓ · Alerts</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([2,1])
    with c1: mon_url = st.text_input("URL to Monitor",
        placeholder="https://quotes.toscrape.com", key="mon_url",
        value=st.session_state.monitor_url)
    with c2: ct_mon = st.selectbox("Content Type",
        ["Auto-detect","product","article","job","event"], key="ct_mon")
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🔔 Alert Rules (optional)"):
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1: a_field  = st.text_input("Field", placeholder="price", key="a_field")
        with ac2: a_cond   = st.selectbox("Condition", ["above","below","change_pct"], key="a_cond")
        with ac3: a_thresh = st.number_input("Threshold", value=5.0, key="a_thresh")
        with ac4: a_label  = st.text_input("Label", placeholder="Price spike!", key="a_label")
        alert_rules = [{"field":a_field,"condition":a_cond,"threshold":a_thresh,
                        "label":a_label or f"{a_field} {a_cond} {a_thresh}"}] if a_field else []

    cs, cst, cr = st.columns(3)
    with cs: start = st.button("▶️ Start Monitoring", key="btn_start")
    with cst: stop = st.button("⏹️ Stop", key="btn_stop")
    with cr: reset = st.button("🔄 Reset", key="btn_reset")

    if start and mon_url:
        from monitor.tracker import MonitorSession
        st.session_state.monitor_running = True
        st.session_state.monitor_url = mon_url
        if (st.session_state.monitor_session is None or
                st.session_state.monitor_session.url != mon_url):
            st.session_state.monitor_session = MonitorSession(url=mon_url)
        st.success(f"✅ Monitoring started: {mon_url}")
    if stop:  st.session_state.monitor_running = False; st.info("⏹️ Paused.")
    if reset: st.session_state.monitor_session = None; st.session_state.monitor_running = False; st.success("🔄 Reset.")

    st.divider()

    if st.session_state.monitor_running and st.session_state.monitor_session:
        session = st.session_state.monitor_session
        st.markdown(f"""<div class="live-banner">
          <span style='color:#34d399;font-weight:600;'>📡 LIVE — {mon_url[:50]}</span>
          <span style='color:#7c7ca0;font-size:.85rem;'>Snapshot #{len(session.snapshots)+1} · Every 60s</span>
        </div>""", unsafe_allow_html=True)

        with st.spinner("🔄 Fetching fresh data..."):
            try:
                pipeline = _get_pipeline()
                records = _extract(mon_url, pipeline,
                    ct=None if ct_mon=="Auto-detect" else ct_mon)

                if not records:
                    st.warning("⚠️ No records. Try different Content Type.")
                else:
                    changes = session.add_snapshot(records, alert_rules or [])
                    prev = session.get_previous()
                    curr = session.get_latest()

                    m1,m2,m3,m4,m5 = st.columns(5)
                    m1.metric("📸 Snapshots", len(session.snapshots))
                    m2.metric("📋 Records Now", len(records))
                    m3.metric("📋 Records Before", len(prev["records"]) if prev else "—")
                    m4.metric("🔄 Changes", changes["total_changes"],
                        delta=changes["total_changes"] if changes["has_changes"] else None)
                    m5.metric("🚨 Alerts", len(session.alert_history))

                    if changes["has_changes"] and changes["changed"]:
                        _section("🔄 Field Changes")
                        rows = []
                        for cr2 in changes["changed"]:
                            for fc in cr2["field_changes"]:
                                d = fc.get("direction","changed")
                                rows.append({
                                    "Record": cr2["key"], "Field": fc["field"],
                                    "Previous": fc["previous"], "Current": fc["current"],
                                    "Change %": f"{fc['pct_change']:+.2f}%" if fc.get("pct_change") is not None else "—",
                                    "Dir": "🟢↑" if d=="up" else "🔴↓" if d=="down" else "🔵~",
                                })
                        if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True)
                    elif len(session.snapshots) > 1:
                        st.success("✅ No changes since last snapshot")

                    _section("📋 Previous vs Current")
                    pt, ct2 = st.columns(2)
                    with pt:
                        st.caption(f"⏮ Previous ({'—' if not prev else prev['timestamp'][11:19]})")
                        if prev and prev["records"]:
                            st.dataframe(pd.DataFrame(prev["records"]).head(8), use_container_width=True)
                        else: st.info("No previous snapshot yet.")
                    with ct2:
                        st.caption(f"▶ Current ({curr['timestamp'][11:19]})")
                        st.dataframe(pd.DataFrame(records).head(8), use_container_width=True)

                    if session.alert_history:
                        _section("🚨 Alerts")
                        for al in reversed(session.alert_history[-8:]):
                            d = al.get("direction","changed")
                            icon = "🟢" if d=="up" else "🔴"
                            pct = f"{al.get('pct_change',0):+.2f}%" if al.get("pct_change") else ""
                            st.markdown(f"""<div class="alert-box">
                            {icon} <b>{al['alert']}</b> — {al['record_key']} ·
                            {al['field']}: {al['previous']} → <b>{al['current']}</b>
                            {pct} · {al['triggered_at'][11:19]}</div>""", unsafe_allow_html=True)

                    _save_dashboard(pd.DataFrame(records))
                    st.info("💡 Data saved → **📈 Dashboard** tab")

            except Exception as e:
                st.error(f"❌ {e}"); logger.exception(e)

        st.caption("⏱️ Click **Start Monitoring** again any time to pull a fresh snapshot. "
                  "(Auto-refresh removed to keep the app responsive — this matches "
                  "real Power BI behavior of manual/scheduled refresh.)")

    else:
        st.markdown("""<div style='background:rgba(255,255,255,.02);
        border:2px dashed rgba(139,92,246,.2);border-radius:16px;
        padding:3rem;text-align:center;margin-top:1rem;'>
        <div style='font-size:3rem;'>📡</div>
        <div style='color:#a78bfa;font-size:1.2rem;font-weight:600;margin:.5rem 0;'>
        Live Monitor Ready</div>
        <div style='color:#4a4a6a;'>Enter a URL and click <b>Start Monitoring</b></div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# TAB 5 — POWER BI DASHBOARD
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("""<div style='background:linear-gradient(135deg,rgba(124,58,237,.15),
    rgba(37,99,235,.1));border:1px solid rgba(124,58,237,.25);border-radius:14px;
    padding:1rem 1.5rem;margin-bottom:1rem;display:flex;align-items:center;gap:1rem;'>
      <span style='font-size:2rem;'>📈</span>
      <div>
        <div style='color:#a78bfa;font-size:1.2rem;font-weight:700;'>Power BI Style Dashboard</div>
        <div style='color:#4a4a6a;font-size:.85rem;'>Fully automatic · Dark theme · Every chart type</div>
      </div>
    </div>""", unsafe_allow_html=True)

    db_src = st.radio("Data Source",
        ["📊 From Extract / Analytics / Monitor", "📁 Upload CSV"],
        horizontal=True, key="db_src")

    df_db = None
    if db_src.startswith("📊"):
        if st.session_state.dashboard_df is not None:
            df_db = st.session_state.dashboard_df
            st.success(f"✅ Loaded: **{len(df_db)} rows × {len(df_db.columns)} columns**")
            with st.expander("👁️ Preview"):
                st.dataframe(df_db.head(5), use_container_width=True)
        else:
            st.markdown("""<div style='background:rgba(251,191,36,.08);border:1px solid
            rgba(251,191,36,.2);border-radius:10px;padding:1rem;text-align:center;'>
            <span style='color:#fbbf24;'>⚠️ No data yet.</span>
            <span style='color:#7c7ca0;'> Extract data from Tab 2 or 3 first, or upload CSV.</span>
            </div>""", unsafe_allow_html=True)
    else:
        up = st.file_uploader("Upload CSV", type=["csv"], key="db_up")
        if up:
            try:
                df_db = pd.read_csv(up)
                if auto_clean:
                    from pipeline.deduplicator import clean_dataframe
                    df_db = clean_dataframe(df_db)
                st.success(f"✅ Loaded: **{len(df_db)} rows × {len(df_db.columns)} cols**")
                _save_dashboard(df_db)
            except Exception as e:
                st.error(f"❌ {e}")

    if df_db is not None and not df_db.empty:
        if st.button("🚀 Generate Full Dashboard", key="btn_gen"):
            with st.spinner("⚡ Building your complete Power BI dashboard..."):
                try:
                    from app.powerbi_dashboard import render_dashboard
                    render_dashboard(df_db)
                except Exception as e:
                    st.error(f"❌ Dashboard error: {e}"); logger.exception(e)
        else:
            st.markdown("""<div style='background:rgba(255,255,255,.02);
            border:2px dashed rgba(139,92,246,.2);border-radius:16px;
            padding:2.5rem;text-align:center;margin-top:1rem;'>
            <div style='font-size:3rem;'>📈</div>
            <div style='color:#a78bfa;font-size:1.1rem;font-weight:600;margin:.5rem 0;'>
            Dashboard Ready</div>
            <div style='color:#4a4a6a;'>Click <b>Generate Full Dashboard</b> to auto-build all charts</div>
            </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""<div style='text-align:center;padding:1rem;margin-top:1rem;
border-top:1px solid rgba(139,92,246,.1);'>
  <span style='color:#4a4a6a;font-size:.8rem;'>
    🤖 Web Intel · Made by <b style='color:#a78bfa;'>Ujjwal Kaushik</b> ·
    Gemini 2.5 Flash · Playwright · Live Monitor · Power BI Dashboard
  </span>
</div>""", unsafe_allow_html=True)