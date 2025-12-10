"""
Content guardrails service for SnackSwap Comics.
Handles profanity filtering, content validation, and safety checks for teen content.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentRating(Enum):
    """Content safety rating levels."""
    SAFE = "safe"
    MILD = "mild"  # Borderline but acceptable for teens
    BLOCKED = "blocked"  # Contains prohibited content


@dataclass
class ValidationResult:
    """Result of content validation."""
    passed: bool
    rating: ContentRating
    flagged_terms: list[str]
    cleaned_content: str | None  # Content with problematic terms removed/replaced
    details: str


class GuardrailsService:
    """Service for content safety validation and filtering."""

    # Explicit profanity - always blocked
    BLOCKED_TERMS = {
        # Explicit profanity (common variations)
        "fuck", "fucking", "fucked", "fucker", "fck", "f*ck", "f**k",
        "shit", "shitting", "sh*t", "sh1t",
        "bitch", "b*tch", "b1tch",
        "ass", "asshole", "a**", "a$$",
        "damn", "damned",
        "cunt", "c*nt",
        "dick", "d*ck", "d1ck",
        "cock", "c*ck",
        "pussy", "p*ssy",
        "whore", "wh*re",
        "slut", "sl*t",
        # Slurs (racial, ethnic, etc.) - zero tolerance
        "nigger", "nigga", "n*gga", "n-word",
        "faggot", "fag", "f*g",
        "retard", "retarded", "r*tard",
        "spic", "chink", "gook", "kike",
        "tranny", "tr*nny",
        # Drug references
        "cocaine", "heroin", "meth", "crack",
        "weed", "marijuana", "420", "blunt",
        # Sexual content
        "sex", "sexual", "porn", "nude", "naked",
        "horny", "orgasm", "masturbate",
        # Violence
        "kill", "murder", "suicide", "die",
        "rape", "molest",
    }

    # Mild terms - allowed but logged for review
    MILD_TERMS = {
        "stupid", "dumb", "idiot", "moron",
        "ugly", "fat", "skinny",
        "loser", "lame", "sucks",
        "hate", "hater", "hating",
        "cringe", "sus", "cap",  # Teen slang - OK
        "cooked", "mid", "trash", "ratio",  # Roast terms - OK for our context
    }

    # Replacement patterns for auto-cleaning
    REPLACEMENTS = {
        r"\bass\b": "butt",
        r"\bdamn\b": "dang",
        r"\bhell\b": "heck",
        r"\bsucks\b": "stinks",
    }

    def __init__(self):
        """Initialize the guardrails service."""
        # Compile regex patterns for efficiency
        self._blocked_pattern = self._build_pattern(self.BLOCKED_TERMS)
        self._mild_pattern = self._build_pattern(self.MILD_TERMS)
        logger.info("Initialized GuardrailsService with %d blocked terms", len(self.BLOCKED_TERMS))

    def _build_pattern(self, terms: set[str]) -> re.Pattern:
        """Build a compiled regex pattern from a set of terms."""
        # Escape special regex characters and join with OR
        escaped = [re.escape(term) for term in terms]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)

    def validate_text(self, text: str, auto_clean: bool = False) -> ValidationResult:
        """
        Validate text content for prohibited terms.

        Args:
            text: The text to validate
            auto_clean: If True, attempt to clean mild issues

        Returns:
            ValidationResult with pass/fail status and details
        """
        if not text:
            return ValidationResult(
                passed=True,
                rating=ContentRating.SAFE,
                flagged_terms=[],
                cleaned_content=text,
                details="Empty content"
            )

        text_lower = text.lower()
        flagged_blocked = []
        flagged_mild = []

        # Check for blocked terms
        blocked_matches = self._blocked_pattern.findall(text_lower)
        if blocked_matches:
            flagged_blocked = list(set(blocked_matches))
            logger.warning("Blocked content detected: %s", flagged_blocked)
            return ValidationResult(
                passed=False,
                rating=ContentRating.BLOCKED,
                flagged_terms=flagged_blocked,
                cleaned_content=None,
                details=f"Prohibited terms found: {', '.join(flagged_blocked)}"
            )

        # Check for mild terms (allowed but logged)
        mild_matches = self._mild_pattern.findall(text_lower)
        if mild_matches:
            flagged_mild = list(set(mild_matches))
            logger.info("Mild content detected (allowed): %s", flagged_mild)

        # Auto-clean if requested
        cleaned = text
        if auto_clean:
            for pattern, replacement in self.REPLACEMENTS.items():
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        rating = ContentRating.MILD if flagged_mild else ContentRating.SAFE

        return ValidationResult(
            passed=True,
            rating=rating,
            flagged_terms=flagged_mild,
            cleaned_content=cleaned if auto_clean else text,
            details="Content passed validation" + (f" (mild terms: {flagged_mild})" if flagged_mild else "")
        )

    def validate_script(self, script: dict, auto_clean: bool = True) -> ValidationResult:
        """
        Validate an entire comic script.

        Args:
            script: The comic script dictionary with panels
            auto_clean: If True, attempt to clean mild issues in dialogue

        Returns:
            ValidationResult for the entire script
        """
        all_flagged = []
        has_blocked = False
        cleaned_script = script.copy()

        # Extract and validate all dialogue
        panels = script.get("panels", [])
        cleaned_panels = []

        for panel in panels:
            panel_copy = panel.copy()
            dialogue_lines = panel.get("dialogue", [])
            cleaned_dialogue = []

            for line in dialogue_lines:
                result = self.validate_text(line, auto_clean=auto_clean)

                if result.rating == ContentRating.BLOCKED:
                    has_blocked = True
                    all_flagged.extend(result.flagged_terms)
                    logger.error("Blocked content in panel %s: %s",
                                 panel.get("panel_number"), result.flagged_terms)
                    # For blocked content, we don't include in cleaned version
                    cleaned_dialogue.append("[CONTENT REMOVED]")
                else:
                    all_flagged.extend(result.flagged_terms)
                    cleaned_dialogue.append(result.cleaned_content or line)

            panel_copy["dialogue"] = cleaned_dialogue
            cleaned_panels.append(panel_copy)

        cleaned_script["panels"] = cleaned_panels

        # Also validate summary caption and alt text
        for field in ["summary_caption", "alt_text"]:
            if field in script:
                result = self.validate_text(script[field], auto_clean=auto_clean)
                if result.rating == ContentRating.BLOCKED:
                    has_blocked = True
                    all_flagged.extend(result.flagged_terms)
                    cleaned_script[field] = "[CONTENT REMOVED]"
                else:
                    all_flagged.extend(result.flagged_terms)
                    cleaned_script[field] = result.cleaned_content or script[field]

        unique_flagged = list(set(all_flagged))

        if has_blocked:
            return ValidationResult(
                passed=False,
                rating=ContentRating.BLOCKED,
                flagged_terms=unique_flagged,
                cleaned_content=None,
                details=f"Script contains prohibited content: {unique_flagged}"
            )

        rating = ContentRating.MILD if unique_flagged else ContentRating.SAFE

        return ValidationResult(
            passed=True,
            rating=rating,
            flagged_terms=unique_flagged,
            cleaned_content=cleaned_script,
            details="Script passed validation" + (f" (mild terms logged)" if unique_flagged else "")
        )

    def validate_image_prompt(self, prompt: str) -> ValidationResult:
        """
        Validate an image generation prompt for safety.

        Args:
            prompt: The image generation prompt

        Returns:
            ValidationResult for the prompt
        """
        # Additional image-specific blocked terms
        image_blocked = {
            "nude", "naked", "sexy", "seductive",
            "violence", "gore", "blood", "weapon",
            "drug", "alcohol", "cigarette", "vape",
            "gun", "knife", "bomb",
        }

        # Check standard terms first
        result = self.validate_text(prompt, auto_clean=False)
        if not result.passed:
            return result

        # Check image-specific terms
        prompt_lower = prompt.lower()
        for term in image_blocked:
            if term in prompt_lower:
                logger.warning("Image prompt contains blocked term: %s", term)
                return ValidationResult(
                    passed=False,
                    rating=ContentRating.BLOCKED,
                    flagged_terms=[term],
                    cleaned_content=None,
                    details=f"Image prompt contains prohibited term: {term}"
                )

        return result


# Singleton instance
_guardrails_service: GuardrailsService | None = None


def get_guardrails_service() -> GuardrailsService:
    """Get or create the guardrails service singleton."""
    global _guardrails_service
    if _guardrails_service is None:
        _guardrails_service = GuardrailsService()
    return _guardrails_service
