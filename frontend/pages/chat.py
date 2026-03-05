"""
Conversational Chat page.
Multi-turn chat with long-term memory and conversation history management.
"""

import streamlit as st
from frontend.components.chat_interface import init_chat_state, render_chat_history
from frontend.utils.api_client import (
    delete_conversation,
    list_conversations,
    send_chat_message,
)


def render() -> None:
    st.title("💬 Conversational Chat")
    st.markdown(
        "Chat with the AI assistant. Your conversations are stored and the assistant "
        "builds long-term memory across sessions."
    )

    init_chat_state("chat")

    # ── Sidebar controls ────────────────────────────────────────────────────
    with st.sidebar:
        st.subheader("Chat Settings")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        use_memory = st.checkbox("Use Long-term Memory", value=True)

        st.subheader("Conversations")
        if st.button("🆕 New Conversation"):
            st.session_state["chat_messages"] = []
            st.session_state["chat_conv_id"] = None
            st.rerun()

        try:
            convs = list_conversations()
            for conv in convs[:10]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    label = conv["title"][:30] + "…" if len(conv["title"]) > 30 else conv["title"]
                    if st.button(f"📝 {label}", key=f"conv_{conv['id']}"):
                        st.session_state["chat_conv_id"] = conv["id"]
                        # Fetch history would go here
                        st.session_state["chat_messages"] = []
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}"):
                        delete_conversation(conv["id"])
                        st.rerun()
        except Exception:
            st.caption("Could not load conversations.")

    # ── Chat display ────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        render_chat_history(st.session_state["chat_messages"])

    # ── Input ───────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask me anything..."):
        # Show user message immediately
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
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
                        st.caption(
                            f"🧠 Stored {response['memory_facts_stored']} memory facts."
                        )
                except Exception as e:
                    reply = f"❌ Error: {e}"
                    st.error(reply)

        st.session_state["chat_messages"].append(
            {"role": "assistant", "content": reply}
        )
