"""
Long-term Memory page.
Displays, searches, and manages the AI's persistent memory facts.
"""

import streamlit as st


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>🧠 Long-term Memory</h1>
            <p>The AI builds a persistent memory of facts from your conversations to personalise every response.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    session_id = st.session_state.get("session_id", "default")
    st.markdown(
        f'<div class="card" style="padding:0.65rem 1rem;margin-bottom:1rem;">'
        f'Viewing memory for session&nbsp;<code>{session_id}</code>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Search & refresh ──────────────────────────────────────────────────
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("🔍 Search memory facts", placeholder="Enter keyword…",
                                     label_visibility="collapsed")
    with col2:
        refresh = st.button("🔄 Refresh", use_container_width=True)

    try:
        from backend.core.database import get_memory_facts, search_memory_facts
        facts = search_memory_facts(session_id, search_query) if search_query.strip() else get_memory_facts(session_id)
    except Exception as e:
        st.error(f"Could not load memory: {e}")
        facts = []

    # ── Metrics ───────────────────────────────────────────────────────────
    if facts:
        categories = {}
        for f in facts:
            cat = f.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1

        metric_cols = st.columns(min(len(categories) + 1, 5))
        metric_cols[0].metric("Total Facts", len(facts))
        for i, (cat, count) in enumerate(categories.items(), 1):
            if i < len(metric_cols):
                metric_cols[i].metric(cat.title(), count)

        st.markdown("<br>", unsafe_allow_html=True)

        # Category filter
        all_cats = ["All"] + sorted(set(f.get("category", "general") for f in facts))
        selected_cat = st.selectbox("Filter by category", options=all_cats)

        filtered = facts if selected_cat == "All" else [f for f in facts if f.get("category") == selected_cat]

        st.markdown(f"**{len(filtered)} fact{'s' if len(filtered) != 1 else ''}**")

        cat_icons = {
            "preference": "⭐", "goal": "🎯", "personal": "👤",
            "technical": "💻", "other": "📌", "general": "📝",
        }

        for fact in filtered:
            importance = fact.get("importance", 0.5)
            cat = fact.get("category", "general")
            icon = cat_icons.get(cat, "📝")

            if importance > 0.7:
                border_color, badge_cls = "#6366f1", "badge-purple"
            elif importance > 0.4:
                border_color, badge_cls = "#f59e0b", "badge-blue"
            else:
                border_color, badge_cls = "#94a3b8", "badge-blue"

            st.markdown(
                f"""
                <div style="padding:12px 16px;margin:6px 0;border-left:4px solid {border_color};
                    border-radius:0 10px 10px 0;background:white;border:1px solid #e2e8f0;
                    border-left-width:4px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span>{icon}</span>
                        <strong style="color:#1e293b;">{fact['fact']}</strong>
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <span class="{badge_cls}">{cat}</span>
                        <span style="font-size:0.72rem;color:#64748b;">
                            Importance: {int(importance * 100)}% &nbsp;·&nbsp;
                            {str(fact.get('created_at', ''))[:10]}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="card" style="text-align:center;padding:2.5rem;color:#64748b;">'
            '💭 No memory facts stored yet.<br>'
            '<span style="font-size:0.88rem;">Start a conversation in Chat — '
            'the AI will automatically extract and remember important information.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Manual entry ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Add a Memory Fact Manually"):
        with st.form("add_fact_form"):
            fact_text = st.text_area("Fact", placeholder="Enter a fact to remember…", height=80)
            c1, c2 = st.columns(2)
            with c1:
                category = st.selectbox(
                    "Category", ["general", "preference", "goal", "personal", "technical", "other"]
                )
            with c2:
                importance = st.slider("Importance", 0.0, 1.0, 0.5, 0.1)

            if st.form_submit_button("💾 Save Fact", type="primary") and fact_text.strip():
                try:
                    from backend.core.database import save_memory_fact
                    save_memory_fact(
                        session_id=session_id,
                        fact=fact_text.strip(),
                        category=category,
                        importance=importance,
                    )
                    st.success("Fact saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
