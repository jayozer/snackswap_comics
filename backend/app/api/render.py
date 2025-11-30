"""Comic rendering endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from app.core.config import get_settings, Settings
from app.models import RenderComicRequest, RenderComicResponse
from app.api.script import scripts_store
from app.services.render_service import RenderService
from app.services.nanobana_service import NanoBananaService
from app.services.freepik_service import FreepikService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/comic", response_model=RenderComicResponse)
async def render_comic(
    request: RenderComicRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> RenderComicResponse:
    """
    Render a comic from a script.

    This endpoint integrates with:
    - Nano-Banana (Gemini 2.5 Flash Image) for comic image generation
    - Freepik API for comic assets (optional enhancement)
    - PIL/Pillow for composition and export formats

    Args:
        request: Render request with script_id
        settings: Application settings

    Returns:
        URIs to rendered comic assets in multiple formats
    """
    # Get script
    if request.script_id not in scripts_store:
        raise HTTPException(status_code=404, detail=f"Script not found: {request.script_id}")

    stored_data = scripts_store[request.script_id]
    # Extract the actual script result (which contains panels, caption, etc.)
    script_data = stored_data.get("script_result", stored_data)

    freepik_service = None
    try:
        logger.info(f"Rendering comic for script {request.script_id}")

        # Initialize services
        nanobana_service = NanoBananaService(settings)

        # Only create FreepikService if API key is configured
        use_freepik = bool(settings.freepik_api_key)
        if use_freepik:
            freepik_service = FreepikService(settings)

        render_service = RenderService(settings, nanobana_service, freepik_service)

        # Render comic with all formats
        result = await render_service.render_comic(
            script=script_data,
            script_id=request.script_id,
            use_freepik=use_freepik,
        )

        logger.info(f"Comic rendered successfully: {request.script_id}")

        return RenderComicResponse(
            comic_square_uri=result["comic_square_uri"],
            comic_portrait_uri=result["comic_portrait_uri"],
            reel_cover_uri=result["reel_cover_uri"],
        )

    except Exception as e:
        logger.error(f"Error rendering comic: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to render comic: {str(e)}")
    finally:
        # Clean up HTTP client to prevent connection leaks
        if freepik_service is not None:
            await freepik_service.close()
