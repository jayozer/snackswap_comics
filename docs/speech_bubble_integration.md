# Speech Bubble Integration Plan (5.5)

> **Status**: Implementation Plan
> **Created**: 2025-12-10
> **Estimated Time**: 3-4 hours

---

## The Problem

AI image generators (including Nano-Banana/Gemini) cannot reliably generate readable text. The current workaround uses PIL to overlay speech bubbles, but this creates a "pasted on" look that feels disconnected from the comic art.

**Current State**:
- Generic white ellipse pasted on top
- Clinical, disconnected look
- Same bubble style for all emotions

**Target State**:
- Emotion-specific bubble shapes (cloud for thought, spiky for exclaim)
- Bubbles generated as part of the art OR enhanced PIL fallback
- Text placed precisely inside detected regions
- Cohesive, integrated appearance

---

## Solution Overview

A 5-phase approach combining AI-generated bubbles with intelligent fallback:

1. **Emotion-Based Prompts** - Request emotion-specific empty bubbles from Nano-Banana
2. **Gemini Vision Detection** - Detect bubble positions in generated comic
3. **Hybrid Retry + Fallback** - Retry once, then fall back to PIL
4. **Smart Text Placement** - Place dialogue inside detected bubbles
5. **Enhanced PIL Fallback** - Emotion-styled PIL bubbles if detection fails

---

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

Add emotion instructions to `compose_script()` and `compose_celebrate_script()`:

```python
# Add to prompt
"""
For each panel, specify the EMOTION for the speech bubble:
- "speech" for normal talking
- "thought" for internal thinking
- "exclaim" for excitement, surprise, realization
- "angry" for anger, frustration
- "whisper" for quiet/secret dialogue

Return in each panel object:
{
  "panel_number": 1,
  "dialogue": ["Hey, what's that?"],
  "emotion": "speech",
  ...
}
"""
```

**Narrative beat → emotion mapping:**

| Panel | Beat | Emotion |
|-------|------|---------|
| 1 | THE FLEX | `speech` (confident) |
| 2 | THE EXPOSÉ | `exclaim` (dramatic) |
| 3 | THE RATIO | `angry` (destruction) |
| 4 | THE VIBE CHECK | `speech` (resolution) |

### 1.4 Update Nano-Banana prompts

**File:** `backend/app/services/nanobana_service.py`

Update `build_comic_prompt()` to request emotion-specific EMPTY bubbles:

```python
# Add to prompt based on script emotions
"""
SPEECH BUBBLE INSTRUCTIONS:
Each panel MUST include an EMPTY speech bubble with NO TEXT:

Panel 1: Round oval speech bubble - EMPTY, white fill, black outline
Panel 2: Spiky starburst bubble - EMPTY, for dramatic moment
Panel 3: Jagged angry bubble - EMPTY, sharp edges
Panel 4: Round speech bubble - EMPTY, for resolution

CRITICAL RULES:
- Bubbles must be hand-drawn style matching the comic art
- Position bubbles in upper 25% of each panel
- Large enough for 2-3 lines of dialogue
- COMPLETELY EMPTY inside (no text, no dots, no placeholders)
- Tail points toward speaking character
"""
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
    prompt = """
    Analyze this 4-panel vertical comic strip (panels numbered 0-3 from top).
    Find ALL speech bubbles and return JSON:
    {
      "bubbles": [
        {
          "panel": 0,
          "bbox": [x1, y1, x2, y2],
          "center": [cx, cy],
          "style": "round|cloud|spiky|jagged",
          "confidence": 0.95
        }
      ],
      "success": true
    }

    If no bubbles found, return {"bubbles": [], "success": false}
    """

    # Read image and call Gemini Vision
    image_data = Path(image_path).read_bytes()
    response = await asyncio.to_thread(
        self.client.models.generate_content,
        model=self.settings.gemini_vision_model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_data, mime_type="image/png"),
                ],
            ),
        ],
    )

    # Parse and return bubble positions
    return self._parse_bubble_detection(response.text)
```

---

## Phase 3: Hybrid Retry + Fallback Strategy

### 3.1 Detection cascade in render_service.py

**File:** `backend/app/services/render_service.py`

```python
async def _add_text_overlay_with_detection(
    self, image: Image, script: dict, gemini_service: GeminiService
) -> Image:
    """Add text overlay with intelligent bubble detection."""
    MAX_RETRIES = 1

    for attempt in range(MAX_RETRIES + 1):
        # Try Gemini Vision detection
        try:
            bubble_positions = await gemini_service.detect_speech_bubbles(image_path)

            if bubble_positions and len(bubble_positions) >= len(script.get("panels", [])):
                logger.info(f"Bubble detection successful on attempt {attempt + 1}")
                return self._place_text_in_detected_bubbles(image, script, bubble_positions)
        except Exception as e:
            logger.warning(f"Bubble detection failed: {e}")

        if attempt < MAX_RETRIES:
            logger.warning(f"Retrying bubble detection ({attempt + 1}/{MAX_RETRIES})")

    # Fallback to enhanced PIL
    logger.warning("Falling back to PIL speech bubbles")
    return self._fallback_pil_bubbles(image, script)
```

### 3.2 Detection cascade order

1. **Gemini Vision** (most reliable, ~1 API call)
2. **OpenCV contour detection** (fast, no cost, existing `_detect_bubble_boundaries()`)
3. **Fixed region fallback** (existing `_get_expected_bubble_region()`)

---

## Phase 4: Intelligent Text Placement

### 4.1 Place text in detected bubbles

**File:** `backend/app/services/render_service.py`

