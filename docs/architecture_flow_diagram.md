# SnackSwap Comics - Architecture Flow Diagram

## Overview

SnackSwap Comics is an AI-powered progressive web app that transforms photos of snacks into 4-panel educational comics teaching kids about dental health.

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     Frontend (Next.js PWA)                               │   │
│  │   • Photo capture/upload                                                 │   │
│  │   • Comic display & sharing                                              │   │
│  │   • Age selection (9-12, 13-17)                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER (FastAPI)                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ /capture │ │ /vision  │ │  /score  │ │ /script  │ │ /render  │ │ /export  │ │
│  │  intake  │ │  detect  │ │ retrieve │ │ compose  │ │  comic   │ │   zip    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   Image     │ │   Gemini    │ │   Qdrant    │ │  Scoring    │               │
│  │  Service    │ │   Service   │ │   Service   │ │  Service    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                               │
│  │ NanoBanana  │ │   Render    │ │  Freepik    │                               │
│  │  Service    │ │   Service   │ │  Service    │                               │
│  └─────────────┘ └─────────────┘ └─────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SERVICES                                       │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                       │
│  │    Google Gemini API    │  │    Qdrant Vector DB     │                       │
│  │  • Vision detection     │  │  • snacks_v1 (768-dim)  │                       │
│  │  • Script generation    │  │  • facts_v1             │                       │
│  │  • Text embeddings      │  │  • swaps_v1             │                       │
│  │  • Image generation     │  │  • styles_v1            │                       │
│  └─────────────────────────┘  └─────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    Local File Storage                                     │   │
│  │   storage/                                                                │   │
│  │   ├── uploads/    # Original photos (JPEG/PNG)                           │   │
│  │   ├── thumbs/     # 512×512 thumbnails                                   │   │
│  │   └── renders/    # Final comics (base, square, portrait, reel)          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6-Step Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE PIPELINE FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

     USER UPLOADS SNACK PHOTO
              │
              ▼
┌─────────────────────────┐
│   STEP 1: CAPTURE       │
│   POST /api/capture/    │
│        intake           │
├─────────────────────────┤
│ • Receive image upload  │
│ • Convert HEIC → JPEG   │
│ • Generate thumbnail    │
│ • Return photo_id       │
└─────────────────────────┘
              │
              │  photo_id
              ▼
┌─────────────────────────┐
│   STEP 2: VISION        │
│   POST /api/vision/     │
│        detect           │
├─────────────────────────┤
│ • Load image from disk  │
│ • Send to Gemini Vision │
│ • Detect 1-3 food items │
│ • Extract name, brand,  │
│   category, confidence  │
└─────────────────────────┘
              │
              │  DetectedItem[]
              ▼
┌─────────────────────────┐
│   STEP 3: SCORE         │
│   POST /api/score/      │
│       retrieve          │
├─────────────────────────┤
│ • Match items to Qdrant │
│   snacks database       │
│ • Calculate dental risk │
│   (0-100 scale)         │
│ • Fetch relevant facts  │
│   (age-appropriate)     │
│ • Find healthier swaps  │
└─────────────────────────┘
              │
              │  ScoredItem[], facts[], swaps[]
              ▼
┌─────────────────────────┐
│   STEP 4: SCRIPT        │
│   POST /api/script/     │
│       compose           │
├─────────────────────────┤
│ • Send context to       │
│   Gemini Writer         │
│ • Generate 4-panel      │
│   comic script          │
│ • Include dialogue,     │
│   characters, scenes    │
│ • Return script_id      │
└─────────────────────────┘
              │
              │  script_id, panels[]
              ▼
┌─────────────────────────┐
│   STEP 5: RENDER        │
│   POST /api/render/     │
│        comic            │
├─────────────────────────┤
│ • Generate comic image  │
│   via Imagen 4.0        │
│ • PIL draws speech      │
│   bubbles               │
│ • PIL adds dialogue     │
│   text overlay          │
│ • Export multiple       │
│   formats               │
└─────────────────────────┘
              │
              │  comic URIs
              ▼
┌─────────────────────────┐
│   STEP 6: EXPORT        │
│   POST /api/export/zip  │
├─────────────────────────┤
│ • Package all formats   │
│ • Include manifest      │
│   (provenance)          │
│ • Return ZIP download   │
└─────────────────────────┘
              │
              ▼
     USER RECEIVES COMIC
