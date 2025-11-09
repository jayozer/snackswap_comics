"""Snack data models for Qdrant snacks_v1 collection."""

from typing import Literal

from pydantic import BaseModel, Field


class AgeFlags(BaseModel):
    """Age-specific flags and considerations for a snack."""

    choking_risk: bool = Field(False, description="Choking hazard for this age group")
    notes: str | None = Field(None, description="Age-specific guidance")


class SnackPayload(BaseModel):
    """Payload structure for snacks_v1 Qdrant collection."""

    snack_id: str = Field(..., description="Unique snack identifier")
    name: str = Field(..., description="Snack name")
    brand: str | None = Field(None, description="Brand name")
    category: str = Field(..., description="Category (e.g., chips, candy, fruit)")
    flavor_notes: list[str] = Field(
        default_factory=list, description="Flavor descriptors (salty, sweet, tangy)"
    )

    # Nutritional
    sugar_g_per_100g: float = Field(0.0, description="Total sugar grams per 100g")
    added_sugar_g: float = Field(0.0, description="Added sugar grams per 100g")

    # Dental factors
    acidity_tag: Literal["low", "medium", "high"] = Field(
        "low", description="Acidity level affecting enamel"
    )
    stickiness: float = Field(0.0, ge=0.0, le=1.0, description="How sticky (0-1)")
    residue: float = Field(
        0.0, ge=0.0, le=1.0, description="Residue clinging to teeth grooves (0-1)"
    )
    crunch_hardness: float = Field(
        0.0, ge=0.0, le=1.0, description="Crunch/hardness that can irritate gums (0-1)"
    )
    water_content: float = Field(0.0, ge=0.0, le=1.0, description="Water content (0-1)")

    # Serving
    typical_portion_g: float = Field(30.0, description="Typical portion size in grams")

    # Safety
    age_flags: dict[str, AgeFlags] = Field(
        default_factory=dict, description="Age-specific flags (<5, 5-8, 9-12)"
    )
    allergy_tags: list[str] = Field(
        default_factory=list, description="Allergen tags (dairy, nuts, gluten)"
    )

    # Taste clustering
    taste_cluster: str = Field("neutral", description="Taste cluster (e.g., savory-crunch)")

    # Media
    images: list[str] = Field(default_factory=list, description="Image URIs")


class Snack(BaseModel):
    """Full snack model with vector embedding."""

    id: str = Field(..., description="Qdrant point ID")
    vector: list[float] = Field(..., description="Embedding vector")
    payload: SnackPayload = Field(..., description="Snack metadata")

    @property
    def dental_risk_score(self) -> float:
        """
        Calculate dental risk score (0-100, higher = riskier).

        Formula:
        risk = 100 * (
          0.45 * norm(added_sugar_g_per_100g) +
          0.20 * acidity_factor +
          0.20 * stickiness +
          0.10 * residue +
          0.05 * crunch_hardness
        )
        """
        # Normalize added sugar (assuming max ~50g/100g for worst offenders)
        sugar_norm = min(self.payload.added_sugar_g / 50.0, 1.0)

        # Acidity factor
        acidity_map = {"low": 0.1, "medium": 0.5, "high": 1.0}
        acidity_factor = acidity_map.get(self.payload.acidity_tag, 0.1)

        risk = 100 * (
            0.45 * sugar_norm
            + 0.20 * acidity_factor
            + 0.20 * self.payload.stickiness
            + 0.10 * self.payload.residue
            + 0.05 * self.payload.crunch_hardness
        )

        return round(risk, 2)
