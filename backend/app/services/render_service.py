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

# Emotion-based bubble styles for speech bubble rendering
# Maps emotion type to visual style properties
BUBBLE_STYLES = {
    "speech": {"shape": "oval", "outline": "black", "fill": "white"},
    "thought": {"shape": "cloud", "outline": "gray", "fill": "white"},
    "exclaim": {"shape": "spiky", "outline": "#cc0000", "fill": "#ffff99"},
    "angry": {"shape": "jagged", "outline": "#8b0000", "fill": "#ffcccc"},
    "whisper": {"shape": "dashed", "outline": "gray", "fill": "#f0f0f0"},
}


class RenderService:
    """Service for rendering comics from scripts."""

    # Feature flag for AI bubble detection (set to False to always use PIL fallback)
    USE_AI_BUBBLE_DETECTION = True

    def __init__(
        self,
        settings: Settings,
        nanobana_service: NanoBananaService = None,
        freepik_service: FreepikService = None,
        image_service: ImageService = None,
        gemini_service=None,  # Optional: for bubble detection
    ):
        """Initialize render service."""
        self.settings = settings
        self.nanobana = nanobana_service or NanoBananaService(settings)
        self.freepik = freepik_service or FreepikService(settings)
        self.image_service = image_service or ImageService(settings)
        self.gemini = gemini_service  # Lazy load if needed

        self.storage_path = Path(settings.storage_path)
        self.renders_path = self.storage_path / "renders"
        self.renders_path.mkdir(parents=True, exist_ok=True)

        logger.info("Initialized render service")

    def _svg_to_png(self, svg_path: Path, width: int, height: int) -> Image.Image:
        """
        Convert SVG to PIL Image at specified size.

        Uses CairoSVG for high-quality vector-to-raster conversion.
        Essential for Freepik assets which are SVG vectors.

        Args:
            svg_path: Path to SVG file
            width: Target width in pixels
            height: Target height in pixels

        Returns:
            PIL Image in RGBA mode
        """
        import cairosvg
        from io import BytesIO

        png_data = cairosvg.svg2png(
            url=str(svg_path),
            output_width=width,
            output_height=height,
        )
        return Image.open(BytesIO(png_data)).convert("RGBA")

    def _blend_background(
        self,
        base_img: Image.Image,
        bg_img: Image.Image,
        opacity: float = 0.35,
    ) -> Image.Image:
        """
        Blend a background image under the base image at specified opacity.

        This creates a subtle texture/mood layer that enhances the comic
        without overwhelming the Nano-Banana generated characters.

        Args:
            base_img: The base comic image (RGBA)
            bg_img: The background to blend (RGBA)
            opacity: Background opacity (0.0 to 1.0), default 0.35

        Returns:
            Blended image (RGBA)
        """
        # Ensure both images are RGBA
        base_img = base_img.convert("RGBA")
        bg_img = bg_img.convert("RGBA")

        # Resize background to match base dimensions
        bg_resized = bg_img.resize(base_img.size, Image.Resampling.LANCZOS)

        # Apply opacity to background by modifying alpha channel
        r, g, b, a = bg_resized.split()
        a = a.point(lambda x: int(x * opacity))
        bg_with_opacity = Image.merge("RGBA", (r, g, b, a))

        # Composite: white base → background at opacity → base image on top
        result = Image.new("RGBA", base_img.size, (255, 255, 255, 255))
        result = Image.alpha_composite(result, bg_with_opacity)
        result = Image.alpha_composite(result, base_img)

        return result

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
                    enhanced_path = await self._enhance_with_freepik(base_comic_path, script)
                    # Re-apply text overlay on top of Freepik bubbles
                    final_output = self.renders_path / f"{content_id}_final.png"
                    base_comic_path = await self._add_text_overlay(enhanced_path, script, final_output)
                    logger.info(f"Freepik enhancement with text overlay complete: {base_comic_path}")
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
        # Generate base comic as 1x4 vertical strip with empty bubbles
        # Resolution: 1K = 512×1024 (vertical strip)
        temp_path = self.renders_path / f"{content_id}_nanobana_raw.png"
        result_path = await self.nanobana.generate_comic_image(script, temp_path, image_size="1K")

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

        Creates a 1x4 vertical strip layout with text and basic shapes.

        Args:
            script: Comic script
            content_id: Content identifier

        Returns:
            Path to generated image
        """
        # Create 4-panel comic (1x4 vertical strip)
        panel_width = 512  # Each panel is 512x256
        panel_height = 256
        margin = 8
        border = 2

        total_width = panel_width + (margin * 2)  # 528px
        total_height = (panel_height * 4) + (margin * 5)  # 1064px

        # Create base image
        img = Image.new('RGB', (total_width, total_height), color='#F5F5F5')
        draw = ImageDraw.Draw(img)

        # Try to load fonts (scaled for smaller 256px panels)
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
            dialogue_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
            caption_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
        except:
            logger.warning("Could not load custom fonts, using default")
            title_font = ImageFont.load_default()
            dialogue_font = ImageFont.load_default()
            caption_font = ImageFont.load_default()

        panels = script.get("panels", [])

        for i, panel in enumerate(panels):
            if i >= 4:  # Only render 4 panels
                break

            # Calculate panel position (1x4 vertical strip)
            x = margin  # Single column
            y = margin + (i * (panel_height + margin))

            # Draw panel background
            bg_colors = ['#FFE5E5', '#E5F5FF', '#FFF5E5', '#E5FFE5']  # Soft pastels
            panel_bg = bg_colors[i % len(bg_colors)]
            draw.rectangle([x, y, x + panel_width, y + panel_height], fill=panel_bg, outline='#333', width=border)

            # Draw title
            title = panel.get("title", f"Panel {i+1}")
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = x + (panel_width - title_width) // 2
            draw.text((title_x, y + 8), title, fill='#333', font=title_font)

            # Draw characters as simple shapes with labels (scaled for 256px panels)
            characters = panel.get("characters", [])
            if characters:
                char_y = y + 55  # Scaled from 80
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

                    # Draw character circle (scaled)
                    radius = 25
                    draw.ellipse(
                        [char_x - radius, char_y - radius, char_x + radius, char_y + radius],
                        fill=char_color,
                        outline='#333',
                        width=2
                    )

                    # Draw simple face (scaled)
                    eye_offset = 8
                    # Eyes
                    draw.ellipse([char_x - eye_offset - 3, char_y - 6, char_x - eye_offset + 3, char_y], fill='#333')
                    draw.ellipse([char_x + eye_offset - 3, char_y - 6, char_x + eye_offset + 3, char_y], fill='#333')

                    # Mouth based on expression (scaled)
                    if expression == "happy" or expression == "excited":
                        draw.arc([char_x - 10, char_y, char_x + 10, char_y + 12], start=0, end=180, fill='#333', width=2)
                    elif expression == "worried" or expression == "shocked":
                        draw.ellipse([char_x - 5, char_y + 6, char_x + 5, char_y + 12], fill='#333')
                    else:
                        draw.line([char_x - 10, char_y + 6, char_x + 10, char_y + 6], fill='#333', width=2)

                    # Draw character name below
                    name_bbox = draw.textbbox((0, 0), char_name, font=caption_font)
                    name_width = name_bbox[2] - name_bbox[0]
                    draw.text((char_x - name_width // 2, char_y + radius + 5), char_name, fill='#333', font=caption_font)

            # Draw dialogue in speech bubbles (scaled for 256px panels)
            dialogue = panel.get("dialogue", [])
            if dialogue:
                dialogue_y = y + panel_height - 80  # Scaled from 150
                bubble_height = 25 * min(len(dialogue), 2)  # Max 2 lines in small panels

                # Speech bubble background
                bubble_margin = 8
                draw.rounded_rectangle(
                    [x + bubble_margin, dialogue_y, x + panel_width - bubble_margin, dialogue_y + bubble_height + 12],
                    radius=6,
                    fill='white',
                    outline='#333',
                    width=2
                )

                # Draw dialogue lines (limit to 2 lines for small panels)
                for j, line in enumerate(dialogue[:2]):
                    text_y = dialogue_y + 6 + (j * 18)
                    # Wrap text if too long
                    wrapped_line = self._wrap_text(line, dialogue_font, panel_width - 30)
                    for k, wrapped in enumerate(wrapped_line[:1]):  # Only first wrap line
                        draw.text((x + 15, text_y + (k * 14)), wrapped, fill='#333', font=dialogue_font)

        # Add caption at bottom (scaled)
        caption = script.get("caption", "")
        if caption:
            caption_y = total_height - 35
            draw.rectangle([0, caption_y - 6, total_width, total_height], fill='white', outline='#333', width=2)
            wrapped_caption = self._wrap_text(caption, dialogue_font, total_width - 30)
            for i, line in enumerate(wrapped_caption[:2]):  # Max 2 lines
                draw.text((15, caption_y + (i * 14)), line, fill='#333', font=dialogue_font)

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
        emotion: str = "speech",
    ) -> None:
        """
        Draw an emotion-appropriate speech bubble with tail.

        Supports different bubble styles based on emotion:
        - speech: Standard oval bubble (white, black outline)
        - thought: Cloud-like bubble with small circles as tail
        - exclaim: Spiky starburst bubble (yellow, red outline)
        - angry: Jagged irregular bubble (light red, dark red outline)
        - whisper: Dashed outline bubble (light gray)

        Args:
            draw: PIL ImageDraw object
            x: Bubble top-left X coordinate
            y: Bubble top-left Y coordinate
            width: Bubble width
            height: Bubble height
            tail_direction: Direction of tail ("left", "center", "right")
            emotion: Bubble emotion style
        """
        style = BUBBLE_STYLES.get(emotion, BUBBLE_STYLES["speech"])

        if style["shape"] == "oval":
            self._draw_oval_bubble(draw, x, y, width, height, style, tail_direction)
        elif style["shape"] == "cloud":
            self._draw_cloud_bubble(draw, x, y, width, height, style, tail_direction)
        elif style["shape"] == "spiky":
            self._draw_spiky_bubble(draw, x, y, width, height, style, tail_direction)
        elif style["shape"] == "jagged":
            self._draw_jagged_bubble(draw, x, y, width, height, style, tail_direction)
        elif style["shape"] == "dashed":
            self._draw_dashed_bubble(draw, x, y, width, height, style, tail_direction)
        else:
            # Default to oval
            self._draw_oval_bubble(draw, x, y, width, height, style, tail_direction)

    def _draw_oval_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        style: dict,
        tail_direction: str,
    ) -> None:
        """Draw standard oval speech bubble."""
        fill = style.get("fill", "white")
        outline = style.get("outline", "black")

        # Draw main bubble ellipse
        draw.ellipse(
            [x, y, x + width, y + height],
            fill=fill,
            outline=outline,
            width=3
        )

        # Calculate tail position
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:
            tail_x = x + width // 2

        # Draw tail triangle
        tail_base_y = y + height - 8
        tail_tip_y = y + height + int(height * 0.25)

        tail_points = [
            (tail_x - 12, tail_base_y),
            (tail_x + 12, tail_base_y),
            (tail_x, tail_tip_y),
        ]

        draw.polygon(tail_points, fill=fill, outline=outline, width=2)
        draw.line(
            [(tail_x - 10, tail_base_y), (tail_x + 10, tail_base_y)],
            fill=fill,
            width=5
        )

    def _draw_cloud_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        style: dict,
        tail_direction: str,
    ) -> None:
        """Draw thought bubble with cloud-like shape."""
        fill = style.get("fill", "white")
        outline = style.get("outline", "gray")

        # Draw overlapping circles to create cloud effect
        cx = x + width // 2
        cy = y + height // 2
        r_main = min(width, height) // 2

        # Main center ellipse
        draw.ellipse(
            [cx - r_main, cy - r_main // 2, cx + r_main, cy + r_main // 2],
            fill=fill,
            outline=outline,
            width=2
        )

        # Bumps around the edges
        bump_positions = [
            (cx - r_main * 0.7, cy - r_main * 0.3, r_main * 0.4),
            (cx + r_main * 0.7, cy - r_main * 0.3, r_main * 0.4),
            (cx - r_main * 0.5, cy + r_main * 0.2, r_main * 0.35),
            (cx + r_main * 0.5, cy + r_main * 0.2, r_main * 0.35),
            (cx, cy - r_main * 0.4, r_main * 0.45),
        ]

        for bx, by, br in bump_positions:
            draw.ellipse(
                [int(bx - br), int(by - br), int(bx + br), int(by + br)],
                fill=fill,
                outline=outline,
                width=2
            )

        # Thought bubble tail - small circles leading down
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:
            tail_x = x + width // 2

        # Three decreasing circles for tail
        tail_y = y + height
        for i, r in enumerate([8, 5, 3]):
            draw.ellipse(
                [tail_x - r, tail_y + i * 12 - r, tail_x + r, tail_y + i * 12 + r],
                fill=fill,
                outline=outline,
                width=2
            )

    def _draw_spiky_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        style: dict,
        tail_direction: str,
    ) -> None:
        """Draw starburst/spiky bubble for exclamations."""
        import math

        fill = style.get("fill", "#ffff99")
        outline = style.get("outline", "#cc0000")

        cx = x + width // 2
        cy = y + height // 2

        # Create starburst polygon
        points = []
        num_spikes = 12
        outer_r = min(width, height) // 2
        inner_r = outer_r * 0.7

        for i in range(num_spikes * 2):
            angle = math.pi * i / num_spikes - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle) * (height / width)  # Adjust for aspect ratio
            points.append((int(px), int(py)))

        draw.polygon(points, fill=fill, outline=outline, width=3)

        # Add tail
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:
            tail_x = x + width // 2

        tail_base_y = y + height - 5
        tail_tip_y = y + height + int(height * 0.3)

        tail_points = [
            (tail_x - 15, tail_base_y),
            (tail_x + 15, tail_base_y),
            (tail_x, tail_tip_y),
        ]

        draw.polygon(tail_points, fill=fill, outline=outline, width=2)

    def _draw_jagged_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        style: dict,
        tail_direction: str,
    ) -> None:
        """Draw jagged/irregular bubble for anger."""
        import math
        import random

        random.seed(42)  # Consistent jaggedness

        fill = style.get("fill", "#ffcccc")
        outline = style.get("outline", "#8b0000")

        # Create irregular polygon with sharp edges
        points = []
        num_points = 16
        cx = x + width // 2
        cy = y + height // 2

        for i in range(num_points):
            angle = 2 * math.pi * i / num_points - math.pi / 2
            # Vary radius randomly for jagged effect
            base_r = min(width, height) // 2
            r = base_r * (0.75 + random.random() * 0.4)
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle) * (height / width)
            points.append((int(px), int(py)))

        draw.polygon(points, fill=fill, outline=outline, width=3)

        # Sharp angular tail
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:
            tail_x = x + width // 2

        tail_base_y = y + height - 8
        tail_tip_y = y + height + int(height * 0.35)

        # Jagged tail with extra point
        tail_points = [
            (tail_x - 18, tail_base_y),
            (tail_x - 5, tail_base_y + 10),
            (tail_x, tail_tip_y),
            (tail_x + 5, tail_base_y + 8),
            (tail_x + 18, tail_base_y),
        ]

        draw.polygon(tail_points, fill=fill, outline=outline, width=2)

    def _draw_dashed_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        style: dict,
        tail_direction: str,
    ) -> None:
        """Draw dashed outline bubble for whispers."""
        import math

        fill = style.get("fill", "#f0f0f0")
        outline = style.get("outline", "gray")

        # Draw filled ellipse first
        draw.ellipse(
            [x, y, x + width, y + height],
            fill=fill,
        )

        # Draw dashed outline manually
        cx = x + width // 2
        cy = y + height // 2
        rx = width // 2
        ry = height // 2

        # Draw dashes around ellipse
        num_dashes = 24
        dash_len = 0.7  # Fraction of segment that's visible

        for i in range(num_dashes):
            angle1 = 2 * math.pi * i / num_dashes
            angle2 = 2 * math.pi * (i + dash_len) / num_dashes

            x1 = cx + rx * math.cos(angle1)
            y1 = cy + ry * math.sin(angle1)
            x2 = cx + rx * math.cos(angle2)
            y2 = cy + ry * math.sin(angle2)

            draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=outline, width=2)

        # Dashed tail
        if tail_direction == "left":
            tail_x = x + width // 4
        elif tail_direction == "right":
            tail_x = x + 3 * width // 4
        else:
            tail_x = x + width // 2

        tail_base_y = y + height - 5
        tail_tip_y = y + height + int(height * 0.2)

        # Draw dashed lines for tail
        for i in range(3):
            y_start = tail_base_y + i * 8
            y_end = min(y_start + 5, tail_tip_y)
            draw.line(
                [(tail_x - 8 + i * 4, y_start), (tail_x - 4 + i * 4, y_end)],
                fill=outline,
                width=2
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

            # Create vision prompt for 1x4 vertical layout
            prompt = """Analyze this 4-panel comic image arranged as a VERTICAL STRIP (1x4 layout).

