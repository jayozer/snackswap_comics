# Qdrant Cloud Migration & Freepik Integration Plan

> **Status**: COMPLETED
> **Last Updated**: 2025-11-29
> **Completed**: 2025-11-29

---

## Table of Contents
1. [Overview](#overview)
2. [Part 1: Qdrant Cloud Migration](#part-1-qdrant-cloud-migration)
3. [Part 2: Freepik Full Integration](#part-2-freepik-full-integration)
4. [Step-by-Step Implementation Checklist](#step-by-step-implementation-checklist)
5. [Testing & Validation](#testing--validation)
6. [Rollback Procedures](#rollback-procedures)

---

## Overview

### Final State (COMPLETED)
| Component | Status | Location |
|-----------|--------|----------|
| Qdrant | Qdrant Cloud (always-on) | `https://*.us-east-1-1.aws.cloud.qdrant.io` |
| Freepik API Client | Complete | `app/services/freepik_service.py` |
| Freepik Enhancement | Fully implemented | `app/services/render_service.py` |
| Payload Indexes | Created | `clinic_approved`, `age_band`, `is_default`, etc. |

---

## Part 1: Qdrant Cloud Migration

### Why Migrate to Cloud?

| Docker (Current) | Qdrant Cloud (Target) |
|------------------|----------------------|
| Must run `docker run` every session | Always available 24/7 |
| Data lost if container deleted | Persistent cloud storage |
| Local machine only | Accessible from anywhere |
| No built-in viewer | **Web dashboard included** |
| Free | Free tier: 1GB storage |

### Architecture Change

```
BEFORE:
┌─────────────────┐     ┌─────────────────┐
│  FastAPI App    │────▶│  Docker Qdrant  │
│  localhost:8000 │     │  localhost:6333 │
└─────────────────┘     └─────────────────┘

AFTER:
┌─────────────────┐     ┌─────────────────────────┐
│  FastAPI App    │────▶│  Qdrant Cloud           │
│  localhost:8000 │     │  *.cloud.qdrant.io:6333 │
└─────────────────┘     └─────────────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Web Dashboard  │
                        │  (Built-in UI)  │
                        └─────────────────┘
```

### Collections to Migrate

| Collection | Purpose | Approx Records |
|------------|---------|----------------|
| `snacks_v1` | Food items with dental risk factors | 4+ |
| `facts_v1` | Clinic-approved dental health facts | 5+ |
| `swaps_v1` | Healthier snack alternatives | 4+ |
| `styles_v1` | Comic branding/styling templates | 1+ |

All collections use **768-dimensional vectors** from `text-embedding-004`.

### Configuration Changes

**File: `backend/.env`**
```env
# Qdrant Cloud Configuration
QDRANT_URL=https://YOUR-CLUSTER-ID.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key_from_qdrant_dashboard

# Get these from: https://cloud.qdrant.io → Clusters → Your Cluster → API Keys
```

### No Code Changes Required

The existing `qdrant_service.py` already supports cloud deployment:

```python
# app/services/qdrant_service.py (existing code)
self.client = QdrantClient(
    url=settings.qdrant_url,      # ← Just change this in .env
    api_key=settings.qdrant_api_key,  # ← Add this in .env
    timeout=30,
)
```

---

## Part 2: Freepik Full Integration

### What Freepik Provides

The Freepik API gives access to professional comic assets:

| Asset Type | Search Query | Use Case |
|------------|--------------|----------|
| **Speech Bubbles** | `"comic speech bubble vector"` | Replace PIL-drawn ellipses |
| **Comic Frames** | `"comic panel border frame vector"` | Stylized panel borders |
| **Backgrounds** | `"bright colorful comic background vector"` | Panel backdrops |

### Current Implementation Status

```
freepik_service.py          render_service.py
┌─────────────────────┐     ┌─────────────────────────────────┐
│ ✅ search_assets()   │     │ _enhance_with_freepik()         │
│ ✅ download_asset()  │     │ ┌─────────────────────────────┐ │
│ ✅ get_speech_bubbles│────▶│ │  # TODO: Implement this     │ │
│ ✅ get_comic_frames  │     │ │  return base_image_path     │ │
│ ✅ get_backgrounds   │     │ └─────────────────────────────┘ │
│ ✅ Caching (MD5)     │     │                                 │
└─────────────────────┘     └─────────────────────────────────┘
      COMPLETE                      NOT IMPLEMENTED
```

### Rendering Pipeline (Enhanced)

```
                          CURRENT PIPELINE
                          ================
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Nano-Banana  │───▶│ PIL Text     │───▶│ (Freepik     │───▶│ Export       │
│ Generate     │    │ Overlay      │    │  SKIPPED)    │    │ Formats      │
│ 2x2 Comic    │    │              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

                          ENHANCED PIPELINE
                          =================
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Nano-Banana  │───▶│ Freepik      │───▶│ PIL Text     │───▶│ Export       │
│ Generate     │    │ Enhancement  │    │ Overlay      │    │ Formats      │
│ 2x2 Comic    │    │ - Bubbles    │    │ (on Freepik  │    │              │
│              │    │ - Frames     │    │  bubbles)    │    │              │
│              │    │ - Backgrounds│    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Layer Compositing Order

```
Layer 4 (Top):    Text dialogue (PIL)
                  ▲
Layer 3:          Speech bubbles (Freepik SVG → PNG)
                  ▲
Layer 2:          Base comic with characters (Nano-Banana)
                  ▲
Layer 1 (Bottom): Comic frames/borders (Freepik SVG → PNG)
```

### Technical Requirements

**New Dependency: `cairosvg`**

Freepik assets are SVG vectors. We need to convert them to PNG for PIL compositing.

```toml
# backend/pyproject.toml
dependencies = [
    # ... existing ...
    "cairosvg>=2.7.0",  # SVG to PNG conversion
]
```

**System Requirement**: `cairosvg` requires Cairo graphics library:
- macOS: `brew install cairo`
- Ubuntu: `sudo apt-get install libcairo2-dev`
- Already installed on most systems

---

## Step-by-Step Implementation Checklist

### Phase 1: Qdrant Cloud Migration

#### Step 1.1: Get Qdrant Cloud Credentials
- [x] Log into https://cloud.qdrant.io
- [x] Navigate to your cluster
- [x] Copy the **Cluster URL** (e.g., `https://abc123.us-east-1-1.aws.cloud.qdrant.io`)
- [x] Generate an **API Key** from the "API Keys" section
- [x] Save both values securely

#### Step 1.2: Update Environment Configuration
- [x] Open `backend/.env`
- [x] Update `QDRANT_URL` to your cloud cluster URL
- [x] Add `QDRANT_API_KEY` with your API key
- [x] Save the file

#### Step 1.3: Seed Data to Cloud
- [x] Activate virtual environment: `source backend/.venv/bin/activate`
- [x] Run seed script: `cd backend && python -m data.seeds.seed_data`
- [x] Verify output shows successful upserts to all 4 collections

#### Step 1.4: Create Payload Indexes (CRITICAL for Cloud)
- [x] Run: `cd backend && python -m data.create_indexes`
- [x] Indexes created: `clinic_approved`, `age_band`, `is_default`, `taste_cluster`, `allergy_tags`, `category`

#### Step 1.5: Verify in Qdrant Dashboard
- [x] Go to https://cloud.qdrant.io → Your Cluster → Collections
- [x] Confirm `snacks_v1`, `facts_v1`, `swaps_v1`, `styles_v1` exist
- [x] Check vector counts match expected seed data

#### Step 1.6: Test Application
- [x] Start server: `./backend/run_server.sh`
- [x] Test health check: `curl http://localhost:8000/health`
- [x] Test score endpoint with sample data
- [x] Verify no connection errors in logs

---

### Phase 2: Freepik Integration

#### Step 2.1: Add Freepik API Key
- [x] Open `backend/.env`
- [x] Add `FREEPIK_API_KEY=your_key_here`
- [x] Save the file

#### Step 2.2: Install Cairo Dependency (if needed)
- [x] macOS: `brew install cairo`
- [x] Linux: `sudo apt-get install libcairo2-dev`

#### Step 2.3: Add CairoSVG to Dependencies
- [x] Open `backend/pyproject.toml`
- [x] Add `"cairosvg>=2.7.0"` to dependencies list
- [x] Run: `cd backend && uv pip install -e .`

#### Step 2.4: Add SVG Conversion Helper
- [x] Open `backend/app/services/render_service.py`
- [x] Add `_svg_to_png()` method after `__init__`:

```python
def _svg_to_png(self, svg_path: Path, width: int, height: int) -> Image.Image:
    """Convert SVG to PIL Image at specified size."""
    import cairosvg
    from io import BytesIO

    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=width,
        output_height=height,
    )
    return Image.open(BytesIO(png_data)).convert("RGBA")
```

#### Step 2.5: Implement `_enhance_with_freepik()`
- [x] Replace the TODO placeholder at line 895-913
- [x] Implement full enhancement logic:

```python
async def _enhance_with_freepik(
    self,
    base_image_path: Path,
    script: dict[str, Any],
) -> Path:
    """
    Enhance comic with Freepik assets.

    Layering order (bottom to top):
    1. Base comic image (characters from Nano-Banana)
    2. Comic frames (panel borders)
    3. Speech bubbles (professional vectors)
    """
    try:
        img = Image.open(base_image_path).convert("RGBA")
        img_width, img_height = img.size
        panel_width = img_width // 2
        panel_height = img_height // 2

        logger.info(f"Enhancing {img_width}x{img_height} comic with Freepik assets")

        # Fetch assets (cached after first download)
        import asyncio
        bubble_paths, frame_paths = await asyncio.gather(
            self.freepik.get_speech_bubbles(style="comic", limit=1),
            self.freepik.get_comic_frames(limit=1),
        )

        # Convert SVG bubble to PNG at appropriate size
        bubble_img = None
        if bubble_paths:
            try:
                bubble_img = self._svg_to_png(
                    bubble_paths[0],
                    width=int(panel_width * 0.75),
                    height=int(panel_height * 0.16),
                )
                logger.info(f"Loaded speech bubble: {bubble_img.size}")
            except Exception as e:
                logger.warning(f"Failed to convert bubble SVG: {e}")

        # Convert SVG frame to PNG
        frame_img = None
        if frame_paths:
            try:
                frame_img = self._svg_to_png(
                    frame_paths[0],
                    width=panel_width,
                    height=panel_height,
                )
                logger.info(f"Loaded comic frame: {frame_img.size}")
            except Exception as e:
                logger.warning(f"Failed to convert frame SVG: {e}")

        # Apply to each panel
        panels = script.get("panels", [])
        for i, panel in enumerate(panels):
            if i >= 4:
                break

            row, col = i // 2, i % 2
            panel_x = col * panel_width
            panel_y = row * panel_height

            # Apply frame border (alpha composite)
            if frame_img:
                # Create a copy to avoid modifying original
                frame_copy = frame_img.copy()
                img.paste(frame_copy, (panel_x, panel_y), frame_copy)

            # Apply speech bubble if panel has dialogue
            if bubble_img and panel.get("dialogue"):
                bubble_x = panel_x + int(panel_width * 0.12)
                bubble_y = panel_y + int(panel_height * 0.02)
                img.paste(bubble_img, (bubble_x, bubble_y), bubble_img)

        # Save enhanced image
        output_path = self.renders_path / f"{base_image_path.stem}_enhanced.png"
        img.save(output_path, "PNG", quality=95)
        logger.info(f"Freepik enhancement saved: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Freepik enhancement failed: {e}", exc_info=True)
        return base_image_path
```

#### Step 2.6: Update Pipeline Order
- [x] Modify `render_comic()` to apply text AFTER Freepik enhancement
- [x] Update the try/except block around line 76-82:

```python
# Step 3: Optionally enhance with Freepik assets
if use_freepik and self.settings.freepik_api_key:
    try:
        logger.info("Enhancing comic with Freepik assets")
        enhanced_path = await self._enhance_with_freepik(base_comic_path, script)
        # Re-apply text overlay on top of Freepik bubbles
        final_output = self.renders_path / f"{content_id}_final.png"
        base_comic_path = await self._add_text_overlay(enhanced_path, script, final_output)
    except Exception as e:
        logger.warning(f"Freepik enhancement failed: {e}. Using base comic.")
```

#### Step 2.7: Update `.env.example`
- [x] Add documentation for new environment variables:

```env
# Freepik API (optional - enables professional comic assets)
# Get your key at: https://www.freepik.com/api
FREEPIK_API_KEY=your_freepik_api_key_here
```

---

### Phase 3: Documentation Updates

#### Step 3.1: Update CLAUDE.md
- [x] Remove "Freepik enhancement optional only" from MVP limitations
- [x] Update Qdrant section to mention cloud option

#### Step 3.2: Update Documentation
- [x] Add Qdrant Cloud setup instructions
- [x] Add Freepik API key instructions
- [x] Update `todo.md` with completion status
- [x] Update `architecture_flow_diagram.md`

---

## Testing & Validation

### Qdrant Cloud Tests

```bash
# 1. Test connection
curl -H "api-key: YOUR_API_KEY" \
     https://YOUR-CLUSTER.cloud.qdrant.io:6333/collections

# 2. Test search endpoint
curl -X POST http://localhost:8000/api/score/retrieve \
     -H "Content-Type: application/json" \
     -d '{"photo_id": "test", "items": [{"name": "gummy bears"}], "age": 7}'
```

### Freepik Integration Tests

```bash
# 1. Test render endpoint with Freepik enabled
curl -X POST http://localhost:8000/api/render/comic \
     -H "Content-Type: application/json" \
     -d '{"script_id": "test-script-id"}'

# 2. Check for cached Freepik assets
ls -la backend/storage/freepik_cache/

# 3. Compare outputs
# - With Freepik: snackswap_*_enhanced.png
# - Without Freepik: snackswap_*_base.png
```

### Visual Comparison Checklist

- [x] Speech bubbles are professional vector quality (not PIL ellipses)
- [x] Text is readable inside Freepik bubbles
- [x] Comic frames add visual polish to panel borders
- [x] No visual artifacts or transparency issues
- [x] All 4 panels have consistent styling

### Test Results (2025-11-29)
- **Test Image**: Gummy bears photo
- **Detection**: "Gummy Bears" (100% confidence)
- **Dental Risk**: 74.4/100 (High Risk)
- **Facts Retrieved**: 3 age-appropriate facts from Qdrant Cloud
- **Comic Generated**: 4-panel comic with AI characters + PIL text overlay
- **Export Formats**: Square, Portrait, Reel all working

---

## Rollback Procedures

### Rollback Qdrant to Docker

```env
# backend/.env
QDRANT_URL=http://localhost:6333
# Remove or comment out: QDRANT_API_KEY=...
```

Then restart Docker: `docker run -p 6333:6333 qdrant/qdrant`

### Disable Freepik Enhancement

Option 1: Remove API key
```env
# backend/.env
# Comment out or remove:
# FREEPIK_API_KEY=...
```

Option 2: Set `use_freepik=False` in render endpoint call

The fallback logic in `render_comic()` already handles failures gracefully.

---

## Future Enhancements

Once this integration is complete, consider:

1. **Background Themes** - Use `get_backgrounds()` for panel-specific backdrops
2. **Style Variants** - Different bubble styles per character emotion
3. **Caching Strategy** - Pre-fetch popular assets at startup
4. **A/B Testing** - Compare engagement with/without Freepik assets
