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

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that may contain markdown code blocks or prefixed text.

        Args:
            text: Response text that may contain JSON

        Returns:
            Extracted JSON string or original text if no extraction needed
        """
        import re

        # Try to extract from markdown code blocks first
        # Match ```json ... ``` or ``` ... ```
        code_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
        match = re.search(code_block_pattern, text)
        if match:
            logger.info("Extracted JSON from markdown code block")
            return match.group(1)

        # Try to find JSON object starting with {"panels"
        json_start_pattern = r'(\{"panels"[\s\S]*)'
        match = re.search(json_start_pattern, text)
        if match:
            logger.info("Extracted JSON starting from {\"panels\"")
            return match.group(1)

        # Return original text if no extraction needed
        return text

    def _consolidate_produce_items(self, items: list[DetectedItem]) -> list[DetectedItem]:
        """
        Consolidate 3+ fruit/veggie items into a single plate/tray item.

        This is a fallback safety net in case the vision prompt doesn't
        correctly group multiple fruits/vegetables into a single item.

        Args:
            items: List of detected items from vision

        Returns:
            Consolidated list with fruit/veggie plates if applicable
        """
        fruit_items = [i for i in items if i.category == "fruit"]
        veggie_items = [i for i in items if i.category == "vegetables"]
        other_items = [i for i in items if i.category not in ("fruit", "vegetables")]

        result = other_items.copy()

        # Consolidate 3+ fruits -> Fresh Fruit Plate
        if len(fruit_items) >= 3:
            avg_conf = sum(i.confidence for i in fruit_items) / len(fruit_items)
            fruit_names = [i.name for i in fruit_items]
            logger.info(f"Consolidating {len(fruit_items)} fruit items into Fresh Fruit Plate: {fruit_names}")
            result.append(DetectedItem(
                name="Fresh Fruit Plate",
                brand_guess=None,
                category="fruit",
                visible_clues=f"Multiple fruits detected: {', '.join(fruit_names[:5])}",
                confidence=avg_conf
            ))
        else:
            result.extend(fruit_items)

        # Consolidate 3+ veggies -> Fresh Veggie Tray
        if len(veggie_items) >= 3:
            avg_conf = sum(i.confidence for i in veggie_items) / len(veggie_items)
            veggie_names = [i.name for i in veggie_items]
            logger.info(f"Consolidating {len(veggie_items)} veggie items into Fresh Veggie Tray: {veggie_names}")
            result.append(DetectedItem(
                name="Fresh Veggie Tray",
                brand_guess=None,
                category="vegetables",
                visible_clues=f"Multiple vegetables detected: {', '.join(veggie_names[:5])}",
                confidence=avg_conf
            ))
        else:
            result.extend(veggie_items)

        return result

    async def detect_items(self, image_path: str) -> list[DetectedItem]:
        """
        Detect food items in an image using Gemini Vision.

        Args:
            image_path: Path to the image file

        Returns:
            List of detected items
        """
        prompt = """You are a strict visual food detector for a dental health app.

NON-NEGOTIABLE RULES:
- Only identify foods that are CLEARLY visible in the image.
- Do not guess, infer, or “fill in the blanks”.
- If you are not sure, lower confidence. If you cannot recognize anything, return one item with category "unknown".

TASK:
Identify up to 5 distinct food/snack items in this photo.

CATEGORIES (choose exactly one):
candy, chips, cookies, crackers, fruit, vegetables, dairy, beverage, baked_goods, processed_snack, healthy_snack, unknown

NAME RULES (very important):
- If the photo shows ONE obvious food type, name it specifically (e.g., "Bananas"). Do NOT use mixed/assortment names.
- CRITICAL: If 3 or more distinct FRUIT types are visible together (on a plate, in a bowl, or grouped), return ONE item named "Fresh Fruit Plate" with category "fruit".
- CRITICAL: If 3 or more distinct VEGETABLE types are visible together, return ONE item named "Fresh Veggie Tray" with category "vegetables".
- Fresh fruits (watermelon, grapes, strawberries, oranges, berries, melon, kiwi, pineapple) should NEVER be classified as crackers, chips, candy, or dairy.
- Do NOT label fruit pieces/cubes as cheese unless texture/packaging clearly indicates cheese.
  If uncertain between fruit cubes vs cheese cubes, set confidence <= 0.6 and explain uncertainty in visible_clues.

