"""
Audio processing pipeline.
Handles file validation, transcription, summarisation, and keyword extraction.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.models.speech import transcribe, summarise_transcript, SUPPORTED_AUDIO
from backend.models.llm import LLMFactory, build_messages

logger = logging.getLogger(__name__)


class AudioPipeline:
    """Orchestrates the complete audio processing workflow."""

    def __init__(self) -> None:
        self.upload_dir = settings.upload_path / "audio"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_audio(self, source_path: str, original_name: str) -> str:
        """Persist the audio file and return the stored path."""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_AUDIO:
            raise ValueError(
                f"Unsupported audio format '{suffix}'. Supported: {SUPPORTED_AUDIO}"
            )
        dest = self.upload_dir / f"{uuid.uuid4()}{suffix}"
        shutil.copy2(source_path, dest)
        logger.info("Audio saved: %s", dest)
        return str(dest)

    def process(self, audio_path: str) -> Dict:
        """
        Full audio pipeline: transcribe → summarise → extract keywords.

        Args:
            audio_path: Path to the saved audio file.

        Returns:
            Dict with keys: transcript, summary, keywords, duration_estimate.
        """
        logger.info("Processing audio: %s", audio_path)

        # 1. Transcribe
        transcript = transcribe(audio_path)

        if not transcript.strip():
            return {
                "transcript": "",
                "summary": "No speech detected in the recording.",
                "keywords": [],
                "word_count": 0,
            }

        # 2. Summarise
        summary = summarise_transcript(transcript)

        # 3. Extract keywords
        keywords = self._extract_keywords(transcript)

        word_count = len(transcript.split())
        logger.info("Audio processed: %d words, %d keywords", word_count, len(keywords))

        return {
            "transcript": transcript,
            "summary": summary,
            "keywords": keywords,
            "word_count": word_count,
        }

    def _extract_keywords(self, transcript: str, max_keywords: int = 15) -> List[str]:
        """Use the LLM to extract the most important keywords / topics."""
        llm = LLMFactory.get_chat_llm(temperature=0.1)
        messages = build_messages(
            system_prompt=(
                "Extract the most important keywords and topics from the given transcript. "
                f"Return ONLY a comma-separated list of up to {max_keywords} keywords, nothing else."
            ),
            conversation_history=[],
            user_message=f"Transcript:\n\n{transcript[:3000]}",
        )
        try:
            response = llm.invoke(messages)
            raw = response.content.strip()
            keywords = [k.strip() for k in raw.split(",") if k.strip()]
            return keywords[:max_keywords]
        except Exception as e:
            logger.warning("Keyword extraction failed: %s", e)
            return []

    def answer_audio_question(
        self,
        transcript: str,
        question: str,
    ) -> str:
        """
        Answer a question about the audio content using the transcript as context.

        Args:
            transcript: Full transcript text.
            question: User's question.

        Returns:
            str: LLM answer.
        """
        llm = LLMFactory.get_chat_llm(temperature=0.4)
        messages = build_messages(
            system_prompt=(
                "You are an expert assistant. The user has provided an audio transcript. "
                "Answer their question based solely on the transcript content."
            ),
            conversation_history=[
                {"role": "assistant", "content": f"Transcript:\n{transcript}"}
            ],
            user_message=question,
        )
        response = llm.invoke(messages)
        return response.content


# Module-level singleton
audio_pipeline = AudioPipeline()
