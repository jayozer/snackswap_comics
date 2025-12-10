"""
Gemini AI service for SnackSwap Comics.
Handles vision detection, script composition, and embeddings.
"""

import asyncio
import base64
import json
import logging
import mimetypes
import time
from typing import Any
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import Settings
from app.models import DetectedItem, Panel
from app.services.guardrails_service import get_guardrails_service, ContentRating
from app.services.audit_service import get_audit_service, GenerationType

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI using the new google.genai SDK."""

    def __init__(self, settings: Settings):
        """Initialize Gemini service with the new SDK."""
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.guardrails = get_guardrails_service()
        self.audit = get_audit_service(settings)

        logger.info("Initialized Gemini service with new google.genai SDK and guardrails")

    def _repair_json(self, text: str) -> str | None:
        """
        Attempt to repair truncated or malformed JSON.

        Args:
            text: Potentially malformed JSON string

        Returns:
            Repaired JSON string or None if repair fails
        """
        import re

        # Count open/close brackets
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')

        # If severely truncated (missing closing structure), try to repair
        if open_braces > close_braces or open_brackets > close_brackets:
            logger.info(f"Attempting JSON repair: {open_braces} {{ vs {close_braces} }}, {open_brackets} [ vs {close_brackets} ]")

            # Find the last complete object/array
            # Look for common truncation points
            truncation_patterns = [
                r',\s*"[^"]*$',  # Truncated in middle of a key
                r',\s*$',  # Trailing comma
                r':\s*"[^"]*$',  # Truncated in middle of a value
                r':\s*\[[^\]]*$',  # Truncated array
            ]

            repaired = text
            for pattern in truncation_patterns:
                match = re.search(pattern, repaired)
                if match:
                    repaired = repaired[:match.start()]
                    break

            # Close any open structures
            while repaired.count('[') > repaired.count(']'):
                repaired += ']'
            while repaired.count('{') > repaired.count('}'):
                repaired += '}'

            # Remove any trailing commas before closing brackets
            repaired = re.sub(r',\s*}', '}', repaired)
            repaired = re.sub(r',\s*]', ']', repaired)

            return repaired

        return None

    async def detect_items(self, image_path: str) -> list[DetectedItem]:
        """
        Detect food items in an image using Gemini Vision.

        Args:
            image_path: Path to the image file

        Returns:
            List of detected items
        """
        prompt = """You are a precise food detection assistant for a dental health app.

⚠️ CRITICAL: ONLY identify what you ACTUALLY SEE in the image. DO NOT guess or assume.

Analyze this photo and identify up to 5 food/snack items. For each item, provide:
- name: The ACCURATE common name of EXACTLY what you see (be specific and literal)
- brand_guess: Brand name if clearly visible on packaging (or null if not visible)
- category: One of: candy, chips, cookies, crackers, fruit, vegetables, dairy, beverage, baked_goods, processed_snack, healthy_snack
- visible_clues: Observable details that helped identify it (color, shape, texture, packaging)
- confidence: Your confidence level (0.0 to 1.0)

🍎 HEALTHY FOOD RECOGNITION (IMPORTANT):
- Fresh fruits: apples, oranges, bananas, grapes, berries, melons, etc.
- Fresh vegetables: carrots, celery, cucumbers, broccoli, peppers, etc.
- Fruit plates/bowls = "Mixed Fruit Plate" or "Fresh Fruit Assortment" (category: fruit)
- Vegetable trays = "Fresh Vegetable Tray" (category: vegetables)
- Cheese slices/cubes = "Cheese" or "Cheddar Cheese" (category: dairy)
- Nuts = "Almonds", "Mixed Nuts" etc. (category: healthy_snack)

🚫 COMMON MISTAKES TO AVOID:
- Do NOT confuse colorful fruits with candy
- Do NOT confuse vegetable trays with processed snacks
- Do NOT confuse cheese with crackers
- Fresh, whole foods are NEVER "crackers" or "chips"
- If you see natural, unprocessed food, it's likely fruit/vegetables/dairy

GROUPING RULES:
- Multiple similar items = ONE grouped item
  - Example: bowl of mixed fruits = "Mixed Fruit Plate" (category: fruit)
  - Example: vegetable tray = "Fresh Vegetable Tray" (category: vegetables)
  - Example: 10 gummy bears = "Gummy Bears" (category: candy)
