"""
Document Intelligence API routes.
Upload documents → ingest into FAISS → ask questions via RAG.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.core.database import list_documents
from backend.pipelines.document_pipeline import ingest_document
from backend.pipelines.rag_pipeline import answer_with_rag
from backend.utils.file_handler import ALLOWED_DOCUMENT_TYPES, save_upload
from backend.vectorstore.faiss_store import delete_namespace, list_namespaces

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


# ── Request / Response models ────────────────────────────────────────────────

class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    namespace: str
    message: str


class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4096)
    namespace: str = Field("default", description="FAISS namespace to query.")
    k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve.")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Prior conversation turns for multi-turn context."
    )
    temperature: float = Field(0.3, ge=0.0, le=2.0)


class RAGResponse(BaseModel):
    answer: str
    sources: List[str]
    retrieved_chunks: int
    context_preview: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    namespace: str = Form("default"),
):
    """
    Upload a document (PDF / DOCX / TXT / MD) and ingest it into the vector store.
    """
    file_id, saved_path = await save_upload(
        file,
        sub_dir="documents",
        allowed_types=ALLOWED_DOCUMENT_TYPES,
    )

    doc_id, chunk_count = ingest_document(
        file_path=saved_path,
        doc_id=file_id,
        namespace=namespace,
    )

    logger.info("Document ingested: id=%s, chunks=%d", doc_id, chunk_count)
    return IngestResponse(
        doc_id=doc_id,
        filename=file.filename or "unknown",
        chunk_count=chunk_count,
        namespace=namespace,
        message=f"Successfully ingested {chunk_count} chunks into namespace '{namespace}'.",
    )


@router.post("/ask", response_model=RAGResponse)
async def ask_document(req: RAGRequest) -> RAGResponse:
    """
    Ask a question answered from the document knowledge base (RAG).
    """
    result = answer_with_rag(
        question=req.question,
        namespace=req.namespace,
        conversation_history=req.conversation_history,
        k=req.k,
        temperature=req.temperature,
    )
    return RAGResponse(
        answer=result["answer"],
        sources=result["sources"],
        retrieved_chunks=result["retrieved_chunks"],
        context_preview=result.get("context_preview", ""),
    )


@router.get("/list")
async def list_all_documents():
    """List all ingested documents from the SQLite registry."""
    return list_documents()


@router.get("/namespaces")
async def list_all_namespaces():
    """List all available FAISS namespaces."""
    return {"namespaces": list_namespaces()}


@router.delete("/namespace/{namespace}")
async def delete_document_namespace(namespace: str):
    """Delete a FAISS namespace and all its indexed content."""
    if namespace == "long_term_memory":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the long-term memory namespace directly."
        )
    delete_namespace(namespace)
    return {"status": "deleted", "namespace": namespace}
