# Speech Bubble Integration - Creative Approaches

> **Problem**: PIL-drawn speech bubbles look disconnected from Nano-Banana generated art
> **Goal**: Integrated, cohesive speech bubbles that feel part of the comic artwork

---

## The Core Challenge

AI image generators (including Nano-Banana/gemini-3-pro-image-preview) are unreliable at generating readable text. Current workaround uses PIL to overlay text, but this creates a "pasted on" look.

---

## Creative Approaches

### Approach 1: Two-Pass Generation with Empty Stylized Bubbles

**Concept**: Generate comic WITH empty speech bubbles as part of the art, then add text inside

```
Pass 1: Nano-Banana generates comic with EMPTY stylized bubbles
        ↓
Pass 2: Detect bubble regions (Gemini Vision or OpenCV)
        ↓
Pass 3: PIL adds text INSIDE the detected bubble regions
```

**Prompt Engineering Example**:
```
"Create a 4-panel comic strip. Each panel MUST include an EMPTY white speech bubble
with a black outline in the comic art style. The bubbles should have NO TEXT inside -
leave them completely blank. The bubbles should appear hand-drawn and match the
illustration style. Position bubbles in the top 20% of each panel."
```

**Pros**:
- Bubbles match art style perfectly (same model generates them)
- Text remains readable (PIL handles it)
- Bubbles feel integrated into the scene

**Cons**:
- Nano-Banana may not reliably generate empty bubbles
- Bubble positions may vary, need detection
- May require multiple retries

**Detection Options**:
1. **Gemini Vision**: Ask "Where are the speech bubbles in this image? Return bounding box coordinates"
2. **OpenCV**: Detect white regions with black outlines
3. **Fixed regions**: If prompt reliably places bubbles in top 20%, use fixed coordinates

---

### Approach 2: Placeholder Text Replacement

**Concept**: Generate comic WITH speech bubbles containing simple placeholder text, then overlay real text

```
Pass 1: Nano-Banana generates comic with bubbles containing "..."
        ↓
Pass 2: Detect bubble regions
        ↓
Pass 3: Fill bubble interiors with white/solid color
        ↓
Pass 4: Add actual dialogue text
```

**Prompt Engineering Example**:
```
"Create a 4-panel comic. Include speech bubbles with '...' as placeholder text.
The bubbles should be large enough to fit 2-3 lines of dialogue."
```

**Pros**:
- Placeholder helps model understand bubble purpose and sizing
- Bubbles are naturally integrated
- Model "expects" text there

**Cons**:
- Placeholder may bleed through
- Need to cleanly mask/replace text area

---

### Approach 3: Style-Matched Post-Processing

**Concept**: Keep current PIL overlay approach but apply heavy post-processing to blend

```
Current: Nano-Banana art → PIL draws white ellipse + text
         ↓
Enhanced: Apply artistic filters to make bubbles match comic style
```

**Post-Processing Techniques**:
1. **Add hand-drawn wobble**: Distort bubble edges slightly
2. **Match line weight**: Use same stroke width as comic outlines
3. **Add texture**: Apply paper/canvas texture to bubbles
4. **Color matching**: Extract comic's color palette, tint bubble borders
5. **Drop shadows**: Add soft shadows that match lighting
6. **Comic-style outlines**: Double-stroke or halftone effects

**Pros**:
- Minimal architecture changes
- Can iterate quickly
- Works with current flow

**Cons**:
- Still fundamentally an overlay
- Quality depends on filter tuning

---

### Approach 4: Freepik Style Matching + Blending

**Concept**: Use Freepik's professional comic bubble assets, color-matched and blended

```
Pass 1: Nano-Banana generates comic (no bubbles requested)
        ↓
Pass 2: Extract dominant colors from comic
        ↓
Pass 3: Fetch Freepik comic bubbles, recolor to match
        ↓
Pass 4: Composite with blend modes (multiply, overlay)
        ↓
Pass 5: Add text
```

**Blending Techniques**:
- Use PIL's `Image.blend()` or `ImageChops`
- Apply "multiply" blend mode for natural integration
- Add slight transparency to bubble fill
- Match bubble outline color to comic's line art color

**Pros**:
- Professional bubble designs
- Can match colors programmatically
- Multiple bubble styles available

**Cons**:
- Still composited (may look overlaid)
- Freepik API dependency

---

### Approach 5: Layered Generation (Separate Bubble Pass)

**Concept**: Generate comic and bubbles separately, composite together

```
Pass 1: Nano-Banana generates scene/characters (NO bubbles)
        ↓
Pass 2: Nano-Banana generates ONLY speech bubbles (transparent/white background)
        Prompt: "Comic-style speech bubbles, hand-drawn, expressive"
        ↓
Pass 3: Composite bubble layer over scene layer
        ↓
Pass 4: Add text
```

