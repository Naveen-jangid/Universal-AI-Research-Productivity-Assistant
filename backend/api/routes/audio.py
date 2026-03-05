"""
Audio / Speech Processing API routes.
Upload audio → transcribe → summarise → Q&A.
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.pipelines.audio_pipeline import audio_pipeline
from backend.utils.file_handler import ALLOWED_AUDIO_TYPES, save_upload

router = APIRouter(prefix="/audio", tags=["Audio & Speech"])
logger = logging.getLogger(__name__)


# ── Response models ──────────────────────────────────────────────────────────

class AudioProcessResponse(BaseModel):
    audio_id: str
    transcript: str
    summary: str
    keywords: list
    word_count: int


class AudioQuestionRequest(BaseModel):
    transcript: str = Field(..., description="Full transcript text.")
    question: str = Field(..., min_length=1, max_length=2048)


class AudioQuestionResponse(BaseModel):
    answer: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/process", response_model=AudioProcessResponse)
async def process_audio(
    file: UploadFile = File(...),
):
    """
    Upload an audio/video file, transcribe it with Whisper, and summarise the content.
    Supported formats: MP3, MP4, WAV, OGG, WebM, M4A.
    """
    file_id, saved_path = await save_upload(
        file,
        sub_dir="audio",
        allowed_types=ALLOWED_AUDIO_TYPES,
    )

    result = audio_pipeline.process(audio_path=saved_path)

    return AudioProcessResponse(
        audio_id=file_id,
        transcript=result["transcript"],
        summary=result["summary"],
        keywords=result["keywords"],
        word_count=result["word_count"],
    )


@router.post("/question", response_model=AudioQuestionResponse)
async def ask_about_audio(req: AudioQuestionRequest) -> AudioQuestionResponse:
    """
    Ask a question about the content of a transcribed audio file.
    """
    answer = audio_pipeline.answer_audio_question(
        transcript=req.transcript,
        question=req.question,
    )
    return AudioQuestionResponse(answer=answer)