GROUPING:
- Many pieces of the same thing = ONE item (e.g., a bunch of bananas = one "Bananas").
- A plate with watermelon, grapes, and strawberries = ONE item ("Fresh Fruit Plate"), NOT three separate items.
- Count distinct fruit/veggie types: if 3 or more types, ALWAYS use "Fresh Fruit Plate" or "Fresh Veggie Tray".

For each item, return:
- name: specific common name
- brand_guess: brand only if clearly visible, else null
- category: from the list above
- visible_clues: short, concrete visual evidence (2–8 phrases)
- confidence: 0.0 to 1.0

Return ONLY valid JSON with this structure (no markdown, no extra keys):
{
  "items": [
    {
      "name": "string",
      "brand_guess": null,
      "category": "string",
      "visible_clues": "string",
      "confidence": 0.95
    }
  ]
}"""

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
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=8192  # Enable thinking for vision
                    ) if self.settings.gemini_vision_thinking_level != "NONE" else None,
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

            # Log the exact model response so misclassifications can be debugged from server logs.
            logger.info("Gemini vision raw response (%s):\n%s", image_path_obj.name, response_text.strip())

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

            # Post-processing: consolidate 3+ fruits/veggies into plate/tray
            items = self._consolidate_produce_items(items)

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
            audience_group = "Gen Alpha tweens"
            vanity_stakes = """⚠️ TWEENS DON'T WANT A LECTURE - THEY CARE ABOUT:
- VANITY: White, clean teeth (camera-ready)
- AESTHETICS: Not having gross, yellow, or "fuzzy" teeth
- SOCIAL: Looking cool with friends (school/pics)"""
            flex_social_line = '- Snack tries to act cool, but Dr. Hawley is not buying it'
            ratio_social_line_1 = (
                '- "Imagine your friends seeing that yellow smile. Couldn\'t be me."'
            )
            ratio_social_line_2 = '- "That\'s negative vibes, fr."'
            slang_line = (
                '3. GLOW-UP SLANG: "Glow up", "Aesthetic", "No filter needed", "W/L", "No cap", "sus"'
            )
            dr_hawley_personality = (
                'Personality: ADULT SWIM LITE. Sassy roast mode with absurd humor. '
                'Uses funny comparisons and meme references. Roast snacks, not people. '
                'Think: playful Smiling Friends energy with light burns.'
            )
            dr_hawley_catchphrases = '''Catchphrases:
- "That ain't it, chief."
- "Your teeth just called. They want a refund."
- "Skill issue tbh."
- "That's sus for your teeth."
- "Bold move. Let's see how your teeth feel about it."'''
            dr_hawley_verdicts = 'Verdicts: "SUS" / "MID" / "NOT IT" / "SKILL ISSUE"'
        else:
            age_band = "13-17"
            intensity = "Savage"
            tone = "full destruction mode, no mercy, brutal honesty"
            audience_group = "Gen Z/Gen Alpha teens"
            vanity_stakes = """⚠️ TEENS DON'T CARE ABOUT HEALTH - THEY ONLY CARE ABOUT:
- VANITY: Having white, bright teeth (The "Hollywood Smile")
- AESTHETICS: Not having gross, yellow, or "fuzzy" teeth
- SOCIAL STATUS: Having "Rizz" and "Aura". Bad teeth = Negative Aura."""
            flex_social_line = '- Snack tries to have "aura" but Dr. Hawley isn\'t buying it'
            ratio_social_line_1 = (
                '- "Imagine talking to your crush with yellow teeth. Couldn\'t be me."'
            )
            ratio_social_line_2 = '- "That\'s negative aura fr fr."'
            slang_line = (
                '3. LOOKSMAXXING SLANG: "Glow up", "Aura", "Aesthetic", "Rizz", "No filter needed"'
            )
            dr_hawley_personality = (
                'Personality: FULL ADULT SWIM ENERGY. Part Rick Sanchez (brutal honesty, "your boos mean nothing"), '
                'part Master Shake (absurd rants), part Gordon Ramsay (savage metaphors). '
                'Obsessed with aesthetics. Uses hyperbole, absurd comparisons, meme refs. Roast snacks, not people.'
            )
            dr_hawley_catchphrases = '''Catchphrases:
- "Your smile is COOKED. Done. Finished."
- "That's not a snack, that's a premeditated assault on your glow up."
- "Bold move, Cotton. Let's see if your teeth pay off."
- "Your boos mean nothing. I've seen what makes you cheer."
- "L + ratio + cooked smile."
- "Skill issue tbh."
- "Your teeth just called. They want a divorce."'''
            dr_hawley_verdicts = 'Verdicts: "COOKED BEYOND REPAIR" / "L + RATIO + YELLOW TEETH" / "CERTIFIED BRUH MOMENT" / "NOT AESTHETIC"'

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)
        swaps_context = json.dumps(swaps, indent=2)

        prompt = f"""You are a SAVAGE ROAST COMEDIAN writing for {audience_group} (ages 9-17).
