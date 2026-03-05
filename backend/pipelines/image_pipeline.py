"""
Image analysis pipeline.
Orchestrates saving, analysing, and optionally indexing image content.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.models.vision import analyze_image
from backend.models.llm import LLMFactory, build_messages

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


class ImagePipeline:
    """Orchestrates the full image analysis workflow."""

    def __init__(self) -> None:
        self.upload_dir = settings.upload_path / "images"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, source_path: str, original_name: str) -> str:
        """
        Copy uploaded image to the permanent uploads directory.

        Returns:
            Path to the stored image.
        """
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_IMAGE_TYPES:
            raise ValueError(
                f"Unsupported image type '{suffix}'. "
                f"Supported: {SUPPORTED_IMAGE_TYPES}"
            )
        dest = self.upload_dir / f"{uuid.uuid4()}{suffix}"
        shutil.copy2(source_path, dest)
        logger.info("Image saved: %s", dest)
        return str(dest)

    def analyse(
        self,
        image_path: str,
        user_prompt: str = "Describe this image in detail.",
    ) -> Dict:
        """
        Run the full image analysis pipeline.

        Args:
            image_path: Path to the image file.
            user_prompt: Specific question or instruction from the user.

        Returns:
            Dict with: description, objects, sentiment, raw_path.
        """
        logger.info("Analysing image: %s", image_path)

        # Primary analysis
        description = analyze_image(image_path, user_prompt)

        # Secondary structured extraction (objects, mood, etc.)
        detail = self._extract_image_details(image_path, description)

        return {
            "description": description,
            "objects": detail.get("objects", []),
            "sentiment": detail.get("sentiment", "neutral"),
            "additional_notes": detail.get("notes", ""),
            "image_path": image_path,
        }

    def _extract_image_details(
        self, image_path: str, initial_description: str
    ) -> Dict:
        """
        Use the LLM to extract structured metadata from the initial description.
        """
        llm = LLMFactory.get_chat_llm(temperature=0.1)
        system_prompt = (
            "You are a computer vision assistant. "
            "Given an image description, extract:\n"
            "1. Objects: List of main objects visible\n"
            "2. Sentiment: Overall mood/sentiment (positive/neutral/negative)\n"
            "3. Notes: Any text, numbers, or charts visible\n"
            "Respond ONLY in this JSON format:\n"
            '{"objects": [...], "sentiment": "...", "notes": "..."}'
        )
        messages = build_messages(
            system_prompt=system_prompt,
            conversation_history=[],
            user_message=f"Image description:\n{initial_description}",
        )
        try:
            response = llm.invoke(messages)
            import json
            # Strip potential code fences
            raw = response.content.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning("Detail extraction failed: %s", e)
            return {"objects": [], "sentiment": "neutral", "notes": ""}

    def answer_image_question(
        self,
        image_path: str,
        question: str,
        prior_description: Optional[str] = None,
    ) -> str:
        """
        Answer a follow-up question about an already-analysed image.

        Args:
            image_path: Path to the image.
            question: The user's question.
            prior_description: Previously generated description (avoids re-analysis).

        Returns:
            str: The LLM's answer.
        """
        if prior_description:
            llm = LLMFactory.get_chat_llm(temperature=0.4)
            messages = build_messages(
                system_prompt="You are a helpful visual analysis assistant.",
                conversation_history=[
                    {"role": "assistant", "content": prior_description}
                ],
                user_message=question,
            )
            response = llm.invoke(messages)
            return response.content
        # No cached description – re-analyse with the question as prompt
        return analyze_image(image_path, question)


# Module-level singleton
image_pipeline = ImagePipeline()
