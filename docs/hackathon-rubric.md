# SnackSwap Comics - Hackathon Rubric Assessment

> **Hackathon**: [Name TBD]
> **Client**: Poppy Kids Pediatric Dentistry
> **Last Updated**: 2025-12-13

---

## 1. Creative Quality
*Creative use of DeepMind (Google Gemini)/Freepik/Qdrant, visual polish, coherent multi-asset story*

### ✅ Currently Implemented

| Technology | Creative Use | File Reference |
|------------|--------------|----------------|
| **Gemini 2.5 Flash Vision** | Detects 1-5 snacks with smart grouping + **Thinking Mode** (8192 token budget) | `gemini_service.py:detect_items()` |
| **Gemini 2.5 Pro Writer** | Age-adaptive "vanity roast" scripts with **Thinking Mode** (24576 token budget) | `gemini_service.py:compose_script()` |
| **Gemini 3 Pro Image (Nano-Banana)** | Creates 1x4 vertical comic strips with consistent DR. DRIP character | `nanobana_service.py` |
| **Imagen 4.0 Support** | Optional 2K high-resolution comic generation | `nanobana_service.py` (dual model support) |
| **Gemini text-embedding-004** | 768-dim embeddings for semantic search across all collections | `gemini_service.py:generate_embedding()` |
| **Freepik API** | Professional speech bubbles, comic frames, **mode-based backgrounds** | `freepik_service.py` |
| **Qdrant Cloud** | Semantic search for snacks, facts, swaps, styles with risk_tags filtering | `qdrant_service.py` |

**DR. DRIP Character System** (Signature Creative Element):
- Recurring mascot: Off-white/pale cyan molar in dark forest green hoodie, sunglasses on forehead, beige Yeezy-style slides
- **Age-adaptive personality**:
  - Ages 9-12 "Spicy Mode": Lighter burns, meme-y ("sus", "mid", "skill issue")
  - Ages 13-17 "Savage Mode": Full destruction ("cooked", "L + ratio", "aura")
- Adult Swim humor style (Rick & Morty, Smiling Friends energy)
- Roast corpus with 50+ few-shot examples: `app/data/drdrip_roast_corpus.py`

**"Vanity Roasting" Concept** (Novel Approach):
- Reframes dental health as AESTHETICS, not health lectures
- All facts reframed: Sugar = "turns teeth YELLOW", Sticky = "looks gross and fuzzy"
- Appeals to teen vanity: "glow up", "unfiltered smile", "Hollywood teeth"

**Emotion-Based Speech Bubbles** (5 distinct styles):
| Emotion | Shape | Visual Style | Use Case |
|---------|-------|--------------|----------|
| `speech` | Oval | White, black outline | Normal dialogue |
| `thought` | Cloud | White, gray outline, bubble tail | Internal thoughts |
| `exclaim` | Spiky starburst | Yellow, red outline | Dramatic reveals |
| `angry` | Jagged irregular | Light red, dark red outline | Destruction mode |
| `whisper` | Dashed oval | Light gray, dashed outline | Secrets |

**Visual Polish**:
- PIL post-processing adds Comic Sans text overlays on Nano-Banana output
- 2 export formats: Portrait (1080×1350), Reel (1080×1920)
- Mode-based Freepik backgrounds at 35% opacity blend

**Coherent Multi-Asset Story** (4-Panel Narrative Arcs):
- **EDUCATE (Roast Arc)**: Flex → Exposé → Ratio → Vibe Check
- **CELEBRATE (W Arc)**: Entrance → Stats → Glaze → Crown
- **UNKNOWN**: Generic DR. DRIP glow-up tips

**Smart Item Detection**:
- Detects up to 5 items with intelligent grouping
- Fruit plates → "Mixed Fruit Plate", Veggie trays → "Fresh Vegetable Tray"
- Graceful error recovery with fallback items → triggers UNKNOWN mode

### 📋 TODO

