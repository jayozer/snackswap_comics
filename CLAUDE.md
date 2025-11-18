# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SnackSwap Comics is an AI-powered progressive web app that transforms photos of snacks into 4-panel comics teaching kids about dental health. It uses Google Gemini for vision detection and script generation, with Qdrant for RAG-based fact retrieval.

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Package Management**: `uv` (required - not pip)
- **AI Models**:
  - Google Gemini Flash (via `google-generativeai`) - Vision detection and script generation
  - Gemini 2.5 Flash Image / Nano-Banana (via `google-genai`) - Comic image generation
- **Vector Database**: Qdrant for semantic search and fact retrieval
- **Image Processing**: Pillow + pillow-heif for HEIC/EXIF handling
- **Frontend**: Next.js/React PWA (planned - not yet implemented)

## Development Setup

### Starting Development

```bash
# From backend directory
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Copy environment template
cp .env.example .env
# Then edit .env to add GEMINI_API_KEY (required)

# Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Seed database (first time only)
./seed_data.sh

# Run development server
./run_server.sh
# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Testing and Linting

```bash
# From backend directory with venv activated

# Run tests (when available)
pytest

# Format code with Black
black app/

# Lint with Ruff
ruff check app/

# Type checking with mypy
mypy app/
```

## Architecture

### API Flow

The application follows a 6-step pipeline:

1. **Capture** (`/api/capture/intake`) - Upload snack photo, return photo_id
2. **Vision** (`/api/vision/detect`) - Gemini detects 1-3 food items
3. **Score** (`/api/score/retrieve`) - Match to snack DB, calculate dental risk, fetch facts/swaps
4. **Script** (`/api/script/compose`) - Gemini generates 4-panel comic script
5. **Render** (`/api/render/comic`) - Generate character images and compose panels
6. **Export** (`/api/export/zip`) - Package with captions and provenance

### Core Components

- **`app/api/`** - FastAPI endpoint handlers, one file per pipeline stage
- **`app/services/`** - Business logic services:
  - `gemini_service.py` - Vision detection and script generation
  - `qdrant_service.py` - Vector search operations
  - `scoring_service.py` - Dental risk calculation (0-100 scale)
  - `image_service.py` - Photo intake and HEIF conversion
  - `render_service.py` - Comic rendering (MVP placeholder)
  - `nanobana_service.py` - Character generation integration
  - `freepik_service.py` - Background/prop generation
- **`app/models/`** - Pydantic models for API contracts and data validation
- **`app/core/`** - Configuration via pydantic-settings

### Qdrant Collections

All collections use 768-dimensional vectors (Gemini text-embedding-004):

- **`snacks_v1`** - Snack database with nutritional and dental risk factors
- **`facts_v1`** - Clinic-approved dental health facts (age-banded: 3-5, 6-8, 9-12)
- **`swaps_v1`** - Healthier alternatives with taste cluster matching
- **`styles_v1`** - Branding styles (colors, fonts, bubble styles)

### Dental Risk Scoring

Formula (app/services/scoring_service.py:23-65):
```
risk_score = 100 * (
    0.45 * normalized(added_sugar_g_per_100g) +
    0.20 * acidity_factor +  # high=1, medium=0.5, low=0.1
    0.20 * stickiness +      # 0..1
    0.10 * residue +         # 0..1
    0.05 * crunch_hardness   # 0..1
)
```

Higher scores = higher dental risk. Swaps must improve score by ≥25 points.

## Key Patterns

### Adding New Endpoints

1. Create handler in `app/api/{stage}.py`
2. Define request/response models in `app/models/api.py`
3. Add business logic to appropriate service in `app/services/`
4. Import and include router in `app/api/__init__.py`

### Working with Qdrant

```python
from app.services.qdrant_service import QdrantService

qdrant = QdrantService(settings)

# Search snacks
results = qdrant.search_snacks(
    query_vector=embedding,
    limit=8,
    filters={"category": "candy"}
)

# Search facts (automatically filters by age band and clinic_approved)
facts = qdrant.search_facts(
    query_vector=embedding,
    age_band="6-8",
    limit=8
)
```

### Generating Embeddings

```python
from app.services.gemini_service import GeminiService

gemini = GeminiService(settings)
embedding = await gemini.generate_embedding(
    text="chocolate chip cookies",
    task_type="retrieval_query"
)
```

## Data Seeding

Edit `data/seeds/seed_data.py` to add snacks, facts, swaps, or styles. Each record needs:
- Unique ID
- Embedding-friendly text (used for vector generation)
- All required fields per schema (see existing examples)

Run `./backend/seed_data.sh` to populate Qdrant.

## Environment Configuration

Required environment variables (in `backend/.env`):
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `QDRANT_URL` - Qdrant server URL (default: http://localhost:6333)

Optional but commonly used:
- `GEMINI_VISION_MODEL` - Model for vision (default: gemini-2.0-flash-exp)
- `GEMINI_WRITER_MODEL` - Model for scripts (default: gemini-2.0-flash-exp)
- `STORAGE_PATH` - Local storage directory (default: ./storage)
- `DEBUG` - Enable debug mode (default: false)

See `backend/.env.example` for complete list.

## Nano-Banana Image Generation

The project uses **Gemini 2.5 Flash Image** (Nano-Banana) for comic image generation via the `google-genai` SDK.

### Key Implementation Details

- Uses the new `google-genai` package (not `google-generativeai`)
- Client-based API: `genai.Client(api_key=...)`
- Streaming response: `generate_content_stream` for receiving image data
- Model name: `"gemini-2.5-flash-image"`
- Image sizes: "256", "512", "1K", "2K", "4K", "8K"
- Response format: Binary image data via `inline_data.data` with mime type

### Workflow

1. **Generate base comic**: Nano-Banana creates 2x2 grid with EMPTY speech bubbles
2. **Text overlay**: Pillow adds Comic Sans text on top of empty bubbles
3. **Export formats**: Resize to square (1080x1080), portrait (1080x1350), reel (1080x1920)

### Important Notes

- Empty bubbles are intentional - text is added as overlay for better control
- Prompts emphasize character consistency across all 4 panels
- Falls back to Pillow rendering if Nano-Banana fails

## Current MVP Limitations

This is an MVP implementation. The following are placeholder implementations:
- **Panel composition** - Freepik API integration needed for enhanced assets
- **Animated comics** - Video generation for Reels (planned v1.1)
- **Database persistence** - Currently uses in-memory storage for scripts
- **Frontend** - Next.js PWA not yet implemented

## Storage Structure

```
backend/storage/
├── uploads/        # Original uploaded photos (JPEG/PNG)
├── thumbs/         # 512×512 thumbnails
└── renders/        # Final comic renders (base, square, portrait, reel)
```

Files are named by photo_id or script_id with appropriate extensions.

## Common Issues

**Qdrant connection fails**: Ensure Docker container is running on port 6333
**HEIC images fail**: Requires pillow-heif, install with: `uv pip install pillow-heif`
**Import errors**: Always activate venv before running: `source backend/.venv/bin/activate`
