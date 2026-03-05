"""
Image Analysis API routes.
Upload images → analyse with GPT-4o vision or BLIP → follow-up Q&A.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.pipelines.image_pipeline import image_pipeline
from backend.utils.file_handler import ALLOWED_IMAGE_TYPES, save_upload

router = APIRouter(prefix="/images", tags=["Image Analysis"])
logger = logging.getLogger(__name__)


# ── Request / Response models ────────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    image_id: str
    description: str
    objects: list
    sentiment: str
    additional_notes: str


class ImageQuestionRequest(BaseModel):
    image_path: str = Field(..., description="Server-side path to the image.")
    question: str = Field(..., min_length=1, max_length=2048)
    prior_description: Optional[str] = Field(None, description="Previously generated description.")


class ImageQuestionResponse(BaseModel):
    answer: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/analyse", response_model=ImageAnalysisResponse)
async def analyse_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail."),
):
    """
    Upload an image and receive an AI-powered analysis.
    Supports JPG, PNG, GIF, WebP, BMP, TIFF.
    """
    file_id, saved_path = await save_upload(
        file,
        sub_dir="images",
        allowed_types=ALLOWED_IMAGE_TYPES,
    )

    result = image_pipeline.analyse(image_path=saved_path, user_prompt=prompt)

    return ImageAnalysisResponse(
        image_id=file_id,
        description=result["description"],
        objects=result["objects"],
        sentiment=result["sentiment"],
        additional_notes=result["additional_notes"],
    )


@router.post("/question", response_model=ImageQuestionResponse)
async def ask_about_image(req: ImageQuestionRequest) -> ImageQuestionResponse:
    """
    Ask a follow-up question about a previously uploaded image.
    """
    answer = image_pipeline.answer_image_question(
        image_path=req.image_path,
        question=req.question,
        prior_description=req.prior_description,
    )
    return ImageQuestionResponse(answer=answer)
