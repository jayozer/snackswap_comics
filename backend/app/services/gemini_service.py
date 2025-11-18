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

        prompt = f"""You are a comedy writer for kids creating HILARIOUS 4-panel dental health comics.

TARGET AUDIENCE: Age {age} ({age_band} years old), tone: {tone} and FUNNY!

🎭 RECURRING CHARACTER - CAPTAIN SPARKLE:
Captain Sparkle is a superhero tooth who appears in EVERY comic. Personality: Enthusiastic, slightly dramatic, loves puns. Always wears a tiny superhero cape. Catchphrase: "Sparkle power!" Expression changes based on situation (excited, shocked, worried, triumphant).

SNACKS IN PHOTO (they become animated characters):
{snacks_context}

DENTAL FACTS (integrate into jokes, cite fact_id in citation_ids):
{facts_context}

HEALTHIER SWAPS (make them sound awesome):
{swaps_context}

🎬 PANEL STRUCTURE (Comedy-First):

PANEL 1 - THE HOOK (Funny Introduction)
- Snack introduces itself with a PUN or funny trait
- Captain Sparkle appears with excited expression
- Set up the comedic situation
- Include at least ONE wordplay or visual gag

PANEL 2 - ESCALATION (The Problem Revealed)
- Captain Sparkle discovers something about the snack (cite a fact here)
- Snack reacts DRAMATICALLY (shocked, worried, or over-confident)
- Use exaggeration for comedy (if sticky, make it SUPER sticky)
- Include a surprising prop or visual element

PANEL 3 - THE TWIST (Role Reversal or Surprise)
- Unexpected moment! (e.g., snack admits truth, Captain Sparkle has idea)
- Another fact revealed in funny way (cite fact_id)
- Character expressions should be extreme (gasp!, idea!, worried!)
- Include callback to Panel 1 or running gag

PANEL 4 - THE PUNCHLINE (Happy Resolution)
- Introduce swap character with funny personality
- Captain Sparkle triumphant pose: "Sparkle power!"
- End with a joke that ties to the beginning
- Positive, no shaming - make swap sound COOL

🎨 COMEDY TECHNIQUES (Use ALL of these):
1. PUNS & WORDPLAY: Character names, dialogue, situations
2. VISUAL GAGS: Props (tiny capes, party hats, magnifying glass), exaggerated expressions
3. CHARACTER COMEDY: Distinct personalities (nervous snack, know-it-all tooth, cheerful swap)
4. SURPRISE MOMENTS: Unexpected reactions, plot twists, dramatic reveals

⚠️ CRITICAL RULES FOR FACT CITATIONS:
- citation_ids field = ONLY fact IDs like ["F001", "F003"]
- dialogue field = ONLY what characters SAY - NEVER include "F001" or fact IDs in dialogue
- The dialogue should naturally incorporate the fact's content WITHOUT mentioning the ID
- WRONG: "I stick to teeth [F001]"
- RIGHT: dialogue: ["I stick to teeth for hours!"], citation_ids: ["F001"]

📝 OTHER RULES:
- Every panel needs a LAUGH MOMENT (joke, pun, visual gag, surprise)
- Keep dialogue VERY SHORT: Maximum 2-3 brief lines per panel
- CRITICAL TEXT LIMITS: Each dialogue line must be under 40 characters, total per panel under 100 characters
- Shorter is better - aim for punchy, concise jokes that kids can read quickly
- Expressions: happy, shocked, worried, excited, triumphant, scheming
- Props add comedy: superhero capes, detective hats, party decorations, microphones
- NO scolding or guilt - keep it light and fun!

EXAMPLE PANEL (showing humor + citations done RIGHT):

{{
  "panel_number": 2,
  "title": "The Sticky Situation",
  "dialogue": [
    "I throw PARTIES for bacteria! They absolutely LOVE me!",
    "*GASP* You mean sticky candies stay on teeth for HOURS?!",
    "Yep! It's like an all-night rave for tiny party animals!"
  ],
  "citation_ids": ["F002"],  // Fact about stickiness - ID here, NOT in dialogue
  "characters": [
    {{
      "name": "Gummy Gary",
      "item_id": "candy_gummy",
      "expression": "proud",
      "position": "left",
      "props": ["party hat", "confetti"]
    }},
    {{
      "name": "Captain Sparkle",
      "item_id": "recurring_tooth",
      "expression": "shocked",
      "position": "right",
      "props": ["superhero cape"]
    }}
  ],
  "visual_prompt": "Gummy bear character wearing party hat with tiny bacteria having a party. Tooth superhero looking shocked with wide eyes and open mouth.",
  "background": "simple with subtle party decorations"
}}

📋 REQUIRED JSON OUTPUT STRUCTURE:

Return your response as valid JSON with this EXACT structure:

{{
  "panels": [
    // Array of 4 panels, each following the structure shown above
  ],
  "summary_caption": "A catchy one-liner that captures the comic's main joke or lesson (under 100 chars)",
  "alt_text": "Accessibility description for screen readers: describe the comic's story and visual elements (1-2 sentences)"
}}

Make it HILARIOUS while teaching dental health!"""

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

            # Safety filter: Remove any fact IDs that slipped into dialogue
            import re
            fact_id_pattern = re.compile(r'\[?F\d{3,4}\]?|\(F\d{3,4}\)')

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    cleaned_dialogue = []
                    for line in panel['dialogue']:
                        # Remove fact IDs from dialogue
                        cleaned_line = fact_id_pattern.sub('', line).strip()
                        # Remove extra spaces
                        cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
                        cleaned_dialogue.append(cleaned_line)
                    panel['dialogue'] = cleaned_dialogue

            # Character limit validation: Truncate lines that are too long
            MAX_LINE_LENGTH = 45  # chars per line
            MAX_PANEL_TOTAL = 110  # total chars per panel

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    validated_dialogue = []
                    panel_total = 0

                    for line in panel['dialogue']:
                        # Truncate individual line if too long
                        if len(line) > MAX_LINE_LENGTH:
                            logger.warning(f"Truncating dialogue line from {len(line)} to {MAX_LINE_LENGTH} chars: {line[:30]}...")
                            line = line[:MAX_LINE_LENGTH-3] + "..."

                        # Check total panel character count
                        if panel_total + len(line) > MAX_PANEL_TOTAL:
                            logger.warning(f"Panel exceeds character limit, stopping at {panel_total} chars")
                            break

                        validated_dialogue.append(line)
                        panel_total += len(line)

                    panel['dialogue'] = validated_dialogue

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
