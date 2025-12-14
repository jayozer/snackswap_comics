"""Comic and panel data models."""

from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    """Single line of dialogue with speaker attribution."""

    speaker: str = Field(..., description="Character name who speaks this line (e.g., 'Dr. Drip')")
    text: str = Field(..., description="The dialogue text")
    position: str = Field("center", description="Speaker position for bubble tail (left, center, right)")
    emotion: str = Field("speech", description="Bubble emotion style (speech, thought, exclaim, angry, whisper)")


class CharacterNote(BaseModel):
    """Character appearance and expression notes for a panel."""

    name: str = Field(..., description="Character name (e.g., 'Captain Carrot')")
    item_id: str = Field(..., description="Source snack/item ID")
    expression: str = Field("neutral", description="Expression (happy, worried, excited)")
    position: str = Field("center", description="Position in panel (left, center, right)")
    props: list[str] = Field(default_factory=list, description="Props or accessories")


class Panel(BaseModel):
    """Single panel in a 4-panel comic."""

    panel_number: int = Field(..., ge=1, le=4, description="Panel number (1-4)")
    title: str | None = Field(None, description="Optional panel title")
    dialogue: list[DialogueLine] = Field(
        default_factory=list,
        description="Lines of dialogue with speaker attribution"
    )
    emotion: str | None = Field(
        None, description="Default bubble emotion style (speech, thought, exclaim, angry, whisper)"
    )
    citation_ids: list[str] = Field(default_factory=list, description="Fact IDs cited in this panel")
    characters: list[CharacterNote] = Field(
        default_factory=list, description="Characters in this panel"
    )
    visual_prompt: str = Field(..., description="Visual description for image generation")
    background: str = Field("simple", description="Background type (simple, kitchen, park)")

    def get_dialogue_texts(self) -> list[str]:
        """Get just the text of all dialogue lines (for backwards compatibility)."""
        return [line.text for line in self.dialogue]


class ComicScript(BaseModel):
    """Complete comic script with all panels."""

    script_id: str = Field(..., description="Unique script identifier")
    panels: list[Panel] = Field(..., min_length=4, max_length=4, description="Four panels")
    summary_caption: str = Field(..., description="Social media caption (140-220 chars)")
    alt_text: str = Field(..., description="Accessibility alt text")
    hashtags: list[str] = Field(default_factory=list, description="Suggested hashtags")

    # Metadata
    snack_ids: list[str] = Field(default_factory=list, description="Source snack IDs")
    fact_ids: list[str] = Field(default_factory=list, description="All fact IDs used")
    swap_ids: list[str] = Field(default_factory=list, description="Suggested swap IDs")
    style_id: str = Field(..., description="Style ID used")
    age_band: str = Field("9-12", description="Target age band (9-12 or 13-17)")


class Comic(BaseModel):
    """Complete comic with rendered assets."""

    content_id: str = Field(..., description="Unique content identifier")
    script: ComicScript = Field(..., description="Comic script")

    # Rendered assets
    comic_portrait_uri: str | None = Field(None, description="1080x1350 PNG")
    reel_cover_uri: str | None = Field(None, description="Reel cover image")

    # Character consistency
    character_embeddings: dict[str, list[float]] = Field(
        default_factory=dict, description="Character visual embeddings for consistency"
    )

    # Provenance
    models_used: dict[str, str] = Field(
        default_factory=dict, description="Models used (vision, writer, image)"
    )
    created_at: str = Field(..., description="ISO 8601 timestamp")
    license_info: dict[str, str] = Field(
        default_factory=dict, description="Asset licenses (Freepik IDs, etc.)"
    )

    def get_full_caption(self) -> str:
        """Get the full caption with hashtags."""
        caption = self.script.summary_caption
        if self.script.hashtags:
            hashtags_str = " ".join(f"#{tag}" for tag in self.script.hashtags)
            caption = f"{caption}\n\n{hashtags_str}"
        return caption
