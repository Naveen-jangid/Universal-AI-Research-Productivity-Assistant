"""
Conversational Chat page.
Multi-turn chat with long-term memory and conversation history management.
"""

import streamlit as st
from frontend.components.chat_interface import init_chat_state, render_chat_history
from frontend.utils.api_client import delete_conversation, list_conversations, send_chat_message


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>💬 Conversational Chat</h1>
            <p>Multi-turn AI chat with long-term memory — the assistant remembers facts across sessions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    init_chat_state("chat")

    # ── Sidebar controls ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.08em;padding:0.25rem 0 0.4rem;">Chat Settings</div>',
            unsafe_allow_html=True,
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1,
                                help="Higher = more creative, lower = more precise")
        use_memory = st.checkbox("Long-term Memory", value=True,
                                 help="Extract and recall facts across sessions")

        st.divider()
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.08em;padding:0.25rem 0 0.4rem;">Conversations</div>',
            unsafe_allow_html=True,
        )
        if st.button("🆕 New Conversation", use_container_width=True, type="primary"):
            st.session_state["chat_messages"] = []
            st.session_state["chat_conv_id"] = None
            st.rerun()

        try:
            convs = list_conversations()
            for conv in convs[:10]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    label = conv["title"][:28] + "…" if len(conv["title"]) > 28 else conv["title"]
                    if st.button(f"📝 {label}", key=f"conv_{conv['id']}", use_container_width=True):
                        st.session_state["chat_conv_id"] = conv["id"]
                        st.session_state["chat_messages"] = []
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{conv['id']}"):
                        delete_conversation(conv["id"])
                        st.rerun()
        except Exception:
            st.caption("Could not load conversations.")

    # ── Status bar ──────────────────────────────────────────────────────────
    conv_id = st.session_state.get("chat_conv_id")
    msg_count = len(st.session_state.get("chat_messages", []))

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown(
            f'<div class="card" style="padding:0.65rem 1rem;margin-bottom:0.75rem;">'
            f'<span style="color:#6366f1;font-weight:600;">Conversation</span>&nbsp;'
            f'<code style="font-size:0.78rem;">{conv_id or "new"}</code>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.metric("Messages", msg_count)
    with c3:
        st.metric("Memory", "On" if use_memory else "Off")

    # ── Chat display ────────────────────────────────────────────────────────
    render_chat_history(st.session_state["chat_messages"])

    # ── Input ───────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask me anything…"):
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    response = send_chat_message(
                        message=prompt,
                        conversation_id=st.session_state.get("chat_conv_id"),
                        session_id=st.session_state.get("session_id"),
                        use_memory=use_memory,
                        temperature=temperature,
                    )
                    reply = response["response"]
                    st.session_state["chat_conv_id"] = response["conversation_id"]
                    st.markdown(reply)

                    if response.get("memory_facts_stored", 0) > 0:
                        st.markdown(
                            f'<span class="badge-purple">🧠 {response["memory_facts_stored"]} new facts stored</span>',
                            unsafe_allow_html=True,
                        )
                except Exception as e:
                    reply = f"Error: {e}"
                    st.error(f"❌ {e}")

        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
