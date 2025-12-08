"""API request and response models."""

from enum import Enum
from pydantic import BaseModel, Field


class ComicMode(str, Enum):
    """Mode for comic generation based on snack dental risk."""

    EDUCATE = "educate"  # Risk >= 30: Educational comic about dental risks
    CELEBRATE = "celebrate"  # Risk < 30: Celebratory comic for healthy snacks
    UNKNOWN = "unknown"  # No match found: Generic informational comic


# Capture & Intake
class CaptureIntakeRequest(BaseModel):
    """Request model for photo upload."""

    # File will be handled via multipart/form-data
    pass


class CaptureIntakeResponse(BaseModel):
    """Response after photo intake."""

    photo_id: str = Field(..., description="Unique photo identifier")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    thumb_uri: str = Field(..., description="Thumbnail URI")


# Vision Detection
class VisionDetectRequest(BaseModel):
    """Request model for vision detection."""

    photo_id: str = Field(..., description="Photo ID from intake")


class DetectedItem(BaseModel):
    """A detected food item."""

    name: str = Field(..., description="Item name")
    brand_guess: str | None = Field(None, description="Guessed brand name")
    category: str = Field(..., description="Category (chips, candy, fruit)")
    visible_clues: str = Field(..., description="Visual clues from the image")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class VisionDetectResponse(BaseModel):
    """Response from vision detection."""

    items: list[DetectedItem] = Field(..., description="Detected items (1-5, grouped for plates/assortments)")
    needs_confirmation: bool = Field(
        False, description="Whether user confirmation is recommended"
    )


# Score & Retrieve
class ScoreRetrieveRequest(BaseModel):
    """Request model for scoring and retrieval."""

    items: list[DetectedItem] = Field(..., description="Detected items from vision")
    age: int = Field(..., ge=3, le=12, description="Child's age")
    allergies: list[str] = Field(default_factory=list, description="Allergies (dairy, nuts, etc.)")


class ScoredItem(BaseModel):
    """A scored snack item with facts and swaps."""

    snack_id: str = Field(..., description="Matched snack ID")
    name: str = Field(..., description="Snack name")
    category: str = Field(..., description="Category")
    dental_risk_score: float = Field(..., description="Risk score (0-100)")
    confidence: float = Field(..., description="Match confidence")


class ScoreRetrieveResponse(BaseModel):
    """Response from scoring and retrieval."""

    scored_items: list[ScoredItem] = Field(..., description="Scored items")
    facts: list[dict] = Field(..., description="Relevant facts (simplified payloads)")
    swaps: list[dict] = Field(..., description="Suggested swaps (simplified payloads)")
    mode: ComicMode = Field(
        default=ComicMode.EDUCATE,
        description="Comic mode: educate (risk>=30), celebrate (risk<30), unknown (no match)"
    )
    average_risk_score: float = Field(
        default=0.0,
        description="Average dental risk score across all matched items"
    )


# Panel Context for context-aware retrieval
class PanelContext(BaseModel):
    """Context for panel-aware fact retrieval."""

    panel_number: int = Field(default=1, ge=1, le=4, description="Panel number (1-4)")
    scene: str | None = Field(default=None, description="Scene setting (playground, kitchen, dentist, school)")
    mood: str = Field(default="educational", description="Panel mood (funny, dramatic, educational, celebratory)")
    narrative_beat: str = Field(default="intro", description="Narrative beat (intro, conflict, revelation, resolution)")


# Script Compose
class ScriptComposeRequest(BaseModel):
    """Request model for script composition."""

    scored_items: list[ScoredItem] = Field(..., description="Scored items")
    facts: list[dict] = Field(..., description="Available facts")
    swaps: list[dict] = Field(..., description="Available swaps")
    style_id: str = Field("default", description="Style ID to use")
    age: int = Field(..., ge=3, le=12, description="Child's age")
    mode: ComicMode = Field(default=ComicMode.EDUCATE, description="Comic mode for script generation")


class ScriptComposeResponse(BaseModel):
    """Response from script composition."""

    script_id: str = Field(..., description="Generated script ID")
    panels: list[dict] = Field(..., description="Panel data")
    caption: str = Field(..., description="Summary caption")
    alt_text: str = Field(..., description="Alt text")


# Render Comic
class RenderComicRequest(BaseModel):
    """Request model for comic rendering."""

    script_id: str = Field(..., description="Script ID to render")


class RenderComicResponse(BaseModel):
    """Response from comic rendering."""

    comic_square_uri: str = Field(..., description="1080x1080 PNG URI")
    comic_portrait_uri: str = Field(..., description="1080x1350 PNG URI")
    reel_cover_uri: str | None = Field(None, description="Reel cover URI")


# Export
class ExportZipRequest(BaseModel):
    """Request model for export ZIP."""

    content_id: str = Field(..., description="Content ID to export")


class ContentManifest(BaseModel):
    """Content provenance manifest."""

    content_id: str = Field(..., description="Unique content identifier")
    models: dict[str, str] = Field(..., description="Model IDs used")
    facts: list[dict] = Field(..., description="Facts with IDs and sources")
    snacks: list[dict] = Field(..., description="Snacks with IDs")
    swaps: list[dict] = Field(..., description="Swaps with IDs")
    style_id: str = Field(..., description="Style ID used")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    license_info: dict[str, str] = Field(default_factory=dict, description="Asset licenses")


class ExportZipResponse(BaseModel):
    """Response from export."""

    zip_uri: str = Field(..., description="ZIP file URI")
    manifest_uri: str = Field(..., description="Manifest JSON URI")
    manifest: ContentManifest = Field(..., description="Content manifest")