```

---

## Detailed Service Interactions

### Vision Detection Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐
│    Client    │      │ VisionAPI    │      │   Gemini Service     │
│              │      │  /detect     │      │                      │
└──────┬───────┘      └──────┬───────┘      └──────────┬───────────┘
       │                     │                         │
       │  POST {photo_id}    │                         │
       │────────────────────▶│                         │
       │                     │                         │
       │                     │  Load image from disk   │
       │                     │─────────────────────────│
       │                     │                         │
       │                     │  detect_items(image)    │
       │                     │────────────────────────▶│
       │                     │                         │
       │                     │                         │  ┌─────────────────┐
       │                     │                         │──│ Gemini 2.5      │
       │                     │                         │  │ Flash Vision    │
       │                     │                         │  │                 │
       │                     │                         │◀─│ JSON response   │
       │                     │                         │  └─────────────────┘
       │                     │                         │
       │                     │  DetectedItem[]         │
       │                     │◀────────────────────────│
       │                     │                         │
       │  {items, confidence}│                         │
       │◀────────────────────│                         │
       │                     │                         │
```

### Score & Retrieve Flow

```
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│  Client   │   │ ScoreAPI  │   │ Gemini    │   │  Qdrant   │   │ Scoring   │
│           │   │ /retrieve │   │ Service   │   │  Service  │   │ Service   │
└─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
      │               │               │               │               │
      │  POST items   │               │               │               │
      │──────────────▶│               │               │               │
      │               │               │               │               │
      │               │  embed(text)  │               │               │
      │               │──────────────▶│               │               │
      │               │               │               │               │
      │               │   vector[768] │               │               │
      │               │◀──────────────│               │               │
      │               │               │               │               │
      │               │  search_snacks(vector)        │               │
      │               │──────────────────────────────▶│               │
      │               │               │               │               │
      │               │               │   snack matches               │
      │               │◀──────────────────────────────│               │
      │               │               │               │               │
      │               │  calculate_dental_risk(snack) │               │
      │               │──────────────────────────────────────────────▶│
      │               │               │               │               │
      │               │               │               │   risk_score  │
      │               │◀──────────────────────────────────────────────│
      │               │               │               │               │
      │               │  search_facts(vector, age)    │               │
      │               │──────────────────────────────▶│               │
      │               │               │               │               │
      │               │  search_swaps(vector)         │               │
      │               │──────────────────────────────▶│               │
      │               │               │               │               │
      │  {scored, facts, swaps}       │               │               │
      │◀──────────────│               │               │               │
```

