# SnackSwap Comics - Implementation Status

> **Last Updated**: 2025-12-08
> **Status**: MVP Complete + "Roast My Snack" Pivot Complete (5.3 ✓)
> **Branch**: user-signup
> **Target Audience**: Teens 9-17 (Spicy/Savage modes)

---

## Completed Features

### Phase 4: Anthropic Brand Update
- [x] Update Tailwind config with Anthropic brand colors
- [x] Update CSS variables in globals.css
- [x] Modernize comic elements (speech bubbles, borders, buttons)
- [x] Update all components with new color scheme
- [x] Fix ScanningOverlay brand colors
- [x] Fix socket hang up error (direct backend call for render)
- [x] Add /storage proxy rewrite for comic images

### Phase 1: Backend - Comic Rendering Service

#### 1.1 Nano-Banana Service
- [x] Create `app/services/nanobana_service.py`
- [x] Implement `NanoBananaService` class
  - [x] `generate_comic_image()` method - takes script, returns 4-panel image
  - [x] Build detailed visual prompts from script panels
  - [x] Handle Gemini Image API calls
  - [x] Implement character consistency techniques
  - [x] Error handling and retry logic

#### 1.2 Freepik Integration Service
- [x] Create `app/services/freepik_service.py`
- [x] Implement `FreepikService` class
  - [x] `search_assets()` - search for comic elements
  - [x] `download_asset()` - fetch and cache assets
  - [x] Asset caching system (avoid re-downloading)
  - [x] Search for speech bubbles, frames, backgrounds
  - [x] Handle API authentication
- [x] Add Freepik API key to configuration

#### 1.3 Comic Rendering Service
- [x] Create `app/services/render_service.py`
- [x] Implement `RenderService` class
  - [x] `render_comic()` - main orchestration method
  - [x] **Step 1**: Parse script and extract panel data
  - [x] **Step 2**: Generate 4-panel image with Nano-Banana
  - [x] **Step 3**: (Optional) Fetch Freepik assets - `_enhance_with_freepik()`
  - [x] **Step 4**: Composite image with Pillow
  - [x] **Step 5**: Add text overlays (dialogue, captions)
  - [x] **Step 6**: Generate 3 export formats (Square, Portrait, Reel)
  - [x] Save to storage with proper naming
- [x] Add helper functions for text rendering (`_svg_to_png()`)
- [x] Add helper functions for image composition

#### 1.4 Render API Endpoint
- [x] Update `app/api/render.py`
- [x] Integrate `RenderService`
- [x] Return real URIs for all 3 formats
- [x] Add proper error handling

#### 1.5 Configuration & Environment
- [x] Verify `FREEPIK_API_KEY` is set
- [x] Add `cairosvg>=2.7.0` dependency for SVG→PNG conversion
- [x] Update `.env.example` with new variables

---

### Phase 2: Frontend Development

#### 2.1 Frontend Structure
- [x] Create `frontend/` directory with React app
- [x] Set up basic file structure
- [x] Add styling (Tailwind-style CSS)

#### 2.2 Comic Viewer Interface
- [x] **Upload Section**: File upload, image preview, age input
- [x] **Processing Indicators**: Step-by-step progress display
- [x] **Results Display**: Detected items, risk score, facts, comic
- [x] **Download Options**: Square, Portrait, Reel download buttons

#### 2.3 API Integration
- [x] Implement API client functions for all 6 endpoints
- [x] Handle API responses and errors
- [x] Update UI based on API responses

#### 2.4 CORS & Serving
- [x] FastAPI CORS configured for frontend
- [x] Frontend served via Vite dev server

---

### Phase 3: Infrastructure

#### 3.1 Qdrant Cloud Migration
- [x] Set up Qdrant Cloud cluster
- [x] Configure `QDRANT_URL` and `QDRANT_API_KEY`
- [x] Seed data to cloud (all 4 collections)
- [x] Create payload indexes for filtered fields:
  - [x] `clinic_approved` (bool) on `facts_v1`
  - [x] `age_band` (keyword) on `facts_v1`
  - [x] `is_default` (bool) on `styles_v1`
  - [x] `taste_cluster` (keyword) on `swaps_v1`
  - [x] `allergy_tags` (keyword) on `swaps_v1`
  - [x] `category` (keyword) on `snacks_v1`
