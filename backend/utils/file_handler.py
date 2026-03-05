"""
File handling utilities: validation, storage, cleanup.
"""

import hashlib
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from backend.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/x-rst",
}
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/ogg",
    "audio/webm",
    "audio/x-m4a",
    "video/mp4",
    "video/mpeg",
    "video/webm",
}
ALLOWED_DATA_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
    "application/octet-stream",  # for .parquet
}


def validate_file_size(file: UploadFile) -> None:
    """Raise HTTPException if file exceeds MAX_UPLOAD_SIZE_MB."""
    # FastAPI reads content-length header; we also cap at read time
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    # We can't check size without reading — caller must do this after saving
    pass  # Size check happens after saving


def generate_file_id() -> str:
    return str(uuid.uuid4())


async def save_upload(
    upload: UploadFile,
    sub_dir: str = "misc",
    allowed_types: Optional[set] = None,
) -> Tuple[str, str]:
    """
    Save an uploaded file to disk.

    Args:
        upload: FastAPI UploadFile object.
        sub_dir: Sub-directory under UPLOAD_DIR.
        allowed_types: Set of allowed MIME types. None = no restriction.

    Returns:
        Tuple of (file_id, saved_path).

    Raises:
        HTTPException: On validation failure.
    """
    # MIME validation
    if allowed_types and upload.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{upload.content_type}'. "
                f"Allowed: {allowed_types}"
            ),
        )

    dest_dir = settings.upload_path / sub_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(upload.filename or "file").suffix.lower() or ".bin"
    file_id = generate_file_id()
    dest_path = dest_dir / f"{file_id}{suffix}"

    # Stream to disk
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    written = 0
    with open(dest_path, "wb") as f:
        while chunk := await upload.read(1024 * 64):  # 64 KB chunks
            written += len(chunk)
            if written > max_bytes:
                f.close()
                os.unlink(dest_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                )
            f.write(chunk)

    logger.info(
        "Saved upload: %s → %s (%d bytes)", upload.filename, dest_path, written
    )
    return file_id, str(dest_path)


def compute_md5(file_path: str) -> str:
    """Compute MD5 hash of a file for deduplication."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def cleanup_file(file_path: str) -> None:
    """Delete a file from disk (best-effort)."""
    try:
        Path(file_path).unlink(missing_ok=True)
        logger.debug("Cleaned up: %s", file_path)
    except Exception as e:
        logger.warning("Could not delete %s: %s", file_path, e)
