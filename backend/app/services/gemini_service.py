"""
Gemini AI service for SnackSwap Comics.
Handles vision detection, script composition, and embeddings.
"""

import asyncio
import base64
import json
import logging
import mimetypes
from typing import Any
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import Settings
from app.models import DetectedItem, Panel

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI using the new google.genai SDK."""

    def __init__(self, settings: Settings):
        """Initialize Gemini service with the new SDK."""
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)

        logger.info("Initialized Gemini service with new google.genai SDK")

    async def detect_items(self, image_path: str) -> list[DetectedItem]:
        """
        Detect food items in an image using Gemini Vision.

        Args:
            image_path: Path to the image file

        Returns:
            List of detected items
        """
        prompt = """You are a food vision assistant for a children's dental health app.

From this photo, identify up to 5 food items or snacks. For each item, provide:
- name: Common name of the item
- brand_guess: Brand name if visible (or null if unclear)
- category: Category (e.g., chips, candy, cookie, fruit, vegetable, beverage, dairy)
- visible_clues: What visual clues helped identify it (packaging color, shape, text)
- confidence: Your confidence level (0.0 to 1.0)

IMPORTANT GROUPING RULES:
- If you see a plate/bowl with multiple similar items (e.g., fruit plate, veggie tray, mixed snacks),
  group them as ONE item with a descriptive name like:
  - "Mixed Fruit Plate" or "Fresh Fruit Assortment" (for assorted fruits)
  - "Fresh Vegetable Tray" (for assorted vegetables)
  - "Mixed Snack Bowl" (for assorted crackers/chips/snacks)
- Only list individual items separately if they are clearly DIFFERENT types of snacks
- Maximum 5 items total - prioritize the most prominent items

Focus on packaged snacks, lunch items, or identifiable foods. Ignore utensils or plates themselves.

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

