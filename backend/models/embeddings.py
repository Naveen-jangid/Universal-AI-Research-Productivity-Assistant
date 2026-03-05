"""
Embedding model abstraction.
Prefers OpenAI text-embedding-3-small; falls back to a local
sentence-transformers model when no API key is provided.
"""

import logging
from functools import lru_cache
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Return a cached LangChain embedding model.
    Uses OpenAI if OPENAI_API_KEY is set, else HuggingFace sentence-transformers.
    """
    if settings.OPENAI_API_KEY:
        logger.info("Using OpenAI embeddings: %s", settings.OPENAI_EMBEDDING_MODEL)
        return OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
    else:
        logger.info("Using HuggingFace embeddings: %s", settings.HF_EMBEDDING_MODEL)
        return HuggingFaceEmbeddings(
            model_name=settings.HF_EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of strings and return their float vectors.
    """
    model = get_embedding_model()
    return model.embed_documents(texts)


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    model = get_embedding_model()
    return model.embed_query(query)
