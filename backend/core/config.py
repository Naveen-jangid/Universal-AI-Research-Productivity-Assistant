"""
Core configuration for Universal AI Research & Productivity Assistant.
Loads environment variables and provides a central Settings object.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "Universal AI Research & Productivity Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_VISION_MODEL: str = "gpt-4o"
    OPENAI_WHISPER_MODEL: str = "whisper-1"

    # ── HuggingFace ────────────────────────────────────────────────────────────
    HUGGINGFACE_API_TOKEN: str = ""
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HF_QA_MODEL: str = "deepset/roberta-base-squad2"

    # ── Vector Store ───────────────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "vectorstore/faiss_index"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5

    # ── Storage ────────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Memory / SQLite ────────────────────────────────────────────────────────
    SQLITE_DB_PATH: str = "memory/assistant.db"
    MEMORY_WINDOW_SIZE: int = 20       # messages kept in short-term memory
    MAX_MEMORY_TOKENS: int = 4000

    # ── Web Search (SerpAPI) ───────────────────────────────────────────────────
    SERPAPI_API_KEY: str = ""

    # ── Data Analysis ──────────────────────────────────────────────────────────
    MAX_ROWS_DISPLAY: int = 1000
    PLOT_BACKEND: str = "plotly"

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/assistant.log"

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_API_KEY_AUTH: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    # ── Derived paths ──────────────────────────────────────────────────────────
    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def faiss_path(self) -> Path:
        p = Path(self.FAISS_INDEX_PATH)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sqlite_path(self) -> Path:
        p = Path(self.SQLITE_DB_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


settings = get_settings()
