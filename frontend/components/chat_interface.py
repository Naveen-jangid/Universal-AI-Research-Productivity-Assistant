"""
Reusable chat interface component for Streamlit.
"""

from typing import List, Dict
import streamlit as st


def render_message(role: str, content: str) -> None:
    """Render a single chat message bubble."""
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(messages: List[Dict[str, str]]) -> None:
    """Render all messages in a conversation."""
    for msg in messages:
        render_message(msg["role"], msg["content"])


def render_typing_indicator() -> st.empty:
    """Show a typing indicator, returns the placeholder."""
    placeholder = st.empty()
    placeholder.markdown("*Assistant is thinking...*")
    return placeholder


def init_chat_state(page_key: str = "chat") -> None:
    """Initialise session state for a chat page."""
    if f"{page_key}_messages" not in st.session_state:
        st.session_state[f"{page_key}_messages"] = []
    if f"{page_key}_conv_id" not in st.session_state:
        st.session_state[f"{page_key}_conv_id"] = None
