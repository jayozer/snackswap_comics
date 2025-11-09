"""Style data models for Qdrant styles_v1 collection."""

from pydantic import BaseModel, Field


class StylePayload(BaseModel):
    """Payload structure for styles_v1 Qdrant collection."""

    style_id: str = Field(..., description="Unique style identifier (e.g., clinic_style_v3)")
    name: str = Field(..., description="Style name")

    # Visual identity
    palette: dict[str, str] = Field(
        default_factory=dict,
        description="Color palette (primary, secondary, background, text, accent)",
    )
    fonts: dict[str, str] = Field(
        default_factory=dict, description="Font pairings (title, dialogue, caption)"
    )

    # Comic styling
    bubble_style: str = Field("rounded", description="Speech bubble style (rounded, sharp, wavy)")
    frame_style: str = Field("clean", description="Panel frame style (clean, sketchy, bold)")

    # Branding
    logo_uri: str | None = Field(None, description="Clinic logo URI")
    mascot_uri: str | None = Field(None, description="Optional mascot character URI")
    watermark_uri: str | None = Field(None, description="Optional watermark URI")

    # Layout preferences
    panel_layout: str = Field("2x2", description="Panel layout (2x2, 1x4, custom)")
    min_font_size_pt: int = Field(15, description="Minimum font size for mobile readability")
    safe_margin_px: int = Field(64, description="Safe margin in pixels")

    # Metadata
    created_by: str | None = Field(None, description="Creator ID")
    is_default: bool = Field(False, description="Whether this is the default style")


class Style(BaseModel):
    """Full style model with vector embedding."""

    id: str = Field(..., description="Qdrant point ID")
    vector: list[float] = Field(..., description="Embedding vector for style similarity")
    payload: StylePayload = Field(..., description="Style metadata")

    def get_color(self, key: str, default: str = "#000000") -> str:
        """Get a color from the palette with a fallback."""
        return self.payload.palette.get(key, default)

    def get_font(self, key: str, default: str = "Arial") -> str:
        """Get a font from the font pairings with a fallback."""
        return self.payload.fonts.get(key, default)
