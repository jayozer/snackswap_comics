#!/usr/bin/env python3
"""
Remove backgrounds from Dr. Hawley images using rembg.
Uses AI (U2-Net) to detect and remove backgrounds, producing true transparent PNGs.
"""

import sys
from pathlib import Path

from rembg import remove
from PIL import Image
import io

# Paths
FRONTEND_IMAGES = Path(__file__).parent.parent.parent / "frontend" / "public" / "images"
BACKUP_DIR = FRONTEND_IMAGES / "originals"

# Images to process
IMAGES_TO_PROCESS = [
    "Dr.Hawley_chillin.png",
    "Dr.Hawley_folded_hands.png",
    "Dr.Hawley_microphone.png",
    "Dr.Hawley_Crowning.png",
    "Dr.Hawley_raised_hands.png",
    "Dr.Hawley_unexpectedly_good.png",
    "roast_my_snack_logo.png",
]


def remove_background(image_path: Path) -> Image.Image | None:
    """
    Use rembg to remove background from an image.

    Args:
        image_path: Path to the input image

    Returns:
        PIL Image with transparent background, or None if failed
    """
    print(f"Processing: {image_path.name}")

    try:
        # Load the image
        with open(image_path, "rb") as f:
            input_bytes = f.read()

        # Remove background using rembg
        output_bytes = remove(input_bytes)

        # Convert to PIL Image
        output_image = Image.open(io.BytesIO(output_bytes))

        # Ensure it's RGBA (has alpha channel)
        if output_image.mode != "RGBA":
            output_image = output_image.convert("RGBA")

        print(f"  -> Processed: {output_image.size}, mode: {output_image.mode}")
        return output_image

    except Exception as e:
        print(f"  -> Error: {e}")
        return None


def process_all_images():
    """Process all images to remove backgrounds."""
    print(f"Images directory: {FRONTEND_IMAGES}")
    print(f"Backup directory: {BACKUP_DIR}")
    print()

    # Process each image
    print("=== Processing images ===")
    success_count = 0
    fail_count = 0

    for image_name in IMAGES_TO_PROCESS:
        # Use backup as source (original files)
        source_path = BACKUP_DIR / image_name
        output_path = FRONTEND_IMAGES / image_name

        if not source_path.exists():
            print(f"Skipping (backup not found): {image_name}")
            continue

        # Remove background
        result_image = remove_background(source_path)

        if result_image:
            # Save the processed image as PNG with alpha
            result_image.save(output_path, "PNG")
            print(f"  -> Saved: {output_path.name}")
            success_count += 1
        else:
            print(f"  -> FAILED: {image_name}")
            fail_count += 1

        print()

    # Summary
    print("=== Summary ===")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    process_all_images()
