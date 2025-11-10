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

        Args:
            script: Comic script
            content_id: Content identifier

        Returns:
            Path to generated image
        """
        output_path = self.renders_path / f"{content_id}_nanobana.png"
        result_path = await self.nanobana.generate_comic_image(script, output_path)
        return result_path

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
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Approximate width (proper way would use textbbox but this is simpler)
            if len(test_line) * 10 < max_width:  # Rough estimate
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
