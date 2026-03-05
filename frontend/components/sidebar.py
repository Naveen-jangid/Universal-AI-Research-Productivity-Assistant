"""
Streamlit sidebar component.
Modern card-style navigation with live backend status badge.
"""

import streamlit as st
from frontend.utils.api_client import health_check


# Page definitions: (label, emoji, key, description)
PAGES = [
    ("Home",           "🏠", "home",          "Dashboard & overview"),
    ("Chat",           "💬", "chat",          "Multi-turn conversation"),
    ("Document Q&A",   "📄", "documents",     "RAG over your files"),
    ("Image Analysis", "🖼️", "images",        "Vision AI"),
    ("Speech & Audio", "🎙️", "audio",         "Transcription"),
    ("Data Analysis",  "📊", "data_analysis", "EDA & insights"),
    ("AI Agent",       "🤖", "agent",         "Autonomous research"),
    ("Memory",         "🧠", "memory",        "Long-term memory viewer"),
]


def _status_badge(healthy: bool) -> str:
    if healthy:
        return '<span class="badge-green" style="font-size:0.72rem;">● Online</span>'
    return '<span class="badge-red" style="font-size:0.72rem;">● Offline</span>'


def render_sidebar() -> str:
    """Render sidebar navigation and return the active page key."""

    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "home"

    with st.sidebar:
        # ── Brand header ──────────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding:1rem 0.5rem 0.5rem; text-align:center;">
                <div style="font-size:2.8rem; line-height:1;">🤖</div>
                <div style="font-size:1.05rem; font-weight:700; color:#c7d2fe; margin-top:0.35rem;">
                    AI Research Assistant
                </div>
                <div style="font-size:0.72rem; color:#64748b; margin-top:0.2rem;">
                    v1.0.0 · GPT-4o + LangChain
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Navigation ────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.08em;padding:0 0.25rem 0.4rem;">Navigation</div>',
            unsafe_allow_html=True,
        )

        active = st.session_state["active_page"]
        for label, emoji, key, desc in PAGES:
            is_active = key == active
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{emoji}  {label}",
                key=f"nav_{key}",
                type=btn_type,
                use_container_width=True,
                help=desc,
            ):
                st.session_state["active_page"] = key
                st.rerun()

        st.divider()

        # ── Backend status ────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.08em;padding:0 0.25rem 0.4rem;">Backend</div>',
            unsafe_allow_html=True,
        )

        status = st.session_state.get("backend_status")
        if status is not None:
            badge_html = _status_badge(status.get("status") == "healthy")
            info_txt = (
                status.get("version", "")
                if status.get("status") == "healthy"
                else status.get("error", "unreachable")
            )
            st.markdown(
                f'<div style="padding:0.4rem 0.25rem;">{badge_html}'
                f'<span style="font-size:0.72rem;color:#64748b;margin-left:8px;">{info_txt}</span></div>',
                unsafe_allow_html=True,
            )

        if st.button("🔄 Check Status", use_container_width=True, key="status_check"):
            with st.spinner(""):
                result = health_check()
                st.session_state["backend_status"] = result
                st.rerun()

        with st.expander("⚙️ API URL", expanded=False):
            new_url = st.text_input(
                "Backend URL",
                value=st.session_state.get("api_base_url", "http://localhost:8000/api/v1"),
                key="api_url_input",
            )
            if st.button("Save", key="save_url"):
                st.session_state["api_base_url"] = new_url
                st.session_state["backend_status"] = None
                st.success("Saved")

        st.divider()

        # ── Session info ──────────────────────────────────────────────────
        st.markdown(
            f'<div style="font-size:0.7rem;color:#475569;padding:0.25rem;">'
            f'Session&nbsp;<code style="background:rgba(99,102,241,0.15);color:#a5b4fc;'
            f'border:none;padding:1px 6px;border-radius:4px;">'
            f'{st.session_state.get("session_id","—")}</code></div>',
            unsafe_allow_html=True,
        )

    return st.session_state["active_page"]
