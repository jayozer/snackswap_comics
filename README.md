# 🍿 SnackSwap Comics

> Turn snacks into delightful, fact-grounded 4-panel comics that teach kids about dental health!

SnackSwap Comics is an AI-powered progressive web app that transforms a simple photo of a snack or lunch into an engaging comic where foods become characters debating tooth health. Every dental claim is grounded in a clinic-approved knowledge base, and the app offers taste-aligned healthier alternatives.

## ✨ Features

- **📸 Snap & Transform**: Take a photo of any snack → get a 4-panel comic in 30-45 seconds
- **🦷 Fact-Grounded**: All dental health claims are RAG-verified from clinic-approved sources
- **🎭 Character Comics**: Foods become delightful characters with personalities and expressions
- **🔄 Smart Swaps**: Get healthier alternatives that match taste profiles (salty, sweet, crunchy)
- **🎨 Brand-Ready**: Customizable styles, colors, and branding for dental practices
- **📱 Social-Optimized**: Export in multiple formats (1080×1080, 1080×1350, Reel covers)
- **♿ Accessible**: Auto-generated alt text and captions for all content

## 🏗️ Architecture

### Tech Stack

- **Backend**: Python 3.11+ with FastAPI and `uv` for dependency management
- **AI**: Google Gemini (Pro 2.5 / Flash) for vision detection and script generation
- **Vector DB**: Qdrant for RAG-based fact retrieval and semantic search
- **Image Processing**: Pillow + pillow-heif for HEIC/EXIF handling
- **Frontend**: Next.js/React PWA (planned)

### System Components

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Camera    │─────▶│   FastAPI    │─────▶│   Qdrant    │
│  Capture    │      │   Backend    │      │  Vector DB  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Gemini    │
                     │   AI Models  │
                     └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Qdrant server (local or cloud)
- Google Gemini API key

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd snackswap_comics
```

2. **Set up the backend**

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install fastapi uvicorn python-multipart pillow pillow-heif \
    google-generativeai qdrant-client pydantic pydantic-settings \
    httpx python-dotenv numpy opencv-python-headless aiofiles
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GEMINI_API_KEY (required)
# - QDRANT_URL (default: http://localhost:6333)
```

4. **Start Qdrant** (if running locally)

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or install locally: https://qdrant.tech/documentation/quick-start/
```

5. **Seed the database**

```bash
./seed_data.sh
```

6. **Run the server**

```bash
./run_server.sh
# Server will start at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## 📚 API Endpoints

### Capture & Intake

**POST** `/api/capture/intake`
- Upload a snack photo
- Returns: `photo_id`, dimensions, thumbnail URI

### Vision Detection

**POST** `/api/vision/detect`
- Detect food items in the photo using Gemini Vision
- Returns: Detected items with confidence scores

### Score & Retrieve

**POST** `/api/score/retrieve`
- Match items to snack database
- Calculate dental risk scores
- Retrieve relevant facts and swaps
- Returns: Scored items, facts, and swap suggestions

### Script Composition

**POST** `/api/script/compose`
- Generate 4-panel comic script with Gemini
- Returns: Complete script with dialogue, characters, citations

### Render Comic

**POST** `/api/render/comic`
- Render the comic (MVP: placeholder)
- Returns: URIs to rendered assets

### Export

**POST** `/api/export/zip`
- Export complete package with provenance
- Returns: ZIP with images, captions, manifest

## 🗄️ Data Model

### Qdrant Collections

#### `snacks_v1`
Stores snack data with nutritional and dental risk factors:
- Sugar content (total and added)
- Acidity level (low/medium/high)
- Stickiness, residue, crunch hardness (0-1)
- Taste cluster (e.g., "savory-crunch", "sweet-chewy")
- Allergen tags and age flags

#### `facts_v1`
Clinic-approved dental health facts:
- Age-banded content (3-5, 6-8, 9-12, all)
- Topic tags (sugar, acidity, timing, brushing)
- Source citations and reviewer info

#### `swaps_v1`
Healthier alternatives:
- Similar taste clusters
- Lower dental risk scores
- Age suitability and allergen info
- Prep time and example brands

#### `styles_v1`
Branding and visual styles:
- Color palettes
- Font pairings
- Panel layouts and bubble styles
- Logo and watermark URIs

## 🧮 Dental Risk Scoring

```python
risk_score = 100 * (
    0.45 * normalized(added_sugar_g_per_100g) +
    0.20 * acidity_factor +  # high=1, medium=0.5, low=0.1
    0.20 * stickiness +      # 0..1
    0.10 * residue +         # 0..1
    0.05 * crunch_hardness   # 0..1
)
```

Higher scores = higher dental risk. Swaps must improve score by ≥25 points.

## 🎯 Workflow

1. **Capture**: User uploads snack photo
2. **Vision**: Gemini detects 1-3 items with confidence
3. **Match**: Vector search finds similar snacks in Qdrant
4. **Score**: Calculate dental risk for each item
5. **Retrieve**: Fetch age-appropriate facts and taste-aligned swaps
6. **Script**: Gemini composes 4-panel comic with citations
7. **Render**: Generate character images and compose panels
8. **Export**: Package with social captions and provenance

## 📝 Example Flow

