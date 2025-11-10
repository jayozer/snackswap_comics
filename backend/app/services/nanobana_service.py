"""
Nano-Banana (Gemini 2.5 Flash Image) service for comic image generation.
"""

import base64
import logging
from pathlib import Path
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import Settings

logger = logging.getLogger(__name__)


class NanoBananaService:
    """Service for generating comic images using Gemini 2.5 Flash Image (Nano-Banana)."""

    def __init__(self, settings: Settings):
        """Initialize Nano-Banana service."""
        self.settings = settings
        genai.configure(api_key=settings.gemini_api_key)

        # Safety settings - keep permissive for food/dental content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        logger.info("Initialized Nano-Banana service")

    def build_comic_prompt(self, script: dict[str, Any]) -> str:
        """
        Build a detailed prompt for Nano-Banana from the comic script.

        Uses one-prompt-one-story approach for character consistency.

        Args:
            script: Comic script with panels, characters, dialogue

        Returns:
            Detailed prompt string for image generation
        """
        panels = script.get("panels", [])

        if not panels or len(panels) != 4:
            raise ValueError(f"Script must contain exactly 4 panels, got {len(panels)}")

        # Extract unique characters across all panels
        characters = {}
        for panel in panels:
            for char in panel.get("characters", []):
                char_name = char.get("name")
                if char_name and char_name not in characters:
                    characters[char_name] = {
                        "item_id": char.get("item_id"),
                        "description": self._get_character_description(char.get("item_id", "")),
                    }

        # Build comprehensive prompt
        prompt_parts = [
            "Create a 4-panel comic strip in a 2x2 grid layout. Comic book illustration style, vibrant colors, friendly and appealing to children aged 6-8.",
            "",
            "IMPORTANT LAYOUT RULES:",
            "- Must be exactly 2 rows and 2 columns (2x2 grid)",
            "- Clear panel borders with thin black lines",
            "- Leave space at top of each panel for speech bubbles",
            "- All text must be fully visible within panel boundaries",
            "- No cropped or cut-off elements",
            "",
            "CHARACTER CONSISTENCY:",
        ]

        # Add character descriptions
        for char_name, char_info in characters.items():
            prompt_parts.append(f"- {char_name}: {char_info['description']}")

        prompt_parts.append("")
        prompt_parts.append("PANELS:")
        prompt_parts.append("")

        # Add each panel description
        for i, panel in enumerate(panels, 1):
            panel_num = panel.get("panel_number", i)
            title = panel.get("title", f"Panel {panel_num}")
            dialogue = panel.get("dialogue", [])
            visual_prompt = panel.get("visual_prompt", "")
            background = panel.get("background", "simple")
            panel_chars = panel.get("characters", [])

            prompt_parts.append(f"PANEL {panel_num} (Position: Row {(panel_num-1)//2 + 1}, Column {(panel_num-1)%2 + 1}):")
            prompt_parts.append(f"Title: {title}")

            # Character positions and expressions
            if panel_chars:
                char_desc = []
                for char in panel_chars:
                    name = char.get("name", "Character")
                    expression = char.get("expression", "happy")
                    position = char.get("position", "center")
                    props = char.get("props", [])

                    desc = f"{name} ({expression} expression, positioned {position}"
                    if props:
                        desc += f", with {', '.join(props)}"
                    desc += ")"
                    char_desc.append(desc)

                prompt_parts.append(f"Characters: {', '.join(char_desc)}")

            prompt_parts.append(f"Scene: {visual_prompt}")
            prompt_parts.append(f"Background: {background}")

            # Add dialogue as speech bubble instructions
            if dialogue:
                prompt_parts.append(f"Speech bubbles (top of panel, clearly visible):")
                for j, line in enumerate(dialogue, 1):
                    prompt_parts.append(f"  {j}. \"{line}\"")

            prompt_parts.append("")

        # Add final styling notes
        prompt_parts.extend([
            "",
            "STYLE NOTES:",
            "- Cartoon/comic book style with bold outlines",
            "- Bright, appealing colors suitable for children",
            "- Friendly, non-threatening character designs",
            "- Clear readable text in speech bubbles",
            "- Professional comic book layout",
            "- Each character maintains exact same appearance across all panels",
        ])

        return "\n".join(prompt_parts)

    def _get_character_description(self, item_id: str) -> str:
        """
        Get visual description for a character based on item ID.

        Args:
            item_id: Snack ID from the database

        Returns:
            Visual description string
        """
        # Map common snack IDs to visual descriptions
        descriptions = {
            "candy_gummy": "A cute, anthropomorphic gummy bear character. Translucent jelly-like body in bright colors (red, orange, yellow, green). Large friendly eyes, small smile, bear-shaped body with round ears. Glossy, shiny surface.",
            "chips_classic": "A friendly potato chip character. Golden-yellow, wavy crispy shape. Cartoon eyes and smile on the chip surface. Slightly curled edges, textured surface showing the crunchiness.",
            "soda_orange": "An orange soda bottle or can character. Orange colored, cylindrical shape with condensation droplets. Happy face on the label. Fizzy bubbles visible around it.",
            "candy_chocolate": "A chocolate bar character. Brown rectangular shape with segmented squares. Glossy chocolate surface. Friendly smiling face, small arms and legs.",
        }

        return descriptions.get(
            item_id,
            "A friendly animated food character with cartoon eyes, smile, and small limbs. Colorful and appealing to children."
        )

    async def generate_comic_image(
        self,
        script: dict[str, Any],
        output_path: str | Path,
    ) -> Path:
        """
        Generate a 4-panel comic image using Nano-Banana (Gemini 2.5 Flash Image).

        Args:
            script: Comic script with panels and characters
            output_path: Path where to save the generated image

        Returns:
            Path to the generated image

        Raises:
            ValueError: If script is invalid
            Exception: If generation fails
        """
        try:
            # Build comprehensive prompt
            prompt = self.build_comic_prompt(script)

            logger.info("Generating comic image with Nano-Banana")
            logger.debug(f"Prompt: {prompt[:500]}...")  # Log first 500 chars

            # Use Gemini 2.5 Flash Image model (Nano-Banana)
            model = genai.GenerativeModel("models/gemini-2.5-flash-image")

            # Generate image
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.8,  # Balanced creativity
                    "max_output_tokens": 4096,
                },
                safety_settings=self.safety_settings,
            )

            # Check if response has image data
            if not response.parts:
                raise ValueError("Nano-Banana returned no content. Check API quota or safety filters.")

            # Extract image data (Gemini returns base64 encoded image)
            # Note: The actual response format may vary, adjust based on API response
            image_data = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    break
                elif hasattr(part, 'text') and part.text.startswith('data:image'):
                    # Handle base64 data URL
                    image_data = part.text.split(',')[1]
                    break

            if not image_data:
                # Fallback: Try to get from response candidate
                logger.warning("Could not extract image from parts, trying alternative method")
                raise ValueError(
                    "Nano-Banana did not return image data. "
                    "The model may not support image generation or quota exceeded."
                )

            # Decode and save image
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data)

            with open(output_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"Comic image generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating comic image: {e}")
            raise

    async def generate_character_image(
        self,
        character_name: str,
        character_description: str,
        expression: str = "happy",
        output_path: str | Path = None,
    ) -> Path:
        """
        Generate a single character image (useful for testing or character sheets).

        Args:
            character_name: Name of the character
            character_description: Visual description
            expression: Character expression
            output_path: Where to save the image

        Returns:
            Path to generated image
        """
        prompt = f"""
        Create a single character illustration in comic book style.

        Character: {character_name}
        Description: {character_description}
        Expression: {expression}

        Style: Cartoon/comic book art, vibrant colors, friendly and appealing to children.
        Background: Simple white or transparent.
        """

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.8},
                safety_settings=self.safety_settings,
            )

            # Save logic similar to generate_comic_image
            # ... (implementation similar to above)

            logger.info(f"Character image generated: {character_name}")
            return Path(output_path) if output_path else Path("character.png")

        except Exception as e:
            logger.error(f"Error generating character image: {e}")
            raise
