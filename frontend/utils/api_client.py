"""
HTTP client for communicating with the FastAPI backend.
Wraps all API calls with error handling and retries.
"""

import logging
import time
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

import httpx
import streamlit as st

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120.0  # seconds
MAX_RETRIES = 3


def get_api_base() -> str:
    """Return the backend API base URL from Streamlit session state or env."""
    return st.session_state.get("api_base_url", "http://localhost:8000/api/v1")


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=get_api_base(),
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )


def _post_json(endpoint: str, payload: Dict) -> Dict:
    """POST JSON payload; raise on HTTP errors."""
    with _client() as client:
        response = client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()


def _post_file(
    endpoint: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    extra_data: Optional[Dict[str, str]] = None,
) -> Dict:
    """POST a multipart file upload."""
    files = {"file": (filename, file_bytes, content_type)}
    data = extra_data or {}
    with _client() as client:
        response = client.post(endpoint, files=files, data=data)
        response.raise_for_status()
        return response.json()


def _get(endpoint: str, params: Optional[Dict] = None) -> Any:
    with _client() as client:
        response = client.get(endpoint, params=params or {})
        response.raise_for_status()
        return response.json()


def _delete(endpoint: str) -> Dict:
    with _client() as client:
        response = client.delete(endpoint)
        response.raise_for_status()
        return response.json()


# ── Chat ─────────────────────────────────────────────────────────────────────

def send_chat_message(
    message: str,
    conversation_id: Optional[str] = None,
    session_id: Optional[str] = None,
    use_memory: bool = True,
    temperature: float = 0.7,
) -> Dict:
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "session_id": session_id,
        "use_memory": use_memory,
        "temperature": temperature,
    }
    return _post_json("/chat/message", payload)


def list_conversations() -> List[Dict]:
    return _get("/chat/conversations")


def get_conversation_messages(conv_id: str) -> List[Dict]:
    return _get(f"/chat/conversations/{conv_id}/messages")


def delete_conversation(conv_id: str) -> Dict:
    return _delete(f"/chat/conversations/{conv_id}")


# ── Documents / RAG ───────────────────────────────────────────────────────────

def upload_document(
    file_bytes: bytes,
    filename: str,
    namespace: str = "default",
    content_type: str = "application/octet-stream",
) -> Dict:
    return _post_file(
        "/documents/upload",
        file_bytes,
        filename,
        content_type,
        extra_data={"namespace": namespace},
    )


def ask_document(
    question: str,
    namespace: str = "default",
    k: int = 5,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    payload = {
        "question": question,
        "namespace": namespace,
        "k": k,
        "conversation_history": conversation_history or [],
    }
    return _post_json("/documents/ask", payload)


def list_documents() -> List[Dict]:
    return _get("/documents/list")


def list_namespaces() -> List[str]:
    data = _get("/documents/namespaces")
    return data.get("namespaces", [])


# ── Images ───────────────────────────────────────────────────────────────────

def analyse_image(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    prompt: str = "Describe this image in detail.",
) -> Dict:
    return _post_file(
        "/images/analyse",
        file_bytes,
        filename,
        content_type,
        extra_data={"prompt": prompt},
    )


# ── Audio ────────────────────────────────────────────────────────────────────

def process_audio(file_bytes: bytes, filename: str, content_type: str) -> Dict:
    return _post_file("/audio/process", file_bytes, filename, content_type)


def ask_about_audio(transcript: str, question: str) -> Dict:
    return _post_json("/audio/question", {"transcript": transcript, "question": question})


# ── Data Analysis ─────────────────────────────────────────────────────────────

def upload_dataset(file_bytes: bytes, filename: str, content_type: str = "text/csv") -> Dict:
    return _post_file("/data/upload", file_bytes, filename, content_type)


def get_visualisations(file_id: str) -> Dict:
    return _get(f"/data/visualisations/{file_id}")


def get_ai_insights(file_id: str) -> Dict:
    return _get(f"/data/insights/{file_id}")


def ask_about_data(file_id: str, question: str) -> Dict:
    return _post_json("/data/ask", {"file_id": file_id, "question": question})


# ── Agent ─────────────────────────────────────────────────────────────────────

def run_agent(
    task: str,
    session_id: Optional[str] = None,
    chat_history: Optional[List[Dict]] = None,
    use_memory: bool = True,
) -> Dict:
    payload = {
        "task": task,
        "session_id": session_id,
        "chat_history": chat_history or [],
        "use_memory": use_memory,
    }
    return _post_json("/agent/run", payload)


def list_agent_tools() -> Dict:
    return _get("/agent/tools")


# ── Health ───────────────────────────────────────────────────────────────────

def health_check() -> Dict:
    try:
        with httpx.Client(timeout=5.0) as client:
            base = get_api_base().replace("/api/v1", "")
            response = client.get(f"{base}/health")
            return response.json()
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}