- Maximum 5 distinct food items total
- Prioritize the most prominent/visible items

Return your response as a JSON object with this structure:
{
  "items": [
    {
      "name": "string",
      "brand_guess": "string or null",
      "category": "string",
      "visible_clues": "string describing what you ACTUALLY see",
      "confidence": 0.95
    }
  ],
  "needs_confirmation": false
}

Set needs_confirmation to true ONLY if the image is blurry or food is unrecognizable.
ALWAYS return valid JSON. Be accurate - identify what you SEE, not what you assume."""

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
            age: User's age (9-17)

        Returns:
            Comic script with panels, caption, and alt text
        """
        # Determine age band: 9-12 (Spicy) or 13-17 (Savage)
        if age <= 12:
            age_band = "9-12"
            intensity = "Spicy"
            tone = "sarcastic, meme-y, lighter burns"
        else:
            age_band = "13-17"
            intensity = "Savage"
            tone = "full destruction mode, no mercy, brutal honesty"

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)
        swaps_context = json.dumps(swaps, indent=2)

        prompt = f"""You are a SAVAGE ROAST COMEDIAN writing for Gen Z/Gen Alpha teens (ages 9-17).
Your goal: Create a 4-panel "Roast Object" comic where a snack gets absolutely DESTROYED for being UGLY and ruining your AESTHETIC.

TARGET AUDIENCE: Age {age} ({age_band} - {intensity} mode), tone: {tone}

⚠️ TEENS DON'T CARE ABOUT HEALTH - THEY ONLY CARE ABOUT:
- VANITY: Having white, bright teeth (The "Hollywood Smile")
- AESTHETICS: Not having gross, yellow, or "fuzzy" teeth
- SOCIAL STATUS: Having "Rizz" and "Aura". Bad teeth = Negative Aura.

🎭 RECURRING CHARACTER - DR. DRIP:
A hype-beast molar tooth with sunglasses, a gold crown, and fresh kicks.
Personality: Obsessed with "The Glow Up" and "Aesthetics". He doesn't care if you get sick. He cares if you look MID.
Catchphrases: "Your smile is COOKED." / "Negative Aura detected."
Verdicts: "COOKED SMILE" / "YELLOW TEETH SIGNAL" / "NOT AESTHETIC"

SNACKS IN PHOTO (The Victims):
{snacks_context}

FACTS (The Ammo - cite fact_id):
{facts_context}

⚠️ CRITICAL: RE-FRAME ALL FACTS TO BE ABOUT LOOKS/VANITY:
- Sugar = "Turns your teeth YELLOW over time"
- Acids = "Melts your enamel so you look transparent/weak"
- Sticky = "Looks gross and fuzzy on your teeth"
- Cavities = "Holes in your teeth are NOT aesthetic"
- Bacteria = "Makes your breath cooked"

SWAPS (The Glow Up Secret):
{swaps_context}

🎬 PANEL STRUCTURE (The Vanity Roast Arc):

PANEL 1 - THE FLEX (The Setup)
- Snack enters acting tasty. "I'm the main character."
- Dr. Drip looks disgusted (behind sunglasses). "Ew. Brother ewww."
- Snack tries to have "aura" but Dr. Drip isn't buying it

PANEL 2 - THE EXPOSÉ (The Vanity Roast)
- Dr. Drip EXPOSES how the snack makes you LOOK BAD (cite fact_id)
- "You turn bright white teeth into YELLOW BRICKS."
- "You give people 'Fuzzy Tooth' syndrome. Cringe."
- Snack looks offended: "But I taste good!"

PANEL 3 - THE RATIO (The Social Destruction)
- Dr. Drip destroys the snack's social status
- "Imagine talking to your crush with yellow teeth. Couldn't be me."
- "That's negative aura fr fr."
- Snack is crying: "I just wanted to be aesthetic!"
- Visual: Snack looks gross, melting, or ugly

PANEL 4 - THE VIBE CHECK (The Glow Up Switch)
- Dr. Drip presents the SWAP as the "Glow Up" secret
- "Eat [Swap Name]. It scrubs your teeth white while you eat."
- "Your smile will be unfiltered. Main character energy."
- Final Verdict: "COOKED SMILE" or "YELLOW TEETH SIGNAL"

🎨 COMEDY TECHNIQUES (VANITY FOCUS):
1. APPEARANCE WORDS: "Yellow", "Stained", "Gross", "Fuzzy", "Crusty", "Transparent"
2. VANITY SHAMING: "Your Instagram pics need a filter with that smile"
3. LOOKSMAXXING SLANG: "Glow up", "Aura", "Aesthetic", "Rizz", "No filter needed"

⚠️ CRITICAL RULES FOR FACT CITATIONS:
- citation_ids field = ONLY fact IDs like ["F001", "F003"]
- dialogue field = ONLY what characters SAY - NEVER include "F001" or fact IDs in dialogue
- The dialogue should naturally incorporate the fact's content WITHOUT mentioning the ID
- WRONG: "I stick to teeth [F001]"
- RIGHT: dialogue: ["Bro sticks to teeth for hours!"], citation_ids: ["F001"]

📝 OTHER RULES:
- Every panel needs a ROAST MOMENT or meme reference
- Keep dialogue SHORT and PUNCHY: Max 2-3 lines per panel
- CRITICAL TEXT LIMITS: Each dialogue line must be under 40 characters, total per panel under 100 characters
- Expressions: smug, skeptical, shocked, defeated, crying, triumphant, flexing
- Props: sunglasses, gold chains, sneakers, "L" signs, sweat drops
- NO PREACHING - Don't sound like a dentist. Sound like a hater with dental knowledge.

🎤 SPEECH BUBBLE EMOTIONS (Required per panel):
Specify the "emotion" for each panel's speech bubble style:
- Panel 1 (THE FLEX): "speech" - normal confident talking
- Panel 2 (THE EXPOSÉ): "exclaim" - dramatic reveal, starburst bubble
- Panel 3 (THE RATIO): "angry" - destruction mode, jagged bubble
- Panel 4 (THE VIBE CHECK): "speech" - resolution, normal bubble

EXAMPLE PANEL (showing VANITY roast + citations + emotion done RIGHT):

{{
  "panel_number": 2,
  "title": "The Exposé",
  "dialogue": [
    "Bro turns white teeth into YELLOW BRICKS.",
    "That's negative aura detected.",
    "But I taste good!"
  ],
  "emotion": "exclaim",
  "citation_ids": ["F002"],
  "characters": [
    {{
      "name": "Sugar Bomb Sam",
      "item_id": "candy_gummy",
      "expression": "sweating",
      "position": "left",
      "props": ["sweat drops", "yellow stains", "gross aura"]
    }},
    {{
      "name": "Dr. Drip",
      "item_id": "recurring_tooth",
      "expression": "disgusted",
      "position": "right",
      "props": ["sunglasses", "gold crown", "fresh kicks", "pristine white shine"]
    }}
  ],
  "visual_prompt": "Gummy candy looking gross with yellow stains while pristine white molar tooth with sunglasses looks disgusted. Contrast between gross and aesthetic.",
  "background": "split background - grimy on left, sparkling clean on right"
}}

📋 REQUIRED JSON OUTPUT STRUCTURE:

Return your response as valid JSON with this EXACT structure:

{{
  "panels": [
    // Array of 4 panels, each with: panel_number, title, dialogue, emotion, citation_ids, characters, visual_prompt, background
    // emotion REQUIRED: "speech" (panels 1,4), "exclaim" (panel 2), "angry" (panel 3)
  ],
  "summary_caption": "A vanity-focused verdict (under 100 chars) - e.g. 'Your smile is COOKED'",
  "alt_text": "Accessibility description for screen readers (1-2 sentences)"
}}

Make it about LOOKS. Make it about AESTHETIC. Make teens care about their smile's appearance."""

        try:
            start_time = time.time()

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

            # Try to parse JSON - with repair attempts on failure
            try:
                result = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parse failed: {e}")
                logger.warning(f"Raw response (first 500 chars): {response_text[:500]}")

                # Attempt to repair truncated JSON
                repaired = self._repair_json(response_text.strip())
                if repaired:
                    try:
                        result = json.loads(repaired)
                        logger.info("JSON repair successful")
                    except json.JSONDecodeError as e2:
                        logger.error(f"JSON repair failed: {e2}")
                        raise ValueError(f"Gemini returned invalid JSON: {e}")
                else:
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

            # Guardrails validation
            validation = self.guardrails.validate_script(result, auto_clean=True)
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit logging
            self.audit.log_generation(
                generation_type=GenerationType.SCRIPT_COMPOSE,
                input_data={
                    "age": age,
                    "snacks": [s.get("name", "unknown") for s in snacks[:5]],
                    "fact_count": len(facts),
                    "swap_count": len(swaps),
                },
                output_data=result,
                validation_passed=validation.passed,
                validation_details=validation.details,
                flagged_terms=validation.flagged_terms,
                user_age=age,
                duration_ms=duration_ms,
            )

            if not validation.passed:
                logger.error(f"Script failed guardrails: {validation.details}")
                raise ValueError(f"Generated content failed safety check: {validation.details}")

            # Use cleaned content if available
            if validation.cleaned_content:
                result = validation.cleaned_content

            logger.info(f"Composed script with {len(result.get('panels', []))} panels (validation: {validation.rating.value})")
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

        Uses positive "W Arc" narrative:
        Panel 1: The Entrance - Healthy snack walks in confident
        Panel 2: The Stats - Dr. Drip impressed by health stats
        Panel 3: The Glaze - Bro-hug moment
        Panel 4: The Crown - Coronation, verdict: GOATED

        Args:
            snacks: List of healthy snack data
            facts: List of celebration facts
            age: User's age (9-17)

        Returns:
            Comic script with panels, caption, and alt text
        """
        # Determine age band: 9-12 (Spicy) or 13-17 (Savage)
        if age <= 12:
            age_band = "9-12"
            intensity = "Spicy"
            tone = "hype, energetic, respectful props"
        else:
            age_band = "13-17"
            intensity = "Savage"
            tone = "maximum hype, real recognizes real, absolute respect"

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)

        prompt = f"""You are a HYPE BEAST writing for teens. This snack is the KEY to LOOKSMAXXING.

