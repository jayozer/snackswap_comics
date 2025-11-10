"""
Gemini AI service for SnackSwap Comics.
Handles vision detection, script composition, and embeddings.
"""

import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import Settings
from app.models import DetectedItem, Panel

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI."""

    def __init__(self, settings: Settings):
        """Initialize Gemini service."""
        self.settings = settings
        genai.configure(api_key=settings.gemini_api_key)

        # Safety settings - keep permissive for food/dental content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        logger.info("Initialized Gemini service")

    async def detect_items(self, image_path: str) -> list[DetectedItem]:
        """
        Detect food items in an image using Gemini Vision.

        Args:
            image_path: Path to the image file

        Returns:
            List of detected items
        """
        prompt = """You are a food vision assistant for a children's dental health app.

From this photo, identify up to 3 primary food items or snacks. For each item, provide:
- name: Common name of the item
- brand_guess: Brand name if visible (or null if unclear)
- category: Category (e.g., chips, candy, cookie, fruit, vegetable, beverage, dairy)
- visible_clues: What visual clues helped identify it (packaging color, shape, text)
- confidence: Your confidence level (0.0 to 1.0)

Focus on packaged snacks, lunch items, or identifiable foods. Ignore utensils or plates.

Return your response as a JSON object with this structure:
{
  "items": [
    {
      "name": "string",
      "brand_guess": "string or null",
      "category": "string",
      "visible_clues": "string",
      "confidence": 0.95
    }
  ],
  "needs_confirmation": false
}

Set needs_confirmation to true if any item has confidence < 0.7."""

        try:
            # Upload image
            uploaded_file = genai.upload_file(image_path)

            # Generate response
            model = genai.GenerativeModel(self.settings.gemini_vision_model)
            response = model.generate_content(
                [prompt, uploaded_file],
                generation_config={
                    "temperature": 0.3,  # Lower for factual detection
                    "max_output_tokens": 1024,
                },
                safety_settings=self.safety_settings,
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

            # Convert to DetectedItem models
            items = [DetectedItem(**item) for item in result.get("items", [])]

            logger.info(f"Detected {len(items)} items from image")
            return items

        except Exception as e:
            logger.error(f"Error detecting items: {e}")
            raise

    async def compose_script(
        self,
        snacks: list[dict[str, Any]],
        facts: list[dict[str, Any]],
        swaps: list[dict[str, Any]],
        age: int,
    ) -> dict[str, Any]:
        """
        Compose a 4-panel comic script using Gemini.

        Args:
            snacks: List of snack data
            facts: List of relevant facts
            swaps: List of suggested swaps
            age: Child's age

        Returns:
            Comic script with panels, caption, and alt text
        """
        # Determine age band
        if age <= 5:
            age_band = "3-5"
            tone = "very simple, playful"
        elif age <= 8:
            age_band = "6-8"
            tone = "friendly, fun"
        else:
            age_band = "9-12"
            tone = "engaging, cool"

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)
        swaps_context = json.dumps(swaps, indent=2)

        prompt = f"""You are a children's content writer creating a 4-panel comic about dental health.

TARGET AUDIENCE: Age {age} ({age_band} years old), tone should be {tone}

SNACKS IN THE PHOTO:
{snacks_context}

APPROVED FACTS (use these exact facts, cite with fact_id):
{facts_context}

SUGGESTED SWAPS:
{swaps_context}

CREATE A 4-PANEL COMIC with these beats:

PANEL 1 - ROLL CALL: Introduce the food characters with fun personalities. Make them come alive!

PANEL 2 - THE DEBATE: Characters discuss their effect on teeth. Use AT LEAST ONE fact from the fact pack (cite fact_id). Keep it playful, not scary.

PANEL 3 - MYTH FLIP: Address a common misconception or surprise twist. Use AT LEAST ONE more fact from the fact pack.

PANEL 4 - THE SWAP: Present the healthier alternatives in a positive, exciting way. No shaming!

RULES:
- Use ONLY facts from the provided fact pack - cite with fact_id in citation_ids
- Keep dialogue to 2-3 short lines per panel
- Make characters friendly and expressive (happy, worried, excited, surprised)
- No scolding or making kids feel bad about their choices
- Emphasize that timing matters (e.g., "I'm okay if you brush after!")
- Make swaps sound delicious and fun, not boring

Return JSON with this structure:
{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Meet the Squad!",
      "dialogue": ["Hi! I'm Captain Crunch!", "And I'm Berry the Wise!"],
      "citation_ids": [],
      "characters": [
        {{
          "name": "Captain Crunch",
          "item_id": "snack_id_here",
          "expression": "happy",
          "position": "left",
          "props": ["superhero cape"]
        }}
      ],
      "visual_prompt": "Two animated snack characters with friendly faces...",
      "background": "simple"
    }}
  ],
  "summary_caption": "When Captain Crunch met Berry, they learned that timing is everything for happy teeth!",
  "alt_text": "A 4-panel comic showing...",
  "hashtags": ["SnackSwapComics", "DentalHealth", "HealthyKids"]
}}

Make it delightful!"""

        try:
            model = genai.GenerativeModel(self.settings.gemini_writer_model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.settings.gemini_temperature,
                    "max_output_tokens": self.settings.gemini_max_tokens,
                },
                safety_settings=self.safety_settings,
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

            # Try to parse JSON - log raw response on failure
            try:
                result = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Raw response (first 1000 chars): {response_text[:1000]}")
                raise ValueError(f"Gemini returned invalid JSON: {e}")

            logger.info(f"Composed script with {len(result.get('panels', []))} panels")
            return result

        except Exception as e:
            logger.error(f"Error composing script: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using Gemini.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )

            return result["embedding"]

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_query_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for query text.

        Args:
            text: Query text

        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query",
            )

            return result["embedding"]

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
