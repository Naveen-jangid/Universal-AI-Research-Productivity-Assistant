"""
Data Analysis API routes.
Upload CSV / Excel → EDA → visualisations → AI insights → Q&A.
"""

import json
import logging
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.pipelines.data_pipeline import (
    answer_data_question,
    compute_eda,
    generate_ai_insights,
    generate_visualisations,
    load_dataframe,
)
from backend.utils.file_handler import ALLOWED_DATA_TYPES, save_upload

router = APIRouter(prefix="/data", tags=["Data Analysis"])
logger = logging.getLogger(__name__)

# Module-level cache: {file_id: (dataframe, eda)}
_df_cache: Dict[str, Any] = {}


# ── Request / Response models ────────────────────────────────────────────────

class EDAResponse(BaseModel):
    file_id: str
    shape: Dict[str, int]
    columns: List[str]
    dtypes: Dict[str, str]
    missing_values: Dict[str, int]
    numeric_columns: List[str]
    categorical_columns: List[str]
    sample: List[Dict]


class InsightsResponse(BaseModel):
    file_id: str
    insights: str


class DataQuestionRequest(BaseModel):
    file_id: str = Field(..., description="File ID returned by /data/upload")
    question: str = Field(..., min_length=1, max_length=2048)


class DataQuestionResponse(BaseModel):
    answer: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
):
    """
    Upload a CSV / Excel / JSON dataset.
    Returns file_id and basic EDA summary.
    """
    file_id, saved_path = await save_upload(
        file,
        sub_dir="data",
        allowed_types=ALLOWED_DATA_TYPES,
    )

    try:
        df = load_dataframe(saved_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse dataset: {e}")

    eda = compute_eda(df)
    _df_cache[file_id] = (df, eda)

    logger.info("Dataset uploaded: %s (%d×%d)", file.filename, *df.shape)
    return {
        "file_id": file_id,
        "filename": file.filename,
        "shape": eda["shape"],
        "columns": eda["columns"],
        "dtypes": eda["dtypes"],
        "missing_values": eda.get("missing_values", {}),
        "numeric_columns": eda["numeric_columns"],
        "categorical_columns": eda["categorical_columns"],
        "sample": eda["sample"],
    }


@router.get("/visualisations/{file_id}")
async def get_visualisations(file_id: str):
    """
    Generate and return Plotly chart JSON objects for the uploaded dataset.
    """
    if file_id not in _df_cache:
        raise HTTPException(status_code=404, detail="Dataset not found. Please upload first.")

    df, eda = _df_cache[file_id]
    charts = generate_visualisations(df)
    return {"file_id": file_id, "chart_count": len(charts), "charts": charts}


@router.get("/insights/{file_id}", response_model=InsightsResponse)
async def get_ai_insights(file_id: str):
    """
    Get AI-generated insights from the EDA summary.
    """
    if file_id not in _df_cache:
        raise HTTPException(status_code=404, detail="Dataset not found. Please upload first.")

    df, eda = _df_cache[file_id]
    insights = generate_ai_insights(df, eda)
    return InsightsResponse(file_id=file_id, insights=insights)


@router.post("/ask", response_model=DataQuestionResponse)
async def ask_about_data(req: DataQuestionRequest) -> DataQuestionResponse:
    """
    Ask a natural language question about the dataset.
    The AI generates and executes pandas code to answer the question.
    """
    if req.file_id not in _df_cache:
        raise HTTPException(status_code=404, detail="Dataset not found. Please upload first.")

    df, eda = _df_cache[req.file_id]
    answer = answer_data_question(df, req.question, eda)
    return DataQuestionResponse(answer=answer)
