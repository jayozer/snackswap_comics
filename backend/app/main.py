"""
Main FastAPI application for SnackSwap Comics.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import get_settings
from app.services.qdrant_service import QdrantService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting SnackSwap Comics API")

    settings = get_settings()

    # Initialize Qdrant collections
    try:
        qdrant_service = QdrantService(settings)
        await qdrant_service.ensure_collections()
        logger.info("Qdrant collections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")

    yield

    logger.info("Shutting down SnackSwap Comics API")


# Create FastAPI app
app = FastAPI(
    title="SnackSwap Comics API",
    description="Turn snacks into delightful dental health comics",
    version="0.1.0",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes first
app.include_router(api_router, prefix="/api")

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Mount static files for storage
try:
    app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")
except Exception as e:
    logger.warning(f"Could not mount storage directory: {e}")

# Mount frontend static files (must be last to not conflict with API routes)
try:
    from pathlib import Path
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
        logger.info(f"Mounted frontend at {frontend_path}")
except Exception as e:
    logger.warning(f"Could not mount frontend directory: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