- [x] Panel Layouts: Portrait (1x4), Reel (1x4) ✓
- [x] Celebrate Mode: Positive comics for healthy snacks ✓
- [x] Unknown Mode: Generic comics for unrecognized items ✓
- [x] Smart Item Grouping ✓
- [x] DR. DRIP character with age-adaptive personality ✓
- [x] Emotion-based speech bubble styles ✓
- [x] Enhanced Freepik Integration: Mode-based backgrounds ✓
- [ ] **Animated comics**: Video generation for Reels (v1.1)
- [ ] **Multiple comic themes** (v1.2)

---

## 2. Search & Similarity
*Effective Qdrant use, search, recommendation, transparent scoring*

### ✅ Currently Implemented

| Feature | Implementation | File Reference |
|---------|----------------|----------------|
| **Semantic Snack Search** | Matches detected items to 33+ snacks via cosine similarity | `qdrant_service.py:search_snacks()` |
| **Fact Retrieval** | Age-banded, fact_type-filtered, risk_tags-matched facts | `qdrant_service.py:search_facts()` |
| **Swap Recommendations** | Taste-cluster matching + allergen filtering | `qdrant_service.py:search_swaps()` |
| **Style Templates** | Branding styles for comic customization | `qdrant_service.py:search_styles()` |
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

**Risk Tag Extraction** (`scoring_service.py:extract_risk_tags()`):
- stickiness > 0.5 → "sticky"
- added_sugar_g > 15 → "sugary"
- acidity_tag in (medium, high) → "acidic"
- crunch_hardness > 0.7 → "hard"

**Payload Indexes** (for filtered queries):
- `clinic_approved` (bool) on facts
- `age_band` (keyword) on facts
- `fact_type` (keyword) on facts
- `risk_tags` (keyword) on facts
- `is_healthy` (bool) on snacks
- `taste_cluster` (keyword) on swaps
- `allergy_tags` (keyword) on swaps
- `category` (keyword) on snacks

### 📋 TODO

- [x] Panel-aware retrieval: Blend mood/scene context into fact queries ✓
- [x] Cross-collection joins: Use snack risk_tags to filter facts ✓
- [x] risk_tags field: Added to all facts ✓
- [x] QueryBuilder service: Context-enriched query generation ✓

---

## 3. Guardrails
*Copyright and brand-safe by design, kid-safe content*

### ✅ Currently Implemented

| Guardrail | Implementation | File Reference |
|-----------|----------------|----------------|
| **Clinic-Approved Facts Only** | `clinic_approved=True` filter on all fact searches | `qdrant_service.py:search_facts()` |
| **Age-Appropriate Content** | Age-band filtering (9-12 Spicy, 13-17 Savage) | `score.py`, `gemini_service.py` |
| **Allergen Filtering** | Swaps exclude items matching user's allergy list | `scoring_service.py:rank_swaps()` |
| **No User-Generated Content** | All content from curated seed data + Gemini generation | `seed_data.py` |
| **Source Attribution** | Facts include `source_key` and `source_url` | `facts_v1` schema |
| **Reviewed By Field** | Facts track clinical reviewer | `facts_v1` schema |

**GuardrailsService** (`guardrails_service.py`) - Comprehensive Content Safety:

| Feature | Details |
|---------|---------|
| **Blocked Terms** | 50+ explicit profanity, slurs, drug refs, violence (zero tolerance) |
| **Teen Slang Allowlist** | "cringe", "sus", "cap", "bruh", "goated", "rizz", "aura" (OK for context) |
| **Roast Terms Allowlist** | "cooked", "mid", "trash", "ratio" (OK for comedy) |
| **Hyperbole Terms Allowlist** | "villain", "chaos", "disaster", "crime" (OK for absurdist humor) |
| **ContentRating Enum** | SAFE, MILD, BLOCKED - three-tier classification |
| **Auto-Clean Replacements** | "ass" → "butt", "damn" → "dang", "hell" → "heck" |
| **Script Validation** | Validates all dialogue, captions, alt text across panels |
| **Image Prompt Validation** | Blocks nude, violence, gore, weapons, drugs in image generation |

**AuditService** (`audit_service.py`) - Compliance Logging:

| Feature | Details |
|---------|---------|
| **Daily JSONL Logs** | `storage/audit/YYYY-MM-DD.jsonl` |
| **Generation Types Tracked** | `VISION_DETECTION`, `SCRIPT_COMPOSE`, `SCRIPT_CELEBRATE`, `SCRIPT_UNKNOWN`, `IMAGE_GENERATION` |
| **Content Hashing** | SHA256 hashes for deduplication/reference |
| **Validation Logging** | pass/fail status, flagged terms, cleaned content |
| **Performance Metrics** | Generation duration in milliseconds |
| **Stats Endpoint** | `get_stats()` returns daily totals, by-type breakdown, term frequency |
| **Flagged Entry Review** | `get_flagged_entries()` for compliance review |

**Kid-Safe Design**:
- Roast targets SNACKS, never the person ("Your teeth are filing a restraining order" not "You're dumb")
- Playful, positive tone even in "savage" mode
- Educational focus wrapped in humor
- No graphic dental procedure mentions
- Age-appropriate vocabulary per band

### 📋 TODO

- [x] Content moderation layer: GuardrailsService ✓
- [x] Profanity filter: Blocked/mild term filtering with auto-clean ✓
- [x] Image safety check: Image prompt validation ✓
- [x] Audit logging: AuditService with daily JSONL logs ✓
- [ ] **Rate limiting**: Prevent abuse (v1.1)

---

## 4. UX & Tradeoffs
*Clear speed/quality/cost controls, parameter clarity*

### ✅ Currently Implemented

| Feature | User Control | File Reference |
|---------|--------------|----------------|
| **Age Selection** | Slider 9-17 with localStorage persistence | `AgeSelector.tsx`, `usePreferences.ts` |
| **Intensity Mode** | Auto-calculated: 9-12 = Spicy, 13-17 = Savage | `usePreferences.ts` |
| **Allergy Input** | Multi-select allergen chips with localStorage persistence | `AllergenSelector.tsx` |
| **Export Formats** | Portrait (1080×1350), Reel (1080×1920) | `ComicDisplay.tsx` |
| **Progress Indicators** | 5-step scanning overlay with custom icons | `ScanningOverlay.tsx` |
| **DR. DRIP Dynamic Messages** | Mode-aware greetings based on app state | `page.tsx:getDrDripMessage()` |

**Preference Persistence** (`usePreferences.ts`):
- Age, allergens, intensity mode saved to localStorage
- Preferences restored on page reload
- `isLoaded` flag prevents flash of default values

**Progress Steps** (5-step pipeline with icons):
1. 📤 Uploading
2. 🔍 Scanning snack
3. 💀 Checking aesthetic threat
4. 🔥 Writing vanity roast
5. 🎨 Creating glow up comic

**Speed/Quality Tradeoffs**:
- Gemini Vision: Thinking Mode enabled (8192 tokens) for better accuracy
- Gemini Writer: Thinking Mode enabled (24576 tokens) for quality scripts
- Nano-Banana generation: ~10-15 seconds per comic
- Qdrant Cloud: <200ms search latency
- Freepik: Always used when API key available; PIL fallback if unavailable

**Cost Controls**:
- Gemini API: Pay-per-use (vision + writer + embedding + imagen)
- Qdrant Cloud: Free tier (1GB storage)
- Freepik: API calls per asset, cached after first download

### 📋 TODO

- [ ] **User Signup Flow** (v1.1): Capture age/allergens during signup
- [ ] **"How it Works" section**: Add clear tutorial
- [ ] **Parameter clarity UI**: Show what age band affects

---

## 5. Real-World Fit
*Practical use cases and measurable impact (Poppy Kids Pediatric Dentistry)*

### ✅ Currently Implemented

| Use Case | Implementation | Impact |
|----------|----------------|--------|
| **Dental Education** | 4-panel comics explain dental risks in kid-friendly way | Makes learning fun |
| **Parent Engagement** | Shareable comics (Portrait, Reel formats) | Social amplification |
| **Snack Awareness** | Risk scores (0-100) quantify dental impact | Informed decisions |
| **Healthier Choices** | Taste-matched swap suggestions | Behavior change |
| **Age-Appropriate** | 2 intensity modes with tailored language | Developmental fit |

**Clinic Integration**:
- `styles_v1` collection stores clinic branding (colors, fonts, logo)
- Footer displays Poppy Kids logo with link to website
- Export formats optimized for Instagram/TikTok sharing

