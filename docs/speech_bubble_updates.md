# Speech Bubble Integration Plan (5.5)

> **Status**: Implementation Plan
> **Created**: 2025-12-10
> **Related**: `docs/speech_bubble_improvement_plan.md` (original research)

## Overview
Transform the current simple PIL-drawn bubbles into emotion-aware, AI-integrated speech bubbles that feel part of the comic art.

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/models/comic.py` | Add `emotion` field to Panel |
| `backend/app/services/gemini_service.py` | Update prompts to return emotion, add `detect_speech_bubbles()` |
| `backend/app/services/nanobana_service.py` | Update prompts for emotion-specific empty bubbles |
| `backend/app/services/render_service.py` | New bubble shapes, detection retry, smart text placement |

---

## Phase 1: Emotion-Based Prompts

### 1.1 Add emotion field to Panel model
**File:** `backend/app/models/comic.py`

```python
class Panel(BaseModel):
    # ... existing fields ...
    emotion: str | None = None  # speech, thought, exclaim, angry, whisper
```

### 1.2 Define BUBBLE_STYLES mapping
**File:** `backend/app/services/render_service.py`

```python
BUBBLE_STYLES = {
    "speech": {"shape": "oval", "outline": "black", "fill": "white"},
    "thought": {"shape": "cloud", "outline": "gray", "fill": "white"},
    "exclaim": {"shape": "spiky", "outline": "red", "fill": "yellow"},
    "angry": {"shape": "jagged", "outline": "darkred", "fill": "#ffcccc"},
    "whisper": {"shape": "dashed", "outline": "gray", "fill": "#f0f0f0"},
}
```

### 1.3 Update Gemini script prompts
**File:** `backend/app/services/gemini_service.py`

Add to both `compose_script()` and `compose_celebrate_script()`:
- Instruct model to return `emotion` field per panel
- Map narrative beats to emotions:
  - THE FLEX → "speech" (confident)
  - THE EXPOSÉ → "exclaim" (dramatic)
  - THE RATIO → "angry" (destruction)
  - THE VIBE CHECK → "speech" (resolution)

### 1.4 Update Nano-Banana prompts
**File:** `backend/app/services/nanobana_service.py`

Update `build_comic_prompt()` to request emotion-specific EMPTY bubbles:
```
BUBBLE STYLE PER PANEL:
- Panel 1: Round speech bubble (empty, no text)
- Panel 2: Spiky exclaim bubble (empty, no text)
- Panel 3: Jagged angry bubble (empty, no text)
- Panel 4: Round speech bubble (empty, no text)
```

---

## Phase 2: Gemini Vision Bubble Detection

### 2.1 Add detect_speech_bubbles() method
**File:** `backend/app/services/gemini_service.py`

```python
async def detect_speech_bubbles(self, image_path: str) -> dict[int, dict]:
    """
    Use Gemini Vision to detect speech bubble positions in comic.

    Returns:
        Dict mapping panel number (0-3) to bubble info:
        {0: {"bbox": [x1,y1,x2,y2], "center": [cx,cy], "style": "round", "confidence": 0.95}}
    """
```

Prompt template:
```
Analyze this 4-panel vertical comic strip.
For each panel (numbered 0-3 from top), locate any speech bubbles.
Return JSON: {"bubbles": [{"panel": 0, "bbox": [x1,y1,x2,y2], "center": [cx,cy], "style": "round|cloud|spiky|jagged", "confidence": 0.95}]}
```

---

## Phase 3: Hybrid Retry + Fallback Strategy

### 3.1 Update _add_text_overlay() with detection cascade
**File:** `backend/app/services/render_service.py`

```python
async def _add_text_overlay(self, image: Image, script: dict) -> Image:
    MAX_RETRIES = 1

    # Try Gemini Vision detection
    bubble_positions = await self._try_detect_bubbles(image)

    if bubble_positions:
        return self._place_text_in_detected_bubbles(image, script, bubble_positions)

    # Retry once
    bubble_positions = await self._try_detect_bubbles(image)
    if bubble_positions:
        return self._place_text_in_detected_bubbles(image, script, bubble_positions)

    # Fallback to enhanced PIL
    return self._fallback_pil_bubbles(image, script)
