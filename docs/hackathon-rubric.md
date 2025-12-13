# SnackSwap Comics - Hackathon Rubric Assessment

> **Hackathon**: [Name TBD]
> **Client**: Poppy Kids Pediatric Dentistry
> **Last Updated**: 2025-12-08

---

## 1. Creative Quality
*Creative use of DeepMind (Google Gemini)/Freepik/Qdrant, visual polish, coherent multi-asset story*

### ✅ Currently Implemented

| Technology | Creative Use | File Reference |
|------------|--------------|----------------|
| **Gemini 2.5 Flash Vision** | Detects 1-5 snacks with smart grouping (plates → single item) | `gemini_service.py:detect_items()` |
| **Gemini 2.5 Flash Writer** | Generates mode-aware 4-panel comic scripts (EDUCATE/CELEBRATE/UNKNOWN) | `gemini_service.py:compose_script()` |
| **Nano-Banana (gemini-3-pro-image-preview)** | Creates 2x2 comic grid with consistent characters (Captain Sparkle + food characters) | `nanobana_service.py` |
| **Gemini text-embedding-004** | 768-dim embeddings for semantic search across all collections | `gemini_service.py:generate_embedding()` |
| **Freepik API** | Professional speech bubbles, comic frames, **mode-based backgrounds** (CELEBRATE/EDUCATE themes) | `freepik_service.py` |
| **Qdrant** | Semantic search for snacks, facts, swaps, styles with risk_tags filtering | `qdrant_service.py` |

**Visual Polish**:
- PIL post-processing adds text overlays on Imagen output
- 3 export formats: Square (1080×1080), Portrait (1080×1350), Reel (1080×1920)
- Anthropic brand colors applied to frontend

**Coherent Multi-Asset Story**:
- 4-panel narrative structure: Intro → Conflict → Revelation → Resolution
- Recurring character "Captain Sparkle" (superhero tooth) across all comics
- Food items become personified characters with expressions

**Smart Item Detection** (NEW):
- Detects up to 5 items (increased from 3)
- Smart grouping: fruit plates → "Mixed Fruit Plate", veggie trays → "Fresh Vegetable Tray"
- Graceful error recovery: returns fallback item on vision errors → triggers UNKNOWN mode

**Comic Modes** (NEW):
- **CELEBRATE** (risk < 30): Positive comics for healthy snacks
- **EDUCATE** (risk ≥ 30): Educational comics with dental risks and swaps
- **UNKNOWN** (no match): Generic dental health comics

**Mode-Based Background Themes** (NEW):
- Freepik vector backgrounds auto-selected by comic mode
- **CELEBRATE** → Bright colorful celebration confetti
- **EDUCATE** → Clean modern gradient
- **UNKNOWN** → Simple colorful cartoon
- Blended at 35% opacity to enhance (not replace) Nano-Banana output
- Layer order: Background → Base comic → Frames → Bubbles → Text

### 📋 TODO

- [x] **Panel Layouts**: Square (2x2), Portrait (1x4), Reel (1x4) ✓
- [x] **Celebrate Mode**: Positive comics for healthy snacks ✓
- [x] **Unknown Mode**: Generic comics for unrecognized items ✓
- [x] **Smart Item Grouping**: Fruit plates, veggie trays grouped as single items ✓
- [x] **Direct Social Sharing**: Instagram and TikTok share buttons with platform-optimized formats ✓
- [ ] **Animated comics**: Video generation for Reels (v1.1)
- [ ] **Multiple comic styles/themes** (v1.2)
- [x] **Enhanced Freepik Integration**: Mode-based backgrounds (CELEBRATE/EDUCATE themes), speech bubbles, comic frames ✓

---

## 2. Search & Similarity
*Effective Qdrant use, search, recommendation, transparent scoring*

### ✅ Currently Implemented

