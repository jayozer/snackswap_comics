"""
Freepik API service for fetching comic assets (speech bubbles, frames, backgrounds).
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

import httpx
from app.core.config import Settings

logger = logging.getLogger(__name__)


class FreepikService:
    """Service for searching and downloading comic assets from Freepik API."""

    BASE_URL = "https://api.freepik.com/v1"

    def __init__(self, settings: Settings):
        """Initialize Freepik service."""
        self.settings = settings
        self.api_key = settings.freepik_api_key
        self.cache_dir = Path(settings.storage_path) / "freepik_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.client = httpx.AsyncClient(
            headers={
                "x-freepik-api-key": self.api_key,
                "Accept": "application/json",
            },
            timeout=30.0,
        )

        logger.info("Initialized Freepik service")

    async def search_assets(
        self,
        query: str,
        content_type: str = "vector",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for assets on Freepik.

        Args:
            query: Search query (e.g., "comic speech bubble")
            content_type: Type of content (vector, photo, psd)
            limit: Number of results to return

        Returns:
            List of asset metadata
        """
        try:
            params = {
                "term": query,
                "limit": limit,
                "order": "relevance",
            }

            # Add content type filter
            if content_type:
                params[f"filters[content_type][{content_type}]"] = "true"

            response = await self.client.get(
                f"{self.BASE_URL}/resources",
                params=params,
            )

            response.raise_for_status()
            data = response.json()

            results = data.get("data", [])
            logger.info(f"Found {len(results)} assets for query: '{query}'")

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Freepik API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error searching Freepik: {e}")
            return []

    async def get_asset_details(self, resource_id: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific asset.

        Args:
            resource_id: Freepik resource ID

        Returns:
            Asset details or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/resources/{resource_id}"
            )

            response.raise_for_status()
            return response.json().get("data")

        except Exception as e:
            logger.error(f"Error getting asset details for {resource_id}: {e}")
            return None

    async def download_asset(
        self,
        resource_id: str,
        format_type: str = "svg",
    ) -> Path | None:
        """
        Download an asset from Freepik.

        Args:
            resource_id: Freepik resource ID
            format_type: Desired format (svg, png, jpg)

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Check cache first
            cache_key = hashlib.md5(f"{resource_id}_{format_type}".encode()).hexdigest()
            cache_file = self.cache_dir / f"{cache_key}.{format_type}"

            if cache_file.exists():
                logger.info(f"Using cached asset: {cache_file}")
                return cache_file

            # Get download URL
            response = await self.client.get(
                f"{self.BASE_URL}/resources/{resource_id}/download"
            )

            response.raise_for_status()
            download_data = response.json().get("data", {})
            download_url = download_data.get("url")

            if not download_url:
                logger.error(f"No download URL found for resource {resource_id}")
                return None

            # Download the file
            download_response = await self.client.get(download_url)
            download_response.raise_for_status()

            # Save to cache
            with open(cache_file, "wb") as f:
                f.write(download_response.content)

            logger.info(f"Downloaded asset {resource_id} to {cache_file}")
            return cache_file

        except Exception as e:
            logger.error(f"Error downloading asset {resource_id}: {e}")
            return None

    async def get_speech_bubbles(self, style: str = "comic", limit: int = 5) -> list[Path]:
        """
        Fetch speech bubble assets.

        Args:
            style: Style of speech bubble (comic, cartoon, modern)
            limit: Number of bubbles to fetch

        Returns:
            List of paths to downloaded speech bubble assets
        """
        query = f"{style} speech bubble vector"
        assets = await self.search_assets(query, content_type="vector", limit=limit)

        bubble_paths = []
        for asset in assets[:limit]:  # Limit downloads
            resource_id = asset.get("id")
            if resource_id:
                path = await self.download_asset(resource_id, format_type="svg")
                if path:
                    bubble_paths.append(path)

        logger.info(f"Fetched {len(bubble_paths)} speech bubble assets")
        return bubble_paths

    async def get_comic_frames(self, limit: int = 3) -> list[Path]:
        """
        Fetch comic panel frame/border assets.

        Args:
            limit: Number of frames to fetch

        Returns:
            List of paths to downloaded frame assets
        """
        query = "comic panel border frame vector"
        assets = await self.search_assets(query, content_type="vector", limit=limit)

        frame_paths = []
        for asset in assets[:limit]:
            resource_id = asset.get("id")
            if resource_id:
                path = await self.download_asset(resource_id, format_type="svg")
                if path:
                    frame_paths.append(path)

        logger.info(f"Fetched {len(frame_paths)} comic frame assets")
        return frame_paths

    async def get_backgrounds(self, theme: str = "bright colorful", limit: int = 3) -> list[Path]:
        """
        Fetch background assets for comic panels.

        Args:
            theme: Background theme
            limit: Number of backgrounds to fetch

        Returns:
            List of paths to downloaded background assets
        """
        query = f"{theme} comic background vector"
        assets = await self.search_assets(query, content_type="vector", limit=limit)

        bg_paths = []
        for asset in assets[:limit]:
            resource_id = asset.get("id")
            if resource_id:
                path = await self.download_asset(resource_id, format_type="svg")
                if path:
                    bg_paths.append(path)

        logger.info(f"Fetched {len(bg_paths)} background assets")
        return bg_paths

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
