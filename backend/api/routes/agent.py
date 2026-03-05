"""
AI Agent API routes.
Exposes the autonomous research agent with tool-use capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.research_agent import create_agent
from backend.memory.long_term_memory import LongTermMemory

router = APIRouter(prefix="/agent", tags=["AI Agent"])
logger = logging.getLogger(__name__)


# ── Request / Response models ────────────────────────────────────────────────

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=8192, description="Task or question for the agent.")
    session_id: Optional[str] = Field(None, description="Session ID for memory retrieval.")
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Prior conversation history."
    )
    use_memory: bool = Field(True, description="Inject long-term memory context.")


class AgentStepSummary(BaseModel):
    tool: str
    input: str
    output: str


class AgentResponse(BaseModel):
    output: str
    steps: List[AgentStepSummary]
    tool_calls: int


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest) -> AgentResponse:
    """
    Run the autonomous AI research agent on a given task.
    The agent will reason, use tools (web search, document retrieval, etc.),
    and return a comprehensive answer.
    """
    memory_context = ""
    if req.use_memory and req.session_id:
        mem = LongTermMemory(req.session_id)
        memory_context = mem.build_memory_context(req.task)

    agent = create_agent(memory_context=memory_context)

    try:
        result = agent.run(task=req.task, chat_history=req.chat_history)
    except Exception as exc:
        logger.error("Agent execution failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}")

    return AgentResponse(
        output=result["output"],
        steps=[AgentStepSummary(**s) for s in result["steps"]],
        tool_calls=result["tool_calls"],
    )


@router.get("/tools")
async def list_agent_tools():
    """List all tools available to the AI agent."""
    from backend.agents.tools import get_all_tools
    tools = get_all_tools()
    return {
        "tool_count": len(tools),
        "tools": [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in tools
        ],
    }