TARGET AUDIENCE: Age {age} ({age_band} - {intensity} mode), tone: {tone}

⚠️ CORE MESSAGE: This snack makes your teeth WHITE, CLEAN, and AESTHETIC.
Teens don't care about "health" - they care about the GLOW UP.

🎭 RECURRING CHARACTER - DR. DRIP:
He's giving out the "Glow Up" award. He's genuinely impressed.
Look: Hype-beast molar with sunglasses, gold crown, fresh kicks, PRISTINE WHITE SHINE
Expressions: "Sheesh!", "Immaculate vibes.", "No filter needed."
Verdicts: "AESTHETIC" / "GLOW UP APPROVED" / "10/10 AURA"

🌟 HEALTHY SNACKS (The Looksmaxxers):
{snacks_context}

💎 FACTS (The Beauty Secrets - cite fact_id):
{facts_context}

⚠️ CRITICAL: RE-FRAME ALL FACTS AS BEAUTY HACKS:
- Fiber scrubs teeth = "Natural Whitening Strip"
- No sugar = "Zero yellow stain risk"
- Crunchy = "Built-in teeth scrubber"
- Hydrating = "Keeps smile fresh and clean"
- Vitamins = "Glow up fuel"

🎬 PANEL STRUCTURE (The Glow Up Arc):