| Feature | Implementation | File Reference |
|---------|----------------|----------------|
| **Semantic Snack Search** | Matches detected items to 33+ snacks in `snacks_v1` via cosine similarity | `qdrant_service.py:search_snacks()` |
| **Fact Retrieval** | Age-banded, fact_type-filtered, risk_tags-matched dental facts from `facts_v1` | `qdrant_service.py:search_facts()` |
| **Swap Recommendations** | Taste-cluster matching + allergen filtering from `swaps_v1` | `qdrant_service.py:search_swaps()` |
| **Style Templates** | Branding styles from `styles_v1` for comic customization | `qdrant_service.py:search_styles()` |
| **QueryBuilder** | Context-enriched queries with mood/scene awareness | `query_builder.py` |

**Transparent Scoring Formula** (`scoring_service.py:23-65`):
```
risk_score = 100 × (
    0.45 × normalized(added_sugar_g_per_100g) +  # Sugar content
    0.20 × acidity_factor +                       # Acid erosion
    0.20 × stickiness +                           # Stays on teeth
    0.10 × residue +                              # Film on teeth
    0.05 × crunch_hardness                        # Can crack teeth
)
```

**Swap Ranking** (`scoring_service.py:67-156`):
- Must improve risk by ≥25 points
- Taste cluster bonus (+20 pts)
- Prep time penalty
- Allergen exclusion
- Age suitability check

**Risk Tag Extraction** (NEW - `scoring_service.py:extract_risk_tags()`):
- stickiness > 0.5 → "sticky"
- added_sugar_g > 15 → "sugary"
- acidity_tag in (medium, high) → "acidic"
- crunch_hardness > 0.7 → "hard"

**Payload Indexes** (for filtered queries):
- `clinic_approved` (bool) on facts
- `age_band` (keyword) on facts
- `fact_type` (keyword) on facts - NEW
- `risk_tags` (keyword) on facts - NEW
- `is_healthy` (bool) on snacks - NEW
- `taste_cluster` (keyword) on swaps
- `allergy_tags` (keyword) on swaps
- `category` (keyword) on snacks

### 📋 TODO

- [x] **Panel-aware retrieval**: Blend mood/scene context into fact queries ✓
- [x] **Cross-collection joins**: Use snack risk_tags to filter facts (sticky→sticky facts) ✓
- [x] **risk_tags field**: Added to all facts for targeted filtering ✓
- [x] **QueryBuilder service**: Context-enriched query generation ✓
- [x] **extract_risk_tags() method**: Auto-extract risk tags from matched snacks ✓

---

## 3. Guardrails
*Copyright and brand-safe by design, kid-safe content*

### ✅ Currently Implemented

| Guardrail | Implementation | File Reference |
|-----------|----------------|----------------|
| **Clinic-Approved Facts Only** | `clinic_approved=True` filter on all fact searches | `qdrant_service.py:search_facts()` |
| **Age-Appropriate Content** | Age-band filtering (9-12, 13-17) for facts and language (TODO: capture preference, use in prompts) | `score.py`, `gemini_service.py` |
| **Allergen Filtering** | Swaps exclude items matching user's allergy list (TODO: capture in signup) | `scoring_service.py:rank_swaps()` |
| **No User-Generated Content** | All content from curated seed data + Gemini generation | `seed_data.py` |
| **Source Attribution** | Facts include `source_key` and `source_url` for provenance | `facts_v1` schema |
| **Reviewed By Field** | Facts track clinical reviewer (e.g., "Dr. Andrea Aduna") | `facts_v1` schema |

**Kid-Safe Design**:
- Playful, positive tone in all generated scripts
- Educational focus (not fear-based)
- No mention of graphic dental procedures
- Age-appropriate vocabulary per band

**Brand Safety**:
- Generic snack categories (no brand attacks)
- Positive swap suggestions (not shame-based)
- Clinic branding customizable via `styles_v1`

### 📋 TODO

- [x] **Content moderation layer**: GuardrailsService validates all generated content ✓
- [x] **Profanity filter**: Blocked/mild term filtering with auto-clean ✓
- [x] **Image safety check**: Image prompt validation before generation ✓
- [ ] **Rate limiting**: Prevent abuse (TODO.md - Technical Debt)
- [x] **Audit logging**: AuditService tracks all generated content ✓

---

