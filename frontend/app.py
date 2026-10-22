from __future__ import annotations

import csv
import html
import io
import json
import os
import re
from datetime import datetime

import requests
import streamlit as st

try:
    import plotly.express as px
except ImportError:
    px = None


API_URL = os.getenv("ONECLICK_API_URL", "http://127.0.0.1:8000/api").rstrip("/")

st.set_page_config(
    page_title="OneClick | Company Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme
# -----------------------------
if "oc_theme" not in st.session_state:
    st.session_state["oc_theme"] = "Light"

with st.sidebar:
    st.markdown("### Appearance")
    theme_choice = st.radio(
        "Theme",
        ["Light", "Dark"],
        horizontal=True,
        key="oc_theme",
        label_visibility="collapsed",
    )

IS_DARK = st.session_state["oc_theme"] == "Dark"

if IS_DARK:
    C = {
        "bg": "#0b1220",
        "bg_top": "#101b2d",
        "surface": "#121e31",
        "surface_alt": "#17263d",
        "sidebar": "#09111f",
        "text": "#edf3ff",
        "muted": "#a8b7d0",
        "subtle": "#7f91ad",
        "border": "#293a56",
        "accent": "#7aa2ff",
        "accent2": "#42d6c5",
        "accent_text": "#07111e",
        "pill_bg": "#153a43",
        "pill_text": "#aaf3e9",
        "shadow": "0 10px 30px rgba(0,0,0,.18)",
        "plot_template": "plotly_dark",
    }
else:
    C = {
        "bg": "#f4f7fb",
        "bg_top": "#ffffff",
        "surface": "#ffffff",
        "surface_alt": "#eef4ff",
        "sidebar": "#ffffff",
        "text": "#17243a",
        "muted": "#52627a",
        "subtle": "#718096",
        "border": "#dce4ef",
        "accent": "#315fce",
        "accent2": "#087f8c",
        "accent_text": "#ffffff",
        "pill_bg": "#e2f6f4",
        "pill_text": "#11656c",
        "shadow": "0 8px 24px rgba(25, 45, 80, .06)",
        "plot_template": "plotly_white",
    }

st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if IS_DARK else "light"};
        --oc-bg: {C["bg"]};
        --oc-bg-top: {C["bg_top"]};
        --oc-surface: {C["surface"]};
        --oc-surface-alt: {C["surface_alt"]};
        --oc-sidebar: {C["sidebar"]};
        --oc-text: {C["text"]};
        --oc-muted: {C["muted"]};
        --oc-subtle: {C["subtle"]};
        --oc-border: {C["border"]};
        --oc-accent: {C["accent"]};
        --oc-accent2: {C["accent2"]};
        --oc-accent-text: {C["accent_text"]};
        --oc-pill-bg: {C["pill_bg"]};
        --oc-pill-text: {C["pill_text"]};
        --oc-shadow: {C["shadow"]};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--oc-bg) !important;
        color: var(--oc-text) !important;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }}
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, var(--oc-bg-top) 0%, var(--oc-bg) 65%) !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    [data-testid="stToolbar"] {{
        right: 1rem;
    }}
    [data-testid="stSidebar"] {{
        background: var(--oc-sidebar) !important;
        border-right: 1px solid var(--oc-border);
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: var(--oc-sidebar) !important;
    }}
    [data-testid="stSidebar"] * {{
        color: var(--oc-text);
    }}
    [data-testid="stMainBlockContainer"], .block-container {{
        max-width: 1480px;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: clamp(1.25rem, 3vw, 3rem) !important;
        padding-right: clamp(1.25rem, 3vw, 3rem) !important;
    }}

    /* Consistent type scale */
    h1 {{
        color: var(--oc-text) !important;
        font-size: clamp(2rem, 3.1vw, 2.8rem) !important;
        line-height: 1.12 !important;
        letter-spacing: -.045em !important;
        font-weight: 780 !important;
        margin-bottom: .65rem !important;
    }}
    h2 {{
        color: var(--oc-text) !important;
        font-size: 1.55rem !important;
        line-height: 1.25 !important;
        letter-spacing: -.025em !important;
        font-weight: 730 !important;
        margin-top: 1.8rem !important;
        margin-bottom: 1rem !important;
        padding-top: .2rem;
    }}
    h3 {{
        color: var(--oc-text) !important;
        font-size: 1.12rem !important;
        line-height: 1.35 !important;
        font-weight: 700 !important;
        margin-top: 1.25rem !important;
        margin-bottom: .7rem !important;
    }}
    p, [data-testid="stMarkdownContainer"] p {{
        color: var(--oc-muted);
        font-size: .96rem;
        line-height: 1.68;
    }}
    label, [data-testid="stWidgetLabel"] p {{
        color: var(--oc-text) !important;
        font-size: .88rem !important;
        font-weight: 650 !important;
    }}
    small, .stCaption, [data-testid="stCaptionContainer"] {{
        color: var(--oc-subtle) !important;
        font-size: .82rem !important;
        line-height: 1.5 !important;
    }}
    strong, b {{
        color: var(--oc-text);
        font-weight: 700;
    }}
    a {{
        color: var(--oc-accent) !important;
        text-decoration-thickness: 1px;
        text-underline-offset: 3px;
    }}
    hr {{
        border-color: var(--oc-border) !important;
        margin: 1.2rem 0 !important;
    }}

    /* Header and cards */
    .oc-brand {{
        font-size: 1.55rem;
        line-height: 1.2;
        font-weight: 820;
        letter-spacing: -.04em;
        color: var(--oc-text);
        margin: .35rem 0 .25rem;
    }}
    .oc-eyebrow {{
        color: var(--oc-accent2);
        text-transform: uppercase;
        letter-spacing: .14em;
        font-size: .72rem;
        line-height: 1.5;
        font-weight: 800;
        margin-bottom: .45rem;
    }}
    .oc-page-title {{
        color: var(--oc-text);
        font-size: clamp(2rem, 3.1vw, 2.8rem);
        line-height: 1.12;
        font-weight: 800;
        letter-spacing: -.045em;
        margin: .15rem 0 .65rem;
    }}
    .oc-subtitle {{
        color: var(--oc-muted);
        font-size: 1.02rem;
        line-height: 1.65;
        max-width: 850px;
    }}
    .oc-card {{
        height: 100%;
        min-height: 150px;
        box-sizing: border-box;
        background: var(--oc-surface);
        border: 1px solid var(--oc-border);
        border-radius: 18px;
        padding: 22px;
        box-shadow: var(--oc-shadow);
    }}
    .oc-card-label {{
        color: var(--oc-subtle);
        text-transform: uppercase;
        letter-spacing: .09em;
        font-size: .74rem;
        font-weight: 750;
        margin-bottom: .7rem;
    }}
    .oc-card-value {{
        color: var(--oc-text);
        font-size: 1.25rem;
        line-height: 1.35;
        font-weight: 760;
        overflow-wrap: anywhere;
        margin-bottom: .45rem;
    }}
    .oc-card-copy {{
        color: var(--oc-muted);
        font-size: .9rem;
        line-height: 1.6;
    }}
    .oc-panel {{
        background: var(--oc-surface);
        color: var(--oc-text);
        border: 1px solid var(--oc-border);
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: var(--oc-shadow);
        line-height: 1.7;
    }}
    .oc-muted {{
        color: var(--oc-muted);
        font-size: .88rem;
        line-height: 1.55;
    }}
    .oc-pill {{
        display: inline-block;
        border-radius: 999px;
        padding: 5px 10px;
        margin: 3px 4px 3px 0;
        color: var(--oc-pill-text);
        background: var(--oc-pill-bg);
        border: 1px solid var(--oc-border);
        font-size: .78rem;
        font-weight: 650;
    }}

    /* Metrics */
    [data-testid="stMetric"] {{
        height: 100%;
        box-sizing: border-box;
        background: var(--oc-surface);
        border: 1px solid var(--oc-border);
        border-radius: 16px;
        padding: 17px 19px;
        box-shadow: var(--oc-shadow);
    }}
    [data-testid="stMetricLabel"] {{
        color: var(--oc-muted) !important;
        font-size: .82rem !important;
        font-weight: 650 !important;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--oc-text) !important;
        font-size: clamp(1.45rem, 2vw, 2rem) !important;
        font-weight: 780 !important;
    }}
    [data-testid="stMetricDelta"] {{
        font-size: .8rem !important;
    }}

    /* Inputs and buttons */
    input, textarea, [data-baseweb="select"] > div {{
        background-color: var(--oc-surface) !important;
        color: var(--oc-text) !important;
        border-color: var(--oc-border) !important;
    }}
    [data-baseweb="input"] > div, [data-baseweb="textarea"] > div {{
        background: var(--oc-surface) !important;
        border-color: var(--oc-border) !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="select"] * {{
        color: var(--oc-text) !important;
    }}
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {{
        min-height: 2.65rem;
        border-radius: 10px !important;
        border: 1px solid var(--oc-border) !important;
        font-weight: 680 !important;
        transition: transform .12s ease, box-shadow .12s ease;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        transform: translateY(-1px);
        box-shadow: var(--oc-shadow);
        border-color: var(--oc-accent) !important;
    }}
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background: linear-gradient(100deg, var(--oc-accent), var(--oc-accent2)) !important;
        color: #ffffff !important;
        border: 0 !important;
    }}
    .stButton > button[kind="primary"] *,
    [data-testid="stFormSubmitButton"] button[kind="primary"] * {{
        color: #ffffff !important;
    }}

    /* Tabs, expanders, alerts */
    [data-testid="stTabs"] [role="tablist"] {{
        gap: .6rem;
        border-bottom: 1px solid var(--oc-border);
        padding-bottom: .25rem;
        margin-bottom: 1.35rem;
    }}
    [data-testid="stTabs"] [data-testid="stTabContent"] {{
        padding-top: .7rem;
    }}
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {{
        margin-bottom: .8rem;
    }}
    [data-testid="stTabs"] button[role="tab"] {{
        color: var(--oc-muted) !important;
        font-size: .9rem !important;
        font-weight: 700 !important;
        padding: .8rem 1rem !important;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--oc-accent) !important;
        border-bottom-color: var(--oc-accent) !important;
    }}
    [data-testid="stExpander"] {{
        background: var(--oc-surface);
        border: 1px solid var(--oc-border);
        border-radius: 12px;
        overflow: hidden;
    }}
    [data-testid="stExpander"] summary {{
        color: var(--oc-text) !important;
        font-weight: 650;
    }}
    [data-testid="stAlert"] {{
        border-radius: 12px;
    }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        border: 1px solid var(--oc-border);
        border-radius: 12px;
        overflow: hidden;
    }}
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, var(--oc-accent), var(--oc-accent2));
    }}

    @media (max-width: 900px) {{
        [data-testid="stMainBlockContainer"], .block-container {{
            padding-top: 1.25rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .oc-card {{ min-height: 125px; padding: 17px; }}
        .oc-page-title {{ font-size: 2rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{ transition: none !important; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str, timeout: int = 20):
    response = requests.get(f"{API_URL}{path}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def load_history_report(report_id: int):
    result = api_get(f"/history/{report_id}", timeout=30)
    st.session_state["intel_result"] = result
    st.session_state["intel_url"] = result.get("url") or st.session_state.get("history_url", "")
    st.session_state["active_report_id"] = report_id


def show_sources(urls):
    if not urls:
        st.caption("No source URLs were attached to this item.")
        return
    for source in urls:
        st.markdown(f"- [{source}]({source})")


def safe_filename(value: str, fallback: str = "company") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip()).strip("_").lower()
    return cleaned or fallback


# Sidebar branding and research controls
with st.sidebar:
    st.markdown(
        "<div class='oc-eyebrow'>Company research platform</div>"
        "<div class='oc-brand'>◈ OneClick</div>"
        "<div class='oc-muted'>Evidence-first company intelligence</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    workspace = st.radio(
        "WORKSPACE",
        ["New research", "Research history"],
        key="workspace",
        label_visibility="visible",
    )
    st.divider()
    st.markdown("**Research a company**")
    target_url = st.text_input(
        "Company website URL",
        value=st.session_state.get("last_url", ""),
        placeholder="https://example.com",
    )
    analyze = st.button(
        "✦  Generate intelligence report",
        type="primary",
        use_container_width=True,
    )
    st.caption("OneClick analyzes public pages and labels what its collected evidence can support.")
    st.divider()
    st.markdown(
        "<div class='oc-muted'>Local workspace · FastAPI + Groq + ChromaDB</div>",
        unsafe_allow_html=True,
    )


if workspace == "Research history":
    st.markdown(
        "<div class='oc-eyebrow'>Workspace library</div>"
        "<div class='oc-page-title'>Research history</div>"
        "<div class='oc-subtitle'>Reopen previous company reports saved on this computer.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    try:
        history = api_get("/history?limit=100").get("reports", [])
        if not history:
            st.info("No saved reports yet. Run your first company analysis from the sidebar.")
        else:
            for item in history:
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([3, 2, 1], vertical_alignment="center")
                    col_a.markdown(f"**{item.get('company_name', 'Company report')}**")
                    col_a.caption(item.get("url", ""))
                    created = item.get("created_at", "")
                    created = created[:19].replace("T", " ") if created else "Unknown date"
                    col_b.caption(f"{created} UTC · {item.get('pages_crawled', 0)} pages")
                    if col_c.button("Open report", key=f"open_{item['id']}", use_container_width=True):
                        try:
                            st.session_state["history_url"] = item.get("url", "")
                            load_history_report(int(item["id"]))
                            st.session_state["workspace"] = "New research"
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(f"Could not load report: {exc}")
    except requests.RequestException as exc:
        st.error(f"Cannot connect to the OneClick API: {exc}")
    st.stop()


st.markdown(
    "<div class='oc-eyebrow'>Research workspace / Company intelligence</div>"
    "<div class='oc-page-title'>Know the company behind the website.</div>"
    "<div class='oc-subtitle'>Discover products, business model, market signals and source-backed facts from public web pages.</div>",
    unsafe_allow_html=True,
)
st.write("")

if analyze:
    if not target_url.strip():
        st.warning("Enter a company website URL in the sidebar.")
    else:
        st.session_state["last_url"] = target_url.strip()
        progress = st.progress(0, text="Starting website research…")
        status = st.empty()
        try:
            status.info("Discovering relevant pages and collecting public website evidence…")
            progress.progress(20, text="Crawling website")
            response = requests.post(
                f"{API_URL}/analyze",
                json={"url": target_url.strip()},
                timeout=600,
            )
            progress.progress(75, text="Extracting facts and indexing evidence")
            response.raise_for_status()
            result = response.json()
            st.session_state["intel_url"] = target_url.strip()
            st.session_state["intel_result"] = result
            st.session_state["active_report_id"] = result.get("report_id")
            progress.progress(100, text="Research report ready")
            status.success("Research completed. Review findings and supporting evidence below.")
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:
                pass
            status.error(f"Analysis failed: {detail or exc}")
        except requests.RequestException as exc:
            status.error(f"Could not connect to the backend: {exc}")


if "intel_result" not in st.session_state:
    st.write("")
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown(
            "<div class='oc-card'><div class='oc-card-label'>01 / Discover</div>"
            "<div class='oc-card-value'>Relevant website pages</div>"
            "<div class='oc-card-copy'>Explore pages such as About, Products, Pricing, Careers and FAQs.</div></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "<div class='oc-card'><div class='oc-card-label'>02 / Verify</div>"
            "<div class='oc-card-value'>Evidence-backed findings</div>"
            "<div class='oc-card-copy'>Inspect source links and supporting quotations for reported claims.</div></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            "<div class='oc-card'><div class='oc-card-label'>03 / Understand</div>"
            "<div class='oc-card-value'>Company intelligence</div>"
            "<div class='oc-card-copy'>Explore business model, products, coverage gaps and ask questions.</div></div>",
            unsafe_allow_html=True,
        )
    st.info("Enter a public company website in the sidebar and select **Generate intelligence report** to begin.")
    st.stop()


result = st.session_state["intel_result"]
profile = result.get("profile", {})
url = st.session_state.get("intel_url", st.session_state.get("last_url", ""))
pages = result.get("pages", [])
products = profile.get("products", []) or []
evidence_items = profile.get("claim_evidence", []) or []

heading_left, heading_right = st.columns([4, 1], gap="large")
with heading_left:
    company_name = profile.get("company_name", "Company report")
    st.markdown(
        f"<div class='oc-page-title'>{company_name}</div><div class='oc-muted'>{url}</div>",
        unsafe_allow_html=True,
    )
with heading_right:
    report_id = result.get("report_id", st.session_state.get("active_report_id", "—"))
    st.markdown(
        f"<div class='oc-panel'><div class='oc-card-label'>REPORT ID</div>"
        f"<div class='oc-card-value'>#{report_id}</div></div>",
        unsafe_allow_html=True,
    )

st.write("")
m1, m2, m3, m4 = st.columns(4, gap="medium")
m1.metric("Pages analyzed", result.get("pages_crawled", len(pages)))
m2.metric("Products / services", len(products))
m3.metric("Verified quotations", len(evidence_items))
m4.metric("Research gaps", len(profile.get("known_gaps", [])))
st.caption(
    f"Research scope: {result.get('discovered_url_count', len(pages))} URLs considered · "
    "Results describe collected pages only."
)

# Report export options
export_col1, export_col2, export_col3 = st.columns([1, 1, 3], gap="medium")
base_name = safe_filename(profile.get("company_name", "company"))
with export_col1:
    st.download_button(
        "Download JSON",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"{base_name}_research.json",
        mime="application/json",
        use_container_width=True,
    )
with export_col2:
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["name", "description", "source_urls"])
    writer.writeheader()
    for product in products:
        writer.writerow({
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "source_urls": "; ".join(product.get("source_urls", [])),
        })
    st.download_button(
        "Download products CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{base_name}_products.csv",
        mime="text/csv",
        use_container_width=True,
    )

if result.get("crawl_warnings"):
    with st.expander(f"Crawl diagnostics · {len(result['crawl_warnings'])} warnings"):
        for warning in result["crawl_warnings"]:
            st.write(f"- {warning}")

tab_overview, tab_products, tab_details, tab_evidence, tab_chat = st.tabs(
    ["Overview", "Products & Services", "Company Details", "Evidence & Sources", "RAG Chat"]
)

with tab_overview:
    st.subheader("Executive summary")
    st.markdown(
        f"<div class='oc-panel'>{html.escape(str(profile.get('executive_summary') or 'No summary available.'))}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("At a glance")
    glance1, glance2 = st.columns(2, gap="large")
    with glance1:
        st.markdown(
            f"<div class='oc-panel'><div class='oc-card-label'>INDUSTRY</div>"
            f"<div class='oc-card-value'>{html.escape(str(profile.get('industry') or 'Not found'))}</div>"
            f"<div class='oc-muted'>Headquarters: {html.escape(str(profile.get('headquarters') or 'Not found'))}</div></div>",
            unsafe_allow_html=True,
        )
    with glance2:
        st.markdown(
            f"<div class='oc-panel'><div class='oc-card-label'>BUSINESS MODEL</div>"
            f"<div class='oc-card-value'>{html.escape(str(profile.get('business_model') or 'Not found'))}</div>"
            f"<div class='oc-muted'>Audience: {html.escape(str(profile.get('target_audience') or 'Not found'))}</div></div>",
            unsafe_allow_html=True,
        )

    st.subheader("Research quality")
    quality_left, quality_right = st.columns([1, 1], gap="large")
    with quality_left:
        source_count = len(pages)
        gap_count = len(profile.get("known_gaps", []) or [])
        if source_count >= 6 and gap_count < 4:
            coverage = "Broader coverage"
            coverage_note = "Several pages were collected. Verify important claims against their sources."
        elif source_count >= 3:
            coverage = "Partial coverage"
            coverage_note = "Useful initial findings, but some company details may be missing."
        else:
            coverage = "Limited coverage"
            coverage_note = "Only a small number of pages were readable. Treat findings as preliminary."
        st.markdown(
            f"<div class='oc-panel'><div class='oc-card-label'>COVERAGE</div>"
            f"<div class='oc-card-value'>{coverage}</div><p>{coverage_note}</p>"
            f"<p>Source pages: <strong>{source_count}</strong></p>"
            f"<p>Products / services: <strong>{len(products)}</strong></p>"
            f"<p>Research gaps: <strong>{gap_count}</strong></p></div>",
            unsafe_allow_html=True,
        )
    with quality_right:
        st.markdown("**Research gaps to review**")
        gaps = profile.get("known_gaps", []) or []
        if gaps:
            for gap in gaps[:6]:
                st.markdown(f"- {gap}")
            if len(gaps) > 6:
                st.caption(f"And {len(gaps) - 6} more. See Company Details for the full report.")
        else:
            st.write("No research gaps were reported by the extraction model.")

with tab_products:
    st.subheader("Products and services")
    st.caption("Descriptions are extracted from the pages collected during this run. Open source links to verify important details.")
    if products:
        for idx, product in enumerate(products, start=1):
            name = str(product.get("name") or "Unnamed product or service")
            with st.expander(f"{idx:02d}  ·  {name}", expanded=(idx == 1)):
                description = product.get("description") or "No description was extracted."
                st.write(description)
                st.markdown("**Supporting pages**")
                show_sources(product.get("source_urls", []))
    else:
        st.info("No products or services were confidently identified in the collected evidence.")

with tab_details:
    st.subheader("Company profile")
    fields = [
        ("Industry", profile.get("industry")),
        ("Headquarters", profile.get("headquarters")),
        ("Founding year", profile.get("founding_year") or "Not found in collected evidence"),
        ("Business model", profile.get("business_model")),
        ("Target audience", profile.get("target_audience")),
        ("Pricing model", profile.get("pricing_model")),
    ]
    for i in range(0, len(fields), 2):
        left_field, right_field = st.columns(2, gap="large")
        for column, (label, value) in zip((left_field, right_field), fields[i:i + 2]):
            with column:
                st.markdown(
                    f"<div class='oc-panel'><div class='oc-card-label'>{html.escape(label.upper())}</div>"
                    f"<div>{html.escape(str(value or 'Not found in collected evidence'))}</div></div>",
                    unsafe_allow_html=True,
                )
    st.subheader("Partnerships")
    partnerships = profile.get("partnerships", []) or []
    if partnerships:
        for item in partnerships:
            st.markdown(f"- {item}")
    else:
        st.write("No partnerships were identified in the collected evidence.")
    st.subheader("Sustainability and impact")
    sustainability = profile.get("sustainability", []) or []
    if sustainability:
        for item in sustainability:
            st.markdown(f"- {item}")
    else:
        st.write("No sustainability information was identified in the collected evidence.")
    st.subheader("Research gaps")
    gaps = profile.get("known_gaps", []) or []
    if gaps:
        for gap in gaps:
            st.markdown(f"- {gap}")
    else:
        st.write("No gaps were reported by the extraction model.")

with tab_evidence:
    st.subheader("Claim evidence")
    st.caption("Quoted text helps you inspect where a claim came from. It does not guarantee that every interpretation is correct.")
    if evidence_items:
        for idx, item in enumerate(evidence_items, start=1):
            with st.container(border=True):
                st.markdown(f"**{idx}. {item.get('claim', 'Claim')}**")
                quote = item.get("quote", "")
                if quote:
                    st.markdown(f"> {quote}")
                source = item.get("source_url", "")
                if source:
                    st.markdown(f"Source: [{source}]({source})")
    else:
        st.info("No matched claim quotations are available in this report. Review the source pages before relying on summary claims.")

    st.subheader("Collected source pages")
    if pages:
        for idx, page in enumerate(pages, start=1):
            title = page.get("title") or page.get("url") or f"Source {idx}"
            page_url = page.get("url", "")
            st.markdown(f"**{idx:02d}. [{title}]({page_url})**")
            st.caption(f"{page.get('characters', 0):,} characters collected")
    else:
        st.write("No source-page details are available.")
    if result.get("crawl_warnings"):
        with st.expander(f"Crawl warnings ({len(result['crawl_warnings'])})"):
            for warning in result["crawl_warnings"]:
                st.markdown(f"- {warning}")

with tab_chat:
    st.subheader("Ask OneClick")
    st.caption("Ask a question about the company. Answers are based on indexed website passages, so check the retrieved evidence below.")
    with st.form("company_chat_form", clear_on_submit=False):
        question = st.text_input("Question", placeholder="How does this company make money?")
        ask = st.form_submit_button("Search evidence and answer", type="primary")

    if ask:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Retrieving relevant passages from the research index…"):
                try:
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={"url": url, "question": question.strip()},
                        timeout=180,
                    )
                    response.raise_for_status()
                    answer = response.json()
                    st.subheader("Answer")
                    st.markdown(
                        f"<div class='oc-panel'>{html.escape(str(answer.get('answer') or 'No answer returned.'))}</div>",
                        unsafe_allow_html=True,
                    )
                    retrieved = answer.get("evidence", []) or []
                    if retrieved:
                        st.subheader("Retrieved evidence")
                        for item in retrieved:
                            title = item.get("title") or item.get("source_url") or "Evidence"
                            with st.expander(f"[{item.get('id', 'E?')}] {title}"):
                                st.write(item.get("excerpt", ""))
                                source = item.get("source_url", "")
                                if source:
                                    st.markdown(f"Source: [{source}]({source})")
                    else:
                        sources = answer.get("sources", []) or []
                        if sources:
                            st.markdown("**Source pages**")
                            show_sources(sources)
                        else:
                            st.info("The response did not include retrieved source details. Verify the answer against the company website.")
                except requests.HTTPError as exc:
                    try:
                        detail = exc.response.json().get("detail", str(exc))
                    except Exception:
                        detail = str(exc)
                    st.error(f"Chat failed: {detail}")
                except requests.RequestException as exc:
                    st.error(f"Could not connect to the backend: {exc}")
