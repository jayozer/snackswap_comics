"""
Audit logging service for SnackSwap Comics.
Logs all generated content (scripts, images) for review and compliance.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GenerationType(Enum):
    """Types of content generation to audit."""
    VISION_DETECTION = "vision_detection"
    SCRIPT_COMPOSE = "script_compose"
    SCRIPT_CELEBRATE = "script_celebrate"
    SCRIPT_UNKNOWN = "script_unknown"
    IMAGE_GENERATION = "image_generation"


class AuditService:
    """Service for logging all generated content for audit and review."""

    def __init__(self, settings: Settings):
        """
        Initialize the audit service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.audit_dir = Path(settings.storage_path) / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Initialized AuditService, logging to %s", self.audit_dir)

    def _get_log_file(self) -> Path:
        """Get the log file path for today."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.audit_dir / f"{today}.jsonl"

    def _hash_content(self, content: Any) -> str:
        """Generate a hash of content for deduplication/reference."""
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True)
        elif isinstance(content, bytes):
            return hashlib.sha256(content).hexdigest()[:16]
        else:
            content_str = str(content)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def log_generation(
        self,
        generation_type: GenerationType,
        input_data: dict[str, Any],
        output_data: dict[str, Any] | str | None,
        validation_passed: bool,
        validation_details: str | None = None,
        flagged_terms: list[str] | None = None,
        user_age: int | None = None,
        photo_id: str | None = None,
        script_id: str | None = None,
        duration_ms: int | None = None,
    ) -> str:
        """
        Log a content generation event.

        Args:
            generation_type: Type of generation (script, image, etc.)
            input_data: Input parameters (will be hashed for privacy)
            output_data: Generated output
            validation_passed: Whether content passed guardrails
            validation_details: Details about validation result
            flagged_terms: Any terms flagged by guardrails
            user_age: User's age for context
            photo_id: Associated photo ID
            script_id: Associated script ID
            duration_ms: Generation duration in milliseconds

        Returns:
            Audit log entry ID
        """
        timestamp = datetime.now(timezone.utc)
        entry_id = f"{generation_type.value}_{timestamp.strftime('%Y%m%d%H%M%S')}_{self._hash_content(input_data)[:8]}"

        # Build audit entry
        entry = {
            "id": entry_id,
            "timestamp": timestamp.isoformat(),
            "type": generation_type.value,
            "input_hash": self._hash_content(input_data),
            "output_hash": self._hash_content(output_data) if output_data else None,
            "validation": {
                "passed": validation_passed,
                "details": validation_details,
                "flagged_terms": flagged_terms or [],
            },
            "context": {
                "user_age": user_age,
                "photo_id": photo_id,
                "script_id": script_id,
            },
            "performance": {
                "duration_ms": duration_ms,
            },
        }

        # Include output content for review (scripts only, not images)
        if generation_type in [
            GenerationType.SCRIPT_COMPOSE,
            GenerationType.SCRIPT_CELEBRATE,
            GenerationType.SCRIPT_UNKNOWN,
        ]:
            entry["output_content"] = output_data

        # For blocked content, include full details for investigation
        if not validation_passed:
            entry["input_summary"] = self._summarize_input(input_data)
            logger.warning("Blocked content logged: %s - %s", entry_id, validation_details)

        # Write to JSONL file
        try:
            log_file = self._get_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            logger.debug("Audit logged: %s", entry_id)
        except Exception as e:
            logger.error("Failed to write audit log: %s", e)

        return entry_id

    def _summarize_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Create a summary of input data for logging (privacy-aware)."""
        summary = {}

        # Include non-sensitive fields
        safe_fields = ["age", "mode", "snack_names", "fact_count", "swap_count"]
        for field in safe_fields:
            if field in input_data:
                summary[field] = input_data[field]

        # Summarize snacks if present
        if "snacks" in input_data:
            snacks = input_data["snacks"]
            if isinstance(snacks, list):
                # Handle both dict items and string items
                snack_names = []
                for s in snacks[:5]:
                    if isinstance(s, dict):
                        snack_names.append(s.get("name", "unknown"))
                    else:
                        snack_names.append(str(s))
                summary["snack_names"] = snack_names

        return summary

    def log_image_generation(
        self,
        prompt: str,
        image_path: str | None,
        validation_passed: bool,
        validation_details: str | None = None,
        script_id: str | None = None,
        duration_ms: int | None = None,
    ) -> str:
        """
        Log an image generation event.

        Args:
            prompt: The image generation prompt
            image_path: Path to generated image (if successful)
            validation_passed: Whether prompt passed guardrails
            validation_details: Details about validation result
            script_id: Associated script ID
            duration_ms: Generation duration in milliseconds

        Returns:
            Audit log entry ID
        """
        return self.log_generation(
            generation_type=GenerationType.IMAGE_GENERATION,
            input_data={"prompt": prompt[:500]},  # Truncate long prompts
            output_data={"image_path": image_path} if image_path else None,
            validation_passed=validation_passed,
            validation_details=validation_details,
            script_id=script_id,
            duration_ms=duration_ms,
        )

    def get_flagged_entries(
        self,
        date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Retrieve flagged (failed validation) entries for review.

        Args:
            date: Date string (YYYY-MM-DD) or None for today
            limit: Maximum entries to return

        Returns:
            List of flagged audit entries
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        log_file = self.audit_dir / f"{date}.jsonl"
        if not log_file.exists():
            return []

        flagged = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if not entry.get("validation", {}).get("passed", True):
                        flagged.append(entry)
                        if len(flagged) >= limit:
                            break
        except Exception as e:
            logger.error("Failed to read audit log: %s", e)

        return flagged

    def get_stats(self, date: str | None = None) -> dict[str, Any]:
        """
        Get statistics for a given date.

        Args:
            date: Date string (YYYY-MM-DD) or None for today

        Returns:
            Statistics dictionary
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        log_file = self.audit_dir / f"{date}.jsonl"
        if not log_file.exists():
            return {"date": date, "total": 0, "passed": 0, "blocked": 0, "by_type": {}}

        stats = {
            "date": date,
            "total": 0,
            "passed": 0,
            "blocked": 0,
            "by_type": {},
            "flagged_terms": {},
        }

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total"] += 1

                    if entry.get("validation", {}).get("passed", True):
                        stats["passed"] += 1
                    else:
                        stats["blocked"] += 1

                    gen_type = entry.get("type", "unknown")
                    stats["by_type"][gen_type] = stats["by_type"].get(gen_type, 0) + 1

                    # Count flagged terms
                    for term in entry.get("validation", {}).get("flagged_terms", []):
                        stats["flagged_terms"][term] = stats["flagged_terms"].get(term, 0) + 1

        except Exception as e:
            logger.error("Failed to read audit log for stats: %s", e)

        return stats


# Service instance cache
_audit_service: AuditService | None = None


def get_audit_service(settings: Settings) -> AuditService:
    """Get or create the audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService(settings)
    return _audit_service
