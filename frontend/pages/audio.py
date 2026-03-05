"""
Speech & Audio Processing page.
Upload audio → transcribe with Whisper → summarise → Q&A.
"""

import streamlit as st
from frontend.utils.api_client import ask_about_audio, process_audio


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>🎙️ Speech & Audio Processing</h1>
            <p>Upload audio or video files to transcribe, summarise, extract keywords, and ask questions.</p>
            <span class="badge">OpenAI Whisper</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Upload section ────────────────────────────────────────────────────
    st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Supported: MP3, MP4, WAV, OGG, WEBM, M4A, MPEG",
        type=["mp3", "mp4", "wav", "ogg", "webm", "m4a", "mpeg"],
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded:
        st.audio(uploaded)
        st.markdown(
            f'<div class="card" style="padding:0.6rem 1rem;margin:0.5rem 0;">'
            f'🎵 <strong>{uploaded.name}</strong>'
            f'<span style="color:#64748b;font-size:0.82rem;margin-left:12px;">'
            f'{uploaded.size / 1024:.1f} KB</span></div>',
            unsafe_allow_html=True,
        )

        if st.button("🎤 Transcribe & Analyse", type="primary"):
            with st.spinner("Transcribing… this may take a minute for long recordings"):
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
        st.markdown("<br>", unsafe_allow_html=True)
        tab_transcript, tab_summary, tab_keywords, tab_qa = st.tabs(
            ["📝 Transcript", "📋 Summary", "🏷️ Keywords", "❓ Q&A"]
        )

        with tab_transcript:
            c1, c2 = st.columns([4, 1])
            with c2:
                st.metric("Words", result.get("word_count", 0))
                st.download_button(
                    "💾 Download",
                    data=result.get("transcript", ""),
                    file_name="transcript.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with c1:
                st.text_area(
                    "Full Transcript",
                    value=result.get("transcript", "No transcript available."),
                    height=400,
                    disabled=True,
                )

        with tab_summary:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(result.get("summary", "No summary available."))
            st.markdown("</div>", unsafe_allow_html=True)
            st.download_button(
                "💾 Download Summary",
                data=result.get("summary", ""),
                file_name="summary.txt",
                mime="text/plain",
            )

        with tab_keywords:
            keywords = result.get("keywords", [])
            if keywords:
                tags_html = " ".join(
                    f'<span class="badge-purple" style="margin:3px;display:inline-block;">{kw}</span>'
                    for kw in keywords
                )
                st.markdown(f'<div style="line-height:2.2;">{tags_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No keywords extracted.")

        with tab_qa:
            if "audio_qa_history" not in st.session_state:
                st.session_state["audio_qa_history"] = []

            for qa in st.session_state["audio_qa_history"]:
                with st.chat_message("user"):
                    st.markdown(qa["question"])
                with st.chat_message("assistant"):
                    st.markdown(qa["answer"])

            question = st.chat_input("Ask about the audio content…")
            if question and question.strip():
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
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
