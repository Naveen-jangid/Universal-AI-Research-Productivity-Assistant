"""
Retrieval-Augmented Generation (RAG) pipeline.
Retrieves relevant document chunks from FAISS and feeds them to the LLM
to answer user questions grounded in uploaded documents.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from backend.core.config import settings
from backend.models.llm import LLMFactory, build_messages
from backend.vectorstore.faiss_store import load_or_create_store, similarity_search

logger = logging.getLogger(__name__)


RAG_PROMPT_TEMPLATE = """You are an expert research assistant with access to the provided documents.
Use the following retrieved context to answer the question accurately and concisely.
If the context does not contain enough information, say so clearly and explain what you do know.
Always cite the source document name when referencing specific information.

Context:
{context}

Question: {question}

Answer:"""


def format_context(retrieved: List[Tuple[Document, float]]) -> str:
    """
    Format retrieved (Document, score) pairs into a readable context string.
    """
    parts = []
    for i, (doc, score) in enumerate(retrieved, start=1):
        source = doc.metadata.get("source", "Unknown")
        chunk_idx = doc.metadata.get("chunk_index", "?")
        parts.append(
            f"[Source {i}: {source}, chunk {chunk_idx}, relevance {score:.2f}]\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def answer_with_rag(
    question: str,
    namespace: str = "default",
    conversation_history: Optional[List[Dict[str, str]]] = None,
    k: int = None,
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline.

    Args:
        question: The user's question.
        namespace: FAISS namespace to search.
        conversation_history: Prior messages for multi-turn context.
        k: Number of chunks to retrieve.
        temperature: LLM temperature.

    Returns:
        Dict with keys: answer, sources, retrieved_chunks.
    """
    k = k or settings.TOP_K_RETRIEVAL

    # 1. Retrieve relevant chunks
    retrieved = similarity_search(question, namespace=namespace, k=k)

    if not retrieved:
        return {
            "answer": (
                "I couldn't find any relevant documents in the knowledge base. "
                "Please upload documents first."
            ),
            "sources": [],
            "retrieved_chunks": 0,
        }

    # 2. Format context
    context = format_context(retrieved)

    # 3. Build prompt
    prompt = PromptTemplate(
        template=RAG_PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )
    filled_prompt = prompt.format(context=context, question=question)

    # 4. Add conversation history if any
    history = conversation_history or []

    # 5. LLM call
    llm = LLMFactory.get_chat_llm(temperature=temperature)
    messages = build_messages(
        system_prompt=(
            "You are an expert research assistant. "
            "Answer questions based strictly on the provided document context."
        ),
        conversation_history=history,
        user_message=filled_prompt,
    )
    response = llm.invoke(messages)
    answer = response.content

    # 6. Collect unique sources
    sources = list(
        {doc.metadata.get("source", "Unknown") for doc, _ in retrieved}
    )

    logger.info(
        "RAG answer: %d chars, %d sources, %d chunks", len(answer), len(sources), len(retrieved)
    )
    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved),
        "context_preview": context[:500] + "..." if len(context) > 500 else context,
    }


def build_langchain_rag_chain(
    namespace: str = "default",
    temperature: float = 0.3,
) -> RetrievalQA:
    """
    Build a LangChain RetrievalQA chain for the given FAISS namespace.
    Useful for streaming / complex orchestration scenarios.
    """
    store = load_or_create_store(namespace)
    retriever = store.as_retriever(search_kwargs={"k": settings.TOP_K_RETRIEVAL})
    llm = LLMFactory.get_chat_llm(temperature=temperature)

    prompt = PromptTemplate(
        template=RAG_PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    return chain
