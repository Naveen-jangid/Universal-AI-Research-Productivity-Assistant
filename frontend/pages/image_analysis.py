"""
Image Analysis page.
Upload images → multimodal AI analysis → follow-up Q&A.
"""

import streamlit as st
from frontend.utils.api_client import analyse_image


def render() -> None:
    st.title("🖼️ Image Analysis")
    st.markdown(
        "Upload images and let the AI describe, analyse, and answer questions about them. "
        "Powered by GPT-4o Vision."
    )

    # ── Upload section ────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"],
    )

    if uploaded:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded, caption=uploaded.name, use_container_width=True)

        with col2:
            prompt = st.text_area(
                "Analysis prompt (optional)",
                value="Describe this image in detail. Include objects, colors, mood, and any text visible.",
                height=120,
            )

            analyse_btn = st.button("🔍 Analyse Image", type="primary")

        if analyse_btn:
            with st.spinner("Analysing image with AI vision..."):
                try:
                    result = analyse_image(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "image/jpeg",
                        prompt=prompt,
                    )

                    # Store result for Q&A
                    st.session_state["last_image_analysis"] = result
                    st.session_state["last_image_path"] = result.get("image_id", "")

                    st.subheader("📊 Analysis Results")

                    # Description
                    st.markdown("**Description:**")
                    st.markdown(result["description"])

                    # Metadata
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if result.get("objects"):
                            st.markdown("**Detected Objects:**")
                            for obj in result["objects"]:
                                st.markdown(f"• {obj}")
                    with col_b:
                        sentiment = result.get("sentiment", "neutral")
                        sentiment_icons = {
                            "positive": "😊",
                            "neutral": "😐",
                            "negative": "😟",
                        }
                        st.metric(
                            "Overall Sentiment",
                            f"{sentiment_icons.get(sentiment, '❓')} {sentiment.title()}",
                        )

                    if result.get("additional_notes"):
                        with st.expander("Additional Notes"):
                            st.markdown(result["additional_notes"])

                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")

    # ── Follow-up Q&A section ─────────────────────────────────────────────
    if st.session_state.get("last_image_analysis"):
        st.divider()
        st.subheader("❓ Ask About This Image")

        if "image_qa_history" not in st.session_state:
            st.session_state["image_qa_history"] = []

        for qa in st.session_state["image_qa_history"]:
            with st.chat_message("user"):
                st.markdown(qa["question"])
            with st.chat_message("assistant"):
                st.markdown(qa["answer"])

        question = st.text_input("Ask a follow-up question about the image...")
        if st.button("Ask") and question.strip():
            prior_desc = st.session_state["last_image_analysis"].get("description", "")
            with st.spinner("Thinking..."):
                try:
                    from frontend.utils.api_client import _post_json

                    resp = _post_json(
                        "/images/question",
                        {
                            "image_path": st.session_state.get("last_image_path", ""),
                            "question": question,
                            "prior_description": prior_desc,
                        },
                    )
                    answer = resp.get("answer", "No answer generated.")
                    st.session_state["image_qa_history"].append(
                        {"question": question, "answer": answer}
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
