"""
Speech / audio transcription and summarisation.
Primary: OpenAI Whisper API.
Fallback: local OpenAI Whisper model via the `whisper` package.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg"}


def transcribe_openai(audio_path: str) -> str:
    """
    Transcribe audio using the OpenAI Whisper API.

    Args:
        audio_path: Path to the audio file.

    Returns:
        str: Transcription text.
    """
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    logger.info("Transcribing via OpenAI Whisper API: %s", audio_path)

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=settings.OPENAI_WHISPER_MODEL,
            file=audio_file,
            response_format="text",
        )
    logger.info("Transcription complete (%d chars)", len(transcript))
    return transcript


def transcribe_local(audio_path: str, model_size: str = "base") -> str:
    """
    Local Whisper transcription using the `openai-whisper` package.
    Slower but works without an API key.
    """
    try:
        import whisper

        logger.info("Transcribing locally with Whisper (%s): %s", model_size, audio_path)
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path)
        text = result["text"]
        logger.info("Local transcription complete (%d chars)", len(text))
        return text
    except ImportError:
        raise RuntimeError(
            "openai-whisper is not installed. Run: pip install openai-whisper"
        )


def transcribe(audio_path: str) -> str:
    """
    Dispatch to the best available transcription backend.
    """
    suffix = Path(audio_path).suffix.lower()
    if suffix not in SUPPORTED_AUDIO:
        raise ValueError(
            f"Unsupported audio format '{suffix}'. Supported: {SUPPORTED_AUDIO}"
        )

    if settings.OPENAI_API_KEY:
        return transcribe_openai(audio_path)
    return transcribe_local(audio_path)


def summarise_transcript(transcript: str, llm=None) -> str:
    """
    Summarise a transcription using the chat LLM.

    Args:
        transcript: The full transcription text.
        llm: An optional pre-built LangChain LLM. Created internally if None.

    Returns:
        str: A concise summary.
    """
    if not transcript.strip():
        return "No speech detected in the audio."

    from backend.models.llm import LLMFactory
    from langchain.schema import HumanMessage, SystemMessage

    llm = llm or LLMFactory.get_chat_llm(temperature=0.3)
    system = SystemMessage(
        content=(
            "You are an expert meeting summariser. "
            "Given a transcript, produce a structured summary with:\n"
            "1. Key Topics\n2. Main Points\n3. Action Items (if any)\n4. Conclusion"
        )
    )
    user = HumanMessage(content=f"Transcript:\n\n{transcript}")
    response = llm.invoke([system, user])
    return response.content
