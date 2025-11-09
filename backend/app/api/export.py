"""Export endpoints."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from app.core.config import get_settings, Settings
from app.models import ExportZipRequest, ExportZipResponse, ContentManifest
from app.api.script import scripts_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/zip", response_model=ExportZipResponse)
async def export_zip(
    request: ExportZipRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExportZipResponse:
    """
    Export a complete content package as a ZIP file.

    Includes:
    - Rendered comic images (square, portrait, reel cover)
    - Caption text file
    - Alt text file
    - Provenance manifest JSON

    For MVP, this returns a placeholder.

    Args:
        request: Export request with content_id
        settings: Application settings

    Returns:
        ZIP file URI and manifest
    """
    # In production, look up content by content_id
    # For now, treat content_id as script_id
    script_id = request.content_id

    if script_id not in scripts_store:
        raise HTTPException(status_code=404, detail=f"Content not found: {request.content_id}")

    script_data = scripts_store[script_id]
    script_result = script_data["script_result"]

    try:
        # TODO: Implement actual ZIP creation
        # 1. Gather all rendered assets
        # 2. Generate caption.txt and alt_text.txt
        # 3. Create manifest.json with provenance
        # 4. ZIP everything
        # 5. Upload to storage and return URI

        # Create manifest
        manifest = ContentManifest(
            content_id=request.content_id,
            models={
                "vision": settings.gemini_vision_model,
                "writer": settings.gemini_writer_model,
                "image": "placeholder",  # Would be Nano-Banana or other
            },
            facts=[
                {"fact_id": fact["fact_id"], "source": fact.get("source_key", "")}
                for fact in script_data["request"]["facts"][:3]
            ],
            snacks=[
                {"snack_id": item.snack_id}
                for item in script_data["request"]["scored_items"]
            ],
            swaps=[
                {"swap_id": swap["swap_id"]}
                for swap in script_data["request"]["swaps"][:3]
            ],
            style_id=script_data["request"]["style_id"],
            created_at=datetime.utcnow().isoformat(),
            license_info={
                "freepik": "Freepik assets used under license",
                "fonts": "Licensed fonts used",
            },
        )

        logger.info(f"Exporting content {request.content_id} (placeholder)")

        return ExportZipResponse(
            zip_uri=f"/storage/exports/{request.content_id}.zip",
            manifest_uri=f"/storage/exports/{request.content_id}_manifest.json",
            manifest=manifest,
        )

    except Exception as e:
        logger.error(f"Error exporting content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export content: {str(e)}")