```

### 3.2 Detection cascade order
1. **Gemini Vision** (most reliable, ~1 API call)
2. **OpenCV contour detection** (fast, no cost, existing `_detect_bubble_boundaries()`)
3. **Fixed region fallback** (existing `_get_expected_bubble_region()`)

---

## Phase 4: Intelligent Text Placement

### 4.1 Add _place_text_in_detected_bubbles()
**File:** `backend/app/services/render_service.py`

```python
def _place_text_in_detected_bubbles(
    self, image: Image, script: dict, bubble_positions: dict
) -> Image:
    """Place dialogue inside detected bubble regions."""
    draw = ImageDraw.Draw(image)

    for panel_idx, panel in enumerate(script.get("panels", [])):
        if panel_idx not in bubble_positions:
            continue

        bubble = bubble_positions[panel_idx]
        bbox = bubble["bbox"]

        # Calculate text area (10px padding inside bubble)
        text_area = (bbox[0]+10, bbox[1]+10, bbox[2]-10, bbox[3]-10)

        # Auto-size font to fit
        dialogue = panel.get("dialogue", [])
        font, wrapped_text = self._fit_text_to_area(dialogue, text_area)

        # Center text in bubble
        self._draw_centered_text(draw, wrapped_text, text_area, font)

    return image
```

### 4.2 Font sizing algorithm
- Start at 28px, reduce until text fits
- Minimum 14px for readability
- Max 3 lines of dialogue
- 1px drop shadow for depth

---

## Phase 5: Enhanced PIL Fallback

### 5.1 Update _draw_speech_bubble() with emotion styles
**File:** `backend/app/services/render_service.py`

```python
def _draw_speech_bubble(
    self, draw: ImageDraw, x: int, y: int, width: int, height: int,
    emotion: str = "speech", tail_direction: str = "center"
) -> None:
    style = BUBBLE_STYLES.get(emotion, BUBBLE_STYLES["speech"])

    if style["shape"] == "oval":
        self._draw_oval_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "cloud":
        self._draw_cloud_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "spiky":
        self._draw_spiky_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "jagged":
        self._draw_jagged_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "dashed":
        self._draw_dashed_bubble(draw, x, y, width, height, style)
```

### 5.2 Implement shape drawing methods
- `_draw_oval_bubble()` - existing ellipse (current implementation)
- `_draw_cloud_bubble()` - overlapping circles for thought bubble
- `_draw_spiky_bubble()` - starburst polygon for exclamations
- `_draw_jagged_bubble()` - irregular polygon for anger
- `_draw_dashed_bubble()` - dashed outline for whispers

### 5.3 Add wobble effect for hand-drawn feel
Extract dominant colors from comic and apply slight randomization to bubble outlines.

---

## Implementation Order

1. **Phase 1.1-1.2**: Add emotion field and BUBBLE_STYLES (~15 min)
2. **Phase 1.3**: Update Gemini prompts to return emotion (~20 min)
3. **Phase 1.4**: Update Nano-Banana prompts for emotion bubbles (~15 min)
4. **Phase 5.1-5.2**: Implement emotion-based PIL shapes (~45 min) ← Do this early for visible progress
5. **Phase 2.1**: Add Gemini Vision detection method (~30 min)
6. **Phase 3.1-3.2**: Implement retry/fallback cascade (~20 min)
7. **Phase 4.1-4.2**: Smart text placement in detected bubbles (~30 min)
8. **Testing**: End-to-end test with different snacks/emotions (~20 min)

**Total estimated: ~3-4 hours**

---

## Testing Strategy

1. Generate comic with gummy bears (EDUCATE mode) → verify angry/exclaim bubbles
2. Generate comic with apple (CELEBRATE mode) → verify speech bubbles
3. Test fallback by mocking failed detection
4. Verify all 3 export formats (square, portrait, reel)

---

## Rollback Plan

If AI-generated bubbles cause issues:
- Set `USE_AI_BUBBLES = False` in render_service.py
- Falls back to enhanced PIL drawing (Phase 5)
- No model changes required