PANEL 1 - THE ENTRANCE
- Healthy snack walks in looking clean/shiny (like it has a natural filter)
- Snack literally GLOWS (sparkles, shine effects)
- Dr. Drip: "Wait... is that a natural filter?"
- Vibe: Aesthetic immediately detected

PANEL 2 - THE STATS (The Beauty Secrets)
- Snack reveals its beauty secrets (Natural scrubber, No stain risk)
- "It literally whitens your teeth while you eat?"
- Dr. Drip is impressed: "So you're basically a whitening kit I can eat?" (cite fact_id)
- Visual: "Glow Up Stats" screen showing aesthetic benefits

PANEL 3 - THE GLAZE (The Hype)
- Dr. Drip hypes up the aesthetic potential
- "Your smile is gonna blind people. 10/10 Aura."
- "That's main character energy fr."
- Mutual respect moment (cite another fact_id if available)

PANEL 4 - THE CROWN (The Glow Up Award)
- Dr. Drip creates a frame with his hands (like taking a photo)
- "No filter needed. Your smile is already unfiltered perfection."
- Final verdict text overlay: "AESTHETIC" or "GLOW UP APPROVED"
- Sparkles, shine effects, golden hour lighting

🎨 LOOKSMAXXING TECHNIQUES:
1. APPEARANCE WORDS: "White", "Clean", "Bright", "Sparkling", "Unfiltered", "Glowing"
2. BEAUTY SLANG: "Glow up", "Aesthetic", "No filter needed", "Natural beauty hack"
3. VANITY FLEX: "Hollywood smile", "Main character teeth", "Rizz-ready smile"
4. VISUAL GLOW: Sparkles, shine effects, pristine white, golden hour lighting