- [x] Create `data/create_indexes.py` helper script
- [x] Update `qdrant_service.py` with `_ensure_payload_indexes()` method

---

## End-to-End Test Results

**Test: Gummy Bears Photo**
- [x] Upload photo: Success
- [x] Vision detection: "Gummy Bears" (100% confidence)
- [x] Dental risk scoring: 74.4/100 (High Risk)
- [x] Fact retrieval: 3 age-appropriate facts
- [x] Script composition: 4-panel narrative generated
- [x] Comic rendering: AI-generated image with PIL text overlay
- [x] Export formats: Square, Portrait, Reel available

---

## Phase 5: Hackathon Enhancements

### 5.1 Panel Layout Overhaul (COMPLETED ✓)
*Prerequisite for: Speech Bubble Integration, Export Format improvements*
*All export formats tested and working: Square (1080×1080), Portrait (1080×1350), Reel (1080×1920)*

- [x] **1x4 Vertical Strip Layout** (Hybrid approach: 1x4 base, 2x2 for square export)
  - [x] Update `nanobana_service.py` prompt to generate 1x4 vertical strip (512×1024 at 1K)
  - [x] Update `render_service.py` panel coordinate calculations:
    - [x] `_generate_with_pillow()` - 1x4 vertical fallback layout
    - [x] `_add_text_overlay()` - adjust text positions for vertical layout
    - [x] `_enhance_with_freepik()` - adjust bubble/frame placement for vertical
    - [x] `_detect_bubbles_with_vision()` - update prompt for vertical panels
  - [x] Update export format resizing logic with hybrid approach:
    - [x] Square (1080×1080): **Rearrange** 1x4 to 2x2 grid, then scale
    - [x] Portrait (1080×1350): Scale 1x4 strip, center crop
    - [x] Reel (1080×1920): Scale 1x4 strip, slight crop
  - [x] Add `_rearrange_to_grid()` helper method for square export
  - [x] Test all 3 export formats with new layout ✓
    - Square (1080×1080): 2x2 grid rearrangement working
    - Portrait (1080×1350): Pillarboxing working
    - Reel (1080×1920): Pillarboxing working
  - **File References**: `nanobana_service.py`, `render_service.py`
  - **Future Enhancement**: Upgrade from 1K (512×1024) to 2K (1024×2048) resolution

### 5.2 Celebrate Mode + Qdrant Enhancements (COMPLETED ✓)
*Shows app handles healthy snacks positively + advanced search - key hackathon features*
*Combined because both require seed data changes and re-seeding*

#### 5.2.1 Seed Data Updates (Single Re-Seed)
- [x] Add `fact_type` field to existing facts (default: "educate")
- [x] Add `risk_tags` field to all facts:
  - [x] "sticky" for sticky candy facts
  - [x] "sugary" for sugar/bacteria facts
  - [x] "acidic" for acid erosion facts
  - [x] "hard" for crunchy/cracking facts
- [x] Add 5+ healthy snacks with `is_healthy` and `health_benefits` fields:
  - [x] Apple (fruit, fiber, stimulates saliva)
  - [x] Carrots (vegetable, crunchy, cleans teeth)
  - [x] Cheese (dairy, calcium, neutralizes acid)
  - [x] Almonds (nuts, calcium, protein)
  - [x] Celery (vegetable, natural toothbrush, high water)
- [x] Add grouped healthy snacks for smart detection:
  - [x] Mixed Fruit Plate (grouped fruit detection)
  - [x] Fresh Fruit Assortment (grouped fruit detection)
  - [x] Fresh Vegetable Tray (grouped vegetable detection)
  - [x] Fruit Salad (grouped fruit detection)
