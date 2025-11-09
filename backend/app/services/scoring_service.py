"""
Scoring and matching service for SnackSwap Comics.
Handles dental risk calculation and swap recommendations.
"""

import logging
from typing import Any

from app.models import DetectedItem, ScoredItem

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring snacks and matching swaps."""

    MIN_RISK_IMPROVEMENT = 25.0  # Minimum risk score improvement for swaps (percentage points)

    def __init__(self):
        """Initialize scoring service."""
        logger.info("Initialized scoring service")

    def calculate_dental_risk(self, snack_payload: dict[str, Any]) -> float:
        """
        Calculate dental risk score (0-100, higher = riskier).

        Formula from PRD:
        risk = 100 * (
          0.45 * norm(added_sugar_g_per_100g) +
          0.20 * acidity_factor +
          0.20 * stickiness +
          0.10 * residue +
          0.05 * crunch_hardness
        )

        Args:
            snack_payload: Snack payload dictionary

        Returns:
            Dental risk score (0-100)
        """
        # Extract values with defaults
        added_sugar_g = snack_payload.get("added_sugar_g", 0.0)
        acidity_tag = snack_payload.get("acidity_tag", "low")
        stickiness = snack_payload.get("stickiness", 0.0)
        residue = snack_payload.get("residue", 0.0)
        crunch_hardness = snack_payload.get("crunch_hardness", 0.0)

        # Normalize added sugar (assuming max ~50g/100g for worst offenders)
        sugar_norm = min(added_sugar_g / 50.0, 1.0)

        # Acidity factor
        acidity_map = {"low": 0.1, "medium": 0.5, "high": 1.0}
        acidity_factor = acidity_map.get(acidity_tag, 0.1)

        # Calculate risk
        risk = 100 * (
            0.45 * sugar_norm
            + 0.20 * acidity_factor
            + 0.20 * stickiness
            + 0.10 * residue
            + 0.05 * crunch_hardness
        )

        return round(risk, 2)

    def rank_swaps(
        self,
        original_snack: dict[str, Any],
        swap_candidates: list[dict[str, Any]],
        age_band: str,
        allergies: list[str],
    ) -> list[dict[str, Any]]:
        """
        Rank swap candidates by suitability.

        Ranking criteria:
        1. Risk improvement (must be >= MIN_RISK_IMPROVEMENT)
        2. Taste cluster match (prefer same cluster)
        3. No allergens
        4. Age suitability
        5. Popularity score
        6. Prep time (shorter is better)

        Args:
            original_snack: Original snack data
            swap_candidates: List of potential swaps
            age_band: Target age band (3-5, 6-8, 9-12)
            allergies: List of allergens to avoid

        Returns:
            Ranked list of suitable swaps
        """
        original_risk = self.calculate_dental_risk(original_snack)
        original_cluster = original_snack.get("taste_cluster", "neutral")

        ranked_swaps = []

        for swap in swap_candidates:
            # Calculate risk improvement
            swap_risk = self.calculate_dental_risk(swap)
            risk_improvement = original_risk - swap_risk

            # Skip if improvement is insufficient
            if risk_improvement < self.MIN_RISK_IMPROVEMENT:
                continue

            # Check allergens
            swap_allergens = swap.get("allergy_tags", [])
            has_allergen = any(allergen in swap_allergens for allergen in allergies)
            if has_allergen:
                continue

            # Check age suitability
            suitability = swap.get("suitability", {})
            if not suitability.get(age_band, True):
                continue

            # Calculate taste cluster match bonus
            swap_cluster = swap.get("taste_cluster", "neutral")
            taste_match_bonus = 20.0 if swap_cluster == original_cluster else 0.0

            # Prep time penalty (shorter is better)
            prep_time = swap.get("prep_time", "0")
            prep_penalty = 0.0
            if prep_time == "<5min":
                prep_penalty = 2.0
            elif prep_time == "5-15min":
                prep_penalty = 5.0

            # Popularity bonus
            popularity = swap.get("popularity_score", 0.5)
            popularity_bonus = popularity * 10.0

            # Calculate total score
            score = risk_improvement + taste_match_bonus + popularity_bonus - prep_penalty

            ranked_swaps.append(
                {
                    **swap,
                    "risk_improvement": risk_improvement,
                    "swap_risk_score": swap_risk,
                    "ranking_score": score,
                }
            )

        # Sort by ranking score (descending)
        ranked_swaps.sort(key=lambda x: x["ranking_score"], reverse=True)

        logger.info(
            f"Ranked {len(ranked_swaps)} suitable swaps "
            f"(from {len(swap_candidates)} candidates) "
            f"for risk={original_risk:.1f}"
        )

        return ranked_swaps

    def match_snack_to_payload(
        self,
        detected_item: DetectedItem,
        search_results: list[Any],
    ) -> dict[str, Any] | None:
        """
        Match a detected item to Qdrant search results.

        Args:
            detected_item: Detected item from vision
            search_results: Qdrant search results (ScoredPoints)

        Returns:
            Best matching snack payload with match confidence, or None
        """
        if not search_results:
            return None

        # For now, take the top result
        # In production, could add more sophisticated matching logic
        top_result = search_results[0]

        # Combine detection confidence with search score
        search_score = top_result.score
        combined_confidence = (detected_item.confidence + search_score) / 2.0

        # Return payload with added metadata
        payload = dict(top_result.payload)
        payload["match_confidence"] = round(combined_confidence, 3)
        payload["search_score"] = round(search_score, 3)
        payload["detected_name"] = detected_item.name
        payload["detected_brand"] = detected_item.brand_guess

        return payload

    def get_age_band(self, age: int) -> str:
        """Convert age to age band string."""
        if age <= 5:
            return "3-5"
        elif age <= 8:
            return "6-8"
        else:
            return "9-12"
