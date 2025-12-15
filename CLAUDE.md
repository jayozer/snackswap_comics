# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SnackSwap Comics is an AI-powered progressive web app that transforms photos of snacks into 4-panel comics teaching kids about dental health through "vanity roasting" - making dental health about aesthetics (white teeth, glow ups) rather than health lectures. It uses Google Gemini for vision detection and script generation, with Qdrant for RAG-based fact retrieval.

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Package Management**: `uv` (required - not pip)
- **AI Models** (via `google-genai` SDK):
  - Gemini 2.5 Flash/Pro - Vision detection with thinking mode
  - Gemini 2.5 Pro - Script generation with thinking budget (up to 24576 tokens)
  - Gemini 3 Pro Image (Nano-Banana) - Comic image generation
- **Vector Database**: Qdrant Cloud for semantic search and fact retrieval
- **Image Processing**: Pillow + pillow-heif for HEIC/EXIF handling
- **Frontend**: Next.js 14 + React 18 + Tailwind CSS + Framer Motion

## Development Commands

### Backend

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .
cp .env.example .env  # Add GEMINI_API_KEY
./seed_data.sh        # First time only
./run_server.sh       # http://localhost:8000, docs at /docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev           # http://localhost:3000
npm run build         # Production build
npm run lint          # ESLint
```

### Testing & Linting (Backend)

```bash
pytest                # Run tests
black app/            # Format
ruff check app/       # Lint
mypy app/             # Type check
```

## Architecture

### 6-Stage Pipeline

1. **Capture** (`/api/capture/intake`) - Upload photo, return photo_id
2. **Vision** (`/api/vision/detect`) - Gemini detects 1-5 items with smart grouping
3. **Score** (`/api/score/retrieve`) - Match to snack DB, calculate dental risk, determine comic mode
4. **Script** (`/api/script/compose`) - Gemini generates 4-panel script with guardrails
5. **Render** (`/api/render/comic`) - Generate images via Nano-Banana, compose panels
6. **Export** (`/api/export/zip`) - Package with captions and provenance

### Comic Modes

| Mode | Trigger | Arc |
|------|---------|-----|
| `CELEBRATE` | avg_risk < 30 | W Arc: Entrance → Stats → Glaze → Crown |
| `EDUCATE` | avg_risk ≥ 30 | Roast Arc: Flex → Exposé → Ratio → Vibe Check |
| `UNKNOWN` | No snack match | Generic Dr. Hawley tips |

### Dr. Hawley Character System

The recurring mascot is Dr. Hawley - an off-white/pale cyan molar in a dark forest green hoodie, shades on forehead, chunky beige slides. Uses "Adult Swim" humor style (Rick and Morty, Smiling Friends energy).

- **Age 9-12 (Spicy)**: Lighter burns, meme-y, "sus", "mid", "skill issue"
- **Age 13-17 (Savage)**: Full destruction mode, "cooked", "L + ratio", "aura"

Roast examples are in `app/data/drhawley_roast_corpus.py` for few-shot prompting.

### Key Services

| Service | Purpose |
|---------|---------|
| `gemini_service.py` | Vision detection, script composition, embeddings |
| `qdrant_service.py` | Vector search across snacks/facts/swaps/styles |
| `scoring_service.py` | Dental risk calculation (0-100 scale) |
| `nanobana_service.py` | Gemini 3 Pro Image generation (2K comics) |
| `render_service.py` | Panel composition, speech bubble overlay |
| `guardrails_service.py` | Content safety validation with auto-clean |
| `audit_service.py` | Generation logging for review |

### Qdrant Collections

All use 768-dim vectors (text-embedding-004):

- `snacks_v1` - Nutritional/dental risk factors
- `facts_v1` - Clinic-approved facts (age-banded: 9-12, 13-17, all)
- `swaps_v1` - Healthier alternatives by taste cluster
- `styles_v1` - Branding (colors, fonts, bubble styles)

### Dental Risk Formula

```
risk = 100 * (
    0.45 * normalized(added_sugar_g_per_100g) +
    0.20 * acidity_factor +  # high=1, medium=0.5, low=0.1
    0.20 * stickiness +      # 0..1
    0.10 * residue +         # 0..1
    0.05 * crunch_hardness   # 0..1
)
```

Swaps must improve score by ≥25 points.

## Key Patterns

### Adding Endpoints

1. Create handler in `app/api/{stage}.py`
2. Define models in `app/models/api.py`
3. Add logic to service in `app/services/`
4. Include router in `app/api/__init__.py`

### Gemini SDK Usage (google-genai)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)

# Vision with thinking
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[...],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=8192)
    )
)

# Embeddings
response = client.models.embed_content(
    model="text-embedding-004",
    contents=[...],
    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
)
```

### Script Dialogue Format

Each dialogue line is an object:
```json
{
  "speaker": "Dr. Hawley",
  "text": "Your teeth are filing a restraining order.",
  "position": "right",
  "emotion": "exclaim"
}
```

Limits: 50 chars per line, 130 chars per panel total.

## Environment Variables

Required:
- `GEMINI_API_KEY` - Google Gemini API key
- `QDRANT_URL` - Qdrant Cloud cluster URL
- `QDRANT_API_KEY` - Qdrant Cloud API key

Key optional:
- `GEMINI_VISION_MODEL` - Vision model (default: gemini-2.5-flash)
- `GEMINI_WRITER_MODEL` - Script model (default: gemini-2.5-pro)
- `GEMINI_IMAGE_MODEL` - Image gen (default: gemini-3-pro-image-preview)
- `GEMINI_WRITER_THINKING_BUDGET` - Thinking tokens (default: 24576)

See `backend/.env.example` for full list.

## Storage Structure

```
backend/storage/
├── uploads/     # Original photos (JPEG/PNG)
├── thumbs/      # 512×512 thumbnails
└── renders/     # Comic renders (base, square 1080×1080, portrait 1080×1350, reel 1080×1920)
```

## Common Issues

- **Qdrant connection fails**: Verify `QDRANT_URL` and `QDRANT_API_KEY` in .env
- **HEIC images fail**: Install `pillow-heif`: `uv pip install pillow-heif`
- **Import errors**: Activate venv: `source backend/.venv/bin/activate`
- **JSON parse errors**: Check for truncated Gemini responses; `_repair_json()` attempts auto-fix

## Commit Guidelines

- Do not mention Claude or Anthropic in commit messages
