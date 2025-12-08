"""Script composition endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from app.core.config import get_settings, Settings
from app.models import ScriptComposeRequest, ScriptComposeResponse, ComicMode
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for scripts (in production, use a database)
scripts_store = {}


def get_gemini_service(settings: Annotated[Settings, Depends(get_settings)]) -> GeminiService:
    """Dependency for Gemini service."""
    return GeminiService(settings)


@router.post("/compose", response_model=ScriptComposeResponse)
async def compose_script(
    request: ScriptComposeRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> ScriptComposeResponse:
    """
    Compose a 4-panel comic script using Gemini.

    Routes to different composition methods based on mode:
    - CELEBRATE: Positive celebration comic for healthy snacks
    - EDUCATE: Educational comic with facts and swap suggestions
    - UNKNOWN: Generic dental health tips when no snacks recognized

    Args:
        request: Script composition request
        gemini_service: Gemini service dependency

    Returns:
        Comic script with panels, caption, and alt text
    """
    try:
        # Prepare snack data
        snacks_data = [
            {
                "snack_id": item.snack_id,
                "name": item.name,
                "category": item.category,
                "risk_score": item.dental_risk_score,
            }
            for item in request.scored_items
        ]

        # Route to appropriate composition method based on mode
        if request.mode == ComicMode.CELEBRATE:
            logger.info(f"Composing CELEBRATE script for {len(snacks_data)} healthy snacks")
            script_result = await gemini_service.compose_celebrate_script(
                snacks=snacks_data,
                facts=request.facts,
                age=request.age,
            )
        elif request.mode == ComicMode.UNKNOWN:
            logger.info("Composing UNKNOWN script with generic dental tips")
            script_result = gemini_service.get_unknown_script(age=request.age)
        else:
            # Default to EDUCATE mode
            logger.info(f"Composing EDUCATE script for {len(snacks_data)} snacks")
            script_result = await gemini_service.compose_script(
                snacks=snacks_data,
                facts=request.facts,
                swaps=request.swaps,
                age=request.age,
            )

        # Generate script ID
        script_id = str(uuid.uuid4())

        # Store script (in production, save to database)
        scripts_store[script_id] = {
            "script_id": script_id,
            "script_result": script_result,
            "request": request.model_dump(),
            "mode": request.mode.value,
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Composed script {script_id} (mode={request.mode.value}) with {len(script_result['panels'])} panels")

        return ScriptComposeResponse(
            script_id=script_id,
            panels=script_result["panels"],
            caption=script_result["summary_caption"],
            alt_text=script_result["alt_text"],
        )

    except Exception as e:
        logger.error(f"Error composing script: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compose script: {str(e)}")


@router.get("/{script_id}")
async def get_script(script_id: str):
    """Get a script by ID."""
    if script_id not in scripts_store:
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")

    return scripts_store[script_id]