```python
def _place_text_in_detected_bubbles(
    self, image: Image, script: dict, bubble_positions: dict
) -> Image:
    """Place dialogue text inside detected bubble regions."""
    draw = ImageDraw.Draw(image)

    for panel_idx, panel in enumerate(script.get("panels", [])):
        if panel_idx not in bubble_positions:
            continue

        bubble = bubble_positions[panel_idx]
        bbox = bubble["bbox"]  # [x1, y1, x2, y2]

        # Calculate text area with padding
        padding = 10
        text_area = (
            bbox[0] + padding,
            bbox[1] + padding,
            bbox[2] - padding,
            bbox[3] - padding
        )

        # Get dialogue and fit text
        dialogue = panel.get("dialogue", [])
        font, wrapped_lines = self._fit_text_to_area(dialogue, text_area)

        # Draw text centered in bubble with shadow
        self._draw_text_with_shadow(draw, wrapped_lines, text_area, font)

    return image
```

### 4.2 Font sizing algorithm

- Start at 28px, reduce until text fits
- Minimum 14px for readability
- Max 3 lines of dialogue
- 1px drop shadow for depth

---

## Phase 5: Enhanced PIL Fallback

### 5.1 Emotion-based bubble drawing

**File:** `backend/app/services/render_service.py`

```python
def _draw_speech_bubble(
    self, draw: ImageDraw, x: int, y: int, width: int, height: int,
    emotion: str = "speech", tail_direction: str = "center"
) -> None:
    """Draw emotion-appropriate speech bubble."""
    style = BUBBLE_STYLES.get(emotion, BUBBLE_STYLES["speech"])

    if style["shape"] == "oval":
        self._draw_oval_bubble(draw, x, y, width, height, style, tail_direction)
    elif style["shape"] == "cloud":
        self._draw_cloud_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "spiky":
        self._draw_spiky_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "jagged":
        self._draw_jagged_bubble(draw, x, y, width, height, style)
    elif style["shape"] == "dashed":
        self._draw_dashed_bubble(draw, x, y, width, height, style, tail_direction)
```

### 5.2 Shape drawing methods

| Method | Shape | Use Case |
|--------|-------|----------|
| `_draw_oval_bubble()` | Ellipse with tail | Normal speech (existing) |
| `_draw_cloud_bubble()` | Overlapping circles | Thought bubbles |
| `_draw_spiky_bubble()` | Starburst polygon | Exclamations, surprise |
| `_draw_jagged_bubble()` | Irregular sharp edges | Anger, frustration |
| `_draw_dashed_bubble()` | Dashed outline | Whispers, secrets |

### 5.3 Enhanced fallback with style matching

```python
def _fallback_pil_bubbles(self, image: Image, script: dict) -> Image:
    """Fallback: Draw emotion-based bubbles with style matching."""
    draw = ImageDraw.Draw(image)

    # Extract dominant colors for style matching
    colors = self._extract_dominant_colors(image)

    for panel_idx, panel in enumerate(script.get("panels", [])):
        emotion = panel.get("emotion", "speech")
        region = self._get_panel_bubble_region(image, panel_idx)

        # Draw emotion-appropriate bubble
        self._draw_speech_bubble(
            draw,
            region["x"], region["y"],
            region["width"], region["height"],
            emotion=emotion,
            tail_direction="left" if panel_idx % 2 == 0 else "right"
        )

        # Add wobble effect for hand-drawn feel
        self._add_wobble_effect(image, region)

        # Add text
        dialogue = panel.get("dialogue", [])
        self._add_dialogue_text(draw, region, dialogue)

    return image
```

---

## Implementation Order

| Step | Task | Time |
|------|------|------|
| 1 | Phase 1.1-1.2: Add emotion field + BUBBLE_STYLES | ~15 min |
| 2 | Phase 1.3: Update Gemini prompts for emotion | ~20 min |
| 3 | Phase 1.4: Update Nano-Banana prompts | ~15 min |
| 4 | **Phase 5.1-5.2: PIL emotion shapes** ← Early for visible progress | ~45 min |
| 5 | Phase 2.1: Gemini Vision detection | ~30 min |
| 6 | Phase 3: Retry/fallback cascade | ~20 min |
| 7 | Phase 4: Smart text placement | ~30 min |
| 8 | Testing | ~20 min |

**Total: ~3-4 hours**

---

## Testing Strategy

1. **EDUCATE mode** (gummy bears) → Verify angry/exclaim bubbles in panels 2-3
2. **CELEBRATE mode** (apple) → Verify positive speech bubbles
3. **Fallback test** → Mock failed detection, verify PIL fallback works
4. **Export formats** → Verify square, portrait, reel all render correctly
5. **Edge cases** → Long dialogue, empty panels, single-word responses

---

## Metrics to Track

| Metric | Description |
|--------|-------------|
| Bubble detection success rate | % of comics where Gemini Vision finds all bubbles |
| Retry rate | % of comics needing retry |
| Fallback rate | % of comics using PIL fallback |
| Generation time | Total seconds for comic with bubble integration |

---

## Rollback Plan

If AI-generated bubbles cause issues:

```python
# In render_service.py
USE_AI_BUBBLES = False  # Toggle to disable

async def render_comic(self, script: dict) -> Path:
    if USE_AI_BUBBLES:
        return await self._render_with_detection(script)
    else:
        return await self._render_with_pil_fallback(script)
```

- Set `USE_AI_BUBBLES = False` to disable AI bubble generation
- Falls back to enhanced PIL drawing (Phase 5)
- No model changes required
- Can toggle per-environment via config
