#!/usr/bin/env python
"""
Test script for content guardrails and audit logging.
Run from backend directory: python test_guardrails.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.guardrails_service import GuardrailsService, ContentRating
from app.services.audit_service import AuditService, GenerationType
from app.core.config import get_settings


def test_profanity_filter():
    """Test the profanity filter with various inputs."""
    print("\n=== Testing Profanity Filter ===\n")

    guardrails = GuardrailsService()

    # Test cases: (input, expected_passed, expected_rating)
    test_cases = [
        # Safe content
        ("This snack is cooked! Your teeth are mid.", True, ContentRating.MILD),
        ("That's a W choice, no cap.", True, ContentRating.MILD),
        ("Dr. Hawley says your smile is aesthetic.", True, ContentRating.SAFE),

        # Mild content (allowed but flagged)
        ("That's stupid and cringe.", True, ContentRating.MILD),
        ("You're such a loser for eating that.", True, ContentRating.MILD),

        # Blocked content
        ("What the fuck is this snack?", False, ContentRating.BLOCKED),
        ("This shit is nasty.", False, ContentRating.BLOCKED),
        ("You're a retard for eating that.", False, ContentRating.BLOCKED),

        # Edge cases
        ("", True, ContentRating.SAFE),
        ("Normal text with no issues.", True, ContentRating.SAFE),
    ]

    passed = 0
    failed = 0

    for text, expected_passed, expected_rating in test_cases:
        result = guardrails.validate_text(text)

        status = "✅" if (result.passed == expected_passed and result.rating == expected_rating) else "❌"

        if status == "✅":
            passed += 1
        else:
            failed += 1

        print(f"{status} Input: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"   Expected: passed={expected_passed}, rating={expected_rating.value}")
        print(f"   Got:      passed={result.passed}, rating={result.rating.value}")
        if result.flagged_terms:
            print(f"   Flagged:  {result.flagged_terms}")
        print()

    print(f"\n=== Results: {passed} passed, {failed} failed ===\n")
    return failed == 0


def test_script_validation():
    """Test script validation with a sample comic script."""
    print("\n=== Testing Script Validation ===\n")

    guardrails = GuardrailsService()

    # Sample safe script
    safe_script = {
        "panels": [
            {
                "panel_number": 1,
                "dialogue": ["That snack is cooked!", "Your smile is mid."],
            },
            {
                "panel_number": 2,
                "dialogue": ["Negative aura detected.", "You're gonna look crusty."],
            },
            {
                "panel_number": 3,
                "dialogue": ["That's not aesthetic.", "Your teeth are gonna be yellow."],
            },
            {
                "panel_number": 4,
                "dialogue": ["Try this instead.", "Glow up approved!"],
            },
        ],
        "summary_caption": "Your smile is COOKED. Get the glow up.",
        "alt_text": "Dr. Hawley roasting a gummy bear snack.",
    }

    result = guardrails.validate_script(safe_script)
    print(f"Safe script validation: passed={result.passed}, rating={result.rating.value}")
    print(f"Details: {result.details}")
    if result.flagged_terms:
        print(f"Flagged terms: {result.flagged_terms}")

    # Sample unsafe script
    unsafe_script = {
        "panels": [
            {
                "panel_number": 1,
                "dialogue": ["What the fuck is this?", "That's some bullshit."],
            },
        ],
        "summary_caption": "This snack is shit.",
    }

    print()
    result = guardrails.validate_script(unsafe_script)
    print(f"Unsafe script validation: passed={result.passed}, rating={result.rating.value}")
    print(f"Details: {result.details}")
    if result.flagged_terms:
        print(f"Flagged terms: {result.flagged_terms}")

    return True


def test_image_prompt_validation():
    """Test image prompt validation."""
    print("\n=== Testing Image Prompt Validation ===\n")

    guardrails = GuardrailsService()

    # Safe prompt
    safe_prompt = """
    Create a 4-panel comic strip with Dr. Hawley, a tooth character.
    Style: Webtoon animation, bright colors, exaggerated expressions.
    Panel 1: Dr. Hawley looking skeptical at a gummy bear.
    """

    result = guardrails.validate_image_prompt(safe_prompt)
    print(f"Safe prompt: passed={result.passed}, rating={result.rating.value}")

    # Unsafe prompt
    unsafe_prompt = """
    Create an image with nude characters and violence.
    Show blood and weapons.
    """

    result = guardrails.validate_image_prompt(unsafe_prompt)
    print(f"Unsafe prompt: passed={result.passed}, rating={result.rating.value}")
    print(f"Details: {result.details}")

    return True


def test_audit_logging():
    """Test audit logging functionality."""
    print("\n=== Testing Audit Logging ===\n")

    settings = get_settings()
    audit = AuditService(settings)

    # Log a test generation
    entry_id = audit.log_generation(
        generation_type=GenerationType.SCRIPT_COMPOSE,
        input_data={"age": 15, "snacks": ["Gummy Bears"]},
        output_data={"panels": [{"dialogue": ["Test"]}]},
        validation_passed=True,
        validation_details="Test entry",
        flagged_terms=[],
        user_age=15,
        duration_ms=1234,
    )

    print(f"Created audit entry: {entry_id}")

    # Log a blocked entry
    blocked_id = audit.log_generation(
        generation_type=GenerationType.SCRIPT_COMPOSE,
        input_data={"age": 13, "snacks": ["Test Snack"]},
        output_data=None,
        validation_passed=False,
        validation_details="Blocked due to profanity",
        flagged_terms=["test_profanity"],
        user_age=13,
        duration_ms=500,
    )

    print(f"Created blocked entry: {blocked_id}")

    # Get stats
    stats = audit.get_stats()
    print(f"\nToday's stats: {stats}")

    # Get flagged entries
    flagged = audit.get_flagged_entries()
    print(f"Flagged entries today: {len(flagged)}")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Content Guardrails Test Suite")
    print("=" * 60)

    all_passed = True

    try:
        if not test_profanity_filter():
            all_passed = False
    except Exception as e:
        print(f"❌ Profanity filter test failed with error: {e}")
        all_passed = False

    try:
        test_script_validation()
    except Exception as e:
        print(f"❌ Script validation test failed with error: {e}")
        all_passed = False

    try:
        test_image_prompt_validation()
    except Exception as e:
        print(f"❌ Image prompt test failed with error: {e}")
        all_passed = False

    try:
        test_audit_logging()
    except Exception as e:
        print(f"❌ Audit logging test failed with error: {e}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed - check output above")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
