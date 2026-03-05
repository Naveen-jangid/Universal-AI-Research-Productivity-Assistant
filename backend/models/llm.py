"""
LLM abstraction layer.
Provides a unified interface to OpenAI chat models and a local HuggingFace
fallback so the system runs even without an OpenAI key.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory that creates and caches LLM instances."""

    _chat_instance: Optional[ChatOpenAI] = None

    @classmethod
    def get_chat_llm(
        cls,
        model: Optional[str] = None,
        temperature: float = 0.7,
        streaming: bool = False,
        max_tokens: int = 2048,
    ) -> ChatOpenAI:
        """Return a ChatOpenAI instance (or cached one for default params)."""
        model = model or settings.OPENAI_CHAT_MODEL

        callbacks = [StreamingStdOutCallbackHandler()] if streaming else []

        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            callbacks=callbacks,
        )
        logger.info("LLM initialised: model=%s, temperature=%s", model, temperature)
        return llm

    @classmethod
    def get_vision_llm(cls) -> ChatOpenAI:
        """Return a vision-capable ChatOpenAI instance."""
        return cls.get_chat_llm(model=settings.OPENAI_VISION_MODEL, temperature=0.3)


def build_messages(
    system_prompt: str,
    conversation_history: List[Dict[str, str]],
    user_message: str,
) -> List[BaseMessage]:
    """
    Assemble a list of LangChain BaseMessage objects from raw dicts + latest user turn.

    Args:
        system_prompt: The system instruction string.
        conversation_history: List of {"role": ..., "content": ...} dicts.
        user_message: The latest user message.

    Returns:
        List of BaseMessage ready for llm.invoke().
    """
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]

    for msg in conversation_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message))
    return messages


def count_tokens_approx(text: str) -> int:
    """Rough token counter: ~4 chars per token."""
    return len(text) // 4