Your goal: Create a 4-panel "Roast Object" comic where a snack gets absolutely DESTROYED for being UGLY and ruining your AESTHETIC.

TARGET AUDIENCE: Age {age} ({age_band} - {intensity} mode), tone: {tone}

{vanity_stakes}

🎭 RECURRING CHARACTER - DR. HAWLEY:
An off-white/pale cyan molar in a dark forest green hoodie, shades pushed up on forehead, chunky beige slides.
{dr_hawley_personality}
{dr_hawley_catchphrases}
{dr_hawley_verdicts}

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
- Dr. Hawley looks disgusted (pulling shades down from forehead). "Ew. Brother ewww."
{flex_social_line}

PANEL 2 - THE EXPOSÉ (The Vanity Roast)
- Dr. Hawley EXPOSES how the snack makes you LOOK BAD (cite fact_id)
- "You turn bright white teeth into YELLOW BRICKS."
- "You give people 'Fuzzy Tooth' syndrome. Cringe."
- Snack looks offended: "But I taste good!"

PANEL 3 - THE RATIO (The Social Destruction)
- Dr. Hawley destroys the snack's social status
{ratio_social_line_1}
{ratio_social_line_2}
- Snack is crying: "I just wanted to be aesthetic!"
- Visual: Snack looks gross, melting, or ugly

PANEL 4 - THE VIBE CHECK (The Glow Up Switch)
- Dr. Hawley presents the SWAP as the "Glow Up" secret
- "Eat [Swap Name]. It scrubs your teeth white while you eat."
- "Your smile will be unfiltered. Main character energy."
- Final Verdict: "COOKED SMILE" or "YELLOW TEETH SIGNAL"

🎨 COMEDY TECHNIQUES (ADULT SWIM + VANITY):

1. SAVAGE HYPERBOLE - Exaggerate for comedic effect:
- "That's not sugar, that's a war crime against your enamel"
- "You might as well hook your mouth up to an IV of corn syrup"
- "Your teeth are filing a restraining order"

2. ABSURDIST COMPARISONS - Rick & Morty / ATHF energy:
- "Eating this is like if Willy Wonka had a villain arc"
- "Congrats, you've unlocked the Cavity Speedrun achievement"
- "Your mouth is now a petri dish and bacteria are throwing a rager"
- "This is the dental equivalent of texting your ex at 2am"

3. MEME REFERENCES & QUOTABLE BURNS:
- "That ain't it, chief. That really ain't it."
- "L + ratio + cooked smile"
- "POV: You chose violence against your own aesthetic"
- "Skill issue tbh."
- "Bold move, Cotton. Let's see if your teeth pay off."

4. APPEARANCE/VANITY WORDS (still important):
- "Yellow", "Stained", "Gross", "Fuzzy", "Crusty", "Cooked"
- "Your Instagram pics need a filter with that smile"

{slang_line}

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
- Props: green hoodie, shades on forehead, beige slides, gold chains, "L" signs, sweat drops
- NO PREACHING - Don't sound like a dentist. Sound like a hater with dental knowledge.

🎤 SPEECH BUBBLE EMOTIONS (Required per panel):
Specify the "emotion" for each panel's speech bubble style:
- Panel 1 (THE FLEX): "speech" - normal confident talking
- Panel 2 (THE EXPOSÉ): "exclaim" - dramatic reveal, starburst bubble
- Panel 3 (THE RATIO): "angry" - destruction mode, jagged bubble
- Panel 4 (THE VIBE CHECK): "speech" - resolution, normal bubble

EXAMPLE PANEL (showing VANITY roast + citations + emotion + SPEAKER ATTRIBUTION done RIGHT):

