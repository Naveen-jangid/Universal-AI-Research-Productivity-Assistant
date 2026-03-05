"""
Universal AI Research & Productivity Assistant — Streamlit Frontend.
Main application entry point. Renders the sidebar and routes to page modules.
"""

import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

st.set_page_config(
    page_title="Universal AI Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-org/universal-ai-assistant",
        "Report a bug": "https://github.com/your-org/universal-ai-assistant/issues",
        "About": "# Universal AI Research & Productivity Assistant\nv1.0.0",
    },
)

# ── Global Design System ───────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Base ─────────────────────────────────────────────────────────── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f0f4ff; }
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }

    /* ── Sidebar ──────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d1a 0%, #111827 60%, #0d1117 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.3);
    }
    section[data-testid="stSidebar"] > div { padding-top: 0.5rem; }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span { color: #e2e8f0 !important; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #c7d2fe !important; }
    section[data-testid="stSidebar"] .stCaption { color: #64748b !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(99,102,241,0.25) !important; }

    /* Sidebar text inputs */
    section[data-testid="stSidebar"] input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(99,102,241,0.35) !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
    }

    /* Nav buttons in sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(99,102,241,0.15);
        color: #cbd5e1 !important;
        border-radius: 10px;
        padding: 0.5rem 0.85rem;
        margin-bottom: 4px;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.18s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(99,102,241,0.2) !important;
        border-color: rgba(99,102,241,0.5) !important;
        color: #fff !important;
        transform: translateX(3px);
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(99,102,241,0.4);
    }

    /* ── Main area ────────────────────────────────────────────────────── */
    /* Page header banner */
    .page-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .page-header::before {
        content: "";
        position: absolute; top: -50%; right: -10%;
        width: 300px; height: 300px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
    }
    .page-header h1 { color: white !important; margin: 0 0 0.35rem 0; font-size: 1.7rem; font-weight: 700; }
    .page-header p  { color: rgba(255,255,255,0.85) !important; margin: 0; font-size: 0.95rem; }
    .page-header .badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }

    /* Cards */
    .card {
        background: white;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .card-accent {
        border-left: 4px solid #6366f1;
    }
    .card-success { border-left: 4px solid #10b981; }
    .card-warn    { border-left: 4px solid #f59e0b; }
    .card-danger  { border-left: 4px solid #ef4444; }

    /* Feature tiles (home page) */
    .feature-tile {
        background: white;
        border-radius: 14px;
        padding: 1.4rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        height: 100%;
        text-align: center;
    }
    .feature-tile:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(99,102,241,0.15);
        border-color: #c7d2fe;
    }
    .feature-tile .icon { font-size: 2.2rem; margin-bottom: 0.6rem; }
    .feature-tile h4 { color: #1e293b; font-size: 1rem; font-weight: 600; margin: 0 0 0.4rem; }
    .feature-tile p  { color: #64748b; font-size: 0.82rem; margin: 0; line-height: 1.5; }

    /* Stat strip */
    .stat-strip {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        display: flex; gap: 2rem;
        color: white;
    }
    .stat-strip .stat-item { text-align: center; }
    .stat-strip .stat-num  { font-size: 1.6rem; font-weight: 700; }
    .stat-strip .stat-lbl  { font-size: 0.75rem; opacity: 0.8; }

    /* ── Metric containers ─────────────────────────────────────────────── */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] label { color: #64748b; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    div[data-testid="stMetricValue"] { color: #1e293b; font-weight: 700; font-size: 1.6rem !important; }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 10px 10px 0 0;
        border: 1px solid #e2e8f0;
        border-bottom: none;
        gap: 2px;
        padding: 4px 6px 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        color: #64748b;
        font-weight: 500;
        font-size: 0.88rem;
        padding: 0.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 1.25rem !important;
    }

    /* ── Chat messages ─────────────────────────────────────────────────── */
    div[data-testid="stChatMessage"] {
        background: white;
        border-radius: 14px;
        border: 1px solid #e8ecf4;
        margin: 6px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        padding: 0.25rem 0;
    }
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #eef2ff, #f5f3ff);
        border-color: #c7d2fe;
    }

    /* ── Buttons ───────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 9px;
        font-weight: 500;
        font-size: 0.88rem;
        transition: all 0.18s ease;
        border: 1px solid #e2e8f0;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(99,102,241,0.35);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
        transform: translateY(-1px);
    }
    .stButton > button:hover {
        border-color: #6366f1;
        color: #6366f1;
    }

    /* ── Chat input ────────────────────────────────────────────────────── */
    div[data-testid="stChatInput"] > div {
        border: 2px solid #e2e8f0 !important;
        border-radius: 14px !important;
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        transition: border-color 0.18s;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.12) !important;
    }

    /* ── Text inputs & areas ────────────────────────────────────────────── */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        background: white !important;
        transition: border-color 0.18s, box-shadow 0.18s;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }

    /* ── File uploader ─────────────────────────────────────────────────── */
    div[data-testid="stFileUploadDropzone"] {
        background: linear-gradient(135deg, #fafbff, #f5f3ff);
        border: 2px dashed #c7d2fe !important;
        border-radius: 14px !important;
        transition: all 0.2s;
    }
    div[data-testid="stFileUploadDropzone"]:hover {
        border-color: #6366f1 !important;
        background: linear-gradient(135deg, #eef2ff, #ede9fe) !important;
    }

    /* ── Expander ─────────────────────────────────────────────────────── */
    div[data-testid="stExpander"] {
        background: white;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600;
        color: #1e293b;
        padding: 0.65rem 1rem;
    }
    div[data-testid="stExpander"] summary:hover { background: #f8faff; }

    /* ── Select boxes ──────────────────────────────────────────────────── */
    div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* ── Alerts ────────────────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-width: 1px !important;
    }

    /* ── Divider ───────────────────────────────────────────────────────── */
    hr { border-color: #e8ecf4 !important; margin: 1rem 0 !important; }

    /* ── Scrollbar ─────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #c7d2fe; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #6366f1; }

    /* ── Code blocks ───────────────────────────────────────────────────── */
    code {
        font-family: 'JetBrains Mono', monospace;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: 2px 6px;
        border-radius: 5px;
        font-size: 0.83em;
        color: #7c3aed;
    }
    pre { background: #0f172a !important; border-radius: 12px !important; }
    pre code { background: transparent !important; border: none !important; color: #e2e8f0 !important; }

    /* ── Status badges ─────────────────────────────────────────────────── */
    .badge-green  { background:#dcfce7; color:#166534; border:1px solid #bbf7d0; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-red    { background:#fee2e2; color:#991b1b; border:1px solid #fecaca; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-blue   { background:#dbeafe; color:#1d4ed8; border:1px solid #bfdbfe; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-purple { background:#ede9fe; color:#6d28d9; border:1px solid #ddd6fe; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }

    /* ── Hide Streamlit chrome ─────────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ── Dataframe ─────────────────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        overflow: hidden;
    }

    /* ── Spinner ───────────────────────────────────────────────────────── */
    div[data-testid="stSpinner"] { color: #6366f1 !important; }

    /* ── Progress ──────────────────────────────────────────────────────── */
    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Imports ────────────────────────────────────────────────────────────────
from frontend.components.sidebar import render_sidebar
from frontend.pages import agent, audio, chat, data_analysis, documents, image_analysis, memory

# ── Session state ──────────────────────────────────────────────────────────
import uuid

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]

if "api_base_url" not in st.session_state:
    st.session_state["api_base_url"] = "http://localhost:8000/api/v1"

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "home"

# ── Routing ────────────────────────────────────────────────────────────────
selected_page = render_sidebar()

PAGE_MODULES = {
    "chat": chat,
    "documents": documents,
    "images": image_analysis,
    "audio": audio,
    "data_analysis": data_analysis,
    "agent": agent,
    "memory": memory,
}

if selected_page == "home":
    # ── Home / Dashboard ──────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-header">
            <h1>🤖 Universal AI Research Assistant</h1>
            <p>Your intelligent workspace — chat, research documents, analyse data, and run autonomous agents.</p>
            <span class="badge">Powered by GPT-4o + LangChain + FAISS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    features = [
        ("💬", "Conversational Chat", "Multi-turn chat with long-term memory across sessions.", "chat"),
        ("📄", "Document Intelligence", "Upload PDFs & docs, then query them with RAG.", "documents"),
        ("🖼️", "Image Analysis", "Vision AI describes, analyses and answers questions about images.", "images"),
        ("🎙️", "Speech & Audio", "Transcribe and summarise audio files instantly.", "audio"),
        ("📊", "Data Analysis", "EDA, interactive charts, and AI insights for your datasets.", "data_analysis"),
        ("🤖", "Autonomous Agent", "Multi-step research agent with web search, code execution & more.", "agent"),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc, page_key) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="feature-tile">
                    <div class="icon">{icon}</div>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"home_{page_key}", use_container_width=True):
                st.session_state["active_page"] = page_key
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card card-accent">
            <strong>Getting started</strong><br>
            <span style="color:#64748b;font-size:0.88rem;">
            1. Add your <code>OPENAI_API_KEY</code> in <code>.env</code> &nbsp;→&nbsp;
            2. Start the backend: <code>uvicorn backend.api.main:app --reload</code> &nbsp;→&nbsp;
            3. Use the sidebar to navigate between features.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif selected_page in PAGE_MODULES:
    PAGE_MODULES[selected_page].render()
else:
    st.error(f"Unknown page: {selected_page}")
