"""
Image Analysis page.
Upload images → multimodal AI analysis → follow-up Q&A.
"""

import streamlit as st
from frontend.utils.api_client import analyse_image


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>🖼️ Image Analysis</h1>
            <p>Upload any image and get an AI-powered description, object detection, sentiment, and follow-up Q&amp;A.</p>
            <span class="badge">GPT-4o Vision</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Upload & analyse ──────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload an image (JPG, PNG, WEBP, GIF, BMP, TIFF)",
        type=["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"],
        label_visibility="collapsed",
    )

    if uploaded:
        col_img, col_ctrl = st.columns([1, 1])

        with col_img:
            st.markdown('<div class="card" style="padding:0.75rem;">', unsafe_allow_html=True)
            st.image(uploaded, caption=uploaded.name, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_ctrl:
            st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
            st.markdown("**Analysis prompt**")
            prompt = st.text_area(
                "Prompt",
                value="Describe this image in detail. Include objects, colors, mood, and any text visible.",
                height=120,
                label_visibility="collapsed",
            )
            analyse_btn = st.button("🔍 Analyse Image", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if analyse_btn:
            with st.spinner("Analysing with GPT-4o Vision…"):
                try:
                    result = analyse_image(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "image/jpeg",
                        prompt=prompt,
                    )
                    st.session_state["last_image_analysis"] = result
                    st.session_state["last_image_path"] = result.get("image_id", "")

                    st.markdown(
                        '<div class="card card-accent" style="margin-top:1rem;">'
                        '<strong style="color:#6366f1;">Analysis Results</strong>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    # Description
                    st.markdown(
                        '<div class="card">'
                        f'<strong>Description</strong><br><br>{result["description"]}'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    # Metadata row
                    c1, c2 = st.columns(2)
                    with c1:
                        if result.get("objects"):
                            st.markdown("**Detected Objects**")
                            tags_html = " ".join(
                                f'<span class="badge-blue">{obj}</span>' for obj in result["objects"]
                            )
                            st.markdown(tags_html, unsafe_allow_html=True)
                    with c2:
                        sentiment = result.get("sentiment", "neutral")
                        icons = {"positive": "😊", "neutral": "😐", "negative": "😟"}
                        st.metric("Sentiment", f"{icons.get(sentiment, '❓')} {sentiment.title()}")

                    if result.get("additional_notes"):
                        with st.expander("Additional Notes"):
                            st.markdown(result["additional_notes"])

                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")

    # ── Follow-up Q&A ─────────────────────────────────────────────────────
    if st.session_state.get("last_image_analysis"):
        st.divider()
        st.markdown(
            '<div style="font-size:1.05rem;font-weight:600;margin-bottom:0.5rem;">❓ Ask about this image</div>',
            unsafe_allow_html=True,
        )

        if "image_qa_history" not in st.session_state:
            st.session_state["image_qa_history"] = []

        for qa in st.session_state["image_qa_history"]:
            with st.chat_message("user"):
                st.markdown(qa["question"])
            with st.chat_message("assistant"):
                st.markdown(qa["answer"])

        question = st.chat_input("Ask a follow-up question about the image…")
        if question and question.strip():
            prior_desc = st.session_state["last_image_analysis"].get("description", "")
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
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
                        st.markdown(answer)
                        st.session_state["image_qa_history"].append({"question": question, "answer": answer})
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
