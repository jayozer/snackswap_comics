"""Capture and intake endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from app.core.config import get_settings, Settings
from app.models import CaptureIntakeResponse
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_image_service(settings: Annotated[Settings, Depends(get_settings)]) -> ImageService:
    """Dependency for image service."""
    return ImageService(settings)


@router.post("/intake", response_model=CaptureIntakeResponse)
async def capture_intake(
    file: UploadFile = File(..., description="Photo of snack/lunch"),
    image_service: ImageService = Depends(get_image_service),
) -> CaptureIntakeResponse:
    """
    Process uploaded photo.

    Steps:
    - Convert HEIC to JPEG if needed
    - Fix EXIF orientation
    - Downscale to max 1400px
    - Generate thumbnail
    - Save and return metadata

    Args:
        file: Uploaded image file
        image_service: Image service dependency

    Returns:
        Photo metadata with ID and URIs
    """
    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Check file size
    settings = get_settings()
    file_bytes = await file.read()

    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {settings.max_upload_size_mb}MB)",
        )

    try:
        # Process image
        result = await image_service.process_upload(file_bytes, file.filename or "image.jpg")

        # Get URIs
        thumb_uri = image_service.get_uri(image_service.get_thumb_path(result["photo_id"]))

        logger.info(f"Processed upload: {result['photo_id']}")

        return CaptureIntakeResponse(
            photo_id=result["photo_id"],
            width=result["width"],
            height=result["height"],
            thumb_uri=thumb_uri,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")
