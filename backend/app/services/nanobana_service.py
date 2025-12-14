"""
Image generation service for comic creation.
Supports both Imagen 4.0 (2K resolution) and Nano-Banana (1K resolution).
Uses the official google-genai SDK for image generation.
"""

import logging
import mimetypes
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from app.core.config import Settings
from app.services.guardrails_service import get_guardrails_service
from app.services.audit_service import get_audit_service, GenerationType

logger = logging.getLogger(__name__)


class NanoBananaService:
    """Service for generating comic images using Google's image generation models."""

    def __init__(self, settings: Settings):
        """Initialize image generation service with the google-genai SDK."""
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.guardrails = get_guardrails_service()
        self.audit = get_audit_service(settings)

        # Determine which model is being used
        self.is_imagen = "imagen" in settings.gemini_image_model.lower()
        model_name = "Imagen 4.0" if self.is_imagen else "Nano-Banana"
        logger.info(f"Initialized image generation service with {model_name} and guardrails ({settings.gemini_image_model})")

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
            "Create a 4-panel comic strip in a VERTICAL 1x4 layout (stacked vertically, one column).",
            "STYLE: Clean 2D digital illustration in modern cartoon style (like contemporary vector animation).",
            "Target Audience: Teenagers (9-17) who care about APPEARANCE and AESTHETICS.",
            "",
            "VISUAL STYLE RULES (CRITICAL - MUST FOLLOW):",
            "- Bold, uniform thickness BLACK OUTLINES for all characters and objects",
            "- FLAT COLORING with large areas of solid color",
            "- Minimal cel-shading - only hard-edged blocks of slightly darker color to suggest depth",
            "- NO complex textures, NO gradients, NO sketchy or gritty lines",
            "- Clean, confident linework - crisp and stable, not rough or textured",
            "- Cartoonish, exaggerated proportions",
            "- Simple backgrounds - solid colors or minimal gradients",
            "- EXPRESSIONS MUST BE EXAGGERATED (shocked, smug, crying, flexing)",
            "",
            "DR. DRIP CHARACTER (MUST MATCH EXACTLY):",
            "- Anthropomorphic molar tooth, off-white/pale cyan body",
            "- Smooth rounded rectangular shape as head/torso, two root-like legs",
            "- Large round white eyes with small black pupils",
            "- Simple black line eyebrows, wide smiling mouth with pink tongue",
            "- Black retro sunglasses pushed up on forehead (above eyes)",
            "- Oversized dark forest green pullover hoodie with front kangaroo pocket",
            "- Chunky beige/tan slip-on slides (Yeezy-style) on feet",
            "",
            "VANITY CONTRAST EFFECTS:",
            "- DR. DRIP: Always pristine, clean, fresh appearance - bright white shine",
            "- Bad snacks: GRIMY appearance - yellow stains, sticky residue, gross effects",
            "- Panel 2 & 3: Add gross visual effects on snacks (green fumes, yellow discoloration)",
            "- Panel 4: Add clean visual effects (sparkles, glow, pristine white)",
            "",
            "CRITICAL RULES - ABSOLUTELY MUST FOLLOW:",
            "- ZERO TEXT: DO NOT generate ANY text, words, letters, numbers, or typography ANYWHERE",
            "- NO LABELS: DO NOT write any labels, signs, captions, titles, or placeholder text",
            "- DO NOT DRAW ANY SPEECH BUBBLES - no bubbles of any kind in the image",
            "- Characters can fill the ENTIRE panel - use full vertical space for dynamic compositions",
            "- Leave small clear area in top corners for text overlay (will be added later)",
            "- Text and dialogue will be professionally added as post-processing overlay",
            "",
            "LAYOUT RULES:",
            "- Must be exactly 4 panels stacked vertically (1 column, 4 rows)",
            "- Panel 1 at the TOP, Panel 4 at the BOTTOM",
            "- Clear HORIZONTAL panel borders with thin black lines between panels",
            "- Image aspect ratio is 1:2 (width:height) - tall vertical strip",
            "- All visual elements must be fully visible within panel boundaries",
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
            emotion = panel.get("emotion", "speech")  # Default to speech

            # Map emotion to visual mood guidance
            emotion_mood = {
                "speech": "calm, conversational mood",
                "thought": "contemplative, dreamy atmosphere",
                "exclaim": "dramatic, intense moment with high energy",
                "angry": "tense, aggressive atmosphere with sharp contrasts",
                "whisper": "quiet, secretive mood with soft lighting",
            }
            mood = emotion_mood.get(emotion, "conversational mood")

            prompt_parts.append(f"PANEL {panel_num} (Row {panel_num} of 4 from top):")
            prompt_parts.append(f"Title: {title}")
            prompt_parts.append(f"Mood: {mood}")

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
            prompt_parts.append("")

        # Add final styling notes
        prompt_parts.extend([
            "",
            "STYLE NOTES (CRITICAL):",
            "- Clean 2D vector animation style with bold uniform BLACK OUTLINES",
            "- FLAT COLORING - large solid color areas, minimal hard-edged cel-shading only",
            "- NO gritty textures, NO sketchy lines, NO complex gradients",
            "- ABSOLUTELY NO TEXT OR SPEECH BUBBLES - zero words, letters, typography, or bubbles",
            "- Characters fill full panel space - dynamic compositions",
            "- VERTICAL 1x4 layout (tall strip, panels stacked top to bottom)",
            "- Each character maintains EXACT same appearance across all 4 panels",
            "- Exaggerated cartoon expressions (shocked, smug, crying, flexing)",
            "",
            "VANITY CONTRAST:",
            "- DR. DRIP: Off-white/pale cyan molar tooth in dark forest green hoodie, black sunglasses on forehead, beige slides - always pristine and clean",
            "- Bad snacks: GRIMY appearance - yellow stains, sticky residue, gross effects",
            "- Good snacks: CLEAN appearance - bright colors, sparkle effects",
            "- Visual contrast: clean/white (good) vs gross/yellow (bad)",
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
        # Map common snack IDs to visual descriptions - teen/edgy style
        descriptions = {
            "candy_gummy": "An anthropomorphic gummy bear character with swagger. Translucent jelly-like body in neon colors. Exaggerated expressions - can look smug, nervous, or defeated. Might wear tiny chains or streetwear. Glossy surface with dramatic lighting.",
            "chips_classic": "A potato chip character with attitude. Golden-yellow, wavy crispy shape. Cartoon eyes that can show smugness or panic. Slightly curled edges, textured surface. Can look like it's trying too hard to be cool.",
            "soda_orange": "An orange soda can character with main-character energy. Neon orange, cylindrical shape with condensation droplets. Expressive face - can be cocky or scared. Fizzy bubbles as dramatic effect.",
            "candy_chocolate": "A chocolate bar character with street style. Brown rectangular shape with segmented squares. Glossy chocolate surface. Can have smug or nervous expressions. Might wear tiny sneakers or gold chain.",
            "recurring_tooth": "DR. DRIP - An anthropomorphic molar tooth character. Off-white/pale cyan body with smooth, rounded, somewhat rectangular shape serving as head and torso. Two root-like appendages as legs. Large, round, prominent white eyes with small black pupils. Simple black line eyebrows. Wide open smiling mouth showing pink tongue. Black retro-style sunglasses pushed up onto forehead (above eyes). Wears an oversized dark forest green pullover hoodie with front kangaroo pocket and drawstrings (hood down). Chunky beige/tan slip-on slides (Yeezy-style) on feet. CRITICAL STYLE: Clean 2D digital illustration with bold, uniform thickness black outlines. Flat coloring with large solid color areas. Minimal hard-edged cel-shading only (no gradients). No complex textures or sketchy lines. Expression range: surprised, excited, impressed, smug, disgusted.",
        }

        return descriptions.get(
            item_id,
            "An animated food character with attitude - can look smug, nervous, or defeated. Streetwear-influenced design, expressive eyes. Teen-appropriate edgy style, NOT cutesy."
        )

    async def generate_comic_image(
        self,
        script: dict[str, Any],
        output_path: str | Path,
        image_size: str = "1K",
    ) -> Path:
        """
        Generate a 4-panel comic image using Imagen 4.0 or Nano-Banana.

        Generates a 1x4 vertical strip (512×1024 at 1K resolution).

        Args:
            script: Comic script with panels and characters
            output_path: Path where to save the generated image
            image_size: Image size ("1K" = 512×1024 vertical strip, "2K" = 1024×2048)

        Returns:
            Path to the generated image

        Raises:
            ValueError: If script is invalid
            Exception: If generation fails
        """
        try:
            start_time = time.time()

            # Build comprehensive prompt
            prompt = self.build_comic_prompt(script)

            # Validate image prompt before generation
            prompt_validation = self.guardrails.validate_image_prompt(prompt)
            if not prompt_validation.passed:
                logger.error(f"Image prompt failed guardrails: {prompt_validation.details}")
                # Log the blocked attempt
                self.audit.log_image_generation(
                    prompt=prompt[:500],
                    image_path=None,
                    validation_passed=False,
                    validation_details=prompt_validation.details,
                    duration_ms=int((time.time() - start_time) * 1000),
                )
                raise ValueError(f"Image prompt failed safety check: {prompt_validation.details}")

            model_name = "Imagen 4.0" if self.is_imagen else "Nano-Banana"
            logger.info(f"Generating comic image with {model_name} (size: {image_size})")
            logger.debug(f"Prompt: {prompt[:500]}...")  # Log first 500 chars

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if self.is_imagen:
                # Use Imagen 4.0 API
                response = self.client.models.generate_images(
                    model=self.settings.gemini_image_model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        image_size=image_size,
                    )
                )

                # Imagen returns PIL Image objects directly
                if not response.generated_images:
                    raise ValueError("Imagen 4.0 did not return any images")

                # Get the first generated image
                generated_image = response.generated_images[0]

                # Save as PNG
                final_path = output_path.with_suffix(".png") if not output_path.suffix else output_path

                # The image object from Imagen 4.0 has a save() method with different signature
                # It takes only the path, not format argument
                generated_image.image.save(final_path)

                # Audit log successful generation
                self.audit.log_image_generation(
                    prompt=prompt[:500],
                    image_path=str(final_path),
                    validation_passed=True,
                    validation_details="Image generated successfully",
                    duration_ms=int((time.time() - start_time) * 1000),
                )

                logger.info(f"Comic image saved to: {final_path}")
                return final_path

            else:
                # Use Nano-Banana API (streaming)
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    ),
                ]

                generate_content_config = types.GenerateContentConfig(
                    response_modalities=[
                        "IMAGE",
                        "TEXT",
                    ],
                    image_config=types.ImageConfig(
                        image_size=image_size,
                        aspect_ratio="9:16",  # Tall portrait for 1x4 vertical comic strip
                    ),
                )

                file_saved = False

                # Stream response chunks
                for chunk in self.client.models.generate_content_stream(
                    model=self.settings.gemini_image_model,
                    contents=contents,
                    config=generate_content_config,
                ):
                    # Check if chunk has content
                    if (
                        chunk.candidates is None
                        or chunk.candidates[0].content is None
                        or chunk.candidates[0].content.parts is None
                    ):
                        continue

                    # Check for image data
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        inline_data = part.inline_data
                        data_buffer = inline_data.data

                        # Determine file extension from mime type
                        file_extension = mimetypes.guess_extension(inline_data.mime_type)
                        if not file_extension:
                            file_extension = ".png"  # Default to PNG

                        # Save the image
                        if output_path.suffix:
                            final_path = output_path
                        else:
                            final_path = output_path.with_suffix(file_extension)

                        with open(final_path, "wb") as f:
                            f.write(data_buffer)

                        # Audit log successful generation
                        self.audit.log_image_generation(
                            prompt=prompt[:500],
                            image_path=str(final_path),
                            validation_passed=True,
                            validation_details="Image generated successfully",
                            duration_ms=int((time.time() - start_time) * 1000),
                        )

                        logger.info(f"Comic image saved to: {final_path}")
                        file_saved = True
                        output_path = final_path
                        break  # We only need the first image

                    elif part.text:
                        # Log any text responses (might be explanations or errors)
                        logger.info(f"Nano-Banana text response: {part.text}")

                if not file_saved:
                    raise ValueError(
                        "Nano-Banana did not return image data. "
                        "The model may not support image generation or quota exceeded."
                    )

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
        image_size: str = "512",
    ) -> Path:
        """
        Generate a single character image (useful for testing or character sheets).

        Args:
            character_name: Name of the character
            character_description: Visual description
            expression: Character expression
            output_path: Where to save the image
            image_size: Image size ("256", "512", "1K")

        Returns:
            Path to generated image
        """
        prompt = f"""
        Create a single character illustration in Webtoon/Adult Swim animation style.

        Character: {character_name}
        Description: {character_description}
        Expression: {expression}

        Style: Modern edgy comic art, neon-accented colors, cool and appealing to teenagers.
        Bold outlines, dramatic lighting, exaggerated expressions.
        Background: Simple gradient or transparent.
        """

        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    image_size=image_size,
                ),
            )

            if output_path is None:
                output_path = Path(f"character_{character_name}.png")
            else:
                output_path = Path(output_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            file_saved = False

            for chunk in self.client.models.generate_content_stream(
                model=self.settings.gemini_image_model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    inline_data = part.inline_data
                    data_buffer = inline_data.data

                    file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                    if not output_path.suffix:
                        output_path = output_path.with_suffix(file_extension)

                    with open(output_path, "wb") as f:
                        f.write(data_buffer)

                    logger.info(f"Character image saved: {output_path}")
                    file_saved = True
                    break

            if not file_saved:
                raise ValueError("Failed to generate character image")

            return output_path

        except Exception as e:
            logger.error(f"Error generating character image: {e}")
            raise