⚠️ CRITICAL RULES FOR FACT CITATIONS:
- citation_ids field = ONLY fact IDs like ["F025", "F027"]
- dialogue field = ONLY what characters SAY - NEVER include fact IDs in dialogue
- The dialogue should naturally incorporate the fact's content WITHOUT mentioning the ID

📝 OTHER RULES:
- Every panel should feel like a W (win)
- Keep dialogue SHORT and PUNCHY: Max 2-3 lines per panel
- CRITICAL TEXT LIMITS: Each dialogue line must be under 40 characters, total per panel under 100 characters
- Expressions: impressed, respectful, hyped, triumphant, nodding
- Props: sunglasses, gold crown, sneakers, trophy, stat screens
- NO CRINGE - Keep it genuinely cool, not try-hard

🎤 SPEECH BUBBLE EMOTIONS (Required per panel):
Specify the "emotion" for each panel's speech bubble style:
- Panel 1 (THE ENTRANCE): "speech" - confident entrance
- Panel 2 (THE STATS): "exclaim" - impressed by beauty secrets
- Panel 3 (THE GLAZE): "speech" - hype moment
- Panel 4 (THE CROWN): "exclaim" - triumphant coronation

📋 REQUIRED JSON OUTPUT STRUCTURE:

Return your response as valid JSON with this EXACT structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "The Entrance",
      "dialogue": ["Wait... is that a natural filter?", "I literally GLOW."],
      "emotion": "speech",
      "citation_ids": ["F025"],
      "characters": [
        {{
          "name": "Crunchy Apple Chad",
          "item_id": "fruit_apple",
          "expression": "glowing",
          "position": "left",
          "props": ["sparkles", "shine effect", "pristine appearance"]
        }},
        {{
          "name": "Dr. Drip",
          "item_id": "recurring_tooth",
          "expression": "impressed",
          "position": "right",
          "props": ["sunglasses", "gold crown", "fresh kicks", "pristine white shine"]
        }}
      ],
      "visual_prompt": "Glowing apple character with sparkles enters scene. Pristine white molar tooth with sunglasses looks impressed. Golden hour lighting, aesthetic vibes.",
      "background": "bright, clean, aesthetic setting with sparkle effects"
    }}
    // ... panels 2-4 with emotion: "exclaim", "speech", "exclaim" respectively
  ],
  "summary_caption": "A beauty-focused verdict (under 100 chars) - e.g. 'Glow Up Approved. No filter needed.'",
  "alt_text": "Accessibility description (1-2 sentences)"
}}