### Comic Rendering Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        COMIC RENDERING PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                              script (4 panels)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         STEP A: IMAGE GENERATION                                 │
│                                                                                  │
│    ┌───────────────────────────────────────────────────────────────────────┐    │
│    │                     NanoBanana Service                                 │    │
│    │                                                                        │    │
│    │    Prompt to Imagen 4.0:                                              │    │
│    │    ┌────────────────────────────────────────────────────────────┐     │    │
│    │    │ "Create a 4-panel comic strip in a 2x2 grid layout..."     │     │    │
│    │    │                                                            │     │    │
│    │    │ CRITICAL RULES:                                            │     │    │
│    │    │ • DO NOT draw any speech bubbles                           │     │    │
│    │    │ • DO NOT include any text, words, letters                  │     │    │
│    │    │ • Leave TOP 25% of each panel as plain background          │     │    │
│    │    │ • Draw all characters in BOTTOM 75% only                   │     │    │
│    │    │                                                            │     │    │
│    │    │ CHARACTER CONSISTENCY:                                      │     │    │
│    │    │ • Gummy Gus: Translucent red gummy bear...                 │     │    │
│    │    │ • Captain Sparkle: Superhero tooth with cape...            │     │    │
│    │    └────────────────────────────────────────────────────────────┘     │    │
│    │                                                                        │    │
│    │                              │                                         │    │
│    │                              ▼                                         │    │
│    │                   ┌──────────────────┐                                │    │
│    │                   │   Google Imagen  │                                │    │
│    │                   │      4.0         │                                │    │
│    │                   │   (2048x2048)    │                                │    │
│    │                   └──────────────────┘                                │    │
│    │                              │                                         │    │
│    │                              ▼                                         │    │
│    │                   Raw comic image (no bubbles, no text)               │    │
│    │                                                                        │    │
│    └───────────────────────────────────────────────────────────────────────┘    │
│                                     │                                            │
└─────────────────────────────────────│────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       STEP B: PIL POST-PROCESSING                                │
│                                                                                  │
│    ┌───────────────────────────────────────────────────────────────────────┐    │
│    │                      Render Service                                    │    │
│    │                                                                        │    │
│    │    For each panel (1-4):                                              │    │
│    │                                                                        │    │
│    │    1. Calculate bubble region (top 20% of panel)                      │    │
│    │       ┌──────────────────────────────────────┐                        │    │
│    │       │  x1 = panel_x + 8% margin            │                        │    │
│    │       │  y1 = panel_y + 3% from top          │                        │    │
│    │       │  x2 = panel_x + panel_width - 8%     │                        │    │
│    │       │  y2 = panel_y + 20% from top         │                        │    │
│    │       └──────────────────────────────────────┘                        │    │
│    │                                                                        │    │
│    │    2. Draw speech bubble (PIL)                                        │    │
│    │       • White ellipse with 3px black outline                          │    │
│    │       • Tail triangle pointing toward characters                      │    │
│    │                                                                        │    │
│    │    3. Add dialogue text (PIL)                                         │    │
│    │       • Comic Sans MS font                                            │    │
│    │       • Auto-size to fit bubble (14-28px)                             │    │
│    │       • Centered horizontally and vertically                          │    │
│    │                                                                        │    │
│    └───────────────────────────────────────────────────────────────────────┘    │
│                                     │                                            │
└─────────────────────────────────────│────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        STEP C: EXPORT FORMATS                                    │
│                                                                                  │
│         Base Image                                                               │
│        (2048x2048)                                                               │
│             │                                                                    │
│             ├──────────────▶  Square (1080x1080)  ──▶  Instagram, TikTok       │
│             │                                                                    │
│             ├──────────────▶  Portrait (1080x1350) ──▶  Instagram Stories       │
│             │                                                                    │
│             └──────────────▶  Reel (1080x1920)    ──▶  Video platforms          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Dental Risk Scoring Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DENTAL RISK CALCULATION                                  │
│                                                                                  │
│    risk_score = 100 × (                                                         │
│        0.45 × normalized(added_sugar_g_per_100g)    ← Sugar content (45%)       │
│      + 0.20 × acidity_factor                         ← Acid erosion (20%)       │
│      + 0.20 × stickiness                             ← Stays on teeth (20%)     │
│      + 0.10 × residue                                ← Film on teeth (10%)      │
│      + 0.05 × crunch_hardness                        ← Can crack teeth (5%)     │
│    )                                                                             │
│                                                                                  │
│    ┌────────────────────────────────────────────────────────────────────────┐   │
│    │  Example: Gummy Bears                                                   │   │
│    │                                                                         │   │
│    │  • added_sugar_g = 40g/100g  →  normalized = 0.8                       │   │
│    │  • acidity_tag = "high"      →  factor = 1.0                           │   │
│    │  • stickiness = 0.9          →  (very sticky)                          │   │
│    │  • residue = 0.3             →  (moderate)                             │   │
│    │  • crunch_hardness = 0.0     →  (soft)                                 │   │
│    │                                                                         │   │
│    │  risk = 100 × (0.45×0.8 + 0.20×1.0 + 0.20×0.9 + 0.10×0.3 + 0.05×0.0)  │   │
│    │       = 100 × (0.36 + 0.20 + 0.18 + 0.03 + 0.00)                       │   │
│    │       = 100 × 0.77                                                      │   │
│    │       = 77 (HIGH RISK)                                                  │   │
│    └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│    Risk Categories:                                                              │
│    ┌────────────────────────────────────────────────────────────────────────┐   │
│    │  0-25   │  LOW      │  Green   │  Generally safe for teeth            │   │
│    │  26-50  │  MODERATE │  Yellow  │  Okay occasionally                    │   │
│    │  51-75  │  HIGH     │  Orange  │  Limit consumption                    │   │
│    │  76-100 │  VERY HIGH│  Red     │  Avoid or brush immediately          │   │
│    └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Qdrant Vector Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         QDRANT COLLECTIONS                                       │
│                      (768-dimensional vectors via Gemini text-embedding-004)     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐
│     snacks_v1               │
├─────────────────────────────┤
│ • snack_id (string)         │
│ • name (string)             │
│ • category (string)         │
│ • added_sugar_g (float)     │
│ • acidity_tag (string)      │
│ • stickiness (float)        │
│ • residue (float)           │
│ • crunch_hardness (float)   │
│ • taste_cluster (string)    │
│ • embedding_text (string)   │
└─────────────────────────────┘

