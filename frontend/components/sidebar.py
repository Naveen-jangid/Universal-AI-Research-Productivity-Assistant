"""
Streamlit sidebar component.
Displays navigation, API config, and system status.
"""

import streamlit as st
from frontend.utils.api_client import health_check


PAGES = {
    "💬 Chat": "chat",
    "📄 Document Q&A": "documents",
    "🖼️ Image Analysis": "images",
    "🎙️ Speech & Audio": "audio",
    "📊 Data Analysis": "data_analysis",
    "🤖 AI Agent": "agent",
    "🧠 Memory": "memory",
}


def render_sidebar() -> str:
    """
    Render the navigation sidebar and return the selected page key.
    """
    with st.sidebar:
        st.image(
            "https://img.icons8.com/fluency/96/artificial-intelligence.png",
            width=80,
        )
        st.title("AI Research Assistant")
        st.markdown("*Powered by GPT-4o + LangChain*")
        st.divider()

        # API Configuration
        with st.expander("⚙️ API Configuration", expanded=False):
            api_url = st.text_input(
                "Backend URL",
                value=st.session_state.get("api_base_url", "http://localhost:8000/api/v1"),
                key="api_url_input",
            )
            if st.button("Save & Test Connection"):
                st.session_state["api_base_url"] = api_url
                with st.spinner("Testing..."):
                    status = health_check()
                if status.get("status") == "healthy":
                    st.success(f"✅ Connected (v{status.get('version', '?')})")
                else:
                    st.error(f"❌ {status.get('error', 'Connection failed')}")

        st.divider()

        # Navigation
        selected_label = st.radio(
            "Navigate",
            options=list(PAGES.keys()),
            index=0,
            key="page_selector",
        )
        selected_page = PAGES[selected_label]

        st.divider()

        # Session info
        if "session_id" not in st.session_state:
            import uuid
            st.session_state["session_id"] = str(uuid.uuid4())[:8]

        st.caption(f"Session: `{st.session_state['session_id']}`")

        # Quick status check
        if st.button("🔄 Check Status"):
            status = health_check()
            if status.get("status") == "healthy":
                st.success("Backend healthy")
            else:
                st.error("Backend unreachable")

        st.divider()
        st.caption("v1.0.0 | Universal AI Assistant")

    return selected_page