**Pros**:
- Full control over both elements
- Can generate multiple bubble variations
- Clean separation

**Cons**:
- Two Nano-Banana calls (cost/time)
- Need alpha channel handling
- Bubbles may not match art style perfectly

---

### Approach 6: Gemini Vision Guided Placement

**Concept**: Use Gemini Vision to intelligently analyze and guide bubble placement

```
Pass 1: Nano-Banana generates comic with integrated bubbles
        ↓
Pass 2: Gemini Vision analyzes: "Identify speech bubble locations,
        return coordinates and suggest optimal text placement"
        ↓
Pass 3: Use Vision guidance to precisely place text
```

**Gemini Vision Prompt**:
```
"Analyze this comic panel. For each speech bubble:
1. Return bounding box coordinates (x1, y1, x2, y2)
2. Identify the bubble's center point
3. Estimate readable text area (accounting for bubble shape)
4. Suggest font size that would fit 2-3 lines"
```

**Pros**:
- Adaptive to any bubble shape/position
- Leverages Gemini's vision capabilities
- Can handle irregular bubble shapes

**Cons**:
- Additional API call
- Vision model accuracy varies

---

## FINAL PLAN: Integrated Speech Bubbles

**User Decisions**:
- Quality > Speed: Accept 2-3 second latency for Gemini Vision detection
- Retry Strategy: Hybrid - retry once, then fall back to PIL
- Bubble Style: Emotion-based (spiky=anger, cloud=thought, round=speech)

---

### Phase 1: Emotion-Based Prompt Engineering

Request empty, EMOTION-SPECIFIC speech bubbles as part of comic generation:

```python
# Map dialogue emotion to bubble style
BUBBLE_STYLES = {
    "speech": "round oval speech bubble with tail",
    "thought": "cloud-shaped thought bubble with small circles as tail",
    "exclaim": "spiky starburst bubble for excitement or surprise",
    "angry": "jagged sharp-edged bubble for anger",
    "whisper": "dashed-outline bubble for whispering",
}

# Prompt includes emotion-specific bubble instructions
prompt = f"""
Create a 4-panel comic strip. Each panel MUST include EMPTY speech bubbles:

Panel 1: {bubble_styles[panel1_emotion]} - EMPTY, no text
Panel 2: {bubble_styles[panel2_emotion]} - EMPTY, no text
Panel 3: {bubble_styles[panel3_emotion]} - EMPTY, no text
Panel 4: {bubble_styles[panel4_emotion]} - EMPTY, no text

CRITICAL RULES:
- Bubbles must be hand-drawn style matching the comic art
- Bubbles positioned in upper 25% of each panel
- Large enough for 2-3 lines of dialogue
- COMPLETELY EMPTY inside (no text, no dots, no placeholders)
- White fill with black comic-style outline
- Tail points toward speaking character
"""
```

### Phase 2: Gemini Vision Bubble Detection

Add `detect_speech_bubbles()` to `gemini_service.py`:

```python
async def detect_speech_bubbles(self, image_path: Path) -> dict:
    """Use Gemini Vision to locate speech bubbles in generated comic."""

    prompt = """
    Analyze this comic image. Find ALL speech bubbles and return JSON:
    {
      "bubbles": [
        {
          "panel": 1,
          "bbox": [x1, y1, x2, y2],  // pixel coordinates
          "center": [cx, cy],
          "style": "round|cloud|spiky|jagged",
          "confidence": 0.95
        }
      ],
      "success": true
    }

    If no bubbles found, return {"bubbles": [], "success": false}
    """

    # Call Gemini Vision with image
    response = await self.vision_model.generate_content([image, prompt])
    return parse_json(response.text)
```

### Phase 3: Hybrid Retry + Fallback Strategy

```python
async def generate_comic_with_bubbles(self, script: dict) -> Path:
    """Generate comic with integrated bubbles, with retry and fallback."""

    MAX_RETRIES = 1

    for attempt in range(MAX_RETRIES + 1):
        # Generate comic with empty bubbles
        comic_path = await self.nanobana.generate_comic(script, include_bubbles=True)

        # Detect bubbles
        detection = await self.gemini.detect_speech_bubbles(comic_path)

        if detection["success"] and len(detection["bubbles"]) >= len(script["panels"]):
            # Success! Place text in detected bubbles
            return await self._place_text_in_bubbles(comic_path, script, detection)

        if attempt < MAX_RETRIES:
            logger.warning(f"Bubble detection failed, retrying ({attempt + 1}/{MAX_RETRIES})")
            continue

    # Fallback to PIL overlay
    logger.warning("Falling back to PIL speech bubbles")
    return await self._fallback_pil_bubbles(comic_path, script)
```

