"""
Document Q&A page.
Upload documents → ingest into vector store → ask questions via RAG.
"""

import streamlit as st
from frontend.utils.api_client import ask_document, list_documents, list_namespaces, upload_document


def render() -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>📄 Document Intelligence</h1>
            <p>Upload PDFs, Word docs, or text files. The AI indexes them for semantic search and RAG-powered Q&amp;A.</p>
            <span class="badge">FAISS · LangChain · GPT-4o</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_upload, tab_qa, tab_library = st.tabs(["📤 Upload", "❓ Ask Questions", "📚 Library"])

    # ── Upload tab ────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
        st.markdown("**Step 1 — Choose a file**")
        uploaded = st.file_uploader(
            "Supported: PDF, DOCX, TXT, MD, RST",
            type=["pdf", "docx", "txt", "md", "rst"],
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        namespaces = ["default"]
        try:
            namespaces = list_namespaces() or ["default"]
        except Exception:
            pass

        st.markdown("**Step 2 — Choose a collection**")
        col1, col2 = st.columns(2)
        with col1:
            namespace = st.selectbox("Existing collection", options=namespaces)
        with col2:
            new_ns = st.text_input("Or create new collection", placeholder="my-research")

        final_namespace = new_ns.strip() if new_ns.strip() else namespace

        st.markdown(f"Will ingest into: `{final_namespace}`")

        if uploaded:
            st.markdown(
                f'<div class="card" style="padding:0.65rem 1rem;margin:0.5rem 0;">'
                f'📎 <strong>{uploaded.name}</strong>'
                f'<span style="color:#64748b;font-size:0.82rem;margin-left:12px;">'
                f'{uploaded.size / 1024:.1f} KB</span></div>',
                unsafe_allow_html=True,
            )

        if uploaded and st.button("📥 Ingest Document", type="primary"):
            with st.spinner(f"Processing '{uploaded.name}'…"):
                try:
                    result = upload_document(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        namespace=final_namespace,
                        content_type=uploaded.type or "application/octet-stream",
                    )
                    st.success(f"✅ **{uploaded.name}** ingested successfully!")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Chunks stored", result["chunk_count"])
                    c2.metric("Collection", result["namespace"])
                    c3.metric("Doc ID", result["doc_id"][:8] + "…")
                    st.session_state["last_doc_namespace"] = final_namespace
                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

    # ── Q&A tab ───────────────────────────────────────────────────────────
    with tab_qa:
        if "doc_qa_history" not in st.session_state:
            st.session_state["doc_qa_history"] = []

        try:
            namespaces = list_namespaces() or ["default"]
        except Exception:
            namespaces = ["default"]

        col1, col2 = st.columns([3, 1])
        with col1:
            qa_namespace = st.selectbox("Search in collection", options=namespaces, key="qa_namespace")
        with col2:
            top_k = st.number_input("Top K chunks", min_value=1, max_value=20, value=5)

        # Q&A history
        for qa in st.session_state["doc_qa_history"]:
            with st.chat_message("user"):
                st.markdown(qa["question"])
            with st.chat_message("assistant"):
                st.markdown(qa["answer"])
                if qa.get("sources"):
                    st.markdown(
                        '<span class="badge-blue">📚 ' + " · ".join(qa["sources"]) + "</span>",
                        unsafe_allow_html=True,
                    )
                st.caption(f"Retrieved {qa.get('chunks', 0)} chunks")

        question = st.chat_input("Ask a question about your documents…")
        if question and question.strip():
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching and generating answer…"):
                    try:
                        result = ask_document(question=question.strip(), namespace=qa_namespace, k=top_k)
                        st.session_state["doc_qa_history"].append({
                            "question": question,
                            "answer": result["answer"],
                            "sources": result.get("sources", []),
                            "chunks": result.get("retrieved_chunks", 0),
                        })
                        st.markdown(result["answer"])
                        if result.get("sources"):
                            st.markdown(
                                '<span class="badge-blue">📚 ' + " · ".join(result["sources"]) + "</span>",
                                unsafe_allow_html=True,
                            )
                        with st.expander("View context chunks"):
                            st.text(result.get("context_preview", ""))
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── Library tab ───────────────────────────────────────────────────────
    with tab_library:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown("**Ingested documents**")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()

        try:
            docs = list_documents()
            if not docs:
                st.markdown(
                    '<div class="card" style="text-align:center;padding:2rem;color:#64748b;">'
                    '📭 No documents ingested yet. Upload documents in the Upload tab.'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                for doc in docs:
                    status_icon = {"ready": "✅", "pending": "⏳", "error": "❌"}.get(doc["status"], "❓")
                    badge_cls = {"ready": "badge-green", "pending": "badge-blue", "error": "badge-red"}.get(
                        doc["status"], "badge-blue"
                    )
                    with st.expander(f"{status_icon} {doc['filename']}  —  {doc['chunk_count']} chunks"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Status", doc["status"])
                        c2.metric("Chunks", doc["chunk_count"])
                        c3.metric("Size", f"{doc['file_size'] / 1024:.1f} KB")
                        st.caption(
                            f"ID: `{doc['id']}` · Type: {doc['file_type']} · "
                            f"Uploaded: {doc['created_at'][:10]}"
                        )
        except Exception as e:
            st.error(f"Could not load document list: {e}")
