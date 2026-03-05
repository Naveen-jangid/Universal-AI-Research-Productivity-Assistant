"""
Data Analysis page.
Upload CSV/Excel → EDA → Plotly visualisations → AI insights → Q&A.
"""

import json

import streamlit as st
import plotly.graph_objects as go

from frontend.utils.api_client import (
    ask_about_data,
    get_ai_insights,
    get_visualisations,
    upload_dataset,
)


def render() -> None:
    st.title("📊 Data Analysis Assistant")
    st.markdown(
        "Upload a CSV, Excel, or JSON dataset. The AI will perform exploratory "
        "data analysis, generate interactive visualisations, and answer questions "
        "about your data using Python code generation."
    )

    # ── Upload section ────────────────────────────────────────────────────
    with st.expander("📤 Upload Dataset", expanded=True):
        uploaded = st.file_uploader(
            "Choose a dataset file",
            type=["csv", "xlsx", "xls", "json", "tsv"],
        )

        if uploaded and st.button("📥 Load Dataset", type="primary"):
            with st.spinner("Uploading and running EDA..."):
                try:
                    result = upload_dataset(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "text/csv",
                    )
                    st.session_state["dataset_info"] = result
                    st.success(
                        f"✅ Dataset loaded: **{result['shape']['rows']:,} rows** × "
                        f"**{result['shape']['columns']} columns**"
                    )
                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

    info = st.session_state.get("dataset_info")
    if not info:
        st.info("Upload a dataset to begin analysis.")
        return

    file_id = info["file_id"]

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_overview, tab_charts, tab_insights, tab_qa = st.tabs(
        ["📋 Overview", "📈 Charts", "🤖 AI Insights", "❓ Ask Data"]
    )

    # Overview
    with tab_overview:
        st.subheader("Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{info['shape']['rows']:,}")
        col2.metric("Columns", info["shape"]["columns"])
        col3.metric("Numeric Cols", len(info["numeric_columns"]))
        col4.metric("Categorical Cols", len(info["categorical_columns"]))

        st.subheader("Columns & Types")
        import pandas as pd

        dtype_df = pd.DataFrame(
            {"Column": list(info["dtypes"].keys()), "Type": list(info["dtypes"].values())}
        )
        missing = info.get("missing_values", {})
        dtype_df["Missing"] = dtype_df["Column"].map(missing).fillna(0).astype(int)
        st.dataframe(dtype_df, use_container_width=True)

        st.subheader("Sample Data (first 5 rows)")
        if info.get("sample"):
            st.dataframe(pd.DataFrame(info["sample"]), use_container_width=True)

    # Charts
    with tab_charts:
        st.subheader("Interactive Visualisations")

        if st.button("🎨 Generate Charts"):
            with st.spinner("Generating visualisations..."):
                try:
                    chart_data = get_visualisations(file_id)
                    st.session_state["charts"] = chart_data.get("charts", [])
                    st.success(f"Generated {chart_data['chart_count']} charts.")
                except Exception as e:
                    st.error(f"❌ Chart generation failed: {e}")

        charts = st.session_state.get("charts", [])
        if charts:
            # Show charts in a 2-column grid
            pairs = [charts[i: i + 2] for i in range(0, len(charts), 2)]
            for pair in pairs:
                cols = st.columns(len(pair))
                for col, chart in zip(cols, pair):
                    with col:
                        st.markdown(f"**{chart['title']}**")
                        try:
                            fig_dict = json.loads(chart["plotly_json"])
                            fig = go.Figure(fig_dict)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Chart render error: {e}")
        elif not st.session_state.get("charts"):
            st.info("Click 'Generate Charts' to create visualisations.")

    # AI Insights
    with tab_insights:
        st.subheader("AI-Generated Insights")

        if st.button("🤖 Generate AI Insights", type="primary"):
            with st.spinner("Analysing dataset with AI..."):
                try:
                    insight_data = get_ai_insights(file_id)
                    st.session_state["ai_insights"] = insight_data["insights"]
                except Exception as e:
                    st.error(f"❌ Insight generation failed: {e}")

        if insights := st.session_state.get("ai_insights"):
            st.markdown(insights)
        else:
            st.info("Click 'Generate AI Insights' to get observations and recommendations.")

    # Q&A
    with tab_qa:
        st.subheader("Ask Questions About Your Data")
        st.markdown(
            "The AI generates and executes pandas code to answer your questions."
        )

        if "data_qa_history" not in st.session_state:
            st.session_state["data_qa_history"] = []

        for qa in st.session_state["data_qa_history"]:
            with st.chat_message("user"):
                st.markdown(qa["question"])
            with st.chat_message("assistant"):
                st.markdown(qa["answer"])

        examples = [
            "What is the average value of each numeric column?",
            "Which rows have the highest values in column X?",
            "How many missing values are there in each column?",
            "What is the correlation between column A and column B?",
            "Show the distribution of the target column.",
        ]
        st.caption(
            "Example questions: " + " | ".join(f"*{e}*" for e in examples[:3])
        )

        if question := st.chat_input("Ask anything about your data..."):
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Running analysis..."):
                    try:
                        resp = ask_about_data(file_id=file_id, question=question)
                        answer = resp.get("answer", "No answer.")
                        st.markdown(answer)
                        st.session_state["data_qa_history"].append(
                            {"question": question, "answer": answer}
                        )
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