Image dimensions: 512×1024 pixels (tall vertical strip)
Each panel is approximately 512×256 pixels.

The panels are stacked vertically:
- Panel 1: Top (rows 0-256)
- Panel 2: Second from top (rows 256-512)
- Panel 3: Third from top (rows 512-768)
- Panel 4: Bottom (rows 768-1024)

For EACH panel, detect the PRIMARY speech bubble (white or light colored oval with black outline).
Focus on bubbles in the TOP 40% of each panel only.

Return JSON with this EXACT structure:
{
  "bubbles": [
    {"panel": 1, "x1": 40, "y1": 10, "x2": 470, "y2": 50},
    {"panel": 2, "x1": 40, "y1": 266, "x2": 470, "y2": 306},
    {"panel": 3, "x1": 40, "y1": 522, "x2": 470, "y2": 562},
    {"panel": 4, "x1": 40, "y1": 778, "x2": 470, "y2": 818}
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
        max_font_size: int = 18,  # Scaled for 1K images (512×1024)
        min_font_size: int = 10,  # Scaled for 1K images
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

    async def _try_detect_bubbles(
        self,
        image_path: Path,
        panels_with_dialogue: list[int],
        max_retries: int = 1,
    ) -> dict[int, dict] | None:
        """
        Try to detect bubble positions with retry logic.

        Detection cascade:
        1. Gemini Vision (most accurate, ~1 API call)
        2. OpenCV contour detection (fast, no cost)
        3. Return None to trigger PIL fallback

        Args:
            image_path: Path to comic image
            panels_with_dialogue: List of panel indices that have dialogue
            max_retries: Number of retries for Gemini Vision

        Returns:
            Dict of detected bubbles or None if detection fails
        """
        # Check if detection is enabled and service available
        if not self.USE_AI_BUBBLE_DETECTION:
            logger.info("AI bubble detection disabled, using PIL fallback")
            return None

        # Lazy load Gemini service if needed
        if self.gemini is None:
            try:
                from app.services.gemini_service import GeminiService
                self.gemini = GeminiService(self.settings)
                logger.info("Lazy-loaded GeminiService for bubble detection")
            except Exception as e:
                logger.warning(f"Could not load GeminiService: {e}")
                return None

        # Try Gemini Vision detection with retries
        for attempt in range(max_retries + 1):
            try:
                bubble_positions = await self.gemini.detect_speech_bubbles(str(image_path))

                if bubble_positions:
                    # Check if we detected bubbles for most panels with dialogue
                    detected_panels = set(bubble_positions.keys())
                    needed_panels = set(panels_with_dialogue)
                    coverage = len(detected_panels & needed_panels) / len(needed_panels) if needed_panels else 0

                    if coverage >= 0.5:  # At least 50% coverage
                        logger.info(f"Gemini Vision detection successful: {len(bubble_positions)} bubbles ({coverage:.0%} coverage)")
                        return bubble_positions
                    else:
                        logger.warning(f"Low bubble coverage ({coverage:.0%}), retry or fallback")

            except Exception as e:
                logger.warning(f"Gemini Vision detection attempt {attempt + 1} failed: {e}")

            if attempt < max_retries:
                logger.info(f"Retrying bubble detection ({attempt + 1}/{max_retries})")

        # Try OpenCV fallback
        logger.info("Trying OpenCV contour detection as fallback")
        try:
            img = Image.open(image_path)
            img_width, img_height = img.size
            panel_height = img_height // 4

            opencv_bubbles = {}
            for panel_idx in panels_with_dialogue:
                panel_y = panel_idx * panel_height
                bbox = self._detect_bubble_boundaries(img, 0, panel_y, img_width, panel_height)
                if bbox:
                    x1, y1, x2, y2 = bbox
                    opencv_bubbles[panel_idx] = {
                        "bbox": [x1, y1, x2, y2],
                        "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                        "style": "round",
                        "confidence": 0.7,
                    }

            if opencv_bubbles:
                logger.info(f"OpenCV detected {len(opencv_bubbles)} bubbles")
                return opencv_bubbles

        except Exception as e:
            logger.warning(f"OpenCV detection failed: {e}")

        logger.info("All detection methods failed, will use PIL fallback")
        return None

    async def _place_text_in_detected_bubbles(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        script: dict[str, Any],
        bubble_positions: dict[int, dict],
        output_path: Path,
    ) -> Path:
        """
        Place dialogue text inside detected bubble regions.

        This method is used when bubbles are detected in the AI-generated image,
        so we only need to add text without drawing new bubbles.

        Args:
            img: PIL Image object
            draw: PIL ImageDraw object
            script: Comic script with dialogue
            bubble_positions: Dict mapping panel index to bubble info
            output_path: Where to save the result

        Returns:
            Path to image with text overlay
        """
        panels = script.get("panels", [])

        for panel_idx, bubble in bubble_positions.items():
            if panel_idx >= len(panels):
                continue

            panel = panels[panel_idx]
            dialogue = panel.get("dialogue", [])

            if not dialogue:
                continue

            # Get bubble bounding box
            bbox = bubble.get("bbox", [0, 0, 100, 50])
            x1, y1, x2, y2 = bbox

            # Calculate text area with padding inside bubble
            padding = 10
            text_area_width = (x2 - x1) - (padding * 2)
            text_area_height = (y2 - y1) - (padding * 2)

            if text_area_width <= 0 or text_area_height <= 0:
                logger.warning(f"Panel {panel_idx}: Invalid bubble bbox, skipping")
                continue

            # Combine dialogue
            full_dialogue = " ".join(dialogue)

            # Fit text to detected bubble size
            font_size, wrapped_lines = self._fit_text_to_bubble(
                full_dialogue,
                text_area_width,
                text_area_height,
                max_font_size=18,
                min_font_size=10,
            )

            # Load font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf", font_size)
                except:
                    font = ImageFont.load_default()

            # Calculate text positioning (centered in bubble)
            line_height = font_size + 4
            total_text_height = len(wrapped_lines) * line_height
            text_start_y = y1 + padding + (text_area_height - total_text_height) // 2

            # Draw text with slight shadow for readability
            for k, wrapped_line in enumerate(wrapped_lines):
                text_bbox = draw.textbbox((0, 0), wrapped_line, font=font)
                text_width = text_bbox[2] - text_bbox[0]

                # Center horizontally
                text_x = x1 + padding + (text_area_width - text_width) // 2
                text_y = text_start_y + (k * line_height)

                # Draw shadow (1px offset)
                draw.text((text_x + 1, text_y + 1), wrapped_line, font=font, fill="#333333")
                # Draw main text
                draw.text((text_x, text_y), wrapped_line, font=font, fill="black")

            logger.info(f"Panel {panel_idx}: Placed text in detected bubble at ({x1},{y1})-({x2},{y2})")

        # Save result
        img.save(output_path, 'PNG', quality=95)
        logger.info(f"Text placement in detected bubbles complete: {output_path}")

        return output_path

    async def _add_text_overlay(
        self,
        base_image_path: Path,
        script: dict[str, Any],
        output_path: Path,
    ) -> Path:
        """
        Add speech bubbles and text overlay to comic image.

        Uses intelligent detection cascade:
        1. Try Gemini Vision to detect existing bubbles
        2. Try OpenCV contour detection
        3. Fall back to PIL bubble drawing if detection fails

        Args:
            base_image_path: Path to base comic image
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

            # 1x4 vertical strip layout
            panel_width = img_width  # Full width (single column)
            panel_height = img_height // 4  # Divide height by 4 panels

            panels = script.get("panels", [])

            # Find which panels have dialogue
            panels_with_dialogue = [i for i, p in enumerate(panels[:4]) if p.get("dialogue")]

            # Try detection cascade
            detected_bubbles = await self._try_detect_bubbles(
                base_image_path, panels_with_dialogue
            )

            if detected_bubbles:
                logger.info(f"Using detected bubbles for {len(detected_bubbles)} panels")
                # Place text in detected bubbles (no bubble drawing needed)
                return await self._place_text_in_detected_bubbles(
                    img, draw, script, detected_bubbles, output_path
                )

            # Fall back to PIL bubble drawing
            logger.info(f"Script has {len(panels)} panels - PIL will draw bubbles (1x4 vertical layout)")

            for i, panel in enumerate(panels):
                if i >= 4:  # Only 4 panels
                    break

                dialogue = panel.get("dialogue", [])
                if not dialogue:
                    logger.info(f"Panel {i+1}: NO DIALOGUE - skipping bubble")
                    continue

                # Calculate panel position (1x4 vertical strip)
                panel_x = 0  # Single column
                panel_y = i * panel_height  # Stacked vertically

                logger.info(f"Panel {i+1}: Position ({panel_x}, {panel_y}), Size {panel_width}x{panel_height}")

                # Get bubble region (top 20% of panel)
                x1, y1, x2, y2 = self._get_expected_bubble_region(
                    panel_x, panel_y, panel_width, panel_height
                )
                bubble_width = x2 - x1
                bubble_height = y2 - y1

                # Get emotion for bubble style (default to "speech" if not specified)
                emotion = panel.get("emotion", "speech")

                # DRAW the speech bubble (PIL draws it, not AI)
                # Alternate tail direction for visual variety
                tail_dir = "left" if i % 2 == 0 else "right"
                self._draw_speech_bubble(draw, x1, y1, bubble_width, bubble_height, tail_dir, emotion)

                logger.info(f"Panel {i+1}: Drew {emotion} bubble at ({x1},{y1}) size {bubble_width}x{bubble_height}")

                # Combine all dialogue into single text block
                full_dialogue = " ".join(dialogue)

                # Calculate optimal font size and wrapping for this bubble
                # Smaller font sizes for 1K resolution (512×1024)
                font_size, wrapped_lines = self._fit_text_to_bubble(
                    full_dialogue,
                    bubble_width,
                    bubble_height,
                    max_font_size=18,  # Scaled down from 28
                    min_font_size=10   # Scaled down from 14
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
        Enhance comic with Freepik assets (backgrounds, speech bubbles, frames).

        Layering order (bottom to top):
        1. Mode background (Freepik) - blended at ~35% opacity
        2. Base comic image (characters from Nano-Banana)
        3. Comic frames (panel borders)
        4. Speech bubbles (professional vectors)

        Args:
            base_image_path: Path to base comic image (1x4 vertical strip)
            script: Comic script (includes mode: CELEBRATE/EDUCATE/UNKNOWN)

        Returns:
            Path to enhanced image
        """
        try:
            img = Image.open(base_image_path).convert("RGBA")
            img_width, img_height = img.size

            # 1x4 vertical strip layout
            panel_width = img_width  # Full width (single column)
            panel_height = img_height // 4  # Divide by 4 panels

            # Get comic mode for background selection
            comic_mode = script.get("mode", "EDUCATE")
            logger.info(f"Enhancing {img_width}x{img_height} comic (1x4 vertical) with Freepik assets (mode: {comic_mode})")

            # Fetch all assets in parallel (cached after first download)
            import asyncio
            bubble_paths, frame_paths, bg_path = await asyncio.gather(
                self.freepik.get_speech_bubbles(style="comic", limit=1),
                self.freepik.get_comic_frames(limit=1),
                self.freepik.get_mode_background(comic_mode),
            )

            # Step 1: Apply mode background to full comic (if available)
            if bg_path:
                try:
                    bg_img = self._svg_to_png(bg_path, width=img_width, height=img_height)
                    img = self._blend_background(img, bg_img, opacity=0.35)
                    logger.info(f"Applied {comic_mode} mode background at 35% opacity")
                except Exception as e:
                    logger.warning(f"Failed to apply background: {e}")

            # Convert SVG bubble to PNG at appropriate size
            bubble_img = None
            if bubble_paths:
                try:
                    bubble_img = self._svg_to_png(
                        bubble_paths[0],
                        width=int(panel_width * 0.75),
                        height=int(panel_height * 0.18),  # Slightly taller for narrow panels
                    )
                    logger.info(f"Loaded speech bubble: {bubble_img.size}")
                except Exception as e:
                    logger.warning(f"Failed to convert bubble SVG: {e}")

            # Convert SVG frame to PNG
            frame_img = None
            if frame_paths:
                try:
                    frame_img = self._svg_to_png(
                        frame_paths[0],
                        width=panel_width,
                        height=panel_height,
                    )
                    logger.info(f"Loaded comic frame: {frame_img.size}")
                except Exception as e:
                    logger.warning(f"Failed to convert frame SVG: {e}")

            # Apply to each panel (1x4 vertical strip)
            panels = script.get("panels", [])
            for i, panel in enumerate(panels):
                if i >= 4:
                    break

                # 1x4 vertical layout: single column, stacked rows
                panel_x = 0
                panel_y = i * panel_height

                # Apply frame border (alpha composite)
                if frame_img:
                    frame_copy = frame_img.copy()
                    img.paste(frame_copy, (panel_x, panel_y), frame_copy)

                # Apply speech bubble if panel has dialogue
                if bubble_img and panel.get("dialogue"):
                    bubble_x = panel_x + int(panel_width * 0.12)
                    bubble_y = panel_y + int(panel_height * 0.02)
                    img.paste(bubble_img, (bubble_x, bubble_y), bubble_img)

            # Save enhanced image
            output_path = self.renders_path / f"{base_image_path.stem}_enhanced.png"
            img.save(output_path, "PNG", quality=95)
            logger.info(f"Freepik enhancement saved: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Freepik enhancement failed: {e}", exc_info=True)
            return base_image_path

    def _rearrange_to_grid(self, img: Image.Image) -> Image.Image:
        """
        Rearrange 1x4 vertical strip to 2x2 grid for square export.

        Input: 1x4 strip (width × height where height = 4 × panel_height)
        Output: 2x2 grid (square-ish image)

        Panel arrangement:
        - Input:  [1] [2] [3] [4] (stacked vertically)
        - Output: [1] [2]
                  [3] [4]

        Args:
            img: PIL Image of 1x4 vertical strip

        Returns:
            PIL Image rearranged as 2x2 grid
        """
        w, h = img.size
        panel_h = h // 4

        # Extract individual panels
        panels = [
            img.crop((0, i * panel_h, w, (i + 1) * panel_h))
            for i in range(4)
        ]

        # Create 2x2 grid (width * 2, panel_height * 2)
        grid_w = w * 2
        grid_h = panel_h * 2
        grid = Image.new('RGB', (grid_w, grid_h), color='#FFFFFF')

        # Place panels: [0,1] top row, [2,3] bottom row
        grid.paste(panels[0], (0, 0))
        grid.paste(panels[1], (w, 0))
        grid.paste(panels[2], (0, panel_h))
        grid.paste(panels[3], (w, panel_h))

        logger.debug(f"Rearranged 1x4 strip ({w}x{h}) to 2x2 grid ({grid_w}x{grid_h})")
        return grid

    async def _generate_export_formats(
        self,
        base_image_path: Path,
        content_id: str,
    ) -> dict[str, str]:
        """
        Generate multiple export formats from 1x4 vertical strip.

        Dynamically calculates dimensions based on actual base image size
        to preserve aspect ratio. Uses letterboxing/pillarboxing as needed.

        Args:
            base_image_path: Path to base comic image (1x4 vertical strip)
            content_id: Content identifier

        Returns:
            Dictionary with URIs for each format
        """
        img = Image.open(base_image_path)
        base_w, base_h = img.size

        logger.info(f"Generating export formats from {base_w}x{base_h} vertical strip")

        # Square (1080x1080) - REARRANGE to 2x2 grid, then scale-to-fit with letterboxing
        square_path = self.renders_path / f"{content_id}_square.png"
        grid = self._rearrange_to_grid(img)
        grid_w, grid_h = grid.size
        target_size = 1080
        # Scale to fit within square while preserving aspect ratio
        scale = min(target_size / grid_w, target_size / grid_h)
        scaled_w = int(grid_w * scale)
        scaled_h = int(grid_h * scale)
        scaled_grid = grid.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        # Center on dark background
        square_img = Image.new('RGB', (target_size, target_size), color='#1a1a1a')
        paste_x = (target_size - scaled_w) // 2
        paste_y = (target_size - scaled_h) // 2
        square_img.paste(scaled_grid, (paste_x, paste_y))
        square_img.save(square_path, 'PNG', quality=95)
        logger.info(f"Square export: grid {grid_w}x{grid_h} scaled to {scaled_w}x{scaled_h}, saved {square_path.name}")

        # Portrait (1080x1350) - Scale to fit within canvas, preserve aspect ratio
        portrait_path = self.renders_path / f"{content_id}_portrait.png"
        target_w, target_h = 1080, 1350
        scale = min(target_w / base_w, target_h / base_h)
        scaled_w = int(base_w * scale)
        scaled_h = int(base_h * scale)
        scaled = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        portrait_img = Image.new('RGB', (target_w, target_h), color='#1a1a1a')
        paste_x = (target_w - scaled_w) // 2
        paste_y = (target_h - scaled_h) // 2
        portrait_img.paste(scaled, (paste_x, paste_y))
        portrait_img.save(portrait_path, 'PNG', quality=95)
        logger.info(f"Portrait export: {base_w}x{base_h} scaled to {scaled_w}x{scaled_h}, saved {portrait_path.name}")

        # Reel (1080x1920) - Scale to fit within canvas, preserve aspect ratio
        reel_path = self.renders_path / f"{content_id}_reel.png"
        target_w, target_h = 1080, 1920
        scale = min(target_w / base_w, target_h / base_h)
        scaled_w = int(base_w * scale)
        scaled_h = int(base_h * scale)
        scaled = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        reel_img = Image.new('RGB', (target_w, target_h), color='#1a1a1a')
        paste_x = (target_w - scaled_w) // 2
        paste_y = (target_h - scaled_h) // 2
        reel_img.paste(scaled, (paste_x, paste_y))
        reel_img.save(reel_path, 'PNG', quality=95)
        logger.info(f"Reel export: {base_w}x{base_h} scaled to {scaled_w}x{scaled_h}, saved {reel_path.name}")

        logger.info(f"Generated all export formats for {content_id}")

        return {
            "comic_square_uri": f"/storage/renders/{square_path.name}",
            "comic_portrait_uri": f"/storage/renders/{portrait_path.name}",
            "reel_cover_uri": f"/storage/renders/{reel_path.name}",
        }
