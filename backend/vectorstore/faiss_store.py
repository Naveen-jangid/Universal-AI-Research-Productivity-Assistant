"""
FAISS-backed vector store wrapper.
Provides persist/load, add-documents, and similarity-search operations.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from backend.core.config import settings
from backend.models.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

_STORE_CACHE: Dict[str, FAISS] = {}


def _index_path(namespace: str) -> str:
    """Return the filesystem path for a named FAISS index."""
    return str(Path(settings.FAISS_INDEX_PATH) / namespace)


def load_or_create_store(namespace: str = "default") -> FAISS:
    """
    Load a persisted FAISS store from disk or create a fresh empty one.

    Args:
        namespace: Logical name for the index (one per document collection).

    Returns:
        FAISS instance ready for querying / adding.
    """
    if namespace in _STORE_CACHE:
        return _STORE_CACHE[namespace]

    embedding_model = get_embedding_model()
    index_dir = _index_path(namespace)

    if Path(index_dir).exists() and any(Path(index_dir).iterdir()):
        logger.info("Loading FAISS index from %s", index_dir)
        store = FAISS.load_local(
            index_dir,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
    else:
        logger.info("Creating new FAISS index (namespace=%s)", namespace)
        # Bootstrap with a placeholder so the index is valid
        placeholder = Document(
            page_content="__placeholder__",
            metadata={"source": "system", "namespace": namespace},
        )
        store = FAISS.from_documents([placeholder], embedding_model)
        _persist(store, namespace)

    _STORE_CACHE[namespace] = store
    return store


def _persist(store: FAISS, namespace: str) -> None:
    """Persist FAISS index to disk."""
    index_dir = _index_path(namespace)
    Path(index_dir).mkdir(parents=True, exist_ok=True)
    store.save_local(index_dir)
    logger.debug("FAISS index saved: %s", index_dir)


def add_documents(
    documents: List[Document],
    namespace: str = "default",
) -> int:
    """
    Embed and add a list of LangChain Document objects to the named index.

    Returns:
        Number of documents added.
    """
    if not documents:
        return 0

    store = load_or_create_store(namespace)
    store.add_documents(documents)
    _persist(store, namespace)
    logger.info("Added %d documents to FAISS (namespace=%s)", len(documents), namespace)
    return len(documents)


def similarity_search(
    query: str,
    namespace: str = "default",
    k: int = None,
    score_threshold: float = 0.0,
) -> List[Tuple[Document, float]]:
    """
    Return the top-k most similar documents and their relevance scores.

    Args:
        query: The user's query string.
        namespace: Which index to search.
        k: Number of results (defaults to settings.TOP_K_RETRIEVAL).
        score_threshold: Minimum score to include (0 = include all).

    Returns:
        List of (Document, score) tuples sorted by descending relevance.
    """
    k = k or settings.TOP_K_RETRIEVAL
    store = load_or_create_store(namespace)

    results = store.similarity_search_with_relevance_scores(query, k=k)

    # Filter placeholder documents and low-score results
    filtered = [
        (doc, score)
        for doc, score in results
        if doc.page_content != "__placeholder__" and score >= score_threshold
    ]
    logger.debug(
        "Similarity search '%s' → %d results (namespace=%s)", query, len(filtered), namespace
    )
    return filtered


def delete_namespace(namespace: str) -> None:
    """Remove a FAISS index from disk and cache."""
    _STORE_CACHE.pop(namespace, None)
    import shutil

    index_dir = _index_path(namespace)
    if Path(index_dir).exists():
        shutil.rmtree(index_dir)
        logger.info("Deleted FAISS namespace: %s", namespace)


def list_namespaces() -> List[str]:
    """List all persisted FAISS namespaces."""
    base = Path(settings.FAISS_INDEX_PATH)
    if not base.exists():
        return []
    return [d.name for d in base.iterdir() if d.is_dir()]