Make it about the GLOW UP. Make teens want that Hollywood smile."""

        try:
            start_time = time.time()

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
                logger.warning(f"Initial celebrate JSON parse failed: {e}")
                logger.warning(f"Raw response (first 500 chars): {response_text[:500]}")

                # Attempt to repair truncated JSON
                repaired = self._repair_json(response_text.strip())
                if repaired:
                    try:
                        result = json.loads(repaired)
                        logger.info("Celebrate JSON repair successful")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Celebrate JSON repair failed: {e2}")
                        raise ValueError(f"Gemini returned invalid JSON: {e}")
                else:
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

            # Guardrails validation
            validation = self.guardrails.validate_script(result, auto_clean=True)
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit logging
            self.audit.log_generation(
                generation_type=GenerationType.SCRIPT_CELEBRATE,
                input_data={
                    "age": age,
                    "snacks": [s.get("name", "unknown") for s in snacks[:5]],
                    "fact_count": len(facts),
                },
                output_data=result,
                validation_passed=validation.passed,
                validation_details=validation.details,
                flagged_terms=validation.flagged_terms,
                user_age=age,
                duration_ms=duration_ms,
            )

            if not validation.passed:
                logger.error(f"Celebrate script failed guardrails: {validation.details}")
                raise ValueError(f"Generated content failed safety check: {validation.details}")

            # Use cleaned content if available
            if validation.cleaned_content:
                result = validation.cleaned_content

            logger.info(f"Composed celebrate script with {len(result.get('panels', []))} panels (validation: {validation.rating.value})")
            return result

        except Exception as e:
            logger.error(f"Error composing celebrate script: {e}")
            raise

    def get_unknown_script(self, age: int) -> dict[str, Any]:
        """
        Get a generic fallback script when no snacks are recognized.

        Provides general appearance/glow-up tips with DR. DRIP character.
        Focused on VANITY (white teeth, aesthetic smile) not health.

        Args:
            age: User's age (9-17)

        Returns:
            Generic comic script with panels, caption, and alt text
        """
        # Determine age band: 9-12 (Spicy) or 13-17 (Savage)
        if age <= 12:
            tone_adj = "spicy"
            brush_tip = "2 mins, twice a day. Keeps teeth WHITE."
            water_tip = "Water washes away the stain. No yellow."
            outro = "Now you know the glow up secrets!"
        else:
            tone_adj = "savage"
            brush_tip = "2 mins, twice daily. Unless you want yellow teeth."
            water_tip = "Hydration = no stains. Water mogs soda aesthetically."
            outro = "Glow up knowledge unlocked. You're welcome."

        return {
            "panels": [
                {
                    "panel_number": 1,
                    "title": "Dr. Drip Enters",
                    "dialogue": [
                        "Yo. Dr. Drip here.",
                        "Let me drop some glow up secrets."
                    ],
                    "emotion": "speech",
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Dr. Drip",
                            "item_id": "recurring_tooth",
                            "expression": "cool",
                            "position": "center",
                            "props": ["sunglasses", "gold crown", "fresh kicks", "pristine white shine"]
                        }
                    ],
                    "visual_prompt": f"Pristine white molar tooth with sunglasses, gold crown, and sneakers in {tone_adj} style, literally glowing, looking directly at viewer",
                    "background": "aesthetic gradient with sparkle effects"
                },
                {
                    "panel_number": 2,
                    "title": "The White Teeth Hack",
                    "dialogue": [
                        brush_tip,
                        "That's the unfiltered smile strat."
                    ],
                    "emotion": "exclaim",
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Dr. Drip",
                            "item_id": "recurring_tooth",
                            "expression": "smug",
                            "position": "left",
                            "props": ["sunglasses", "gold crown", "toothbrush sword", "sparkle effect"]
                        }
                    ],
                    "visual_prompt": "Pristine white tooth character wielding toothbrush like a sword, teeth literally sparkling, dramatic pose",
                    "background": "clean neon bathroom with mirror showing bright smile"
                },
                {
                    "panel_number": 3,
                    "title": "The No-Stain Move",
                    "dialogue": [
                        water_tip,
                        "Yellow teeth = cooked. Water = glow up."
                    ],
                    "emotion": "speech",
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Dr. Drip",
                            "item_id": "recurring_tooth",
                            "expression": "nodding",
                            "position": "right",
                            "props": ["sunglasses", "gold crown", "water bottle", "pristine white shine"]
                        }
                    ],
                    "visual_prompt": "Pristine white tooth character holding water bottle, refreshing sparkle effects around the smile",
                    "background": "clean aesthetic with crystal water splash effects"
                },
                {
                    "panel_number": 4,
                    "title": "The Verdict",
                    "dialogue": [
                        outro,
                        "No filter needed. ✌️"
                    ],
                    "emotion": "speech",
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Dr. Drip",
                            "item_id": "recurring_tooth",
                            "expression": "triumphant",
                            "position": "center",
                            "props": ["sunglasses", "gold crown", "fresh kicks", "peace sign", "sparkle effects"]
                        }
                    ],
                    "visual_prompt": "Pristine white tooth character doing peace sign, Hollywood smile energy, walking away with sparkles",
                    "background": "golden hour lighting with aesthetic glow"
                }
            ],
            "summary_caption": "Dr. Drip drops the glow up secrets. No filter needed.",
            "alt_text": "A 4-panel comic featuring Dr. Drip, a pristine white molar tooth with sunglasses and gold crown, sharing appearance tips about keeping teeth white and aesthetic."
        }

    async def detect_speech_bubbles(self, image_path: str) -> dict[int, dict] | None:
        """
        Use Gemini Vision to detect speech bubble positions in a comic image.

        Analyzes a 4-panel vertical comic strip and returns bubble locations
        for each panel, enabling smart text placement.

        Args:
            image_path: Path to the comic image file

        Returns:
            Dict mapping panel number (0-3) to bubble info:
            {
                0: {"bbox": [x1,y1,x2,y2], "center": [cx,cy], "style": "round", "confidence": 0.95},
                1: {"bbox": [...], ...},
                ...
            }
            Returns None if detection fails or no bubbles found.
        """
        prompt = """Analyze this 4-panel vertical comic strip (panels numbered 0-3 from top).

