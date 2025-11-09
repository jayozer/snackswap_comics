"""Fact data models for Qdrant facts_v1 collection."""

from pydantic import BaseModel, Field


class FactPayload(BaseModel):
    """Payload structure for facts_v1 Qdrant collection."""

    fact_id: str = Field(..., description="Unique fact identifier (e.g., F031)")
    text: str = Field(..., description="The factual statement (kid-friendly)")
    topic: list[str] = Field(
        default_factory=list,
        description="Topics (sugar, acidity, stickiness, timing, brushing)",
    )
    age_band: str = Field("all", description="Target age band (3-5, 6-8, 9-12, all)")

    # Provenance
    source_key: str = Field(..., description="Source identifier (e.g., ClinicKB#SugarChildren)")
    source_url: str | None = Field(None, description="Link to source material")
    reviewed_by: str | None = Field(None, description="Reviewer name/ID")
    clinic_approved: bool = Field(True, description="Approved by clinic for use")

    # Metadata
    created_at: str | None = Field(None, description="ISO 8601 timestamp")
    updated_at: str | None = Field(None, description="ISO 8601 timestamp")


class Fact(BaseModel):
    """Full fact model with vector embedding."""

    id: str = Field(..., description="Qdrant point ID")
    vector: list[float] = Field(..., description="Embedding vector")
    payload: FactPayload = Field(..., description="Fact metadata")

    def matches_age(self, age: int) -> bool:
        """Check if fact is suitable for the given age."""
        if self.payload.age_band == "all":
            return True

        age_ranges = {
            "3-5": (3, 5),
            "6-8": (6, 8),
            "9-12": (9, 12),
        }

        if self.payload.age_band in age_ranges:
            min_age, max_age = age_ranges[self.payload.age_band]
            return min_age <= age <= max_age

        return True

    def format_citation(self) -> str:
        """Format a gentle citation for the fact."""
        if self.payload.source_url:
            return f"[{self.payload.fact_id}]({self.payload.source_url})"
        return f"[{self.payload.fact_id}]"