### Phase 4: Intelligent Text Placement

```python
async def _place_text_in_bubbles(
    self,
    comic_path: Path,
    script: dict,
    detection: dict
) -> Path:
    """Place dialogue text inside detected bubble regions."""

    img = Image.open(comic_path)
    draw = ImageDraw.Draw(img)

    for i, panel in enumerate(script["panels"]):
        bubble = detection["bubbles"][i]
        bbox = bubble["bbox"]  # [x1, y1, x2, y2]

        # Calculate text area (slightly smaller than bubble)
        padding = 10
        text_area = (
            bbox[0] + padding,
            bbox[1] + padding,
            bbox[2] - padding,
            bbox[3] - padding
        )

        # Auto-size font to fit
        dialogue = panel.get("dialogue", [""])[0]
        font_size = self._calculate_font_size(dialogue, text_area)
        font = ImageFont.truetype("Comic Sans MS", font_size)

        # Center text in bubble
        text_bbox = draw.textbbox((0, 0), dialogue, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        center_x = (text_area[0] + text_area[2]) // 2 - text_width // 2
        center_y = (text_area[1] + text_area[3]) // 2 - text_height // 2

        # Draw text with slight shadow for depth
        shadow_offset = 1
        draw.text((center_x + shadow_offset, center_y + shadow_offset),
                  dialogue, fill=(100, 100, 100), font=font)
        draw.text((center_x, center_y), dialogue, fill="black", font=font)

    output_path = comic_path.with_stem(f"{comic_path.stem}_with_text")
    img.save(output_path)
    return output_path
```

### Phase 5: Enhanced PIL Fallback

If all else fails, improve the current PIL approach:

```python
async def _fallback_pil_bubbles(self, comic_path: Path, script: dict) -> Path:
    """Fallback: Draw bubbles with post-processing to match art style."""

    img = Image.open(comic_path)

    # Extract dominant colors from comic for style matching
    colors = self._extract_dominant_colors(img)
    outline_color = colors["darkest"]  # Match line art color

    for i, panel in enumerate(script["panels"]):
        emotion = panel.get("emotion", "speech")

        # Draw emotion-appropriate bubble shape
        if emotion == "thought":
            self._draw_cloud_bubble(img, panel_region, outline_color)
        elif emotion in ["exclaim", "angry"]:
            self._draw_spiky_bubble(img, panel_region, outline_color)
        else:
            self._draw_round_bubble(img, panel_region, outline_color)

        # Add hand-drawn effect
        self._add_wobble_effect(img, panel_region)

        # Add text
        self._add_dialogue_text(img, panel_region, panel["dialogue"])

    return img
```

---

## Implementation Files

| File | Changes |
|------|---------|
| `nanobana_service.py` | Add emotion-based bubble prompts, `include_bubbles` param |
| `gemini_service.py` | Add `detect_speech_bubbles()` method |
| `render_service.py` | Add retry logic, `_place_text_in_bubbles()`, enhanced fallback |
| `models/api.py` | Add `emotion` field to panel model |

---

## Emotion Mapping

Script generation should include emotion per panel:

```python
# In gemini_service.py compose_script()
script_prompt += """
For each panel, also specify the EMOTION of the dialogue:
- "speech" for normal talking
- "thought" for internal thinking
- "exclaim" for excitement, surprise, realization
- "angry" for anger, frustration
- "whisper" for quiet/secret dialogue

Return in JSON:
{
  "panels": [
    {
      "dialogue": ["Hey, what's that?"],
      "emotion": "speech",
      ...
    }
  ]
}
"""
```

---

## Expected Results

**Before** (current):
- Generic white ellipse pasted on top
- Clinical, disconnected look
- Same bubble style for all emotions

**After** (new):
- Bubbles generated as part of art (Nano-Banana)
- Emotion-specific shapes (cloud for thought, spiky for exclaim)
- Text placed precisely inside detected regions
- Cohesive, integrated appearance

---

## Metrics to Track

1. **Bubble detection success rate**: % of comics where Gemini Vision finds all bubbles
2. **Retry rate**: % of comics needing retry
3. **Fallback rate**: % of comics using PIL fallback
4. **Generation time**: Total seconds for comic with bubble integration

---

## This is a TODO for later implementation

This plan documents the approach for integrated speech bubbles. Implementation should be prioritized after:
1. 1x4 panel layout change
2. Celebrate mode
3. User signup flow

Add to `docs/hackathon-rubric.md` as a TODO under Creative Quality.