┌─────────────────────────────┐
│     facts_v1                │
├─────────────────────────────┤
│ • fact_id (string)          │
│ • fact_text (string)        │
│ • age_band (string)         │ ← "9-12", "13-17", "all"
│ • clinic_approved (bool)    │
│ • source (string)           │
│ • embedding_text (string)   │
└─────────────────────────────┘

┌─────────────────────────────┐
│     swaps_v1                │
├─────────────────────────────┤
│ • swap_id (string)          │
│ • name (string)             │
│ • dental_risk_score (float) │
│ • taste_cluster (string)    │
│ • allergy_tags (list)       │
│ • prep_time (string)        │
│ • popularity_score (float)  │
│ • suitability (dict)        │
│ • embedding_text (string)   │
└─────────────────────────────┘

┌─────────────────────────────┐
│     styles_v1               │
├─────────────────────────────┤
│ • style_id (string)         │
│ • name (string)             │
│ • colors (dict)             │
│ • fonts (dict)              │
│ • bubble_style (string)     │
│ • embedding_text (string)   │
└─────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

  User Photo                                                      Final Comic
      │                                                                ▲
      │                                                                │
      ▼                                                                │
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐    │
│   JPEG/   │────▶│  Gemini   │────▶│  Qdrant   │────▶│  Gemini   │────┤
│   HEIC    │     │  Vision   │     │  Search   │     │  Writer   │    │
│   PNG     │     │           │     │           │     │           │    │
└───────────┘     └───────────┘     └───────────┘     └───────────┘    │
                        │                 │                 │           │
                        ▼                 ▼                 ▼           │
                  ┌───────────┐     ┌───────────┐     ┌───────────┐    │
                  │ Detected  │     │ • Snacks  │     │  4-Panel  │    │
                  │  Items:   │     │ • Facts   │     │  Script   │    │
                  │ • Name    │     │ • Swaps   │     │ • Title   │    │
                  │ • Brand   │     │ • Risk    │     │ • Dialog  │    │
                  │ • Type    │     │   Score   │     │ • Scene   │    │
                  └───────────┘     └───────────┘     └───────────┘    │
                                                            │           │
                                                            ▼           │
                                                      ┌───────────┐    │
                                                      │  Imagen   │    │
                                                      │   4.0     │────┘
                                                      │           │
                                                      └───────────┘
                                                            │
                                                            ▼
                                                      ┌───────────┐
                                                      │   PIL     │
                                                      │ Overlay   │
                                                      │ • Bubbles │
                                                      │ • Text    │
                                                      └───────────┘
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TECHNOLOGY STACK                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│  BACKEND                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                     │
│  │   Python 3.11  │  │    FastAPI     │  │    Pydantic    │                     │
│  │                │  │   (async)      │  │  (validation)  │                     │
│  └────────────────┘  └────────────────┘  └────────────────┘                     │
│                                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                     │
│  │   Pillow       │  │  pillow-heif   │  │  opencv-python │                     │
│  │ (image proc)   │  │ (HEIC support) │  │  (detection)   │                     │
│  └────────────────┘  └────────────────┘  └────────────────┘                     │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│  AI SERVICES                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          Google Gemini API                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │ Gemini 2.5   │  │ Gemini Flash │  │ text-embed   │  │  Imagen 4.0  │   │ │
│  │  │ Flash Vision │  │   (writer)   │  │   -004       │  │  (images)    │   │ │
│  │  │              │  │              │  │              │  │              │   │ │
│  │  │ • Detect     │  │ • Script     │  │ • 768-dim    │  │ • 2048×2048  │   │ │
│  │  │   snacks     │  │   generation │  │   vectors    │  │ • 4-panel    │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│  DATA STORAGE                                                                    │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │         Qdrant Vector DB           │  │        Local File System           │ │
│  │  • Semantic search                 │  │  • storage/uploads/                │ │
│  │  • 768-dim embeddings              │  │  • storage/thumbs/                 │ │
│  │  • Docker: localhost:6333          │  │  • storage/renders/                │ │
│  └────────────────────────────────────┘  └────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│  PACKAGE MANAGEMENT                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                               UV                                            │ │
│  │           Fast Python package manager (NOT pip)                             │ │
│  │           • uv venv                                                         │ │
│  │           • uv pip install -e .                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
snackswap_comics/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoint handlers
│   │   │   ├── __init__.py         # Router aggregation
│   │   │   ├── capture.py          # POST /api/capture/intake
│   │   │   ├── vision.py           # POST /api/vision/detect
│   │   │   ├── score.py            # POST /api/score/retrieve
│   │   │   ├── script.py           # POST /api/script/compose
│   │   │   ├── render.py           # POST /api/render/comic
│   │   │   └── export.py           # POST /api/export/zip
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── image_service.py    # Photo intake, HEIC conversion
│   │   │   ├── gemini_service.py   # Vision, embeddings, script writing
│   │   │   ├── qdrant_service.py   # Vector search operations
│   │   │   ├── scoring_service.py  # Dental risk calculation
│   │   │   ├── nanobana_service.py # Imagen 4.0 image generation
│   │   │   ├── render_service.py   # Comic composition, PIL overlay
│   │   │   └── freepik_service.py  # Asset enhancement (planned)
│   │   │
│   │   ├── models/                 # Pydantic models
│   │   │   ├── api.py              # Request/Response models
│   │   │   ├── snack.py            # Snack data model
│   │   │   ├── fact.py             # Dental fact model
│   │   │   ├── swap.py             # Swap suggestion model
│   │   │   ├── comic.py            # Comic panel model
│   │   │   └── style.py            # Styling model
│   │   │
│   │   ├── core/
│   │   │   └── config.py           # pydantic-settings configuration
│   │   │
│   │   └── main.py                 # FastAPI application entry
│   │
│   ├── data/
│   │   └── seeds/
│   │       └── seed_data.py        # Database seed data
│   │
│   ├── storage/                    # Generated files
│   │   ├── uploads/
│   │   ├── thumbs/
│   │   └── renders/
│   │
│   ├── pyproject.toml              # Python dependencies
│   ├── run_server.sh               # Start dev server
│   └── seed_data.sh                # Seed Qdrant
│
├── frontend/                       # Next.js PWA (planned)
│
├── docs/
│   └── architecture_flow_diagram.md  # This document
│
└── CLAUDE.md                       # Project instructions
```

---

## API Endpoints Summary

| Endpoint | Method | Input | Output | Service |
|----------|--------|-------|--------|---------|
| `/api/capture/intake` | POST | Image file (multipart) | `photo_id`, thumbnail URI | ImageService |
| `/api/vision/detect` | POST | `photo_id` | Detected items (1-3) | GeminiService |
| `/api/score/retrieve` | POST | Items, age, allergies | Scored items, facts, swaps | ScoringService, QdrantService |
| `/api/script/compose` | POST | Scored data, style | 4-panel script | GeminiService |
| `/api/render/comic` | POST | `script_id` | Comic URIs (3 formats) | RenderService, NanoBananaService |
| `/api/export/zip` | POST | `content_id` | ZIP with manifest | (not yet implemented) |

---

## Key Design Decisions

1. **PIL-drawn speech bubbles**: AI image models cannot reliably create empty bubbles, so PIL draws them during post-processing for consistency.

2. **Three-tier bubble detection** (legacy): Vision API → OpenCV → Fixed-position fallback. Now simplified to fixed-position only.

3. **768-dimensional embeddings**: Using Gemini's `text-embedding-004` model for semantic search across all Qdrant collections.

4. **Age-banded facts**: Facts are filtered by age band (9-12, 13-17) to ensure age-appropriate content.

5. **Swap ranking algorithm**: Considers risk improvement (must be ≥25 points), taste cluster match, allergens, age suitability, and prep time.

6. **Multiple export formats**: Square (1080×1080), Portrait (1080×1350), and Reel (1080×1920) to support various social media platforms.
