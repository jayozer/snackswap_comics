"""Swap data models for Qdrant swaps_v1 collection."""

from typing import Literal

from pydantic import BaseModel, Field


class SwapPayload(BaseModel):
    """Payload structure for swaps_v1 Qdrant collection."""

    swap_id: str = Field(..., description="Unique swap identifier")
    name: str = Field(..., description="Swap name (e.g., 'Plain yogurt + berries')")
    category: str = Field(..., description="Category (e.g., dairy, fruit, veggie)")
    flavor_notes: list[str] = Field(
        default_factory=list, description="Flavor descriptors (creamy, sweet-tart)"
    )

    # Nutritional
    sugar_g_per_100g: float = Field(0.0, description="Total sugar grams per 100g")
    added_sugar_g: float = Field(0.0, description="Added sugar grams per 100g")

    # Dental factors (same as snacks)
    acidity_tag: Literal["low", "medium", "high"] = Field("low", description="Acidity level")
    stickiness: float = Field(0.0, ge=0.0, le=1.0, description="Stickiness (0-1)")
    residue: float = Field(0.0, ge=0.0, le=1.0, description="Residue (0-1)")
    water_content: float = Field(0.0, ge=0.0, le=1.0, description="Water content (0-1)")

    # Safety
    allergy_tags: list[str] = Field(
        default_factory=list, description="Allergen tags (dairy, nuts, gluten)"
    )

    # Taste clustering
    taste_cluster: str = Field("neutral", description="Taste cluster for matching")

    # Practical info
    prep_time: str = Field("0", description="Prep time (0, <5min, 5-15min)")
    suitability: dict[str, bool] = Field(
        default_factory=dict, description="Age band suitability (9-12, 13-17)"
    )
    example_brands: list[str] = Field(
        default_factory=list, description="Example brands (for Maps queries)"
    )

    # Metadata
    popularity_score: float = Field(
        0.5, ge=0.0, le=1.0, description="User acceptance/click-through score"
    )


class Swap(BaseModel):
    """Full swap model with vector embedding."""

    id: str = Field(..., description="Qdrant point ID")
    vector: list[float] = Field(..., description="Embedding vector")
    payload: SwapPayload = Field(..., description="Swap metadata")

    @property
    def dental_risk_score(self) -> float:
        """
        Calculate dental risk score (same formula as snacks).
        """
        sugar_norm = min(self.payload.added_sugar_g / 50.0, 1.0)
        acidity_map = {"low": 0.1, "medium": 0.5, "high": 1.0}
        acidity_factor = acidity_map.get(self.payload.acidity_tag, 0.1)

        risk = 100 * (
            0.45 * sugar_norm
            + 0.20 * acidity_factor
            + 0.20 * self.payload.stickiness
            + 0.10 * self.payload.residue
            + 0.05 * 0.0  # swaps typically don't have crunch_hardness
        )

        return round(risk, 2)

    def is_suitable_for_age(self, age_band: str) -> bool:
        """Check if swap is suitable for the given age band."""
        return self.payload.suitability.get(age_band, True)

    def has_allergens(self, allergens: list[str]) -> bool:
        """Check if swap contains any of the specified allergens."""
        return any(allergen in self.payload.allergy_tags for allergen in allergens)