## 4. UX & Tradeoffs
*Clear speed/quality/cost controls, parameter clarity*

### ✅ Currently Implemented

| Feature | User Control | File Reference |
|---------|--------------|----------------|
| **Age Selection** | User selects age band (9-12, 13-17) for appropriate content | `frontend/src/components/AgeSelector.tsx` |
| **Allergy Input** | Users can specify allergies to filter swap suggestions | `ScoreRetrieveRequest.allergies` |
| **Multiple Export Formats** | Square, Portrait, Reel - user chooses what to download | `frontend/src/components/ComicDisplay.tsx` |
| **Progress Indicators** | Step-by-step scanning overlay shows pipeline progress | `frontend/src/components/ScanningOverlay.tsx` |
| **Debug Mode** | `DEBUG=true` env var shows age/allergen selectors for admin testing | `frontend` |

**Speed/Quality Tradeoffs**:
- Always use Freepik for professional assets; falls back to PIL only if Freepik API unavailable
- Nano-Banana generation: ~10-15 seconds per comic
- Qdrant Cloud: <200ms search latency

**Cost Controls**:
- Gemini API: Pay-per-use (vision + writer + embedding + imagen)
- Qdrant Cloud: Free tier (1GB storage)
- Freepik: API calls per asset

### 📋 TODO

- [ ] **User Signup Flow** (v1.1): Capture age and allergens during signup. Use this info in Gemini prompts rather than frontend toggles. Age/allergen selectors only visible when `DEBUG=true` for admin testing.
- [ ] **"How it Works" section**: Add clear tutorial for users (TODO.md - Backlog)
- [ ] **Parameter clarity UI**: Show what age band affects (language, facts, swaps) - visible in debug mode

---

## 5. Real-World Fit
*Practical use cases and measurable impact (Poppy Kids Pediatric Dentistry)*

### ✅ Currently Implemented

| Use Case | Implementation | Impact |
|----------|----------------|--------|
| **Dental Education** | 4-panel comics explain dental risks in kid-friendly way | Makes learning fun |
| **Parent Engagement** | Shareable comics (Square for posts, Story for Instagram) | Social amplification |
| **Snack Awareness** | Risk scores (0-100) quantify dental impact | Informed decisions |
| **Healthier Choices** | Taste-matched swap suggestions | Behavior change |
| **Age-Appropriate** | 3 age bands with tailored content | Developmental fit |

**Clinic Integration**:
- `styles_v1` collection stores clinic branding (colors, fonts, logo)
- Comics can be watermarked with clinic info
- Export formats optimized for social media sharing

**Measurable Impact** (potential metrics):
- Comics generated per month
- Swap acceptance rate (if tracked)
- Social shares (if tracked)
- Clinic referral traffic (if tracked)

### 📋 TODO

- [ ] **Header branding**: Update to "Poppy Kids Pediatric Dentistry" with logo (TODO.md)
- [ ] **Clinic website link**: Add link when clicking logo
- [ ] **Analytics integration**: Track comic generation, downloads, shares
- [ ] **User accounts**: Enable history/gallery per family (v1.1)
- [ ] **Production deployment**: Cloud Run / Vercel (TODO.md - Infrastructure)
- [ ] **Monitoring & alerting**: Track usage and errors

---

## 6. Innovation & Creativity
*Novel approaches, unique solutions, and creative problem-solving*

### ✅ Currently Implemented

| Innovation | Description | Why It's Novel |
|------------|-------------|----------------|
| **Food-as-Character** | Detected snacks become personified comic characters | Emotional connection to education |
| **Captain Sparkle** | Recurring superhero tooth mascot across all comics | Brand consistency + engagement |
| **Dental Risk Formula** | Multi-factor scoring (sugar, acidity, stickiness, residue, crunch) | Science-based, transparent |
| **Taste-Cluster Swaps** | Recommendations match flavor profiles (sweet-chewy → sweet-chewy) | Higher acceptance rate |
| **PIL Post-Processing** | Nano-Banana generates art, PIL adds precise text overlays | Best of both worlds |
| **Age-Banded RAG** | Same snack → different facts based on child's age | Developmentally appropriate |
| **Mode-Based Backgrounds** | Freepik backgrounds auto-selected by comic mode at 35% opacity | Visual polish without obscuring characters |

