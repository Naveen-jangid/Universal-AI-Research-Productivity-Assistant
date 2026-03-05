"""
Document Q&A page.
Upload documents → ingest into vector store → ask questions via RAG.
"""

import streamlit as st
from frontend.utils.api_client import (
    ask_document,
    list_documents,
    list_namespaces,
    upload_document,
)


def render() -> None:
    st.title("📄 Document Intelligence (RAG)")
    st.markdown(
        "Upload PDF, Word, or text documents. The AI will extract, chunk, "
        "and index them so you can ask questions in natural language."
    )

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab_upload, tab_qa, tab_library = st.tabs(["📤 Upload", "❓ Ask Questions", "📚 Library"])

    # ── Upload tab ────────────────────────────────────────────────────────
    with tab_upload:
        st.subheader("Upload a Document")
        uploaded = st.file_uploader(
            "Choose a file (PDF, DOCX, TXT, MD)",
            type=["pdf", "docx", "txt", "md", "rst"],
        )

        namespaces = ["default"]
        try:
            namespaces = list_namespaces() or ["default"]
        except Exception:
            pass

        col1, col2 = st.columns(2)
        with col1:
            namespace = st.selectbox(
                "Collection (namespace)", options=namespaces, index=0
            )
        with col2:
            new_ns = st.text_input("Or create new collection")

        final_namespace = new_ns.strip() if new_ns.strip() else namespace

        if uploaded and st.button("📥 Ingest Document", type="primary"):
            with st.spinner(f"Processing '{uploaded.name}'..."):
                try:
                    result = upload_document(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        namespace=final_namespace,
                        content_type=uploaded.type or "application/octet-stream",
                    )
                    st.success(
                        f"✅ **{uploaded.name}** ingested successfully!\n\n"
                        f"- Chunks stored: **{result['chunk_count']}**\n"
                        f"- Collection: **{result['namespace']}**\n"
                        f"- Document ID: `{result['doc_id']}`"
                    )
                    st.session_state["last_doc_namespace"] = final_namespace
                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

    # ── Q&A tab ───────────────────────────────────────────────────────────
    with tab_qa:
        st.subheader("Ask Questions About Your Documents")

        if "doc_qa_history" not in st.session_state:
            st.session_state["doc_qa_history"] = []

        try:
            namespaces = list_namespaces() or ["default"]
        except Exception:
            namespaces = ["default"]

        col1, col2 = st.columns([3, 1])
        with col1:
            qa_namespace = st.selectbox(
                "Search in collection",
                options=namespaces,
                index=0,
                key="qa_namespace",
            )
        with col2:
            top_k = st.number_input("Top K chunks", min_value=1, max_value=20, value=5)

        # Display Q&A history
        for qa in st.session_state["doc_qa_history"]:
            with st.expander(f"Q: {qa['question'][:80]}..."):
                st.markdown(f"**Answer:** {qa['answer']}")
                if qa.get("sources"):
                    st.markdown(f"**Sources:** {', '.join(qa['sources'])}")
                st.caption(f"Retrieved {qa.get('chunks', 0)} chunks")

        question = st.text_area(
            "Your question",
            placeholder="What does the document say about...?",
            height=100,
        )
        if st.button("🔍 Search & Answer", type="primary") and question.strip():
            with st.spinner("Searching documents and generating answer..."):
                try:
                    result = ask_document(
                        question=question.strip(),
                        namespace=qa_namespace,
                        k=top_k,
                    )
                    st.session_state["doc_qa_history"].append(
                        {
                            "question": question,
                            "answer": result["answer"],
                            "sources": result.get("sources", []),
                            "chunks": result.get("retrieved_chunks", 0),
                        }
                    )

                    st.subheader("Answer")
                    st.markdown(result["answer"])

                    if result.get("sources"):
                        st.info(f"📚 **Sources:** {', '.join(result['sources'])}")

                    with st.expander("View context chunks"):
                        st.text(result.get("context_preview", ""))

                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # ── Library tab ───────────────────────────────────────────────────────
    with tab_library:
        st.subheader("Ingested Documents")
        if st.button("🔄 Refresh"):
            st.rerun()

        try:
            docs = list_documents()
            if not docs:
                st.info("No documents ingested yet. Upload documents in the Upload tab.")
            else:
                for doc in docs:
                    status_icon = {"ready": "✅", "pending": "⏳", "error": "❌"}.get(
                        doc["status"], "❓"
                    )
                    with st.expander(
                        f"{status_icon} {doc['filename']} ({doc['chunk_count']} chunks)"
                    ):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Status", doc["status"])
                        col2.metric("Chunks", doc["chunk_count"])
                        col3.metric(
                            "Size", f"{doc['file_size'] / 1024:.1f} KB"
                        )
                        st.caption(
                            f"ID: `{doc['id']}` | Type: {doc['file_type']} | "
                            f"Uploaded: {doc['created_at'][:10]}"
                        )
        except Exception as e:
            st.error(f"Could not load document list: {e}")