- [x] Add 5+ celebration facts with `fact_type: "celebrate"`:
  - [x] Crunchy foods as natural toothbrushes
  - [x] Calcium strengthens enamel
  - [x] Water content washes away debris
  - [x] Natural sugars with fiber are gentler
  - [x] Protein builds strong teeth
- [x] Add payload indexes: `fact_type`, `risk_tags`, `is_healthy`
- [x] Re-seed Qdrant Cloud (33 snacks total)
- [x] **File References**: `seed_data.py`, `qdrant_service.py`, `create_indexes.py`

#### 5.2.2 Qdrant Service Updates
- [x] Add `fact_type` parameter to `search_facts()`
- [x] Add `risk_tags` filter parameter to `search_facts()`
- [x] Add `extract_risk_tags()` method to `scoring_service.py`:
  - [x] stickiness > 0.5 → "sticky"
  - [x] added_sugar_g > 15 → "sugary"
  - [x] acidity_tag in (medium, high) → "acidic"
  - [x] crunch_hardness > 0.7 → "hard"
- [x] **File References**: `qdrant_service.py`, `scoring_service.py`

#### 5.2.3 API Layer (Mode + Cross-Collection)
- [x] Create `ComicMode` enum in `models/api.py`: EDUCATE, CELEBRATE, UNKNOWN
- [x] Add `mode` and `average_risk_score` to `ScoreRetrieveResponse`
- [x] Add mode determination logic in `score.py`:
  - [x] risk >= 30 → EDUCATE
  - [x] risk < 30 → CELEBRATE
  - [x] no match → UNKNOWN
- [x] Integrate risk_tags filtering based on matched snack
- [x] Return empty swaps for non-EDUCATE modes
- [x] **File References**: `models/api.py`, `score.py`

#### 5.2.4 Panel-Aware Retrieval (QueryBuilder)
- [x] Create `PanelContext` model in `models/api.py`:
  - [x] `panel_number: int` (1-4)
  - [x] `scene: str` (playground, kitchen, dentist, school)
  - [x] `mood: str` (funny, dramatic, educational, celebratory)
  - [x] `narrative_beat: str` (intro, conflict, revelation, resolution)
- [x] Create `QueryBuilder` service in `services/query_builder.py`:
  - [x] `build_fact_query()` - context-enriched query strings
  - [x] Mood keywords: funny→"fun fact, surprising", dramatic→"warning, danger"
  - [x] Beat keywords: intro→"discovery", resolution→"recommendation, tip"
- [x] Integrate QueryBuilder into `score.py`
- [x] **File References**: `models/api.py`, `query_builder.py`, `score.py`

#### 5.2.5 Script Composition
- [x] Add `compose_celebrate_script()` method in `gemini_service.py`:
  - [x] Positive narrative: THE ENTRANCE → THE STATS → THE GLAZE → THE CROWN (W Arc)
  - [x] DR. HAWLEY character as hype-beast giving props
  - [x] Focus on WHY snack is great (verdicts: "W", "BASED", "GOATED")
- [x] Add `compose_unknown_script()` method for generic dental health comics
- [x] Update `script.py` endpoint to route based on mode
- [x] **File References**: `gemini_service.py`, `script.py`

#### 5.2.6 Frontend (Mode Display)
- [x] Add mode-based banner display (celebrate/educate/unknown)
- [x] Hide swaps section for non-educate modes
- [x] Style celebrate banner with positive colors/icons
- [x] **File References**: `ResultsPanel.tsx`, `page.tsx`

#### 5.2.7 Smart Item Grouping (Multi-Item Detection)
- [x] Update vision detection prompt to support up to 5 items (from 3)
- [x] Add smart grouping rules for plates/assortments:
  - [x] Fruit plates → "Mixed Fruit Plate" (single item)
  - [x] Veggie trays → "Fresh Vegetable Tray" (single item)
  - [x] Mixed snacks → Individual items up to 5
- [x] Add error recovery for vision detection:
  - [x] Handle None response.text gracefully
  - [x] Handle malformed JSON responses
  - [x] Return "Unidentified Food" fallback → triggers UNKNOWN mode