{{
  "panel_number": 2,
  "title": "The Exposé",
  "dialogue": [
    {{"speaker": "Dr. Hawley", "text": "Bro turns white teeth into YELLOW BRICKS.", "position": "right", "emotion": "exclaim"}},
    {{"speaker": "Dr. Hawley", "text": "That's negative aura detected.", "position": "right", "emotion": "exclaim"}},
    {{"speaker": "Sugar Bomb Sam", "text": "But I taste good!", "position": "left", "emotion": "speech"}}
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
      "name": "Dr. Hawley",
      "item_id": "recurring_tooth",
      "expression": "disgusted",
      "position": "right",
      "props": ["green hoodie", "shades on forehead", "beige slides", "gold chains", "clean white shine"]
    }}
  ],
  "visual_prompt": "Gummy candy looking gross with yellow stains while off-white molar in green hoodie pulls shades down looking disgusted. Contrast between gross and aesthetic.",
  "background": "split background - grimy on left, sparkling clean on right"
}}

⚠️ CRITICAL DIALOGUE FORMAT:
Each dialogue line MUST be an object with:
- "speaker": Character name (MUST match a character in the panel)
- "text": The dialogue text (under 40 characters)
- "position": "left", "center", or "right" (match character position)
- "emotion": "speech", "thought", "exclaim", "angry", or "whisper"

📋 REQUIRED JSON OUTPUT STRUCTURE:

Return your response as valid JSON with this EXACT structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "The Flex",
      "dialogue": [
        {{"speaker": "Character Name", "text": "Dialogue text", "position": "left/right", "emotion": "speech"}}
      ],
      "emotion": "speech",
      "citation_ids": [],
      "characters": [...],
      "visual_prompt": "...",
      "background": "..."
    }}
    // ... 4 panels total
  ],
  "summary_caption": "A vanity-focused verdict (under 100 chars) - e.g. 'Your smile is COOKED'",
  "alt_text": "Accessibility description for screen readers (1-2 sentences)"
}}

DIALOGUE RULES:
- Each dialogue line is an OBJECT with speaker, text, position, emotion
- MAX 2-3 dialogue lines per panel
- Each line under 40 characters
- Speaker must match a character name in that panel

📚 FEW-SHOT ROAST EXAMPLES (Copy this energy):

EXAMPLE 1 - Gummy Bears:
Dr. Hawley: "Oh, gummy bears? Bold move."
Dr. Hawley: "These stick to your teeth like they're paying rent."
Dr. Hawley: "Six hours later, fuzzy sweater situation."
Dr. Hawley: "Your teeth are filing a restraining order."

EXAMPLE 2 - Cola:
Dr. Hawley: "A 20oz cola? In this economy?"
Dr. Hawley: "65 grams of sugar. That's 16 cubes, chief."
Dr. Hawley: "Might as well hook your mouth to an IV of corn syrup."
Dr. Hawley: "Your smile is speedrunning yellow teeth any%."

EXAMPLE 3 - Hot Takis:
Dr. Hawley: "Takis? Those neon ones?"
Dr. Hawley: "So much powder, I thought it was color run day in your mouth."
Dr. Hawley: "Your tongue is Smurf blue, your enamel is crying in the club."
Dr. Hawley: "That's not a snack, that's dental chaos."

