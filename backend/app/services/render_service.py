"""
Comic rendering service - orchestrates the entire rendering pipeline.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from app.core.config import Settings
from app.services.nanobana_service import NanoBananaService
from app.services.freepik_service import FreepikService
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)


class RenderService:
    """Service for rendering comics from scripts."""

    def __init__(
        self,
        settings: Settings,
        nanobana_service: NanoBananaService = None,
        freepik_service: FreepikService = None,
        image_service: ImageService = None,
    ):
        """Initialize render service."""
        self.settings = settings
        self.nanobana = nanobana_service or NanoBananaService(settings)
        self.freepik = freepik_service or FreepikService(settings)
        self.image_service = image_service or ImageService(settings)

        self.storage_path = Path(settings.storage_path)
        self.renders_path = self.storage_path / "renders"
        self.renders_path.mkdir(parents=True, exist_ok=True)

        logger.info("Initialized render service")

    async def render_comic(
        self,
        script: dict[str, Any],
        script_id: str,
        use_freepik: bool = True,
    ) -> dict[str, str]:
        """
        Render a complete comic from a script.

        Args:
            script: Comic script with panels, dialogue, characters
            script_id: Unique script identifier
            use_freepik: Whether to use Freepik assets for enhancement

        Returns:
            Dictionary with URIs to rendered comic files
        """
        try:
            content_id = f"snackswap_{script_id[:8]}"
            logger.info(f"Rendering comic: {content_id}")

            # Step 1: Try to generate comic with Nano-Banana
            base_comic_path = None
            try:
                logger.info("Attempting to generate comic with Nano-Banana")
                base_comic_path = await self._generate_with_nanobana(script, content_id)
            except Exception as e:
                logger.warning(f"Nano-Banana generation failed: {e}. Falling back to Pillow rendering.")
                base_comic_path = None

            # Step 2: Fallback to Pillow-based rendering if Nano-Banana fails
            if not base_comic_path:
                logger.info("Using Pillow fallback for comic rendering")
                base_comic_path = await self._generate_with_pillow(script, content_id)

            # Step 3: Optionally enhance with Freepik assets
            if use_freepik and self.settings.freepik_api_key:
                try:
                    logger.info("Enhancing comic with Freepik assets")
                    base_comic_path = await self._enhance_with_freepik(base_comic_path, script)
                except Exception as e:
                    logger.warning(f"Freepik enhancement failed: {e}. Using base comic.")

            # Step 4: Generate multiple export formats
            logger.info("Generating export formats")
            formats = await self._generate_export_formats(base_comic_path, content_id)

            logger.info(f"Comic rendering complete: {content_id}")
            return formats

        except Exception as e:
            logger.error(f"Error rendering comic: {e}")
            raise

    async def _generate_with_nanobana(
        self,
        script: dict[str, Any],
        content_id: str,
    ) -> Path:
        """
        Generate comic image using Nano-Banana (Gemini 2.5 Flash Image).
        Then overlay text on the empty speech bubbles.

        Args:
            script: Comic script
            content_id: Content identifier

        Returns:
            Path to generated image with text overlay
        """
        # Generate base comic with empty bubbles
        # Note: Nano-Banana max resolution is 1K (1024x1024), API will ignore "2K" request
        temp_path = self.renders_path / f"{content_id}_nanobana_raw.png"
        result_path = await self.nanobana.generate_comic_image(script, temp_path, image_size="2K")

        # Add text overlay to the comic
        output_path = self.renders_path / f"{content_id}_base.png"
        final_path = await self._add_text_overlay(result_path, script, output_path)

        return final_path

    async def _generate_with_pillow(
        self,
        script: dict[str, Any],
        content_id: str,
    ) -> Path:
        """
        Generate comic using Pillow (fallback method).

        Creates a simple 4-panel layout with text and basic shapes.

        Args:
            script: Comic script
            content_id: Content identifier

        Returns:
            Path to generated image
        """
        # Create 4-panel comic (2x2 grid)
        panel_width = 540  # Each panel is 540x540
        panel_height = 540
        margin = 20
        border = 3

        total_width = (panel_width * 2) + (margin * 3)  # 1120px
        total_height = (panel_height * 2) + (margin * 3)  # 1120px

        # Create base image
        img = Image.new('RGB', (total_width, total_height), color='#F5F5F5')
        draw = ImageDraw.Draw(img)

        # Try to load fonts
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            dialogue_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
            caption_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except:
            logger.warning("Could not load custom fonts, using default")
            title_font = ImageFont.load_default()
            dialogue_font = ImageFont.load_default()
            caption_font = ImageFont.load_default()

        panels = script.get("panels", [])

        for i, panel in enumerate(panels):
            if i >= 4:  # Only render 4 panels
                break

            # Calculate panel position (2x2 grid)
            row = i // 2
            col = i % 2
            x = margin + (col * (panel_width + margin))
            y = margin + (row * (panel_height + margin))

            # Draw panel background
            bg_colors = ['#FFE5E5', '#E5F5FF', '#FFF5E5', '#E5FFE5']  # Soft pastels
            panel_bg = bg_colors[i % len(bg_colors)]
            draw.rectangle([x, y, x + panel_width, y + panel_height], fill=panel_bg, outline='#333', width=border)

            # Draw title
            title = panel.get("title", f"Panel {i+1}")
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = x + (panel_width - title_width) // 2
            draw.text((title_x, y + 15), title, fill='#333', font=title_font)

            # Draw characters as simple shapes with labels
            characters = panel.get("characters", [])
            if characters:
                char_y = y + 80
                char_spacing = panel_width // (len(characters) + 1)

                for j, char in enumerate(characters):
                    char_x = x + char_spacing * (j + 1)
                    char_name = char.get("name", "Character")
                    expression = char.get("expression", "happy")

                    # Draw character as a circle with color
                    char_colors = ['#FF6B9D', '#4ECDC4', '#FFE66D', '#95E1D3']
                    char_color = char_colors[j % len(char_colors)]

                    # Expression affects color intensity
                    if expression == "worried":
                        char_color = self._darken_color(char_color)
                    elif expression == "excited":
                        char_color = self._brighten_color(char_color)

                    # Draw character circle
                    radius = 40
                    draw.ellipse(
                        [char_x - radius, char_y - radius, char_x + radius, char_y + radius],
                        fill=char_color,
                        outline='#333',
                        width=2
                    )

                    # Draw simple face
                    eye_offset = 12
                    # Eyes
                    draw.ellipse([char_x - eye_offset - 5, char_y - 10, char_x - eye_offset + 5, char_y], fill='#333')
                    draw.ellipse([char_x + eye_offset - 5, char_y - 10, char_x + eye_offset + 5, char_y], fill='#333')

                    # Mouth based on expression
                    if expression == "happy" or expression == "excited":
                        draw.arc([char_x - 15, char_y, char_x + 15, char_y + 20], start=0, end=180, fill='#333', width=2)
                    elif expression == "worried" or expression == "shocked":
                        draw.ellipse([char_x - 8, char_y + 10, char_x + 8, char_y + 18], fill='#333')
                    else:
                        draw.line([char_x - 15, char_y + 10, char_x + 15, char_y + 10], fill='#333', width=2)

                    # Draw character name below
                    name_bbox = draw.textbbox((0, 0), char_name, font=caption_font)
                    name_width = name_bbox[2] - name_bbox[0]
                    draw.text((char_x - name_width // 2, char_y + radius + 10), char_name, fill='#333', font=caption_font)

            # Draw dialogue in speech bubbles
            dialogue = panel.get("dialogue", [])
            if dialogue:
                dialogue_y = y + panel_height - 150
                bubble_height = 40 * len(dialogue)

                # Speech bubble background
                bubble_margin = 10
                draw.rounded_rectangle(
                    [x + bubble_margin, dialogue_y, x + panel_width - bubble_margin, dialogue_y + bubble_height + 20],
                    radius=10,
                    fill='white',
                    outline='#333',
                    width=2
                )

                # Draw dialogue lines
                for j, line in enumerate(dialogue):
                    text_y = dialogue_y + 10 + (j * 35)
                    # Wrap text if too long
                    wrapped_line = self._wrap_text(line, dialogue_font, panel_width - 40)
                    for k, wrapped in enumerate(wrapped_line):
                        draw.text((x + 20, text_y + (k * 20)), wrapped, fill='#333', font=dialogue_font)

        # Add caption at bottom
        caption = script.get("caption", "")
        if caption:
            caption_y = total_height - 60
            draw.rectangle([0, caption_y - 10, total_width, total_height], fill='white', outline='#333', width=2)
            wrapped_caption = self._wrap_text(caption, dialogue_font, total_width - 40)
            for i, line in enumerate(wrapped_caption):
                draw.text((20, caption_y + (i * 22)), line, fill='#333', font=dialogue_font)

        # Save
        output_path = self.renders_path / f"{content_id}_base.png"
        img.save(output_path, 'PNG', quality=95)

        logger.info(f"Pillow comic generated: {output_path}")
        return output_path

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        """
        Wrap text to fit within max width using accurate font measurements.

        Uses PIL textbbox for pixel-perfect wrapping instead of character count estimation.
        """
        from PIL import ImageDraw

        # Create temporary draw context for measurements
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Use textbbox for accurate width measurement
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color by 20%."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * 0.8), int(g * 0.8), int(b * 0.8)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _brighten_color(self, hex_color: str) -> str:
        """Brighten a hex color by 20%."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _detect_bubble_position(
        self,
        img: Image.Image,
        panel_x: int,
        panel_y: int,
        panel_width: int,
        panel_height: int,
    ) -> tuple[int, int] | None:
        """
        Detect speech bubble position in a panel by finding white/light regions.

        Args:
            img: PIL Image
            panel_x: Panel X position
            panel_y: Panel Y position
            panel_width: Panel width
            panel_height: Panel height

        Returns:
            (center_x, center_y) of detected bubble or None if not found
        """
        try:
            # Scan top 40% of panel for bubbles
            scan_height = int(panel_height * 0.4)

            # Convert to grayscale for easier detection
            gray_img = img.convert('L')

            # Sample points in a grid across the top region
            white_points = []
            step = 20  # Sample every 20 pixels

            for y in range(panel_y + 10, panel_y + scan_height, step):
                for x in range(panel_x + 10, panel_x + panel_width - 10, step):
                    # Get pixel value
                    if 0 <= x < img.width and 0 <= y < img.height:
                        pixel = gray_img.getpixel((x, y))
                        # If pixel is very bright (white/light), it might be a bubble
                        if pixel > 230:  # Very white
                            white_points.append((x, y))

            # If we found enough white points, calculate their center
            if len(white_points) > 10:
                avg_x = sum(p[0] for p in white_points) // len(white_points)
                avg_y = sum(p[1] for p in white_points) // len(white_points)
                return (avg_x, avg_y)

            return None

        except Exception as e:
            logger.warning(f"Bubble detection failed: {e}")
            return None

    def _detect_bubble_boundaries(
        self,
        img: Image.Image,
        panel_x: int,
        panel_y: int,
        panel_width: int,
        panel_height: int,
    ) -> tuple[int, int, int, int] | None:
        """
        Detect speech bubble boundaries using OpenCV contour detection.

        This provides precise bubble boundaries instead of just center points,
        enabling accurate text sizing and positioning.

        Args:
            img: PIL Image
            panel_x: Panel X position
            panel_y: Panel Y position
            panel_width: Panel width
            panel_height: Panel height

        Returns:
            (x1, y1, x2, y2) bounding box of detected bubble or None if not found
        """
        try:
            import cv2
            import numpy as np

            # Extract panel region
            panel = img.crop((panel_x, panel_y, panel_x + panel_width, panel_y + panel_height))

            # Convert PIL to OpenCV format
            panel_cv = cv2.cvtColor(np.array(panel), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(panel_cv, cv2.COLOR_BGR2GRAY)

            # Find white/light regions (speech bubbles)
            # Lower threshold from 230 to 210 for more tolerance with off-white bubbles
            _, binary = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)

            # Apply morphological operations to clean up bubble detection
            kernel = np.ones((5, 5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # Fill small holes
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)   # Remove noise

            # Find contours of white regions
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Scan top 35% of panel for bubble contours (more focused region)
            scan_height = int(panel_height * 0.35)
            best_contour = None
            best_area = 0

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Check if contour is in top region and meets size requirements
                min_w = max(50, int(panel_width * 0.15))  # At least 15% of panel width
                min_h = max(25, int(panel_height * 0.05))  # At least 5% of panel height

                # CRITICAL: Add maximum size limits - bubbles shouldn't be too large
                # Reject if detected region is too big (likely detected background, not bubble)
                max_w = int(panel_width * 0.85)   # Max 85% of panel width
                max_h = int(panel_height * 0.30)  # Max 30% of panel height (bubbles are at top)

                # Must START in top region AND be reasonably sized
                if y < scan_height and w > min_w and h > min_h and w < max_w and h < max_h:
                    area = w * h
                    # Prefer larger contours (likely the main bubble)
                    if area > best_area:
                        best_area = area
                        best_contour = (x, y, w, h)

            if best_contour:
                x, y, w, h = best_contour
                # Convert from panel-relative to absolute image coordinates
                x1 = panel_x + x
                y1 = panel_y + y
                x2 = panel_x + x + w
                y2 = panel_y + y + h

                logger.info(f"OpenCV detected bubble: ({x1},{y1}) to ({x2},{y2}), size: {w}x{h}")
                return (x1, y1, x2, y2)

            logger.debug("No bubble boundaries detected with OpenCV")
            return None

        except ImportError:
            logger.warning("OpenCV not available, cannot use boundary detection")
            return None
        except Exception as e:
            logger.warning(f"Bubble boundary detection failed: {e}")
            return None

    def _get_expected_bubble_region(
        self,
        panel_x: int,
        panel_y: int,
        panel_width: int,
        panel_height: int,
    ) -> tuple[int, int, int, int]:
        """
        Get expected bubble region based on prompt instructions.

        The AI is instructed to leave the TOP 25% of each panel empty for bubbles.
        PIL will draw bubbles in this region.

        Args:
            panel_x: Panel X position
            panel_y: Panel Y position
            panel_width: Panel width
            panel_height: Panel height

        Returns:
            (x1, y1, x2, y2) bounding box for expected bubble region
        """
        # Bubbles should be in top 20% of panel with horizontal margins
        margin_x = int(panel_width * 0.08)  # 8% margin on each side
        bubble_y_start = panel_y + int(panel_height * 0.03)  # Start 3% from top
        bubble_y_end = panel_y + int(panel_height * 0.20)  # End at 20% from top

        x1 = panel_x + margin_x
        y1 = bubble_y_start
        x2 = panel_x + panel_width - margin_x
        y2 = bubble_y_end

        logger.debug(f"Expected bubble region: ({x1},{y1}) to ({x2},{y2})")
        return (x1, y1, x2, y2)

    def _draw_speech_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        tail_direction: str = "center",
    ) -> None:
        """
        Draw a speech bubble with tail pointing toward characters.

        Since AI can't reliably create empty bubbles, PIL draws them directly.
        This ensures consistent, clean bubbles without garbled AI text.

        Args:
            draw: PIL ImageDraw object
            x: Bubble top-left X coordinate
            y: Bubble top-left Y coordinate
            width: Bubble width
            height: Bubble height
            tail_direction: Direction of tail ("left", "center", "right")
        """
        # Draw main bubble ellipse - white fill with black outline
        draw.ellipse(
            [x, y, x + width, y + height],
            fill="white",
            outline="black",
            width=3
        )

        # Calculate tail position based on direction
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:  # center
            tail_x = x + width // 2

        # Draw tail triangle pointing down toward characters
        # The tail connects the bubble to the characters below
        tail_base_y = y + height - 8  # Slightly inside bubble for overlap
        tail_tip_y = y + height + int(height * 0.25)  # 25% below bubble

        tail_points = [
            (tail_x - 12, tail_base_y),  # Left point of tail base
            (tail_x + 12, tail_base_y),  # Right point of tail base
            (tail_x, tail_tip_y),        # Tip of tail pointing down
        ]

        # Draw tail with same styling as bubble
        draw.polygon(tail_points, fill="white", outline="black", width=2)

        # Cover the outline where tail meets bubble (clean connection)
        draw.line(
            [(tail_x - 10, tail_base_y), (tail_x + 10, tail_base_y)],
            fill="white",
            width=5
        )

    async def _detect_bubbles_with_vision(
        self,
        image_path: Path,
    ) -> dict[int, tuple[int, int, int, int]] | None:
        """
        Use Gemini Vision to detect speech bubble locations in comic panels.

        This provides AI-powered bubble detection that's more reliable than
        OpenCV for varied layouts and bubble styles.

        Args:
            image_path: Path to the generated comic image

        Returns:
            Dict mapping panel number (0-3) to bubble bbox (x1, y1, x2, y2)
            or None if detection fails
        """
        try:
            from google import genai
            from google.genai import types
            import json
            import mimetypes

            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Determine mime type
            mime_type, _ = mimetypes.guess_type(str(image_path))
            if not mime_type:
                mime_type = "image/png"

            # Create vision prompt
            prompt = """Analyze this 4-panel comic image arranged in a 2x2 grid.

The panels are numbered:
- Panel 1: Top-left
- Panel 2: Top-right
- Panel 3: Bottom-left
- Panel 4: Bottom-right

For EACH panel, detect the PRIMARY speech bubble (white or light colored oval with black outline).
Focus on bubbles in the TOP 40% of each panel only.

Return JSON with this EXACT structure:
{
  "bubbles": [
    {"panel": 1, "x1": 50, "y1": 20, "x2": 450, "y2": 120},
    {"panel": 2, "x1": 550, "y1": 25, "x2": 950, "y2": 115},
    {"panel": 3, "x1": 45, "y1": 520, "x2": 445, "y2": 620},
    {"panel": 4, "x1": 545, "y1": 525, "x2": 945, "y2": 615}
  ]
}

Rules:
- Coordinates are ABSOLUTE pixels from image top-left (0,0)
- x1,y1 is top-left corner of bubble
- x2,y2 is bottom-right corner of bubble
- Only include the LARGEST/PRIMARY bubble per panel
- Ignore small decorative elements
- Return ONLY valid JSON, no other text"""

            # Initialize client with new SDK
            client = genai.Client(api_key=self.settings.gemini_api_key)

            # Generate response using vision model with inline data
            response = client.models.generate_content(
                model=self.settings.gemini_vision_model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_bytes(
                                data=image_data,
                                mime_type=mime_type
                            ),
                        ],
                    ),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low for factual detection
                    max_output_tokens=1024,
                ),
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            # Convert to dict mapping panel number to bbox
            bubbles_by_panel = {}
            for bubble in result.get("bubbles", []):
                panel_num = bubble["panel"] - 1  # Convert to 0-indexed
                if 0 <= panel_num < 4:
                    bubbles_by_panel[panel_num] = (
                        bubble["x1"],
                        bubble["y1"],
                        bubble["x2"],
                        bubble["y2"],
                    )

            logger.info(f"Gemini Vision detected {len(bubbles_by_panel)} bubbles")
            return bubbles_by_panel if bubbles_by_panel else None

        except Exception as e:
            logger.warning(f"Gemini Vision bubble detection failed: {e}")
            return None

    def _fit_text_to_bubble(
        self,
        text: str,
        bubble_width: int,
        bubble_height: int,
        max_font_size: int = 32,  # Scaled for 2K images
        min_font_size: int = 16,  # Scaled for 2K images
    ) -> tuple[int, list[str]]:
        """
        Find the optimal font size and text wrapping to fit text in bubble.

        Iterates from max to min font size, testing if text fits.
        Returns largest size that fits comfortably.

        Args:
            text: Text to fit
            bubble_width: Available width in pixels
            bubble_height: Available height in pixels
            max_font_size: Maximum font size to try
            min_font_size: Minimum font size (readability limit)

        Returns:
            (font_size, wrapped_lines) tuple
        """
        from PIL import ImageDraw, ImageFont

        # Create temporary draw context for measurements
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        # Leave margins for bubble outline and padding
        available_width = int(bubble_width * 0.85)  # 15% margin
        available_height = int(bubble_height * 0.75)  # 25% margin

        # Try font sizes from largest to smallest
        for font_size in range(max_font_size, min_font_size - 1, -2):  # Step by 2 for speed
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf", font_size)

                # Wrap text with this font size
                wrapped = self._wrap_text(text, font, available_width)

                # Calculate total height needed
                line_height = font_size + 4  # 4px spacing between lines
                total_height = len(wrapped) * line_height

                # Check if it fits vertically
                if total_height <= available_height and len(wrapped) <= 3:  # Max 3 lines
                    logger.debug(f"Fit text at font size {font_size}: {len(wrapped)} lines")
                    return (font_size, wrapped)

            except Exception as e:
                logger.debug(f"Error testing font size {font_size}: {e}")
                continue

        # Fallback: use minimum size
        logger.warning(f"Could not fit text optimally, using minimum font size {min_font_size}")
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf", min_font_size)
        wrapped = self._wrap_text(text, font, available_width)
        return (min_font_size, wrapped[:3])  # Truncate to 3 lines max

    async def _add_text_overlay(
        self,
        base_image_path: Path,
        script: dict[str, Any],
        output_path: Path,
    ) -> Path:
        """
        Add speech bubbles and text overlay to comic image.

        Since AI cannot reliably create empty bubbles (generates garbled text),
        PIL now draws the bubbles directly in a fixed position (top 20% of each panel).

        This approach:
        1. Calculates fixed bubble position in top 20% of panel
        2. Draws clean speech bubble with tail
        3. Adds text centered inside the bubble

        Args:
            base_image_path: Path to base comic image (from AI - no bubbles)
            script: Comic script with dialogue
            output_path: Where to save the result

        Returns:
            Path to image with bubbles and text
        """
        try:
            img = Image.open(base_image_path)
            draw = ImageDraw.Draw(img)

            # Get image dimensions
            img_width, img_height = img.size
            logger.info(f"Processing comic image: {img_width}x{img_height}")

            # Assuming 2x2 grid layout
            panel_width = img_width // 2
            panel_height = img_height // 2

            panels = script.get("panels", [])
            logger.info(f"Script has {len(panels)} panels - PIL will draw bubbles")

            for i, panel in enumerate(panels):
                if i >= 4:  # Only 4 panels
                    break

                dialogue = panel.get("dialogue", [])
                if not dialogue:
                    logger.info(f"Panel {i+1}: NO DIALOGUE - skipping bubble")
                    continue

                # Calculate panel position
                row = i // 2
                col = i % 2
                panel_x = col * panel_width
                panel_y = row * panel_height

                logger.info(f"Panel {i+1}: Position ({panel_x}, {panel_y}), Size {panel_width}x{panel_height}")

                # Get bubble region (top 20% of panel)
                x1, y1, x2, y2 = self._get_expected_bubble_region(
                    panel_x, panel_y, panel_width, panel_height
                )
                bubble_width = x2 - x1
                bubble_height = y2 - y1

                # DRAW the speech bubble (PIL draws it, not AI)
                # Tail direction based on panel position (left panels point left, right panels point right)
                tail_dir = "left" if col == 0 else "right"
                self._draw_speech_bubble(draw, x1, y1, bubble_width, bubble_height, tail_dir)

                logger.info(f"Panel {i+1}: Drew bubble at ({x1},{y1}) size {bubble_width}x{bubble_height}")

                # Combine all dialogue into single text block
                full_dialogue = " ".join(dialogue)

                # Calculate optimal font size and wrapping for this bubble
                font_size, wrapped_lines = self._fit_text_to_bubble(
                    full_dialogue,
                    bubble_width,
                    bubble_height,
                    max_font_size=28,
                    min_font_size=14
                )

                # Load font at optimal size
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf", font_size)
                    except:
                        logger.warning(f"Comic Sans not found, using default font")
                        font = ImageFont.load_default()

                # Position text in bubble center
                line_height = font_size + 4
                total_text_height = len(wrapped_lines) * line_height
                text_start_y = y1 + (bubble_height - total_text_height) // 2

                logger.info(f"Panel {i+1}: font {font_size}px, {len(wrapped_lines)} lines")

                # Draw the wrapped lines
                for k, wrapped_line in enumerate(wrapped_lines):
                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), wrapped_line, font=font)
                    text_width = bbox[2] - bbox[0]

                    # Center text horizontally within bubble
                    text_x = x1 + (bubble_width - text_width) // 2
                    actual_text_y = text_start_y + (k * line_height)

                    # Draw black text on white bubble (no outline needed)
                    draw.text((text_x, actual_text_y), wrapped_line, font=font, fill="black")

                    logger.debug(f"Panel {i+1}: Drew line {k+1} at ({text_x}, {actual_text_y})")

            # Save the result
            img.save(output_path, 'PNG', quality=95)
            logger.info(f"Text overlay complete: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error adding text overlay: {e}", exc_info=True)
            # If overlay fails, return the original image
            return base_image_path

    def _wrap_text_simple(self, text: str, max_chars: int) -> list[str]:
        """Simple text wrapping by character count."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length <= max_chars:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    async def _enhance_with_freepik(
        self,
        base_image_path: Path,
        script: dict[str, Any],
    ) -> Path:
        """
        Enhance comic with Freepik assets (speech bubbles, frames, etc.).

        Args:
            base_image_path: Path to base comic image
            script: Comic script

        Returns:
            Path to enhanced image
        """
        # TODO: Implement Freepik enhancement
        # For now, just return the base image
        logger.info("Freepik enhancement not yet implemented, using base image")
        return base_image_path

    async def _generate_export_formats(
        self,
        base_image_path: Path,
        content_id: str,
    ) -> dict[str, str]:
        """
        Generate multiple export formats from base image.

        Args:
            base_image_path: Path to base comic image
            content_id: Content identifier

        Returns:
            Dictionary with URIs for each format
        """
        img = Image.open(base_image_path)

        # Square format (1080x1080) - for Instagram, TikTok
        square_path = self.renders_path / f"{content_id}_square.png"
        square_img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        square_img.save(square_path, 'PNG', quality=95)

        # Portrait format (1080x1350) - for Instagram Stories, Pinterest
        portrait_path = self.renders_path / f"{content_id}_portrait.png"
        portrait_img = img.resize((1080, 1350), Image.Resampling.LANCZOS)
        portrait_img.save(portrait_path, 'PNG', quality=95)

        # Reel cover (1080x1920) - for video platforms
        reel_path = self.renders_path / f"{content_id}_reel.png"
        reel_img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        reel_img.save(reel_path, 'PNG', quality=95)

        logger.info(f"Generated export formats for {content_id}")

        return {
            "comic_square_uri": f"/storage/renders/{square_path.name}",
            "comic_portrait_uri": f"/storage/renders/{portrait_path.name}",
            "reel_cover_uri": f"/storage/renders/{reel_path.name}",
        }
