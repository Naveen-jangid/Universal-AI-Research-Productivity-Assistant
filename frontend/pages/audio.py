"""
Speech & Audio Processing page.
Upload audio → transcribe with Whisper → summarise → Q&A.
"""

import streamlit as st
from frontend.utils.api_client import ask_about_audio, process_audio


def render() -> None:
    st.title("🎙️ Speech & Audio Processing")
    st.markdown(
        "Upload audio or video files to transcribe speech using OpenAI Whisper, "
        "generate structured summaries, extract keywords, and ask questions."
    )

    # ── Upload section ────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload audio/video file",
        type=["mp3", "mp4", "wav", "ogg", "webm", "m4a", "mpeg"],
    )

    if uploaded:
        st.audio(uploaded)

        if st.button("🎤 Transcribe & Analyse", type="primary"):
            with st.spinner("Transcribing... this may take a minute for long recordings..."):
                try:
                    result = process_audio(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "audio/mpeg",
                    )
                    st.session_state["audio_result"] = result
                    st.success("✅ Audio processed successfully!")
                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")

    # ── Results section ───────────────────────────────────────────────────
    if result := st.session_state.get("audio_result"):
        tab_transcript, tab_summary, tab_keywords, tab_qa = st.tabs(
            ["📝 Transcript", "📋 Summary", "🏷️ Keywords", "❓ Q&A"]
        )

        with tab_transcript:
            st.subheader("Full Transcript")
            col1, col2 = st.columns([3, 1])
            with col2:
                st.metric("Word Count", result.get("word_count", 0))
                st.download_button(
                    "💾 Download Transcript",
                    data=result.get("transcript", ""),
                    file_name="transcript.txt",
                    mime="text/plain",
                )
            with col1:
                transcript_text = result.get("transcript", "No transcript available.")
                st.text_area("Transcript", value=transcript_text, height=400, disabled=True)

        with tab_summary:
            st.subheader("AI-Generated Summary")
            st.markdown(result.get("summary", "No summary available."))

            st.download_button(
                "💾 Download Summary",
                data=result.get("summary", ""),
                file_name="summary.txt",
                mime="text/plain",
            )

        with tab_keywords:
            st.subheader("Extracted Keywords & Topics")
            keywords = result.get("keywords", [])
            if keywords:
                # Display as tags
                cols = st.columns(min(len(keywords), 5))
                for i, kw in enumerate(keywords):
                    cols[i % 5].markdown(
                        f"<span style='background:#e8f4f8;padding:4px 8px;"
                        f"border-radius:12px;font-size:0.85em'>{kw}</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No keywords extracted.")

        with tab_qa:
            st.subheader("Ask Questions About the Audio")

            if "audio_qa_history" not in st.session_state:
                st.session_state["audio_qa_history"] = []

            for qa in st.session_state["audio_qa_history"]:
                with st.chat_message("user"):
                    st.markdown(qa["question"])
                with st.chat_message("assistant"):
                    st.markdown(qa["answer"])

            question = st.chat_input("Ask about the audio content...")
            if question and question.strip():
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            resp = ask_about_audio(
                                transcript=result.get("transcript", ""),
                                question=question,
                            )
                            answer = resp.get("answer", "")
                            st.markdown(answer)
                            st.session_state["audio_qa_history"].append(
                                {"question": question, "answer": answer}
                            )
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