**Poppy Kids Branding** (Currently Implemented):
- Logo in footer: `/images/poppykids_logo.png`
- Link to: https://www.poppykidsdental.com
- Footer text: "Powered by Gemini Vision & Qdrant"

**Measurable Impact** (potential metrics):
- Comics generated per month
- Swap acceptance rate (if tracked)
- Social shares (if tracked)
- Clinic referral traffic (if tracked)

### 📋 TODO

- [x] Poppy Kids logo in footer with link ✓
- [ ] **Header branding** - Update to Poppy Kids theme
- [ ] **Analytics integration**: Track generation, downloads, shares
- [ ] **User accounts**: Enable history/gallery per family (v1.1)
- [ ] **Production deployment**: Cloud Run / Vercel

---

## 6. Innovation & Creativity
*Novel approaches, unique solutions, and creative problem-solving*

### ✅ Currently Implemented

| Innovation | Description | Why It's Novel |
|------------|-------------|----------------|
| **"Vanity Roasting"** | Dental health reframed as aesthetics ("glow up", "Hollywood teeth") | Speaks teen language |
| **DR. DRIP Character** | Consistent mascot with Adult Swim personality | Brand recall + engagement |
| **Age-Adaptive Personality** | Same character, different intensity (Spicy vs Savage) | Developmentally appropriate |
| **Roast Corpus** | 50+ few-shot examples in `drdrip_roast_corpus.py` | Quality script generation |
| **Thinking Mode** | Vision (8192) and Writer (24576) thinking budgets | Better reasoning |
| **5 Emotion Bubble Styles** | speech, thought, exclaim, angry, whisper | Dynamic visual storytelling |
| **Dynamic Bubble Sizing** | Bubble width scales with text length (35%-55%) | Optimal text fit |
| **Position-Aware Dialogue** | Left/right bubble placement based on speaker position | Clear attribution |
| **Dental Risk Formula** | Multi-factor scoring (sugar, acidity, stickiness, residue, crunch) | Science-based, transparent |
| **Taste-Cluster Swaps** | Recommendations match flavor profiles (sweet-chewy → sweet-chewy) | Higher acceptance |
| **PIL Post-Processing** | Nano-Banana generates art, PIL adds precise text overlays | Best of both worlds |
| **Age-Banded RAG** | Same snack → different facts based on child's age | Developmentally appropriate |
| **Mode-Based Backgrounds** | Freepik backgrounds auto-selected by CELEBRATE/EDUCATE mode | Visual mood setting |

**Technical Innovations**:
- **Dual Image Model Support**: Nano-Banana (1K) or Imagen 4.0 (2K) via config
- **Bubble Detection Cascade**: Gemini Vision → OpenCV contours → PIL fallback
- **OpenCV Inpainting**: Removes AI-generated text for clean bubble overlay
- **SVG-to-PNG Pipeline**: CairoSVG converts Freepik vectors at exact panel size
- **Alpha Compositing**: Semi-transparent bubbles (180 alpha) for comic effect
- **JSONL Audit Logs**: Daily compliance logs with SHA256 content hashing

**Novel Character Design** (DR. DRIP visual spec):
- Off-white/pale cyan molar body
- Dark forest green pullover hoodie
- Black retro sunglasses pushed up on forehead
- Chunky beige/tan Yeezy-style slides
- Large round eyes with small black pupils
- Wide smiling mouth with pink tongue
- Root-like legs

### 📋 TODO

- [x] Panel Layouts: Portrait (1x4), Reel (1x4) ✓
- [x] Celebrate Mode: Positive reinforcement ✓
- [x] Smart Item Grouping ✓
- [x] Panel-aware retrieval ✓
- [x] Cross-collection joins ✓
- [x] Mode-Based Backgrounds ✓
- [x] Emotion-based speech bubbles (5 types) ✓
- [x] DR. DRIP character system ✓
- [x] Roast corpus for few-shot learning ✓
- [ ] **Animated comics**: Video generation (novel format)
- [ ] **Character customization**: Let users pick mascot style (v1.2)
- [ ] **Multi-language support**: Expand reach (v1.2)

