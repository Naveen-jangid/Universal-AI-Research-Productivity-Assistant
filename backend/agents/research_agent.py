"""
Autonomous Research Agent.
Uses LangChain's ReAct / OpenAI-functions agent to reason, plan, and
execute multi-step research tasks using the registered tool set.
"""

import logging
from typing import Any, Callable, Dict, Iterator, List, Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.agents.tools import get_all_tools
from backend.core.config import settings
from backend.models.llm import LLMFactory

logger = logging.getLogger(__name__)


AGENT_SYSTEM_PROMPT = """You are an expert autonomous research assistant with access to powerful tools.

Your capabilities:
- 🔍 Web Search: Find current information, news, and research online
- 📚 Document Retrieval: Search uploaded documents in the knowledge base
- 🧮 Calculator: Perform mathematical computations
- 🕐 Date/Time: Access current time information
- 📝 Summariser: Condense large amounts of information
- 💻 Python Executor: Run analysis code

Guidelines:
1. Break complex tasks into clear sub-steps
2. Use tools strategically — always explain WHY you are using a tool
3. Combine information from multiple sources for comprehensive answers
4. If a tool fails, try alternative approaches
5. Cite sources and indicate confidence levels
6. Be honest when information is uncertain or unavailable
7. Provide structured, well-organised responses

Current session context:
{memory_context}

Always strive to give accurate, well-researched, and helpful responses."""


class StepCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that collects agent reasoning steps for display in the UI.
    """

    def __init__(self, step_callback: Optional[Callable[[str], None]] = None) -> None:
        self.steps: List[Dict[str, str]] = []
        self._callback = step_callback

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        step = {
            "type": "action",
            "tool": action.tool,
            "input": str(action.tool_input),
        }
        self.steps.append(step)
        if self._callback:
            self._callback(f"🔧 Using tool: **{action.tool}**\nInput: `{action.tool_input}`")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        step = {"type": "observation", "output": output[:500]}
        self.steps.append(step)
        if self._callback:
            self._callback(f"📊 Observation: {output[:300]}...")

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        if self._callback:
            self._callback("✅ Agent task complete.")


class ResearchAgent:
    """
    Wraps the LangChain agent executor with convenience methods
    for single-turn and multi-turn interactions.
    """

    def __init__(
        self,
        memory_context: str = "",
        step_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.memory_context = memory_context
        self.step_callback = step_callback
        self._executor: Optional[AgentExecutor] = None

    def _build_executor(self) -> AgentExecutor:
        """Construct the LangChain agent executor."""
        tools = get_all_tools()
        llm = LLMFactory.get_chat_llm(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.2,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    AGENT_SYSTEM_PROMPT.format(
                        memory_context=self.memory_context or "No prior context."
                    ),
                ),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

        callback_handler = StepCallbackHandler(self.step_callback)

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            max_execution_time=120,
            early_stopping_method="generate",
            handle_parsing_errors=True,
            callbacks=[callback_handler],
            return_intermediate_steps=True,
        )
        return executor

    @property
    def executor(self) -> AgentExecutor:
        if self._executor is None:
            self._executor = self._build_executor()
        return self._executor

    def run(
        self,
        task: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a research task.

        Args:
            task: The task description or question.
            chat_history: Prior conversation messages.

        Returns:
            Dict with: output, steps, tool_calls.
        """
        logger.info("Agent task: %s", task[:100])

        # Build LangChain message history
        lc_history = []
        for msg in (chat_history or []):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))

        result = self.executor.invoke(
            {"input": task, "chat_history": lc_history}
        )

        output = result.get("output", "")
        intermediate = result.get("intermediate_steps", [])

        steps_summary = []
        for action, observation in intermediate:
            steps_summary.append(
                {
                    "tool": action.tool,
                    "input": str(action.tool_input)[:300],
                    "output": str(observation)[:500],
                }
            )

        logger.info(
            "Agent done: %d chars, %d steps", len(output), len(steps_summary)
        )
        return {
            "output": output,
            "steps": steps_summary,
            "tool_calls": len(steps_summary),
        }


def create_agent(
    memory_context: str = "",
    step_callback: Optional[Callable[[str], None]] = None,
) -> ResearchAgent:
    """Factory function to create a ResearchAgent instance."""
    return ResearchAgent(memory_context=memory_context, step_callback=step_callback)