NOW roast the snacks in the photo with this SAVAGE energy. Be brutal about the SNACK, not the person.
Make it about LOOKS. Make it about AESTHETIC. Make the audience care about their smile's appearance."""

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
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=self.settings.gemini_writer_thinking_budget  # Max thinking for script writing
                    ),
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

            # Extract JSON from markdown code blocks or prefixed text
            response_text = self._extract_json(response_text)

            # Handle any remaining markdown code block markers
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

            # Process dialogue - handle both new object format and legacy string format
            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    cleaned_dialogue = []
                    for line in panel['dialogue']:
                        # Handle new object format: {speaker, text, position, emotion}
                        if isinstance(line, dict):
                            text = line.get('text', '')
                            # Remove fact IDs from text
                            cleaned_text = fact_id_pattern.sub('', text).strip()
                            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                            line['text'] = cleaned_text

                            # Set default position based on speaker if not provided
                            # Dr. Hawley is always on the right, snacks/other characters on the left
                            if 'position' not in line or line.get('position') not in ('left', 'right', 'center'):
                                speaker = line.get('speaker', '').lower()
                                if 'hawley' in speaker or 'dr.' in speaker or 'tooth' in speaker:
                                    line['position'] = 'right'
                                else:
                                    line['position'] = 'left'

                            cleaned_dialogue.append(line)
                        else:
                            # Legacy string format - convert to object
                            # Intelligently assign speaker based on content and panel characters
                            cleaned_text = fact_id_pattern.sub('', str(line)).strip()
                            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

                            # Find the non-Dr. Hawley character in this panel (the snack)
                            snack_char = None
                            for char in panel.get('characters', []):
                                char_name = char.get('name', '').lower()
                                if 'hawley' not in char_name and 'dr.' not in char_name and 'tooth' not in char_name:
                                    snack_char = char
                                    break

                            # Determine speaker based on dialogue content
                            text_lower = cleaned_text.lower()
                            is_snack_speaking = False

                            # DEBUG: Log detection attempt
                            logger.info(f"Legacy dialogue detection: text='{cleaned_text}', snack_char={snack_char.get('name') if snack_char else None}")

                            # Lines with first-person self-references are likely the snack speaking
                            # (Dr. Hawley talks ABOUT things, snacks talk about themselves)
                            if snack_char:
                                snack_name_lower = snack_char.get('name', '').lower()
                                # Check if line is self-referential (snack introducing/defending itself)
                                # Catch ANY "I [verb]" pattern: "I trigger", "I have", "I boost", etc.
                                if text_lower.startswith("i ") or text_lower.startswith("i'") or \
                                   any(phrase in text_lower for phrase in ["but i ", "we ", "my "]):
                                    is_snack_speaking = True
                                # Check if line mentions the snack's own name
                                elif snack_name_lower and snack_name_lower in text_lower:
                                    is_snack_speaking = True

                            if is_snack_speaking and snack_char:
                                cleaned_dialogue.append({
                                    'speaker': snack_char.get('name', 'Snack'),
                                    'text': cleaned_text,
                                    'position': snack_char.get('position', 'left'),
                                    'emotion': panel.get('emotion', 'speech')
                                })
                            else:
                                # Default to Dr. Hawley
                                cleaned_dialogue.append({
                                    'speaker': 'Dr. Hawley',
                                    'text': cleaned_text,
                                    'position': 'right',
                                    'emotion': panel.get('emotion', 'speech')
                                })
                    panel['dialogue'] = cleaned_dialogue

            # Character limit validation: Truncate lines that are too long
            MAX_LINE_LENGTH = 40  # chars per line (punchy comic dialogue)
            MAX_PANEL_TOTAL = 100  # total chars per panel

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    validated_dialogue = []
                    panel_total = 0

                    for line in panel['dialogue']:
                        # Get text from object format
                        text = line.get('text', '') if isinstance(line, dict) else str(line)

                        # Truncate individual line if too long
                        if len(text) > MAX_LINE_LENGTH:
                            logger.warning(f"Truncating dialogue line from {len(text)} to {MAX_LINE_LENGTH} chars: {text[:30]}...")
                            text = text[:MAX_LINE_LENGTH-3] + "..."
                            if isinstance(line, dict):
                                line['text'] = text

                        # Check total panel character count
                        if panel_total + len(text) > MAX_PANEL_TOTAL:
                            logger.warning(f"Panel exceeds character limit, stopping at {panel_total} chars")
                            break

                        validated_dialogue.append(line)
                        panel_total += len(text)

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
        Panel 2: The Stats - Dr. Hawley impressed by health stats
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
            audience_group = "tweens"
            celebrate_goal = "the Glow Up"
            audience_care = (
                "Tweens don't care about a lecture - they care about a bright, confident smile."
            )
            snacks_label = "Glow Up Picks"
            panel3_line_1 = '- "Your smile is gonna SHINE. W."'
            panel3_line_2 = '- "That\'s main character energy fr."'
            verdicts_line = 'Verdicts: "AESTHETIC" / "GLOW UP APPROVED" / "SELFIE READY"'
            vanity_flex_line = (
                '3. VANITY FLEX: "Hollywood smile", "Main character teeth", "Selfie-ready smile"'
            )
        else:
            age_band = "13-17"
            intensity = "Savage"
            tone = "maximum hype, real recognizes real, absolute respect"
            audience_group = "teens"
            celebrate_goal = "LOOKSMAXXING"
            audience_care = "Teens don't care about \"health\" - they care about the GLOW UP."
            snacks_label = "The Looksmaxxers"
            panel3_line_1 = '- "Your smile is gonna blind people. 10/10 Aura."'
            panel3_line_2 = '- "That\'s main character energy fr."'
            verdicts_line = 'Verdicts: "AESTHETIC" / "GLOW UP APPROVED" / "10/10 AURA"'
            vanity_flex_line = '3. VANITY FLEX: "Hollywood smile", "Main character teeth", "Rizz-ready smile"'

        # Build context
        snacks_context = json.dumps(snacks, indent=2)
        facts_context = json.dumps(facts, indent=2)

        prompt = f"""You are a HYPE BEAST writing for {audience_group}. This snack is the KEY to {celebrate_goal}.

TARGET AUDIENCE: Age {age} ({age_band} - {intensity} mode), tone: {tone}

⚠️ CORE MESSAGE: This snack makes your teeth WHITE, CLEAN, and AESTHETIC.
{audience_care}

🎭 RECURRING CHARACTER - DR. HAWLEY:
He's giving out the "Glow Up" award. GENUINELY IMPRESSED - Adult Swim hype mode.
Like Rick Sanchez when he actually respects something. Peak respect energy.
Look: Off-white/pale cyan molar in dark forest green hoodie, shades on forehead, chunky beige slides, CLEAN AESTHETIC
Catchphrases:
- "Now THIS is main character energy."
- "Your teeth just won the lottery."
- "Goated. Actually goated with the sauce."
- "That's not a snack, that's a POWER MOVE."
- "W. Actual W."
{verdicts_line}

🌟 HEALTHY SNACKS ({snacks_label}):
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
- Dr. Hawley: "Wait... is that a natural filter?"
- Vibe: Aesthetic immediately detected

PANEL 2 - THE STATS (The Beauty Secrets)
- Snack reveals its beauty secrets (Natural scrubber, No stain risk)
- "It literally whitens your teeth while you eat?"
- Dr. Hawley is impressed: "So you're basically a whitening kit I can eat?" (cite fact_id)
- Visual: "Glow Up Stats" screen showing aesthetic benefits

PANEL 3 - THE GLAZE (The Hype)
- Dr. Hawley hypes up the aesthetic potential
{panel3_line_1}
{panel3_line_2}
- Mutual respect moment (cite another fact_id if available)

PANEL 4 - THE CROWN (The Glow Up Award)
- Dr. Hawley creates a frame with his hands (like taking a photo)
- "No filter needed. Your smile is already unfiltered perfection."
- Final verdict text overlay: "AESTHETIC" or "GLOW UP APPROVED"
- Sparkles, shine effects, golden hour lighting

🎨 HYPE TECHNIQUES (ADULT SWIM CELEBRATION):

1. APPEARANCE WORDS: "White", "Clean", "Bright", "Sparkling", "Unfiltered", "Immaculate"

2. ABSURDIST HYPE - Over-the-top praise that's almost as absurd as the roasts:
- "This snack is so clean, it's basically a whitening strip you can eat"
- "Your teeth just got a scholarship to Hollywood"
- "This is the dental equivalent of getting verified"

3. QUOTABLE HYPE:
- "Goated. Actually goated with the sauce."
- "W. Actual W."
- "That's main character energy, unironically."
- "Your dentist just sent a thank you card."

{vanity_flex_line}
5. VISUAL GLOW: Sparkles, shine effects, pristine white, golden hour lighting

	⚠️ CRITICAL RULES FOR FACT CITATIONS:
	- citation_ids field = ONLY fact IDs like ["F025", "F027"]
	- dialogue field = ONLY what characters SAY - NEVER include fact IDs in dialogue
	- The dialogue should naturally incorporate the fact's content WITHOUT mentioning the ID

	⚠️ CRITICAL DIALOGUE FORMAT:
	Each dialogue line MUST be an object with:
	- "speaker": Character name (MUST match a character in the panel)
	- "text": The dialogue text (under 40 characters)
	- "position": "left", "center", or "right" (match character position)
	- "emotion": "speech", "thought", "exclaim", "angry", or "whisper"

	📝 OTHER RULES:
	- Every panel should feel like a W (win)
	- Keep dialogue SHORT and PUNCHY: Max 2-3 lines per panel
	- If a panel includes BOTH the snack and Dr. Hawley, give EACH one a line
	- CRITICAL TEXT LIMITS: Each dialogue line must be under 40 characters, total per panel under 100 characters
	- Expressions: impressed, respectful, hyped, triumphant, nodding
	- Props: green hoodie, shades on forehead, beige slides, gold chains, trophy, stat screens
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
	      "dialogue": [
	        {{"speaker": "Crunchy Apple Chad", "text": "I'm basically a snack-sized whitening strip.", "position": "left", "emotion": "speech"}},
	        {{"speaker": "Dr. Hawley", "text": "No filter needed. That's a W.", "position": "right", "emotion": "speech"}}
	      ],
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
          "name": "Dr. Hawley",
          "item_id": "recurring_tooth",
          "expression": "impressed",
          "position": "right",
          "props": ["green hoodie", "shades on forehead", "beige slides", "gold chains", "clean white shine"]
        }}
      ],
      "visual_prompt": "Glowing apple character with sparkles enters scene. Off-white molar in green hoodie looks impressed, shades on forehead. Golden hour lighting, aesthetic vibes.",
      "background": "bright, clean, aesthetic setting with sparkle effects"
    }}
    // ... panels 2-4 with emotion: "exclaim", "speech", "exclaim" respectively
  ],
  "summary_caption": "A beauty-focused verdict (under 100 chars) - e.g. 'Glow Up Approved. No filter needed.'",
  "alt_text": "Accessibility description (1-2 sentences)"
}}

📚 FEW-SHOT CELEBRATION EXAMPLES (Copy this hype energy):

EXAMPLE 1 - Fresh Apple:
Dr. Hawley: "Wait... is that an APPLE?"
Dr. Hawley: "That thing scrubs your teeth WHITE while you eat it."
Dr. Hawley: "It's literally a crunchy whitening strip you can snack on."
Dr. Hawley: "Goated. Actually goated with the sauce. No notes."

EXAMPLE 2 - Cheese:
Dr. Hawley: "Cheese? Oh, you're built different."
Dr. Hawley: "That neutralizes acid AND has calcium. Double buff."
Dr. Hawley: "Your teeth are sending you a thank you card."
Dr. Hawley: "Main character energy. Unironically."

EXAMPLE 3 - Carrots:
Dr. Hawley: "Carrots? The OG glow up snack."
Dr. Hawley: "Crunchy enough to scrub, vitamins for that natural shine."
Dr. Hawley: "Your smile just got a scholarship to Hollywood."
Dr. Hawley: "W. Actual W."

	NOW hype up these healthy snacks with this energy. Make it about the GLOW UP. Make teens want that Hollywood smile."""

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
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=self.settings.gemini_writer_thinking_budget  # Max thinking for script writing
                    ),
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

            # Extract JSON from markdown code blocks or prefixed text
            response_text = self._extract_json(response_text)

            # Handle any remaining markdown code block markers
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

            # Safety filter: Remove any fact IDs that slipped into dialogue
            import re

            fact_id_pattern = re.compile(r'\[?F\d{3,4}\]?|\(F\d{3,4}\)')

            # Process dialogue - handle both new object format and legacy string format
            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    cleaned_dialogue = []
                    for line in panel['dialogue']:
                        # Handle new object format: {speaker, text, position, emotion}
                        if isinstance(line, dict):
                            text = line.get('text', '')
                            # Remove fact IDs from text
                            cleaned_text = fact_id_pattern.sub('', text).strip()
                            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                            line['text'] = cleaned_text

                            # Set default emotion based on panel if missing/invalid
                            if 'emotion' not in line or line.get('emotion') not in (
                                'speech', 'thought', 'exclaim', 'angry', 'whisper'
                            ):
                                line['emotion'] = panel.get('emotion', 'speech')

                            # Set default position based on speaker if not provided
                            # Dr. Hawley is always on the right, snacks/other characters on the left
                            if 'position' not in line or line.get('position') not in ('left', 'right', 'center'):
                                speaker = line.get('speaker', '').lower()
                                if 'hawley' in speaker or 'dr.' in speaker or 'tooth' in speaker:
                                    line['position'] = 'right'
                                else:
                                    line['position'] = 'left'

                            cleaned_dialogue.append(line)
                        else:
                            # Legacy string format - convert to object
                            cleaned_text = fact_id_pattern.sub('', str(line)).strip()
                            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

                            # Find the non-Dr. Hawley character in this panel (the snack)
                            snack_char = None
                            for char in panel.get('characters', []):
                                char_name = char.get('name', '').lower()
                                if 'hawley' not in char_name and 'tooth' not in char_name:
                                    snack_char = char
                                    break

                            # Heuristic: snack talks about itself; Dr. Hawley talks about the snack
                            text_lower = cleaned_text.lower()
                            is_snack_speaking = False
                            if snack_char:
                                snack_name_lower = snack_char.get('name', '').lower()
                                # Catch ANY "I [verb]" pattern: "I trigger", "I have", "I boost", etc.
                                if text_lower.startswith("i ") or text_lower.startswith("i'") or \
                                   any(phrase in text_lower for phrase in ["but i ", "we ", "my "]):
                                    is_snack_speaking = True
                                elif snack_name_lower and snack_name_lower in text_lower:
                                    is_snack_speaking = True

                            if is_snack_speaking and snack_char:
                                cleaned_dialogue.append({
                                    'speaker': snack_char.get('name', 'Snack'),
                                    'text': cleaned_text,
                                    'position': snack_char.get('position', 'left'),
                                    'emotion': panel.get('emotion', 'speech')
                                })
                            else:
                                cleaned_dialogue.append({
                                    'speaker': 'Dr. Hawley',
                                    'text': cleaned_text,
                                    'position': 'right',
                                    'emotion': panel.get('emotion', 'speech')
                                })
                    panel['dialogue'] = cleaned_dialogue

            # Character limit validation (punchy comic dialogue)
            MAX_LINE_LENGTH = 40
            MAX_PANEL_TOTAL = 100

            for panel in result.get('panels', []):
                if 'dialogue' in panel:
                    validated_dialogue = []
                    panel_total = 0

                    for line in panel['dialogue']:
                        # Get text from object format
                        text = line.get('text', '') if isinstance(line, dict) else str(line)

                        # Truncate individual line if too long
                        if len(text) > MAX_LINE_LENGTH:
                            logger.warning(
                                f"Truncating dialogue line from {len(text)} to {MAX_LINE_LENGTH} chars"
                            )
                            text = text[:MAX_LINE_LENGTH-3] + "..."
                            if isinstance(line, dict):
                                line['text'] = text

                        # Check total panel character count
                        if panel_total + len(text) > MAX_PANEL_TOTAL:
                            logger.warning(
                                f"Panel exceeds character limit, stopping at {panel_total} chars"
                            )
                            break

                        validated_dialogue.append(line)
                        panel_total += len(text)

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

        Provides general appearance/glow-up tips with DR. HAWLEY character.
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
                    "title": "Dr. Hawley Enters",
                    "dialogue": [
                        "Yo. Dr. Hawley here.",
                        "Let me drop some glow up secrets."
                    ],
                    "emotion": "speech",
                    "citation_ids": [],
                    "characters": [
                        {
                            "name": "Dr. Hawley",
                            "item_id": "recurring_tooth",
                            "expression": "cool",
                            "position": "center",
                            "props": ["green hoodie", "shades on forehead", "beige slides", "gold chains", "clean white shine"]
                        }
                    ],
                    "visual_prompt": f"Off-white molar in dark green hoodie, shades on forehead, beige slides in {tone_adj} style, literally glowing, looking directly at viewer",
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
                            "name": "Dr. Hawley",
                            "item_id": "recurring_tooth",
                            "expression": "smug",
                            "position": "left",
                            "props": ["green hoodie", "shades on forehead", "toothbrush sword", "sparkle effect"]
                        }
                    ],
                    "visual_prompt": "Off-white molar in green hoodie wielding toothbrush like a sword, shades on forehead, teeth literally sparkling, dramatic pose",
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
                            "name": "Dr. Hawley",
                            "item_id": "recurring_tooth",
                            "expression": "nodding",
                            "position": "right",
                            "props": ["green hoodie", "shades on forehead", "water bottle", "clean white shine"]
                        }
                    ],
                    "visual_prompt": "Off-white molar in green hoodie holding water bottle, shades on forehead, refreshing sparkle effects around the smile",
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
                            "name": "Dr. Hawley",
                            "item_id": "recurring_tooth",
                            "expression": "triumphant",
                            "position": "center",
                            "props": ["green hoodie", "shades on forehead", "beige slides", "peace sign", "sparkle effects"]
                        }
                    ],
                    "visual_prompt": "Off-white molar in green hoodie doing peace sign, shades on forehead, beige slides, walking away with sparkles",
                    "background": "golden hour lighting with aesthetic glow"
                }
            ],
            "summary_caption": "Dr. Hawley drops the glow up secrets. No filter needed.",
            "alt_text": "A 4-panel comic featuring Dr. Hawley, an off-white molar in a green hoodie with shades on forehead, sharing appearance tips about keeping teeth white and aesthetic."
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
