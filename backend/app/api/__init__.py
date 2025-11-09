"""API routes for SnackSwap Comics."""

from fastapi import APIRouter

from .capture import router as capture_router
from .vision import router as vision_router
from .score import router as score_router
from .script import router as script_router
from .render import router as render_router
from .export import router as export_router

router = APIRouter()

# Include all route modules
router.include_router(capture_router, prefix="/capture", tags=["capture"])
router.include_router(vision_router, prefix="/vision", tags=["vision"])
router.include_router(score_router, prefix="/score", tags=["score"])
router.include_router(script_router, prefix="/script", tags=["script"])
router.include_router(render_router, prefix="/render", tags=["render"])
router.include_router(export_router, prefix="/export", tags=["export"])

__all__ = ["router"]
