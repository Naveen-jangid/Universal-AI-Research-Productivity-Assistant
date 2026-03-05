"""
Long-term memory module.
Stores important facts from conversations in SQLite and retrieves them
by semantic relevance using FAISS so the assistant remembers users across sessions.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.core.config import settings
from backend.core.database import (
    get_memory_facts,
    save_memory_fact,
    search_memory_facts,
)
from backend.models.llm import LLMFactory, build_messages
from backend.vectorstore.faiss_store import (
    add_documents,
    similarity_search,
)
from langchain.schema import Document

logger = logging.getLogger(__name__)

MEMORY_NAMESPACE = "long_term_memory"


class LongTermMemory:
    """
    Provides persistent, cross-session memory for the AI assistant.

    Architecture:
    - Facts are stored in SQLite (for persistence and metadata).
    - Facts are also embedded and stored in FAISS (for semantic retrieval).
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    # ── Extraction ─────────────────────────────────────────────────────────

    def extract_facts(self, conversation_turn: str) -> List[Dict]:
        """
        Use the LLM to extract memorable facts from a conversation turn.

        Args:
            conversation_turn: A combined user+assistant message string.

        Returns:
            List of fact dicts: {fact, category, importance}.
        """
        llm = LLMFactory.get_chat_llm(temperature=0.1)
        messages = build_messages(
            system_prompt=(
                "You are a memory extraction system. "
                "Extract ONLY factual, important, and reusable information from the conversation. "
                "Focus on: user preferences, stated goals, personal details, key decisions. "
                "Return a JSON array of objects with fields:\n"
                '  - "fact": the factual statement (concise, ≤ 50 words)\n'
                '  - "category": one of [preference, goal, personal, technical, other]\n'
                '  - "importance": float 0.0-1.0\n'
                "Return [] if nothing important to remember.\n"
                "ONLY output valid JSON, no explanation."
            ),
            conversation_history=[],
            user_message=f"Conversation:\n{conversation_turn}",
        )
        try:
            response = llm.invoke(messages)
            raw = response.content.strip().lstrip("```json").rstrip("```").strip()
            facts = json.loads(raw)
            return facts if isinstance(facts, list) else []
        except Exception as e:
            logger.warning("Fact extraction failed: %s", e)
            return []

    # ── Storage ────────────────────────────────────────────────────────────

    def store_facts(self, facts: List[Dict]) -> None:
        """Persist extracted facts to SQLite and FAISS."""
        for f in facts:
            fact_text = f.get("fact", "")
            category = f.get("category", "general")
            importance = float(f.get("importance", 0.5))

            if not fact_text:
                continue

            # SQLite
            save_memory_fact(
                session_id=self.session_id,
                fact=fact_text,
                category=category,
                importance=importance,
            )

            # FAISS (for semantic similarity search)
            doc = Document(
                page_content=fact_text,
                metadata={
                    "session_id": self.session_id,
                    "category": category,
                    "importance": importance,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            add_documents([doc], namespace=MEMORY_NAMESPACE)

        logger.info("Stored %d memory facts for session %s", len(facts), self.session_id)

    # ── Retrieval ──────────────────────────────────────────────────────────

    def retrieve_relevant_facts(self, query: str, k: int = 10) -> List[str]:
        """
        Retrieve the most relevant long-term memory facts for a query.

        Args:
            query: The user's current message.
            k: Maximum number of facts to retrieve.

        Returns:
            List of fact strings.
        """
        # Semantic search in FAISS
        results = similarity_search(query, namespace=MEMORY_NAMESPACE, k=k)
        semantic_facts = [
            doc.page_content
            for doc, score in results
            if doc.metadata.get("session_id") == self.session_id and score > 0.5
        ]

        # Keyword fallback from SQLite
        keyword_facts = search_memory_facts(self.session_id, query[:30])
        keyword_texts = [f["fact"] for f in keyword_facts[:5]]

        # Merge and deduplicate
        all_facts = list(dict.fromkeys(semantic_facts + keyword_texts))
        logger.debug("Retrieved %d memory facts for query '%s'", len(all_facts), query[:50])
        return all_facts[:k]

    def get_all_facts(self) -> List[Dict]:
        """Return all stored facts for this session from SQLite."""
        return get_memory_facts(self.session_id)

    # ── Memory context builder ─────────────────────────────────────────────

    def build_memory_context(self, query: str) -> str:
        """
        Build a formatted memory context string to inject into the system prompt.

        Args:
            query: Current user query.

        Returns:
            str: Formatted memory context, or empty string if no facts.
        """
        facts = self.retrieve_relevant_facts(query)
        if not facts:
            return ""
        lines = ["[Long-term memory context]"]
        for i, fact in enumerate(facts, 1):
            lines.append(f"{i}. {fact}")
        return "\n".join(lines)

    # ── Conversation processing ────────────────────────────────────────────

    def process_conversation_turn(
        self, user_message: str, assistant_reply: str
    ) -> int:
        """
        Extract and store facts from a completed conversation turn.

        Args:
            user_message: What the user said.
            assistant_reply: What the assistant replied.

        Returns:
            Number of facts stored.
        """
        combined = f"User: {user_message}\nAssistant: {assistant_reply}"
        facts = self.extract_facts(combined)
        if facts:
            self.store_facts(facts)
        return len(facts)