- [x] Update API documentation (1-5 items, grouped)
- [x] **File References**: `gemini_service.py:43-199`, `api.py`

### 5.3 User Preferences (COMPLETED - MODIFIED ✓)
*"Roast My Snack" Pivot: localStorage preferences instead of signup flow*

#### 5.3.1 Backend
- [x] Update age validation to 9-17 range in `api.py`
- [x] Update age bands to 9-12 (Spicy) and 13-17 (Savage) in `scoring_service.py`
- [x] Update script prompts for DR. HAWLEY character in `gemini_service.py`
- [x] Update visual style to Webtoon/Adult Swim in `nanobana_service.py`
- [x] Add teen facts (F033-F046) with savage language in `seed_data.py`
- [x] Fix Qdrant client API (`query_points` instead of deprecated `search`)
- **File References**: `api.py`, `scoring_service.py`, `gemini_service.py`, `nanobana_service.py`, `qdrant_service.py`

#### 5.3.2 Frontend
- [x] Create `usePreferences.ts` hook for localStorage persistence
- [x] Create `AllergenSelector.tsx` component (8 common allergens)
- [x] Update `AgeSelector.tsx` for 9-17 range with Tween/Teen modes
- [x] Update `page.tsx` with dark theme and DR. HAWLEY messaging
- [x] Pass age and allergens to score/retrieve API
- **File References**: `usePreferences.ts`, `AllergenSelector.tsx`, `AgeSelector.tsx`, `page.tsx`

### 5.4 Content Guardrails (TEEN-SAFE) ✓
*Explicit safety filters for generated content*

- [x] Add Gemini safety filters to script output in `gemini_service.py`
- [x] Add profanity filter validation on all generated dialogue
- [x] Add image safety check before serving Nano-Banana output
- [x] Log all generated content for audit review
- **New Files**: `guardrails_service.py`, `audit_service.py`, `test_guardrails.py`
- **File References**: `gemini_service.py`, `nanobana_service.py`

### 5.5 Speech Bubble Integration (VISUAL POLISH)
*Integrated bubbles that feel part of the comic art*
*Prerequisite: 5.1 Panel Layout must be complete*
*See: `docs/speech_bubble_improvement_plan.md` for detailed implementation*

#### 5.5.1 Emotion-Based Prompts
- [ ] Add `emotion` field to panel model in `models/api.py`
- [ ] Define `BUBBLE_STYLES` mapping in `nanobana_service.py`:
  - [ ] "speech" → round oval bubble
  - [ ] "thought" → cloud-shaped bubble
  - [ ] "exclaim" → spiky starburst bubble
  - [ ] "angry" → jagged sharp-edged bubble
  - [ ] "whisper" → dashed-outline bubble
- [ ] Update Nano-Banana prompt to request EMPTY emotion-specific bubbles
- [ ] Update `gemini_service.py` compose_script to return emotion per panel
- [ ] **File References**: `models/api.py`, `nanobana_service.py`, `gemini_service.py`

#### 5.5.2 Bubble Detection
- [ ] Add `detect_speech_bubbles()` method to `gemini_service.py`:
  - [ ] Use Gemini Vision to analyze generated comic
  - [ ] Return JSON with bbox coordinates, center, style, confidence
- [ ] Implement hybrid retry + fallback strategy in `render_service.py`:
  - [ ] MAX_RETRIES = 1
  - [ ] If detection fails → retry once
  - [ ] If still fails → fall back to PIL
- [ ] **File References**: `gemini_service.py`, `render_service.py`

#### 5.5.3 Text Placement
- [ ] Add `_place_text_in_bubbles()` method to `render_service.py`:
  - [ ] Calculate text area from detected bbox
  - [ ] Auto-size font to fit
  - [ ] Center text in bubble
  - [ ] Add slight shadow for depth
- [ ] Add `_fallback_pil_bubbles()` enhanced method:
  - [ ] Extract dominant colors from comic
  - [ ] Draw emotion-appropriate bubble shapes
  - [ ] Add hand-drawn wobble effect
