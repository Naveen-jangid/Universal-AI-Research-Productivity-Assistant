"""
Universal AI Research & Productivity Assistant — Streamlit Frontend.
Main application entry point. Renders the sidebar and routes to page modules.
"""

import sys
from pathlib import Path

# Ensure project root is on path so both `frontend` and `backend` packages resolve
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────
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

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Main background */
    .stApp { background-color: #f0f2f6; }

    /* Card-like containers */
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        margin-bottom: 8px;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 16px;
    }

    /* Chat messages */
    div[data-testid="stChatMessage"] {
        background: white;
        border-radius: 12px;
        margin: 4px 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        color: white;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #a8d8ff !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        border-radius: 8px;
    }

    /* File uploader */
    div[data-testid="stFileUploadDropzone"] {
        background: white;
        border: 2px dashed #667eea;
        border-radius: 12px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 4px;
    }

    /* Code blocks */
    code {
        background: #f6f8fa;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Imports (after path setup) ─────────────────────────────────────────────
from frontend.components.sidebar import render_sidebar
from frontend.pages import (
    agent,
    audio,
    chat,
    data_analysis,
    documents,
    image_analysis,
    memory,
)

# ── Initialise global session state ────────────────────────────────────────
import uuid

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]

if "api_base_url" not in st.session_state:
    st.session_state["api_base_url"] = "http://localhost:8000/api/v1"

# ── Sidebar + routing ─────────────────────────────────────────────────────
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

page_module = PAGE_MODULES.get(selected_page)
if page_module:
    page_module.render()
else:
    st.error(f"Unknown page: {selected_page}")