IMAGE LAYOUT:
- Vertical strip with 4 panels stacked (1x4 layout)
- Each panel is approximately 512×256 pixels
- Panel 0: rows 0-256 (top)
- Panel 1: rows 256-512
- Panel 2: rows 512-768
- Panel 3: rows 768-1024 (bottom)

TASK: Find the PRIMARY speech bubble in each panel.
Look for white/light colored oval, cloud, spiky, or jagged shapes in the TOP 40% of each panel.

Return JSON with this EXACT structure:
{
  "bubbles": [
    {
      "panel": 0,
      "bbox": [x1, y1, x2, y2],
      "center": [cx, cy],
      "style": "round",
      "confidence": 0.95
    }
  ],
  "success": true
}

RULES:
- Coordinates are ABSOLUTE pixels from image top-left (0,0)
- bbox: [x1, y1, x2, y2] where (x1,y1) is top-left, (x2,y2) is bottom-right
- center: [cx, cy] is the center point of the bubble
- style: "round" | "cloud" | "spiky" | "jagged" | "dashed"
- confidence: 0.0 to 1.0 based on certainty
- Only include PRIMARY/LARGEST bubble per panel
- If no bubble found in a panel, omit that panel from the array
- If no bubbles found at all, return {"bubbles": [], "success": false}

Return ONLY valid JSON, no other text."""

        try:
            # Read image file
            image_path_obj = Path(image_path)
            with open(image_path_obj, "rb") as f:
                image_data = f.read()

            # Determine mime type
            mime_type, _ = mimetypes.guess_type(str(image_path_obj))
            if not mime_type:
                mime_type = "image/png"

            # Call Gemini Vision
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
                    temperature=0.1,  # Low for factual detection
                    max_output_tokens=1024,
                ),
            )

            # Parse JSON response
            if response.text is None:
                logger.warning("Gemini Vision returned None for bubble detection")
                return None

            response_text = response.text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            # Check if detection was successful
            if not result.get("success", False) or not result.get("bubbles"):
                logger.info("No bubbles detected by Gemini Vision")
                return None

            # Convert to dict mapping panel number to bubble info
            bubbles_by_panel = {}
            for bubble in result.get("bubbles", []):
                panel_num = bubble.get("panel")
                if panel_num is not None and 0 <= panel_num < 4:
                    bubbles_by_panel[panel_num] = {
                        "bbox": bubble.get("bbox", [0, 0, 0, 0]),
                        "center": bubble.get("center", [0, 0]),
                        "style": bubble.get("style", "round"),
                        "confidence": bubble.get("confidence", 0.5),
                    }

            if bubbles_by_panel:
                logger.info(f"Gemini Vision detected bubbles in {len(bubbles_by_panel)} panels")
                return bubbles_by_panel

            return None

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse bubble detection JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Bubble detection failed: {e}")
            return None
