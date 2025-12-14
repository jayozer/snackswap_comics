from app.services.render_service import RenderService


def _service() -> RenderService:
    # Avoid initializing external dependencies (Gemini, Freepik, etc.).
    return RenderService.__new__(RenderService)


def test_dialogue_entries_for_bubbles_preserves_individual_lines() -> None:
    service = _service()
    dialogue = [
        {"speaker": "Dr. Drip", "text": "Line one", "position": "right", "emotion": "speech"},
        {"speaker": "Glow Berry", "text": "Line two", "position": "left", "emotion": "speech"},
        {"speaker": "Dr. Drip", "text": "Line three", "position": "right", "emotion": "exclaim"},
    ]

    entries = service._dialogue_entries_for_bubbles(dialogue)

    assert [e["speaker"] for e in entries] == ["Dr. Drip", "Glow Berry", "Dr. Drip"]
    assert [e["text"] for e in entries] == ["Line one", "Line two", "Line three"]
    assert [e["position"] for e in entries] == ["right", "left", "right"]


def test_dialogue_entries_for_bubbles_legacy_strings_default_to_dr_drip() -> None:
    service = _service()
    entries = service._dialogue_entries_for_bubbles(["Hello", "World"])

    assert entries == [
        {"speaker": "Dr. Drip", "text": "Hello", "emotion": "speech", "position": "right"},
        {"speaker": "Dr. Drip", "text": "World", "emotion": "speech", "position": "right"},
    ]