---

## Summary: Hackathon Readiness

| Criteria | Status | Key Strengths | Demo Points |
|----------|--------|---------------|-------------|
| **1. Creative Quality** | 🟢 Strong | DR. DRIP character, vanity roasting concept, 5 bubble styles, thinking mode | Show age toggle → personality change |
| **2. Search & Similarity** | 🟢 Strong | Transparent scoring, 4 collections, QueryBuilder, risk_tags | Show risk score breakdown |
| **3. Guardrails** | 🟢 Strong | 50+ blocked terms, teen slang allowlist, daily audit logs | Show guardrails_service.py |
| **4. UX & Tradeoffs** | 🟢 Strong | 5-step progress, localStorage persistence, mode-aware messages | Show scanning overlay |
| **5. Real-World Fit** | 🟢 Strong | Poppy Kids branding, social export formats | Show logo + export |
| **6. Innovation** | 🟢 Strong | Vanity roasting, dual model support, emotion bubbles | Show roast corpus |

---

## Presentation Demo Script

### 1. Opening (30 sec)
- "Meet DR. DRIP - a molar tooth who's about to roast your snack's aesthetic"
- Show DR. DRIP character design

### 2. Age Toggle Demo (30 sec)
- Toggle age from 10 to 15
- Show how DR. DRIP's message changes from "Spicy" to "Savage"
- Highlight: "Same character, different intensity"

### 3. Full Pipeline Demo (90 sec)
- Upload a photo of gummy bears
- Watch 5-step scanning progress
- Show risk score breakdown (sugar, stickiness, etc.)
- View generated comic with roast dialogue
- Highlight: Emotion-based bubbles (exclaim on Panel 2)

### 4. Celebrate Mode Demo (30 sec)
- Upload apple or carrot photo
- Show CELEBRATE mode comic ("Glow Up Approved")
- Highlight: Different narrative arc

### 5. Technical Deep-Dive (60 sec)
- Show `drdrip_roast_corpus.py` - 50+ few-shot examples
- Show `guardrails_service.py` - teen slang allowlist
- Show audit logs in `storage/audit/`
- Highlight: Production-ready safety

### 6. Close (30 sec)
- Download portrait format
- Show Poppy Kids branding in footer
- "Making dental health about the glow up, one roast at a time"

---

## Recently Completed Features

- ✅ **DR. DRIP Character System**: Age-adaptive personality (Spicy/Savage)
- ✅ **Vanity Roasting Concept**: Dental health reframed as aesthetics
- ✅ **Roast Corpus**: 50+ few-shot examples for quality scripts
- ✅ **Thinking Mode**: Vision (8192) and Writer (24576) budgets
- ✅ **5 Emotion Bubble Styles**: speech, thought, exclaim, angry, whisper
- ✅ **Dynamic Bubble Sizing**: Width scales with text length
- ✅ **Position-Aware Dialogue**: Left/right based on speaker position
- ✅ **GuardrailsService**: 50+ blocked terms, teen slang allowlist, auto-clean
- ✅ **AuditService**: Daily JSONL logs with SHA256 hashing
- ✅ **Image Prompt Validation**: Blocks unsafe content before generation
- ✅ **Celebrate Mode**: Positive comics for healthy snacks
- ✅ **Unknown Mode**: Generic DR. DRIP tips for unrecognized items
- ✅ **Smart Item Grouping**: Fruit plates, veggie trays as single items
- ✅ **Panel-aware Retrieval**: Facts match comic mood/scene
- ✅ **Cross-collection Joins**: Snack risk_tags filter relevant facts
- ✅ **Mode-Based Backgrounds**: Freepik backgrounds per comic mode
- ✅ **Poppy Kids Branding**: Logo in footer with website link
- ✅ **localStorage Persistence**: Age, allergens, intensity mode saved

---

## Priority TODOs for Hackathon

1. ✅ All core features implemented

### Deferred to v1.1
- **Animated Comics** - Video generation for Reels
- **User Signup Flow** - Capture preferences upfront
- **Rate Limiting** - Prevent abuse
- **Analytics** - Track usage metrics
