"""
Query builder for context-aware Qdrant searches.
Enriches queries with panel context and snack traits for better fact matching.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Builds context-enriched query strings for embedding generation."""

    # Mood-specific keywords for query augmentation
    MOOD_KEYWORDS = {
        "funny": "fun fact, surprising, amusing",
        "dramatic": "serious consequence, warning, danger",
        "educational": "learning, science, explanation",
        "celebratory": "positive, healthy, good choice, celebration",
    }

    # Narrative beat keywords for query augmentation
    BEAT_KEYWORDS = {
        "intro": "introduction, discovery",
        "conflict": "problem, consequence, risk",
        "revelation": "surprise, revelation, science",
        "resolution": "solution, recommendation, tip",
    }

    @staticmethod
    def build_fact_query(
        snack_category: str,
        snack_traits: list[str] | None = None,
        panel_context: Optional[dict] = None,
    ) -> str:
        """
        Build a fact search query enriched with panel context.

        Args:
            snack_category: Category of detected snack (candy, chips, fruit, etc.)
            snack_traits: Risk traits from snack (sticky, sugary, acidic, hard)
            panel_context: Optional panel mood/scene context

        Returns:
            Query string optimized for fact retrieval
        """
        base_query = f"dental health, {snack_category}"

        # Add snack traits for targeted facts
        if snack_traits:
            trait_terms = []
            for trait in snack_traits:
                if trait == "sticky":
                    trait_terms.append("sticky residue teeth")
                elif trait == "sugary":
                    trait_terms.append("sugar bacteria cavity")
                elif trait == "acidic":
                    trait_terms.append("acid enamel erosion")
                elif trait == "hard":
                    trait_terms.append("hard crunchy teeth damage")
            if trait_terms:
                base_query += f", {', '.join(trait_terms)}"

        # Add panel context if provided
        if panel_context:
            mood = panel_context.get("mood", "educational")
            beat = panel_context.get("narrative_beat", "")

            # Add mood keywords
            if mood in QueryBuilder.MOOD_KEYWORDS:
                base_query += f", {QueryBuilder.MOOD_KEYWORDS[mood]}"

            # Add narrative beat keywords
            if beat in QueryBuilder.BEAT_KEYWORDS:
                base_query += f", {QueryBuilder.BEAT_KEYWORDS[beat]}"

        logger.debug(f"Built fact query: {base_query}")
        return base_query

    @staticmethod
    def build_celebrate_query(
        snack_category: str,
        health_benefits: list[str] | None = None,
    ) -> str:
        """
        Build a query for celebration facts about healthy snacks.

        Args:
            snack_category: Category of detected snack (fruit, vegetable, dairy, etc.)
            health_benefits: Health benefits of the snack

        Returns:
            Query string optimized for celebration fact retrieval
        """
        base_query = f"healthy teeth, {snack_category}, positive dental benefits"

        if health_benefits:
            # Extract key benefit themes
            benefit_themes = []
            for benefit in health_benefits[:2]:  # Use top 2 benefits
                if "calcium" in benefit.lower():
                    benefit_themes.append("calcium strong teeth")
                elif "saliva" in benefit.lower():
                    benefit_themes.append("saliva protection")
                elif "fiber" in benefit.lower() or "crunchy" in benefit.lower():
                    benefit_themes.append("natural cleaning crunchy")
                elif "water" in benefit.lower():
                    benefit_themes.append("high water content cleaning")

            if benefit_themes:
                base_query += f", {', '.join(benefit_themes)}"

        logger.debug(f"Built celebrate query: {base_query}")
        return base_query

    @staticmethod
    def build_snack_query(
        detected_name: str,
        brand_guess: str | None,
        category: str,
    ) -> str:
        """
        Build a snack search query.

        Args:
            detected_name: Name detected by vision
            brand_guess: Guessed brand name
            category: Snack category

        Returns:
            Query string for snack matching
        """
        return f"brand={brand_guess or 'generic'}, type={category}, name={detected_name}"
