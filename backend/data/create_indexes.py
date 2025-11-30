"""
Create payload indexes for Qdrant Cloud.

Qdrant Cloud requires explicit indexes for filtered queries.
Run this script if you get "Index required but not found" errors.

Usage:
    cd backend
    source .venv/bin/activate
    python -m data.create_indexes
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import Settings
from app.services.qdrant_service import QdrantService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Create all required payload indexes."""
    logger.info("Creating payload indexes for Qdrant Cloud...")

    settings = Settings()
    logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")

    qdrant = QdrantService(settings)

    # This will create indexes if they don't exist
    await qdrant._ensure_payload_indexes()

    logger.info("Payload indexes created successfully!")
    logger.info("You can now restart your backend server.")


if __name__ == "__main__":
    asyncio.run(main())
