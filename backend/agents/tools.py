"""
Custom LangChain tools for the autonomous AI agent.

Available tools:
  - WebSearchTool  : searches the web via SerpAPI (or DuckDuckGo fallback)
  - DocumentRetrieverTool : searches the FAISS vector store
  - CalculatorTool  : evaluates math expressions safely
  - DateTimeTool    : returns current date/time info
  - SummariseTool   : summarises long text
  - CodeExecutorTool: executes safe Python snippets
"""

import json
import logging
import math
import re
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.vectorstore.faiss_store import similarity_search

logger = logging.getLogger(__name__)


# ── Input schemas ────────────────────────────────────────────────────────────

class SearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web.")


class DocumentInput(BaseModel):
    query: str = Field(description="Query to search in the document knowledge base.")
    namespace: str = Field(default="default", description="FAISS namespace to search.")


class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate.")


class SummariseInput(BaseModel):
    text: str = Field(description="Long text to summarise.")
    style: str = Field(default="bullet", description="Style: 'bullet', 'paragraph', or 'table'.")


class CodeInput(BaseModel):
    code: str = Field(description="Python code snippet to execute (read-only operations).")


# ── Tools ────────────────────────────────────────────────────────────────────

class WebSearchTool(BaseTool):
    """Search the web for up-to-date information."""

    name: str = "web_search"
    description: str = (
        "Search the internet for current information, news, facts, or research. "
        "Use this when you need real-time or recent information."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        logger.info("Web search: %s", query)
        if settings.SERPAPI_API_KEY:
            return self._serpapi_search(query)
        return self._duckduckgo_search(query)

    async def _arun(self, query: str) -> str:
        return self._run(query)

    def _serpapi_search(self, query: str) -> str:
        try:
            from langchain_community.utilities import SerpAPIWrapper
            search = SerpAPIWrapper(serpapi_api_key=settings.SERPAPI_API_KEY)
            return search.run(query)
        except Exception as e:
            logger.error("SerpAPI error: %s", e)
            return self._duckduckgo_search(query)

    def _duckduckgo_search(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(
                        f"Title: {r.get('title', '')}\n"
                        f"URL: {r.get('href', '')}\n"
                        f"Snippet: {r.get('body', '')}"
                    )
            return "\n\n---\n\n".join(results) if results else "No results found."
        except ImportError:
            return (
                "Web search unavailable. Install: pip install duckduckgo-search "
                "or provide SERPAPI_API_KEY."
            )
        except Exception as e:
            logger.error("DuckDuckGo search error: %s", e)
            return f"Search failed: {e}"


class DocumentRetrieverTool(BaseTool):
    """Retrieve relevant passages from uploaded documents."""

    name: str = "document_retriever"
    description: str = (
        "Search the internal knowledge base (uploaded documents) for relevant information. "
        "Use this to find answers from PDFs, Word docs, or text files the user has uploaded."
    )
    args_schema: Type[BaseModel] = DocumentInput

    def _run(self, query: str, namespace: str = "default") -> str:
        logger.info("Document retrieval: '%s' (namespace=%s)", query, namespace)
        results = similarity_search(query, namespace=namespace, k=5)
        if not results:
            return "No relevant documents found in the knowledge base."

        parts = []
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            parts.append(
                f"[{i}] Source: {source} (relevance: {score:.2f})\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(parts)

    async def _arun(self, query: str, namespace: str = "default") -> str:
        return self._run(query, namespace)


class CalculatorTool(BaseTool):
    """Evaluate mathematical expressions."""

    name: str = "calculator"
    description: str = (
        "Evaluate mathematical expressions, perform arithmetic, "
        "statistics, or unit conversions. Input must be a valid Python math expression."
    )
    args_schema: Type[BaseModel] = CalculatorInput

    _ALLOWED_NAMES: Dict[str, Any] = {
        k: v for k, v in vars(math).items() if not k.startswith("_")
    }
    _ALLOWED_NAMES.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})

    def _run(self, expression: str) -> str:
        # Safety: allow only safe characters
        if re.search(r"[^0-9+\-*/().,%^e\s\w]", expression):
            return "Error: expression contains disallowed characters."
        try:
            result = eval(expression, {"__builtins__": {}}, self._ALLOWED_NAMES)  # noqa: S307
            return str(result)
        except Exception as e:
            return f"Calculation error: {e}"

    async def _arun(self, expression: str) -> str:
        return self._run(expression)


class DateTimeTool(BaseTool):
    """Get current date and time information."""

    name: str = "datetime_info"
    description: str = (
        "Get the current date, time, day of week, UTC offset, "
        "or calculate time differences."
    )

    def _run(self, tool_input: str = "") -> str:
        now = datetime.utcnow()
        return (
            f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Day of week: {now.strftime('%A')}\n"
            f"ISO 8601: {now.isoformat()}Z"
        )

    async def _arun(self, tool_input: str = "") -> str:
        return self._run(tool_input)


class SummariseTool(BaseTool):
    """Summarise long text into a concise format."""

    name: str = "summarise_text"
    description: str = (
        "Summarise a long piece of text. Useful when you have retrieved "
        "large amounts of information and need to condense it."
    )
    args_schema: Type[BaseModel] = SummariseInput

    def _run(self, text: str, style: str = "bullet") -> str:
        from backend.models.llm import LLMFactory, build_messages

        style_instructions = {
            "bullet": "Produce a bullet-point summary with the most important information.",
            "paragraph": "Produce a concise paragraph summary.",
            "table": "Produce a markdown table with key facts and values.",
        }
        instruction = style_instructions.get(style, style_instructions["bullet"])

        llm = LLMFactory.get_chat_llm(temperature=0.3)
        messages = build_messages(
            system_prompt=f"You are an expert summariser. {instruction}",
            conversation_history=[],
            user_message=f"Text to summarise:\n\n{text[:8000]}",
        )
        response = llm.invoke(messages)
        return response.content

    async def _arun(self, text: str, style: str = "bullet") -> str:
        return self._run(text, style)


class CodeExecutorTool(BaseTool):
    """Execute safe Python code snippets for analysis tasks."""

    name: str = "python_executor"
    description: str = (
        "Execute Python code snippets for data analysis, string manipulation, "
        "or algorithmic tasks. Only safe, read-only operations are allowed. "
        "The output variable must be named 'result'."
    )
    args_schema: Type[BaseModel] = CodeInput

    _SAFE_BUILTINS = {
        "print": print,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "isinstance": isinstance,
        "type": type,
        "__import__": __import__,
    }

    def _run(self, code: str) -> str:
        local_vars: Dict[str, Any] = {}
        try:
            exec(code, {"__builtins__": self._SAFE_BUILTINS}, local_vars)  # noqa: S102
            result = local_vars.get("result", "(no result variable set)")
            return str(result)
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            return f"Execution error:\n{tb}"

    async def _arun(self, code: str) -> str:
        return self._run(code)


def get_all_tools() -> List[BaseTool]:
    """Return all registered agent tools."""
    return [
        WebSearchTool(),
        DocumentRetrieverTool(),
        CalculatorTool(),
        DateTimeTool(),
        SummariseTool(),
        CodeExecutorTool(),
    ]
