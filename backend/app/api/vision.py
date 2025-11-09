"""Vision detection endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from app.core.config import get_settings, Settings
from app.models import VisionDetectRequest, VisionDetectResponse
from app.services.gemini_service import GeminiService
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_gemini_service(settings: Annotated[Settings, Depends(get_settings)]) -> GeminiService:
    """Dependency for Gemini service."""
    return GeminiService(settings)


def get_image_service(settings: Annotated[Settings, Depends(get_settings)]) -> ImageService:
    """Dependency for image service."""
    return ImageService(settings)


@router.post("/detect", response_model=VisionDetectResponse)
async def detect_items(
    request: VisionDetectRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
    image_service: ImageService = Depends(get_image_service),
) -> VisionDetectResponse:
    """
    Detect food items in uploaded photo using Gemini Vision.

    Args:
        request: Vision detection request with photo_id
        gemini_service: Gemini service dependency
        image_service: Image service dependency

    Returns:
        Detected items with confidence scores
    """
    # Get image path
    image_path = image_service.get_file_path(request.photo_id)

    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Photo not found: {request.photo_id}")

    try:
        # Detect items using Gemini
        items = await gemini_service.detect_items(str(image_path))

        # Check if confirmation needed (any item with low confidence)
        needs_confirmation = any(item.confidence < 0.7 for item in items)

        logger.info(
            f"Detected {len(items)} items for photo {request.photo_id} "
            f"(needs_confirmation={needs_confirmation})"
        )

        return VisionDetectResponse(
            items=items,
            needs_confirmation=needs_confirmation,
        )

    except Exception as e:
        logger.error(f"Error detecting items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect items: {str(e)}")