- [ ] **File References**: `render_service.py`

### 5.6 Branding & Polish

- [ ] **Header branding**: Update to "Poppy Kids Pediatric Dentistry" with logo
- [ ] **Clinic website link**: Add click-through to business website
- [ ] **Export Format Buttons**: Make more dynamic and mobile-suitable
- [ ] **"How it Works" section**: Add tutorial for users
- [ ] **Progress Feedback**: During the long "Creating glow up comic" step, show a progress bar or animation so users know the app hasn't frozen
- [ ] **File References**: Frontend components

### 5.7 User Customization

- [ ] **Comic Style Picker**: Let users pick different comic styles (e.g., superhero, manga, vaporwave) to better suit individual tastes
- [ ] **Multi-language support**: Localization for broader accessibility

### 5.8 Design Enhancements

#### Visual & Interaction Style

- [ ] **Bold colour palettes & expressive typography**: Teens are drawn to vibrant, expressive visuals. Material 3 Expressive design language promotes rich purples, pinks and blues, funky fonts, and more abstract themes to make apps feel energetic. Pair purple gradient background with accent colours like neon green or electric pink and use eye-catching headings and captions.

- [ ] **Motion & micro-animations**: Kinetic typography and subtle animations are trending. Animate Dr. Hawley's reactions and have panels slide in with a spring effect. Use motion sparingly (e.g., a bouncing progress indicator or a sparkle animation when users get a "glow-up" snack) to add life without overwhelming.

- [ ] **Comic-panel storytelling**: Keep the comic layout but explore different panel shapes (e.g., diagonal cuts or speech bubbles that overlap panels) to mimic popular webtoons. Allow the user to tap on a panel for a zoomed-in view or hold to reveal a fun fact.

#### User Experience & Accessibility

- [ ] **Simplify interactions**: Child-friendly UI guidelines emphasise uncluttered screens, large tappable areas and minimal text. Reduce cognitive load by offering only a few clear actions (e.g., "Upload," "See Comic," "Share") on each screen. Ensure buttons are big and spaced apart to avoid accidental taps.

- [ ] **Inclusive & accessible design**: Inclusive design means adding alt text for images, using relative text sizes and avoiding elements that require precise tapping. The app can still be edgy while ensuring colour contrast and optional captions for the comics.

- [ ] **Dark mode**: Dark mode has gone from novelty to expectation. Offer both dark and light themes so users can pick what suits their mood. Purple gradient could become a deep navy-to-black gradient in dark mode, with neon accents that pop.

#### Personalisation & Variety

- [ ] **Style selection**: Teens love customisation. Offer different "drip styles" for the comic (cyberpunk, vintage manga, glitch art). This gives a sense of ownership and encourages repeat use.

- [ ] **Adaptive difficulty & feedback**: The risk score is great; consider turning it into a "smile health meter" that levels up when users choose healthier snacks. Provide badges or streaks for trying less sugary snacks, aligning with gamification to encourage better dental habits.

*By combining a vibrant aesthetic, smooth interactions and social integration, you can keep SnackSwap Comics relevant and exciting for its teen and tween audience while still delivering helpful dental-health guidance.*

---

## Phase 6: Production Readiness (Post-Hackathon)

### 6.1 Analytics & Monitoring
- [ ] Analytics integration (track generations, downloads, shares)
- [ ] Error tracking and alerting
- [ ] Usage metrics dashboard

### 6.2 Infrastructure
- [ ] Production deployment (Cloud Run / Vercel)
- [ ] CI/CD pipeline
- [ ] Monitoring & alerting
- [ ] Database persistence for scripts

### 6.3 Technical Debt
- [ ] Request rate limiting
- [ ] Caching layer for embeddings
- [ ] Comprehensive error handling tests
- [ ] Image compression optimization
- [ ] Upgrade Nano-Banana generation from 1K (512×1024) to 2K (1024×2048) for higher quality exports

---

## v1.1 Features (Later)

