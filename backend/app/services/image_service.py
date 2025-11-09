"""
Image processing service for SnackSwap Comics.
Handles uploads, EXIF rotation, HEIC conversion, and downscaling.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps

try:
    import pillow_heif

    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False
    logging.warning("pillow-heif not available, HEIC/HEIF support disabled")

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image processing and storage."""

    MAX_DIMENSION = 1400  # Max dimension for processing
    THUMBNAIL_SIZE = (400, 400)
    JPEG_QUALITY = 85

    def __init__(self, settings: Settings):
        """Initialize image service."""
        self.settings = settings
        self.storage_path = Path(settings.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.uploads_path = self.storage_path / "uploads"
        self.uploads_path.mkdir(exist_ok=True)

        self.thumbs_path = self.storage_path / "thumbs"
        self.thumbs_path.mkdir(exist_ok=True)

        logger.info(f"Initialized image service with storage at {self.storage_path}")

    async def process_upload(self, file_bytes: bytes, filename: str) -> dict:
        """
        Process an uploaded image file.

        Steps:
        1. Convert HEIC to JPEG if needed
        2. Fix EXIF orientation
        3. Downscale to max dimension
        4. Generate thumbnail
        5. Save processed images

        Args:
            file_bytes: Raw file bytes
            filename: Original filename

        Returns:
            Dictionary with photo_id, width, height, paths
        """
        photo_id = str(uuid.uuid4())

        # Determine if HEIC conversion needed
        file_ext = Path(filename).suffix.lower()
        is_heic = file_ext in [".heic", ".heif"]

        # Load image
        if is_heic:
            if not HEIF_AVAILABLE:
                raise ValueError("HEIC/HEIF format not supported (pillow-heif not installed)")

            # Register HEIF opener
            pillow_heif.register_heif_opener()

        # Open image from bytes
        try:
            image = Image.open(io.BytesIO(file_bytes))

            # Convert to RGB if needed (handles RGBA, P, etc.)
            if image.mode not in ["RGB", "L"]:
                image = image.convert("RGB")

        except Exception as e:
            logger.error(f"Error opening image: {e}")
            raise ValueError(f"Invalid or corrupted image file: {e}")

        # Fix EXIF orientation
        image = ImageOps.exif_transpose(image)

        # Downscale if needed
        original_width, original_height = image.size
        image = self._downscale_image(image, self.MAX_DIMENSION)
        width, height = image.size

        # Save processed image
        output_filename = f"{photo_id}.jpg"
        output_path = self.uploads_path / output_filename

        image.save(output_path, "JPEG", quality=self.JPEG_QUALITY, optimize=True)
        logger.info(
            f"Saved processed image: {output_filename} "
            f"({original_width}x{original_height} → {width}x{height})"
        )

        # Generate thumbnail
        thumb_filename = f"{photo_id}_thumb.jpg"
        thumb_path = self.thumbs_path / thumb_filename

        thumbnail = image.copy()
        thumbnail.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumbnail.save(thumb_path, "JPEG", quality=self.JPEG_QUALITY)

        logger.info(f"Generated thumbnail: {thumb_filename}")

        return {
            "photo_id": photo_id,
            "width": width,
            "height": height,
            "file_path": str(output_path),
            "thumb_path": str(thumb_path),
            "original_size": (original_width, original_height),
        }

    def _downscale_image(self, image: Image.Image, max_dimension: int) -> Image.Image:
        """
        Downscale image if either dimension exceeds max_dimension.

        Args:
            image: PIL Image
            max_dimension: Maximum width or height

        Returns:
            Downscaled image (or original if already small enough)
        """
        width, height = image.size

        if width <= max_dimension and height <= max_dimension:
            return image

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        logger.info(f"Downscaling image from {width}x{height} to {new_width}x{new_height}")

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def get_file_path(self, photo_id: str) -> Path:
        """Get the file path for a photo ID."""
        return self.uploads_path / f"{photo_id}.jpg"

    def get_thumb_path(self, photo_id: str) -> Path:
        """Get the thumbnail path for a photo ID."""
        return self.thumbs_path / f"{photo_id}_thumb.jpg"

    def get_uri(self, path: Path) -> str:
        """Convert a file path to a URI (relative to storage root)."""
        try:
            rel_path = path.relative_to(self.storage_path)
            return f"/storage/{rel_path}"
        except ValueError:
            # Path is not relative to storage_path
            return str(path)


# Missing import for io
import io
