"""
Long-term Memory page.
Displays, searches, and manages the AI's persistent memory facts.
"""

import streamlit as st


def render() -> None:
    st.title("🧠 Long-term Memory")
    st.markdown(
        "The AI assistant builds a persistent memory of important facts from your "
        "conversations. These facts are retrieved automatically to personalise responses."
    )

    session_id = st.session_state.get("session_id", "default")
    st.info(f"Viewing memory for session: **{session_id}**")

    # ── Load memory facts ──────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search memory facts", placeholder="Enter keyword...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh")

    try:
        from backend.core.database import get_memory_facts, search_memory_facts

        if search_query.strip():
            facts = search_memory_facts(session_id, search_query)
        else:
            facts = get_memory_facts(session_id)
    except Exception as e:
        st.error(f"Could not load memory: {e}")
        facts = []

    # ── Summary metrics ────────────────────────────────────────────────────
    if facts:
        categories = {}
        for f in facts:
            cat = f.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1

        cols = st.columns(min(len(categories) + 1, 5))
        cols[0].metric("Total Facts", len(facts))
        for i, (cat, count) in enumerate(categories.items(), 1):
            if i < len(cols):
                cols[i].metric(cat.title(), count)

        st.divider()

        # Category filter
        all_cats = ["All"] + sorted(set(f.get("category", "general") for f in facts))
        selected_cat = st.selectbox("Filter by category", options=all_cats)

        filtered = (
            facts if selected_cat == "All"
            else [f for f in facts if f.get("category") == selected_cat]
        )

        # Display facts
        st.subheader(f"Memory Facts ({len(filtered)} shown)")
        for fact in filtered:
            importance = fact.get("importance", 0.5)
            cat = fact.get("category", "general")

            cat_icons = {
                "preference": "⭐",
                "goal": "🎯",
                "personal": "👤",
                "technical": "💻",
                "other": "📌",
                "general": "📝",
            }
            icon = cat_icons.get(cat, "📝")

            # Colour-code by importance
            importance_pct = int(importance * 100)
            color = "#2ecc71" if importance > 0.7 else "#f39c12" if importance > 0.4 else "#95a5a6"

            st.markdown(
                f"""
                <div style="
                    padding: 12px 16px;
                    margin: 8px 0;
                    border-left: 4px solid {color};
                    border-radius: 4px;
                    background: #f8f9fa;
                ">
                    <span style="font-size:1.1em">{icon}</span>
                    <strong> {fact['fact']}</strong><br>
                    <small style="color:#6c757d">
                        Category: <em>{cat}</em> |
                        Importance: {importance_pct}% |
                        Stored: {str(fact.get('created_at', ''))[:10]}
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "No memory facts stored yet. Start a conversation in the Chat page and "
            "the AI will automatically extract and store important information."
        )

    # ── Manual fact entry ──────────────────────────────────────────────────
    st.divider()
    st.subheader("➕ Add Memory Fact Manually")

    with st.form("add_fact_form"):
        fact_text = st.text_area("Fact", placeholder="Enter a fact to remember...", height=80)
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox(
                "Category", ["general", "preference", "goal", "personal", "technical", "other"]
            )
        with col2:
            importance = st.slider("Importance", 0.0, 1.0, 0.5, 0.1)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)

        if st.form_submit_button("💾 Save Fact") and fact_text.strip():
            try:
                from backend.core.database import save_memory_fact

                save_memory_fact(
                    session_id=session_id,
                    fact=fact_text.strip(),
                    category=category,
                    importance=importance,
                )
                st.success("Fact saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save: {e}")