- [ ] **Animated comics**: Video generation for Reels
- [ ] **User accounts**: Session persistence, history/gallery
- [ ] **Social sharing**: Direct share to Instagram/TikTok

## v1.2 Features (Later)

- [ ] Character customization (pick mascot style)
- [ ] PWA offline support

---

## Completed Refactoring

### ✅ Rename Dr. Drip → Dr. Hawley (COMPLETED 2025-12-14)

**Scope:** 244+ occurrences across 20 files + 2 file renames + 13 image renames

#### Files Renamed
- [x] `backend/app/data/drdrip_roast_corpus.py` → `drhawley_roast_corpus.py`
- [x] `backend/generate_dr_drip.py` → `generate_dr_hawley.py`
- [x] 13 image files: `Dr.Drip_*.png` → `Dr.Hawley_*.png`

#### Code Files Updated
- [x] `gemini_service.py` (67 occurrences)
- [x] `drhawley_roast_corpus.py`, `nanobana_service.py`, `render_service.py`
- [x] `comic.py`, `__init__.py`, `remove_backgrounds.py`
- [x] Test files, frontend components (`page.tsx`, `ToothMascot.tsx`)

#### Documentation Updated
- [x] `README.md`, `CLAUDE.md`, `TODO.md`, `todo.md`
- [x] `tween_teen_pivot.md`, `new_prompts.md`, `hackathon-rubric.md`, `presentation-2min.md`
- [x] `roast_my_snak.jsonl`, `seed_data.py`

---

## Implementation Priority Order

```
WEEK 1: Foundation + Data
├── Day 1-2: 1x4 Panel Layout (blocks everything else)
├── Day 3-4: Celebrate Mode + Qdrant Enhancements - Seed Data (combined re-seed)
└── Day 5: Payload indexes, re-seed Qdrant Cloud

WEEK 2: API + Search Features
├── Day 1-2: Mode logic + cross-collection joins in score.py
├── Day 3: QueryBuilder service + panel-aware retrieval
├── Day 4: Script composition (celebrate + unknown modes)
└── Day 5: Frontend mode display

WEEK 3: User Experience
├── Day 1-2: User Signup Flow (backend)
├── Day 3: User Signup Flow (frontend)
├── Day 4-5: Content Guardrails

WEEK 4: Visual Polish
├── Day 1-3: Speech Bubble Integration (emotion prompts, detection)
├── Day 4: Speech Bubble Text Placement + Fallback
└── Day 5: Branding, polish, final testing
```

---

## Documentation Cross-References

| Doc File | Covers | TODO Sections |
|----------|--------|---------------|
| `docs/database-enhancements.md` | Celebrate Mode details | 5.2.1-5.2.6 |
| `docs/qdrant-enhancements-plan.md` | Panel-aware + cross-collection | 5.2.2, 5.2.4 |
| `docs/speech_bubble_improvement_plan.md` | Bubble integration | 5.5 |
| `docs/hackathon-rubric.md` | Judging criteria mapping | All |
| `docs/qdrantcloud-freepik.md` | Completed migration | N/A (done) |

---

## Environment Setup Checklist

### Required
- [x] `GEMINI_API_KEY` - Google Gemini API key
- [x] `QDRANT_URL` - Qdrant Cloud cluster URL
- [x] `QDRANT_API_KEY` - Qdrant Cloud API key

### Optional
- [x] `FREEPIK_API_KEY` - Freepik API for enhanced assets
- [ ] `DEBUG` - Enable debug mode (shows age/allergen selectors)

See `backend/.env.example` for full configuration options.

---

## Definition of Done

**Backend:**
- [x] `/api/render/comic` returns actual comic images
- [x] Comics are visually appealing with clear characters
- [x] Educational facts are visible and readable
- [x] All 3 formats export correctly

**Frontend:**
- [x] Users can upload images
- [x] Comic displays in browser
- [x] Download buttons work
- [x] Responsive design

**Overall:**
- [x] End-to-end test passes with gummy bears image
- [x] Documentation is complete
- [x] MVP is functional