Set needs_confirmation to true if any item has confidence < 0.7.
ALWAYS return valid JSON even if you're uncertain - use lower confidence scores for uncertain items."""

        try:
            # Read image file and encode as base64
            image_path_obj = Path(image_path)
            with open(image_path_obj, "rb") as f:
                image_data = f.read()

            # Determine mime type
            mime_type, _ = mimetypes.guess_type(str(image_path_obj))
            if not mime_type:
                mime_type = "image/jpeg"  # Default to JPEG

            # Generate response using new SDK with inline data
            # Use asyncio.to_thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
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
                    temperature=0.3,  # Lower for factual detection
                    max_output_tokens=1024,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_NONE"
                        ),
                    ],
                ),
            )

            # Parse JSON response - handle None response
            if response.text is None:
                logger.warning("Gemini returned None response text for vision detection")
                return [
                    DetectedItem(
                        name="Unidentified Food",
                        brand_guess=None,
                        category="unknown",
                        visible_clues="Vision model returned empty response",
                        confidence=0.2,
                    )
                ]

            response_text = response.text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            try:
                result = json.loads(response_text.strip())
                # Convert to DetectedItem models
                items = [DetectedItem(**item) for item in result.get("items", [])]
            except (json.JSONDecodeError, KeyError, TypeError) as parse_error:
                logger.warning(f"Failed to parse vision response: {parse_error}")
                logger.warning(f"Raw response (first 500 chars): {response_text[:500]}")
                # Return fallback item to trigger UNKNOWN mode
                items = [
                    DetectedItem(
                        name="Unidentified Food",
                        brand_guess=None,
                        category="unknown",
                        visible_clues="Could not clearly identify the food items in this image",
                        confidence=0.3,
                    )
                ]

            # Ensure we always return at least one item
            if not items:
                logger.warning("No items detected, returning fallback")
                items = [
                    DetectedItem(
                        name="Unidentified Food",
                        brand_guess=None,
                        category="unknown",
                        visible_clues="No recognizable food items found in the image",
                        confidence=0.3,
                    )
                ]

            logger.info(f"Detected {len(items)} items from image")
            return items

        except Exception as e:
            logger.error(f"Error detecting items: {e}")
            # Return fallback item instead of raising to prevent frontend crash
            return [
                DetectedItem(
                    name="Unidentified Food",
                    brand_guess=None,
                    category="unknown",
                    visible_clues=f"Error processing image: {str(e)[:100]}",
                    confidence=0.1,
                )
            ]

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
            # Use asyncio.to_thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.settings.gemini_writer_model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    ),
                ],
                config=types.GenerateContentConfig(
                    temperature=self.settings.gemini_temperature,
                    max_output_tokens=self.settings.gemini_max_tokens,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_NONE"
                        ),
                    ],
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
            # Use asyncio.to_thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.models.embed_content,
                model="text-embedding-004",
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=text)],
                    ),
                ],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )

            return response.embeddings[0].values

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
            # Use asyncio.to_thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.models.embed_content,
                model="text-embedding-004",
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=text)],
                    ),
                ],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                ),
            )

            return response.embeddings[0].values

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    async def compose_celebrate_script(
        self,
        snacks: list[dict[str, Any]],
        facts: list[dict[str, Any]],
        age: int,
    ) -> dict[str, Any]:
        """
        Compose a celebratory 4-panel comic script for healthy snacks.

        Uses positive narrative arc:
        Panel 1: Hero Entrance - Healthy snack introduced as hero
        Panel 2: Superpower - Health benefits revealed
        Panel 3: Team Up - Captain Sparkle and snack team up
        Panel 4: Celebration - Victory pose and positive reinforcement

        Args:
            snacks: List of healthy snack data
            facts: List of celebration facts
            age: Child's age

        Returns:
            Comic script with panels, caption, and alt text
        """
        # Determine age band
        if age <= 5:
            age_band = "3-5"
            tone = "very simple, playful, super cheerful"
        elif age <= 8:
            age_band = "6-8"
            tone = "friendly, fun, celebratory"
        else:
            age_band = "9-12"
            tone = "engaging, cool, triumphant"

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)

        prompt = f"""You are a comedy writer for kids creating CELEBRATORY 4-panel dental health comics about HEALTHY SNACKS!

TARGET AUDIENCE: Age {age} ({age_band} years old), tone: {tone} and POSITIVE!

🎭 RECURRING CHARACTER - CAPTAIN SPARKLE:
Captain Sparkle is a superhero tooth who appears in EVERY comic. In celebrate mode, Captain Sparkle is THRILLED and acts like meeting a celebrity. Personality: Enthusiastic, celebratory, loves giving high-fives. Always wears a tiny superhero cape. Catchphrase: "Sparkle power!" Expression: excited, amazed, starstruck, triumphant.

🌟 HEALTHY SNACKS IN PHOTO (they are HEROES!):
{snacks_context}

🎉 CELEBRATION FACTS (integrate into praise, cite fact_id in citation_ids):
{facts_context}

🎬 CELEBRATE MODE PANEL STRUCTURE:

PANEL 1 - HERO ENTRANCE (The Champion Arrives!)
- Healthy snack enters like a SUPERSTAR (red carpet, spotlight, cheering)
- Captain Sparkle is AMAZED: "Is that really YOU?!"
- Snack has a cool superhero name and poses heroically
- Set up the celebratory mood with confetti or sparkles

PANEL 2 - SUPERPOWER REVEAL (Show Off the Powers!)
- Snack demonstrates its AMAZING dental superpowers
- Captain Sparkle takes notes excitedly (cite a celebration fact here)
- Use power effects: glowing, sparkling, strength lines
- Make the health benefits sound like actual superpowers!

PANEL 3 - TEAM UP (Best Friends!)
- Captain Sparkle and snack do a team pose or high-five
- Another celebration fact revealed (cite fact_id)
- They discover they have matching powers or goals
- Include a funny "best friends" moment

PANEL 4 - VICTORY CELEBRATION (Party Time!)
- Epic victory pose with both characters
- Captain Sparkle: "Sparkle power!" with confetti explosion
- End with an invitation: "Eat more of me!"
- Positive, exciting, makes healthy eating feel AWESOME

🎨 CELEBRATION TECHNIQUES (Use ALL of these):
1. HERO TREATMENT: Red carpets, spotlights, trophies, medals
2. POWER EFFECTS: Sparkles, glow, energy waves, strength lines
3. TEAM BONDING: High-fives, fist bumps, friendship poses
4. PARTY VIBES: Confetti, balloons, fireworks, cheering

⚠️ CRITICAL RULES FOR FACT CITATIONS:
- citation_ids field = ONLY fact IDs like ["F025", "F027"]
- dialogue field = ONLY what characters SAY - NEVER include fact IDs in dialogue
- The dialogue should naturally incorporate the fact's content WITHOUT mentioning the ID

📝 OTHER RULES:
- Every panel should feel like a CELEBRATION
- Keep dialogue VERY SHORT: Maximum 2-3 brief lines per panel
- CRITICAL TEXT LIMITS: Each dialogue line must be under 40 characters, total per panel under 100 characters
- Expressions: excited, amazed, proud, triumphant, starstruck
- Props: capes, medals, trophies, confetti cannons, spotlights
- NO negatives - everything is positive and awesome!

📋 REQUIRED JSON OUTPUT STRUCTURE:

Return your response as valid JSON with this EXACT structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Panel Title",
      "dialogue": ["Line 1", "Line 2"],
      "citation_ids": ["F025"],
      "characters": [
        {{
          "name": "Character Name",
          "item_id": "snack_id",
          "expression": "excited",
          "position": "left",
          "props": ["cape", "medal"]
        }}
      ],
      "visual_prompt": "Description of the scene",
      "background": "celebration themed"
    }}
  ],
  "summary_caption": "A celebratory one-liner (under 100 chars)",
  "alt_text": "Accessibility description (1-2 sentences)"
}}

Make it a CELEBRATION of healthy eating!"""

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.settings.gemini_writer_model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    ),
                ],
                config=types.GenerateContentConfig(
                    temperature=self.settings.gemini_temperature,
                    max_output_tokens=self.settings.gemini_max_tokens,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_NONE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_NONE"
                        ),
                    ],
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

            try:
                result = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse celebrate script response: {e}")
                logger.error(f"Raw response (first 1000 chars): {response_text[:1000]}")
                raise ValueError(f"Gemini returned invalid JSON: {e}")

            # Safety filter: Remove any fact IDs from dialogue
            import re
            fact_id_pattern = re.compile(r'\[?F\d{3,4}\]?|\(F\d{3,4}\)')

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    cleaned_dialogue = []
                    for line in panel['dialogue']:
                        cleaned_line = fact_id_pattern.sub('', line).strip()
                        cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
                        cleaned_dialogue.append(cleaned_line)
                    panel['dialogue'] = cleaned_dialogue

            # Character limit validation
            MAX_LINE_LENGTH = 45
            MAX_PANEL_TOTAL = 110

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    validated_dialogue = []
                    panel_total = 0

                    for line in panel['dialogue']:
                        if len(line) > MAX_LINE_LENGTH:
                            logger.warning(f"Truncating dialogue line from {len(line)} to {MAX_LINE_LENGTH} chars")
                            line = line[:MAX_LINE_LENGTH-3] + "..."

                        if panel_total + len(line) > MAX_PANEL_TOTAL:
                            logger.warning(f"Panel exceeds character limit, stopping at {panel_total} chars")
                            break

                        validated_dialogue.append(line)
                        panel_total += len(line)

                    panel['dialogue'] = validated_dialogue

            logger.info(f"Composed celebrate script with {len(result.get('panels', []))} panels")
            return result

        except Exception as e:
            logger.error(f"Error composing celebrate script: {e}")
            raise

    def get_unknown_script(self, age: int) -> dict[str, Any]:
        """
        Get a generic fallback script when no snacks are recognized.

        Provides general dental health tips without specific snack references.

        Args:
            age: Child's age

        Returns:
            Generic comic script with panels, caption, and alt text
        """
        # Determine age band for tone
        if age <= 5:
            tone_adj = "simple"
            brush_tip = "Brush twice a day!"
            water_tip = "Drink lots of water!"
        elif age <= 8:
            tone_adj = "fun"
            brush_tip = "Brush for 2 whole minutes!"
            water_tip = "Water is your teeth's best friend!"
        else:
            tone_adj = "cool"
            brush_tip = "2 minutes, twice daily - that's the pro move!"
            water_tip = "Hydration = healthy smile game!"

        return {
            "panels": [
                {
                    "panel_number": 1,
                    "title": "Captain Sparkle's Daily Patrol",
                    "dialogue": [
                        "Hey there! Captain Sparkle here!",
                        "Ready for some tooth wisdom?"
                    ],
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Captain Sparkle",
                            "item_id": "recurring_tooth",
                            "expression": "excited",
                            "position": "center",
                            "props": ["superhero cape", "sparkle wand"]
                        }
                    ],
                    "visual_prompt": f"Friendly superhero tooth character in {tone_adj} style, waving hello with sparkles around",
                    "background": "bright cheerful sky"
                },
                {
                    "panel_number": 2,
                    "title": "The Brushing Power",
                    "dialogue": [
                        brush_tip,
                        "That's how we fight the cavity crew!"
                    ],
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Captain Sparkle",
                            "item_id": "recurring_tooth",
                            "expression": "determined",
                            "position": "left",
                            "props": ["superhero cape", "giant toothbrush"]
                        }
                    ],
                    "visual_prompt": "Tooth superhero demonstrating brushing with oversized sparkly toothbrush",
                    "background": "bathroom with sparkles"
                },
                {
                    "panel_number": 3,
                    "title": "Hydration Station",
                    "dialogue": [
                        water_tip,
                        "It washes away sneaky sugar!"
                    ],
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Captain Sparkle",
                            "item_id": "recurring_tooth",
                            "expression": "happy",
                            "position": "right",
                            "props": ["superhero cape", "water bottle"]
                        }
                    ],
                    "visual_prompt": "Tooth superhero drinking water with refreshing splash effects",
                    "background": "water droplets and sparkles"
                },
                {
                    "panel_number": 4,
                    "title": "Sparkle Power!",
                    "dialogue": [
                        "Now YOU have the power!",
                        "Sparkle power!"
                    ],
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Captain Sparkle",
                            "item_id": "recurring_tooth",
                            "expression": "triumphant",
                            "position": "center",
                            "props": ["superhero cape", "sparkle trail"]
                        }
                    ],
                    "visual_prompt": "Tooth superhero in triumphant pose with sparkle explosion and cape billowing",
                    "background": "celebration with confetti"
                }
            ],
            "summary_caption": "Captain Sparkle shares the secrets to a super smile!",
            "alt_text": "A 4-panel comic featuring Captain Sparkle, a superhero tooth, sharing dental health tips about brushing and drinking water."
        }