```bash
# 1. Upload photo
curl -X POST http://localhost:8000/api/capture/intake \
  -F "file=@snack.jpg"
# → {"photo_id": "abc123", "width": 1200, "height": 900, ...}

# 2. Detect items
curl -X POST http://localhost:8000/api/vision/detect \
  -H "Content-Type: application/json" \
  -d '{"photo_id": "abc123"}'
# → {"items": [{"name": "Gummy Bears", "category": "candy", ...}]}

# 3. Score and retrieve
curl -X POST http://localhost:8000/api/score/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "items": [...],
    "age": 7,
    "allergies": []
  }'
# → {"scored_items": [...], "facts": [...], "swaps": [...]}

# 4. Compose script
curl -X POST http://localhost:8000/api/script/compose \
  -H "Content-Type: application/json" \
  -d '{...}'
# → {"script_id": "def456", "panels": [...], ...}
```

## 🔧 Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | *required* |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` |
| `GEMINI_VISION_MODEL` | Model for vision tasks | `gemini-2.0-flash-exp` |
| `GEMINI_WRITER_MODEL` | Model for script writing | `gemini-2.0-flash-exp` |
| `MAX_UPLOAD_SIZE_MB` | Max image upload size | `10` |
| `ENABLE_MAPS_SWAPS` | Enable Google Maps local swaps | `false` |

See `.env.example` for full configuration options.

## 🧪 Development

### Project Structure

```
snackswap_comics/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration
│   │   ├── models/        # Pydantic models
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Tests (planned)
│   ├── .env.example       # Environment template
│   ├── pyproject.toml     # Python dependencies
│   └── run_server.sh      # Start server script
├── frontend/              # Next.js PWA (planned)
├── data/
│   └── seeds/
│       └── seed_data.py   # Database seeding
└── README.md              # This file
```

### Adding New Snacks

Edit `data/seeds/seed_data.py` and add to the `snacks` list:

```python
{
    "snack_id": "your_snack_id",
    "name": "Snack Name",
    "category": "chips",  # chips, candy, cookie, fruit, beverage, etc.
    "flavor_notes": ["salty", "crunchy"],
    "sugar_g_per_100g": 5.0,
    "added_sugar_g": 2.0,
    "acidity_tag": "low",  # low, medium, high
    "stickiness": 0.2,
    "residue": 0.3,
    # ... see seed_data.py for complete schema
}
```

Then re-run `./backend/seed_data.sh`.

### Adding New Facts

```python
{
    "fact_id": "F999",
    "text": "Your fun, kid-friendly fact here!",
    "topic": ["sugar", "timing"],
    "age_band": "6-8",  # 3-5, 6-8, 9-12, or all
    "source_key": "ClinicKB#YourSource",
    "source_url": "https://...",
    "clinic_approved": True,
}
```

## 🎨 Customization

### Brand Styles

Edit `styles_v1` collection to customize:

- **Colors**: Primary, secondary, accent, background
- **Fonts**: Title, dialogue, caption fonts
- **Bubble styles**: Rounded, sharp, wavy
- **Logos**: Add clinic logo, mascot, watermark

### Age Bands

Content is automatically tailored to three age groups:

- **3-5**: Very simple, playful language
- **6-8**: Friendly, fun explanations
- **9-12**: Engaging, "cool" tone

## 🚧 MVP Limitations

This is an MVP implementation with placeholders for:

- **Character Rendering**: Nano-Banana / DALL-E integration needed
- **Panel Composition**: Freepik API integration and PIL/Pillow assembly
- **Animated Comics**: Video generation for Reels (v1.1)
- **Google Maps Swaps**: Local swap recommendations (v1.1)
- **Database Persistence**: Currently uses in-memory storage for scripts

## 📋 Roadmap

### v0.1 (Current - MVP Backend)
- ✅ FastAPI backend with uv
- ✅ Gemini vision and script composition
- ✅ Qdrant vector database setup
- ✅ Image processing pipeline
- ✅ Dental risk scoring engine
- ✅ Seed data and examples

### v0.2 (Next - Rendering)
- [ ] Character rendering integration
- [ ] Panel composition with Freepik
- [ ] Final image assembly
- [ ] Next.js PWA frontend
- [ ] Camera capture interface

### v0.3 (Enhanced Features)
- [ ] Animated comic shorts (≤15s)
- [ ] Google Maps local swaps
- [ ] User profiles and preferences
- [ ] Analytics and tracking

### v1.0 (Production Ready)
- [ ] Admin dashboard
- [ ] Approval workflow
- [ ] S3/GCS storage
- [ ] Database persistence
- [ ] Comprehensive testing
- [ ] CI/CD pipeline

## 🤝 Contributing

Contributions welcome! Areas of focus:

1. **Character Rendering**: Integrate Nano-Banana or similar for consistent character generation
2. **Panel Composition**: Build the visual compositor for assembling comics
3. **Frontend**: Develop the Next.js PWA with camera capture
4. **Testing**: Add unit and integration tests
5. **Documentation**: Expand API docs and guides

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Google Gemini](https://ai.google.dev/) - Vision and language models
- [Qdrant](https://qdrant.tech/) - Vector database for RAG
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the API docs at `/docs` endpoint
- Review the PRD in the repository

---

**SnackSwap Comics** - Making dental health education delightful, one snack at a time! 🦷✨
