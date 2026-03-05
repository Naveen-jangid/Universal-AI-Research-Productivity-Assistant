"""
Data Analysis page.
Upload CSV/Excel → EDA → Plotly visualisations → AI insights → Q&A.
"""

import json

import streamlit as st
import plotly.graph_objects as go

from frontend.utils.api_client import ask_about_data, get_ai_insights, get_visualisations, upload_dataset


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>📊 Data Analysis Assistant</h1>
            <p>Upload a dataset for automated EDA, interactive charts, AI insights, and natural language Q&amp;A.</p>
            <span class="badge">Pandas · Plotly · GPT-4o Code Interpreter</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Upload section ────────────────────────────────────────────────────
    with st.expander("📤 Upload Dataset", expanded=not st.session_state.get("dataset_info")):
        uploaded = st.file_uploader(
            "Supported: CSV, Excel (XLSX/XLS), JSON, TSV",
            type=["csv", "xlsx", "xls", "json", "tsv"],
            label_visibility="collapsed",
        )

        if uploaded and st.button("📥 Load & Analyse", type="primary"):
            with st.spinner("Uploading and running EDA…"):
                try:
                    result = upload_dataset(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "text/csv",
                    )
                    st.session_state["dataset_info"] = result
                    st.session_state.pop("charts", None)
                    st.session_state.pop("ai_insights", None)
                    st.success(
                        f"✅ **{uploaded.name}** loaded: "
                        f"**{result['shape']['rows']:,} rows** × **{result['shape']['columns']} columns**"
                    )
                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

    info = st.session_state.get("dataset_info")
    if not info:
        st.markdown(
            '<div class="card" style="text-align:center;padding:2.5rem;color:#64748b;">'
            '📁 Upload a dataset above to begin analysis.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    file_id = info["file_id"]

    tab_overview, tab_charts, tab_insights, tab_qa = st.tabs(
        ["📋 Overview", "📈 Charts", "🤖 AI Insights", "❓ Ask Data"]
    )

    # Overview
    with tab_overview:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{info['shape']['rows']:,}")
        c2.metric("Columns", info["shape"]["columns"])
        c3.metric("Numeric", len(info["numeric_columns"]))
        c4.metric("Categorical", len(info["categorical_columns"]))

        st.markdown("<br>", unsafe_allow_html=True)

        import pandas as pd
        dtype_df = pd.DataFrame(
            {"Column": list(info["dtypes"].keys()), "Type": list(info["dtypes"].values())}
        )
        missing = info.get("missing_values", {})
        dtype_df["Missing"] = dtype_df["Column"].map(missing).fillna(0).astype(int)
        st.dataframe(dtype_df, use_container_width=True, hide_index=True)

        if info.get("sample"):
            st.markdown("**Sample rows**")
            st.dataframe(pd.DataFrame(info["sample"]), use_container_width=True, hide_index=True)

    # Charts
    with tab_charts:
        if st.button("🎨 Generate Charts", type="primary"):
            with st.spinner("Generating visualisations…"):
                try:
                    chart_data = get_visualisations(file_id)
                    st.session_state["charts"] = chart_data.get("charts", [])
                    st.success(f"Generated {chart_data['chart_count']} charts.")
                except Exception as e:
                    st.error(f"❌ Chart generation failed: {e}")

        charts = st.session_state.get("charts", [])
        if charts:
            pairs = [charts[i: i + 2] for i in range(0, len(charts), 2)]
            for pair in pairs:
                cols = st.columns(len(pair))
                for col, chart in zip(cols, pair):
                    with col:
                        st.markdown(f'<div class="card"><strong>{chart["title"]}</strong>', unsafe_allow_html=True)
                        try:
                            fig = go.Figure(json.loads(chart["plotly_json"]))
                            fig.update_layout(margin=dict(l=0, r=0, t=24, b=0), height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Chart render error: {e}")
                        st.markdown("</div>", unsafe_allow_html=True)
        elif not charts:
            st.markdown(
                '<div class="card" style="text-align:center;padding:2rem;color:#64748b;">'
                'Click <strong>Generate Charts</strong> to create visualisations.'
                '</div>',
                unsafe_allow_html=True,
            )

    # AI Insights
    with tab_insights:
        if st.button("🤖 Generate AI Insights", type="primary"):
            with st.spinner("Analysing dataset…"):
                try:
                    insight_data = get_ai_insights(file_id)
                    st.session_state["ai_insights"] = insight_data["insights"]
                except Exception as e:
                    st.error(f"❌ Insight generation failed: {e}")

        if insights := st.session_state.get("ai_insights"):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(insights)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="card" style="text-align:center;padding:2rem;color:#64748b;">'
                'Click <strong>Generate AI Insights</strong> to analyse your data.'
                '</div>',
                unsafe_allow_html=True,
            )

    # Q&A
    with tab_qa:
        st.markdown(
            '<div class="card card-accent" style="margin-bottom:1rem;">'
            'The AI generates and executes pandas code to answer your questions.'
            '</div>',
            unsafe_allow_html=True,
        )

        if "data_qa_history" not in st.session_state:
            st.session_state["data_qa_history"] = []

        for qa in st.session_state["data_qa_history"]:
            with st.chat_message("user"):
                st.markdown(qa["question"])
            with st.chat_message("assistant"):
                st.markdown(qa["answer"])

        if question := st.chat_input("Ask anything about your data…"):
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Running analysis…"):
                    try:
                        resp = ask_about_data(file_id=file_id, question=question)
                        answer = resp.get("answer", "No answer.")
                        st.markdown(answer)
                        st.session_state["data_qa_history"].append(
                            {"question": question, "answer": answer}
                        )
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