**Technical Innovations**:
- Gemini-native stack (vision + writer + embedding + Nano-Banana)
- Qdrant semantic search with payload filters
- Multi-stage pipeline (6 endpoints, modular services)
- Freepik integration with PIL fallback for reliability

### 📋 TODO

- [x] **Panel Layouts**: Square (2x2), Portrait (1x4), Reel (1x4) ✓
- [x] **Celebrate Mode**: Positive reinforcement for healthy snacks (novel narrative) ✓
- [x] **Smart Item Grouping**: Multi-item plates detected as single grouped items ✓
- [x] **Panel-aware retrieval**: Facts match comic mood/scene context ✓
- [x] **Cross-collection joins**: Snack traits drive fact selection ✓
- [x] **Mode-Based Backgrounds**: Freepik backgrounds per comic mode (CELEBRATE/EDUCATE/UNKNOWN) ✓
- [x] **Direct Social Sharing**: Instagram and TikTok share buttons ✓
- [ ] **Animated comics**: Video generation (novel format)
- [ ] **Character customization**: Let users pick mascot style (v1.2)
- [ ] **Multi-language support**: Expand reach (v1.2)

---

## Summary: Hackathon Readiness

| Criteria | Status | Strength | Gap |
|----------|--------|----------|-----|
| **1. Creative Quality** | 🟢 Strong | Full Gemini stack + Celebrate/Unknown modes + Smart grouping + 3 layouts + **Mode-based backgrounds** + **Social sharing** | All key features implemented ✓ |
| **2. Search & Similarity** | 🟢 Strong | Transparent scoring, 4 collections, QueryBuilder, risk_tags | All key features implemented ✓ |
| **3. Guardrails** | 🟢 Strong | GuardrailsService + AuditService + profanity filter + image safety | Rate limiting (v1.1) |
| **4. UX & Tradeoffs** | 🟢 Strong | Age selection, 3 export formats, debug mode | User signup flow (v1.1) |
| **5. Real-World Fit** | 🟢 Strong | Built for Poppy Kids Dental | Analytics not integrated |
| **6. Innovation** | 🟢 Strong | Celebrate mode + Smart grouping + Risk tag extraction + **Mode-based backgrounds** | Key differentiators implemented ✓ |

---

## Recently Completed (Section 5.2)

- ✅ **Celebrate Mode**: Positive comics for healthy snacks (apples, carrots, fruit plates)
- ✅ **Unknown Mode**: Generic dental health comics when snacks aren't recognized
- ✅ **Smart Item Grouping**: Fruit plates (10+ items) → "Mixed Fruit Plate" (single detection)
- ✅ **Panel-aware Retrieval**: QueryBuilder blends mood/scene context into fact queries
- ✅ **Cross-collection Joins**: Snack risk_tags filter relevant facts (sticky→sticky facts)
- ✅ **Risk Tag Extraction**: Auto-extract sticky/sugary/acidic/hard from matched snacks
- ✅ **Error Recovery**: Vision detection gracefully handles None responses, malformed JSON
- ✅ **Content Guardrails**: GuardrailsService with profanity filter, blocked/mild term lists, auto-clean
- ✅ **Audit Logging**: AuditService tracks all generated content with daily JSONL logs
- ✅ **Image Safety**: Prompt validation before image generation
- ✅ **Panel Layouts**: Square (2x2), Portrait (1x4), Reel (1x4)
- ✅ **Mode-Based Background Themes**: Freepik backgrounds per comic mode (CELEBRATE/EDUCATE/UNKNOWN)
- ✅ **Direct Social Sharing**: Instagram and TikTok share buttons with Web Share API

---

## Priority TODOs for Hackathon

1. **Header branding** - Polish for Poppy Kids Pediatric Dentistry

### Deferred to v1.1
- **User Signup Flow** - Capture age/allergens upfront, use in prompts (not frontend toggles)
- **Rate Limiting** - Prevent abuse
