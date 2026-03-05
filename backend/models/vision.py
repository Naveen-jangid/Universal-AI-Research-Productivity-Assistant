"""
Vision / image analysis model.
Uses GPT-4o vision capabilities via the OpenAI API.
Falls back to BLIP via HuggingFace Transformers when no API key is available.
"""

import base64
import logging
from pathlib import Path
from typing import Optional

from openai import OpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)


def _encode_image(image_path: str) -> str:
    """Base64-encode an image file."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image_openai(
    image_path: str,
    prompt: str = "Describe this image in detail.",
    max_tokens: int = 1024,
) -> str:
    """
    Analyse an image using GPT-4o vision.

    Args:
        image_path: Local path to the image file.
        prompt: Instruction / question about the image.
        max_tokens: Maximum tokens in the response.

    Returns:
        str: The model's analysis.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    suffix = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/jpeg")

    b64 = _encode_image(image_path)
    logger.info("Sending image to GPT-4o vision (%s bytes base64)", len(b64))

    response = client.chat.completions.create(
        model=settings.OPENAI_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        max_tokens=max_tokens,
    )
    result = response.choices[0].message.content
    logger.info("Vision analysis complete (%d chars)", len(result))
    return result


def analyze_image_blip(image_path: str) -> str:
    """
    Fallback image captioning using BLIP (salesforce/blip-image-captioning-base).
    Requires: pip install transformers torch pillow
    """
    try:
        from PIL import Image
        from transformers import BlipProcessor, BlipForConditionalGeneration
        import torch

        logger.info("Using BLIP for image captioning (no OpenAI key)")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=200)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return f"Image caption (BLIP): {caption}"
    except Exception as e:
        logger.error("BLIP inference failed: %s", e)
        return f"Image analysis unavailable: {e}"


def analyze_image(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """
    Dispatch to the best available vision model.
    """
    if settings.OPENAI_API_KEY:
        return analyze_image_openai(image_path, prompt)
    return analyze_image_blip(image_path)
