from app.services.render_service import RenderService


def _service() -> RenderService:
    # Avoid initializing external dependencies (Gemini, Freepik, etc.).
    return RenderService.__new__(RenderService)


def test_dialogue_entries_for_bubbles_preserves_individual_lines() -> None:
    service = _service()
    dialogue = [
        {"speaker": "Dr. Hawley", "text": "Line one", "position": "right", "emotion": "speech"},
        {"speaker": "Glow Berry", "text": "Line two", "position": "left", "emotion": "speech"},
        {"speaker": "Dr. Hawley", "text": "Line three", "position": "right", "emotion": "exclaim"},
    ]

    entries = service._dialogue_entries_for_bubbles(dialogue)

    assert [e["speaker"] for e in entries] == ["Dr. Hawley", "Glow Berry", "Dr. Hawley"]
    assert [e["text"] for e in entries] == ["Line one", "Line two", "Line three"]
    assert [e["position"] for e in entries] == ["right", "left", "right"]


def test_dialogue_entries_for_bubbles_legacy_strings_default_to_dr_hawley() -> None:
    service = _service()
    entries = service._dialogue_entries_for_bubbles(["Hello", "World"])

    assert entries == [
        {"speaker": "Dr. Hawley", "text": "Hello", "emotion": "speech", "position": "right"},
        {"speaker": "Dr. Hawley", "text": "World", "emotion": "speech", "position": "right"},
    ]

