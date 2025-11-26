"""
Configuration management for SnackSwap Comics.
Uses pydantic-settings for environment variable management.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    freepik_api_key: str | None = Field(None, description="Freepik API key (optional in MVP)")

    # Qdrant Configuration
    qdrant_url: str = Field("http://localhost:6333", description="Qdrant server URL")
    qdrant_api_key: str | None = Field(None, description="Qdrant API key (optional)")

    # Storage Configuration
    storage_backend: Literal["local", "s3", "gcs"] = Field("local", description="Storage backend")
    storage_path: str = Field("./storage", description="Local storage path")
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    aws_bucket: str | None = None
    gcs_bucket: str | None = None
    gcs_credentials_path: str | None = None

    # Database
    database_url: str = Field("sqlite:///./snackswap.db", description="Database connection URL")

    # Application Settings
    debug: bool = Field(False, description="Debug mode")
    enable_maps: bool = Field(False, description="Enable Google Maps integration")
    cors_origins: str = Field(
        "http://localhost:3000,http://localhost:5173", description="Comma-separated CORS origins"
    )
    max_upload_size_mb: int = Field(10, description="Maximum upload size in MB")
    content_retention_days: int = Field(30, description="Content retention period in days")

    # Model Configuration (using new google.genai SDK - no models/ prefix)
    gemini_vision_model: str = Field(
        "gemini-2.5-flash", description="Gemini model for vision tasks"
    )
    gemini_writer_model: str = Field(
        "gemini-2.5-pro", description="Gemini model for script writing"
    )
    gemini_image_model: str = Field(
        "gemini-3-pro-image-preview", description="Gemini model for image generation (Nano-Banana Pro)"
    )
    gemini_temperature: float = Field(0.7, description="Gemini generation temperature")
    gemini_max_tokens: int = Field(8192, description="Maximum tokens for generation")

    # Feature Flags
    enable_admin_approval: bool = Field(False, description="Require admin approval before download")
    enable_maps_swaps: bool = Field(False, description="Enable Maps-powered local swaps")
    enable_analytics: bool = Field(False, description="Enable analytics tracking")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size to bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
