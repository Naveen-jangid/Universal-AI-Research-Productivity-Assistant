"""
Chat API routes.
Provides conversational chat with short-term memory and optional long-term memory injection.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.core.database import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
)
from backend.memory.long_term_memory import LongTermMemory
from backend.models.llm import LLMFactory, build_messages

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are a highly capable, friendly, and knowledgeable AI research assistant.
You help users with research, writing, coding, analysis, and general questions.
Be concise but thorough. Use markdown formatting when appropriate.
If you don't know something, say so honestly.
{memory_context}"""


# ── Request / Response models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID. Creates new if absent.")
    message: str = Field(..., min_length=1, max_length=32000)
    session_id: Optional[str] = Field(None, description="Session ID for long-term memory.")
    use_memory: bool = Field(True, description="Inject long-term memory context.")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=64, le=8192)


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: int
    response: str
    memory_facts_stored: int = 0


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI assistant and receive a reply.
    Maintains conversation history stored in SQLite.
    """
    # Resolve or create conversation
    conv_id = req.conversation_id or str(uuid.uuid4())
    session_id = req.session_id or conv_id

    if not req.conversation_id:
        # Derive a title from the first message
        title = req.message[:60] + ("..." if len(req.message) > 60 else "")
        create_conversation(conv_id, title=title)
    else:
        conv = get_conversation(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")

    # Build memory context
    memory_context = ""
    if req.use_memory:
        mem = LongTermMemory(session_id)
        memory_context = mem.build_memory_context(req.message)

    # Build message history (last N messages)
    history_records = get_messages(conv_id, limit=settings.MEMORY_WINDOW_SIZE)
    history = [{"role": r["role"], "content": r["content"]} for r in history_records]

    # LLM call
    llm = LLMFactory.get_chat_llm(
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    system_prompt = CHAT_SYSTEM_PROMPT.format(
        memory_context=f"\n\n{memory_context}" if memory_context else ""
    )
    messages = build_messages(system_prompt, history, req.message)

    try:
        ai_response = llm.invoke(messages)
        reply = ai_response.content
    except Exception as exc:
        logger.error("LLM call failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}")

    # Persist messages
    add_message(conv_id, "user", req.message)
    msg_id = add_message(conv_id, "assistant", reply)

    # Extract and store memory facts asynchronously
    facts_stored = 0
    if req.use_memory:
        try:
            mem = LongTermMemory(session_id)
            facts_stored = mem.process_conversation_turn(req.message, reply)
        except Exception as e:
            logger.warning("Memory extraction failed: %s", e)

    return ChatResponse(
        conversation_id=conv_id,
        message_id=msg_id,
        response=reply,
        memory_facts_stored=facts_stored,
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_all_conversations():
    """List all conversations ordered by most recent activity."""
    return list_conversations()


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = 100):
    """Retrieve all messages in a conversation."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return get_messages(conversation_id, limit=limit)


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    delete_conversation(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}
