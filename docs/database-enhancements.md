# Celebrate Mode Feature Plan

> **Status**: Planning
> **Created**: 2025-11-30

## Overview

Add support for healthy snacks and unknown items by introducing 3 comic modes:

| Mode | Trigger | Comic Narrative |
|------|---------|-----------------|
| **Educate** | risk >= 40 | Current flow - problem snack, dental risks, swap suggestions |
| **Celebrate** | risk < 40 | Fun facts about WHY snack is tooth-friendly (calcium, fiber, low sugar) |
| **Unknown** | No Qdrant match | Boilerplate generic dental health comic |

---

## Part 1: Database Changes

### 1.1 Add Healthy Snacks to `snacks_v1`

**File: `data/seeds/seed_data.py`**

Add healthy snacks with low risk scores:

```python
healthy_snacks = [
    {
        "snack_id": "fruit_apple",
        "name": "Apple",
        "brand": "Generic",
        "category": "fruit",
        "flavor_notes": ["sweet", "crisp", "fresh"],
        "sugar_g_per_100g": 10.0,  # Natural sugars
        "added_sugar_g": 0.0,      # No added sugar
        "acidity_tag": "medium",
        "stickiness": 0.1,
        "residue": 0.2,
        "crunch_hardness": 0.5,
        "water_content": 0.86,
        "typical_portion_g": 180,
        "allergy_tags": [],
        "taste_cluster": "sweet-fresh",
        "is_healthy": True,  # NEW FIELD
        "health_benefits": ["fiber helps clean teeth", "stimulates saliva", "vitamin C"],
    },
    {
        "snack_id": "vegetable_carrot",
        "name": "Carrots",
        "brand": "Generic",
        "category": "vegetable",
        "flavor_notes": ["sweet", "crunchy", "earthy"],
        "sugar_g_per_100g": 5.0,
        "added_sugar_g": 0.0,
        "acidity_tag": "low",
        "stickiness": 0.0,
        "residue": 0.1,
        "crunch_hardness": 0.7,
        "water_content": 0.88,
        "typical_portion_g": 80,
        "allergy_tags": [],
        "taste_cluster": "savory-crunch",
        "is_healthy": True,
        "health_benefits": ["crunching cleans teeth", "vitamin A", "low sugar"],
    },
    {
        "snack_id": "dairy_cheese",
        "name": "Cheese",
        "brand": "Generic",
        "category": "dairy",
        "flavor_notes": ["savory", "creamy", "rich"],
        "sugar_g_per_100g": 0.5,
        "added_sugar_g": 0.0,
        "acidity_tag": "low",
        "stickiness": 0.2,
        "residue": 0.3,
        "crunch_hardness": 0.0,
        "water_content": 0.37,
        "typical_portion_g": 30,
        "allergy_tags": ["dairy"],
        "taste_cluster": "savory-creamy",
        "is_healthy": True,
        "health_benefits": ["calcium strengthens enamel", "neutralizes acid", "protein"],
    },
    {
        "snack_id": "nut_almonds",
        "name": "Almonds",
        "brand": "Generic",
        "category": "nuts",
        "flavor_notes": ["nutty", "crunchy", "mild"],
        "sugar_g_per_100g": 4.0,
        "added_sugar_g": 0.0,
        "acidity_tag": "low",
        "stickiness": 0.0,
        "residue": 0.2,
        "crunch_hardness": 0.8,
        "water_content": 0.04,
        "typical_portion_g": 30,
        "allergy_tags": ["tree_nuts"],
        "taste_cluster": "savory-crunch",
        "is_healthy": True,
        "health_benefits": ["calcium for strong teeth", "protein", "healthy fats"],
    },
    {
        "snack_id": "vegetable_celery",
        "name": "Celery",
        "brand": "Generic",
        "category": "vegetable",
        "flavor_notes": ["fresh", "crunchy", "mild"],
        "sugar_g_per_100g": 1.3,
        "added_sugar_g": 0.0,
        "acidity_tag": "low",
        "stickiness": 0.0,
        "residue": 0.05,
        "crunch_hardness": 0.6,
        "water_content": 0.95,
        "typical_portion_g": 100,
        "allergy_tags": [],
        "taste_cluster": "fresh-light",
        "is_healthy": True,
        "health_benefits": ["natural toothbrush", "high water content", "stimulates gums"],
    },
]
```

### 1.2 Add Positive/Celebration Facts to `facts_v1`

**File: `data/seeds/seed_data.py`**

Add facts that explain WHY healthy snacks are good:

```python
celebrate_facts = [
    {
        "fact_id": "CF001",
        "text": "Crunchy fruits and vegetables like apples and carrots act like natural toothbrushes, scrubbing away plaque as you chew!",
        "topic": ["crunchy", "cleaning", "healthy"],
        "age_band": "all",
        "source_key": "ClinicKB#CrunchyFoods",
        "clinic_approved": True,
        "fact_type": "celebrate",  # NEW FIELD
    },
    {
        "fact_id": "CF002",
        "text": "Cheese is a superhero for teeth! It has calcium to make enamel strong and helps neutralize acids in your mouth.",
        "topic": ["calcium", "dairy", "healthy"],
        "age_band": "6-8",
        "source_key": "ClinicKB#DairyBenefits",
        "clinic_approved": True,
        "fact_type": "celebrate",
    },
    {
        "fact_id": "CF003",
        "text": "Foods with lots of water, like celery and cucumber, help wash away food bits and keep your mouth hydrated!",
        "topic": ["water", "hydration", "healthy"],
        "age_band": "all",
        "source_key": "ClinicKB#Hydration",
        "clinic_approved": True,
        "fact_type": "celebrate",
    },
    {
        "fact_id": "CF004",
        "text": "Nuts like almonds are packed with calcium and protein - the building blocks for super strong teeth!",
        "topic": ["nuts", "calcium", "protein"],
        "age_band": "9-12",
        "source_key": "ClinicKB#NutsBenefits",
        "clinic_approved": True,
        "fact_type": "celebrate",
    },
    {
        "fact_id": "CF005",
        "text": "When you eat fruits instead of candy, you're giving your teeth a treat - natural sugars with fiber are much gentler!",
        "topic": ["fruit", "natural_sugar", "healthy"],
        "age_band": "6-8",
        "source_key": "ClinicKB#NaturalSugars",
        "clinic_approved": True,
        "fact_type": "celebrate",
    },
]
```

### 1.3 Add Payload Index for New Fields

**File: `backend/app/services/qdrant_service.py`**

Add index for `fact_type` field:

```python
indexes_config = {
    self.FACTS_COLLECTION: [
        ("clinic_approved", models.PayloadSchemaType.BOOL),
        ("age_band", models.PayloadSchemaType.KEYWORD),
        ("fact_type", models.PayloadSchemaType.KEYWORD),  # NEW
    ],
    # ... existing indexes
}
```

---

## Part 2: API Response Changes

### 2.1 Add `mode` Field to Response Models

**File: `backend/app/models/api.py`**

```python
from enum import Enum

class ComicMode(str, Enum):
    EDUCATE = "educate"    # Risk >= 40, problem snack
    CELEBRATE = "celebrate" # Risk < 40, healthy snack
    UNKNOWN = "unknown"     # No match in database

class ScoreRetrieveResponse(BaseModel):
    scored_items: list[ScoredItem]
    facts: list[dict[str, Any]]
    swaps: list[dict[str, Any]]
    mode: ComicMode  # NEW FIELD
    average_risk_score: float  # NEW - for determining mode
```

### 2.2 Update Score Endpoint

**File: `backend/app/api/score.py`**

Add mode determination logic:

```python
HEALTHY_THRESHOLD = 40.0  # Risk below this = celebrate mode

# After scoring all items...
if not scored_items:
    # No matches found - unknown mode
    mode = ComicMode.UNKNOWN
    average_risk = 0.0
else:
    # Calculate average risk
    average_risk = sum(item.dental_risk_score for item in scored_items) / len(scored_items)
    mode = ComicMode.CELEBRATE if average_risk < HEALTHY_THRESHOLD else ComicMode.EDUCATE

# Fetch appropriate facts based on mode
if mode == ComicMode.CELEBRATE:
    # Get celebration facts
    fact_results = qdrant_service.search_facts(
        fact_embedding,
        age_band=age_band,
        limit=4,
        fact_type="celebrate",  # Filter for positive facts
    )
elif mode == ComicMode.UNKNOWN:
    # Get generic dental facts
    fact_results = qdrant_service.search_facts(
        generic_dental_embedding,
        age_band=age_band,
        limit=4,
    )
else:
    # Current educate behavior
    fact_results = qdrant_service.search_facts(...)

return ScoreRetrieveResponse(
    scored_items=scored_items,
    facts=list(unique_facts),
    swaps=list(unique_swaps) if mode == ComicMode.EDUCATE else [],  # No swaps for healthy!
    mode=mode,
    average_risk_score=average_risk,
)
```

### 2.3 Update Qdrant Service for Fact Type Filter

**File: `backend/app/services/qdrant_service.py`**

Add `fact_type` parameter to `search_facts()`:

```python
def search_facts(
    self,
    query_vector: list[float],
    age_band: str,
    limit: int = 8,
    clinic_approved_only: bool = True,
    fact_type: str | None = None,  # NEW: "celebrate" or None for all
) -> list[models.ScoredPoint]:
    """Search for relevant facts, optionally filtering by type."""

    must_conditions = [
        models.FieldCondition(
            key="clinic_approved",
            match=models.MatchValue(value=True),
        ),
        models.Filter(
            should=[
                models.FieldCondition(key="age_band", match=models.MatchValue(value=age_band)),
                models.FieldCondition(key="age_band", match=models.MatchValue(value="all")),
            ]
        ),
    ]

    # Add fact_type filter if specified
    if fact_type:
        must_conditions.append(
            models.FieldCondition(
                key="fact_type",
                match=models.MatchValue(value=fact_type),
            )
        )

    query_filter = models.Filter(must=must_conditions)
    # ... rest of search
```

---

## Part 3: Script Composition Changes

### 3.1 Add Celebrate Mode Prompt

**File: `backend/app/services/gemini_service.py`**

Add new method `compose_celebrate_script()`:

```python
async def compose_celebrate_script(
    self,
    snacks: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    age: int,
) -> dict[str, Any]:
    """Compose a CELEBRATION 4-panel comic for healthy snacks."""

    # Age band and tone logic (same as current)

    prompt = f"""You are a comedy writer for kids creating CELEBRATORY 4-panel dental health comics!

TARGET AUDIENCE: Age {age} ({age_band} years old), tone: {tone} and POSITIVE!

🎭 RECURRING CHARACTER - CAPTAIN SPARKLE:
Captain Sparkle is a superhero tooth. In CELEBRATE comics, Captain Sparkle is IMPRESSED and EXCITED about the healthy snack choice!

HEALTHY SNACKS DETECTED (they become hero characters!):
{snacks_context}

FUN FACTS ABOUT WHY THEY'RE GREAT FOR TEETH:
{facts_context}

🎬 CELEBRATE PANEL STRUCTURE:

PANEL 1 - THE HERO ENTRANCE
- Healthy snack introduces itself proudly
- Captain Sparkle appears excited: "Wow!"
- Set up the snack's superpower (crunchy, calcium-rich, etc.)

PANEL 2 - THE SUPERPOWER REVEAL
- Explain WHY this snack is great for teeth (cite fact)
- Visual demonstration of the benefit
- Captain Sparkle learns something cool

PANEL 3 - TEAM UP MOMENT
- Captain Sparkle and snack become friends/partners
- Another fun fact about dental health (cite fact)
- Positive energy, high-fives, teamwork

PANEL 4 - THE CELEBRATION
- Captain Sparkle gives a "Tooth Approved!" badge or stamp
- Encouraging message: "Great choice!"
- End with snack looking proud, Captain Sparkle triumphant

🎨 TONE GUIDELINES:
- POSITIVE only - no guilt, no "instead of bad snacks"
- Focus on what makes THIS snack awesome
- Educational but fun - facts should feel like cool discoveries
- Captain Sparkle is genuinely impressed, not just being nice

... (same JSON output structure as educate mode)
"""
```

### 3.2 Add Unknown Mode Boilerplate

**File: `backend/app/services/gemini_service.py`**

Add method for generic/unknown snacks:

```python
def get_unknown_script(self, detected_name: str, age: int) -> dict[str, Any]:
    """Return a boilerplate comic for unknown food items."""

    return {
        "panels": [
            {
                "panel_number": 1,
                "title": "A Mystery Snack!",
                "dialogue": [
                    f"Hmm, I found a {detected_name}!",
                    "Captain Sparkle here! Let's talk teeth!"
                ],
                "characters": [
                    {"name": "Mystery Snack", "expression": "curious", "position": "left"},
                    {"name": "Captain Sparkle", "expression": "friendly", "position": "right", "props": ["cape"]}
                ],
                "visual_prompt": f"A friendly question mark shaped snack next to a superhero tooth character",
            },
            {
                "panel_number": 2,
                "title": "The Golden Rule",
                "dialogue": [
                    "Whatever you eat, remember this:",
                    "Brush twice a day for sparkly teeth!"
                ],
                "characters": [
                    {"name": "Captain Sparkle", "expression": "teaching", "position": "center", "props": ["toothbrush"]}
                ],
            },
            {
                "panel_number": 3,
                "title": "Water is Your Friend",
                "dialogue": [
                    "Drink water after snacks!",
                    "It washes away the sneaky bits!"
                ],
                "characters": [
                    {"name": "Captain Sparkle", "expression": "excited", "position": "left"},
                    {"name": "Water Glass", "expression": "happy", "position": "right"}
                ],
            },
            {
                "panel_number": 4,
                "title": "Sparkle Power!",
                "dialogue": [
                    "Take care of your teeth...",
                    "And they'll take care of you! Sparkle power!"
                ],
                "characters": [
                    {"name": "Captain Sparkle", "expression": "triumphant", "position": "center", "props": ["cape", "sparkles"]}
                ],
            }
        ],
        "summary_caption": "Captain Sparkle's tips for healthy teeth!",
        "alt_text": "A 4-panel comic with Captain Sparkle the tooth superhero sharing dental health tips.",
        "mode": "unknown"
    }
```

### 3.3 Update Script API Endpoint

**File: `backend/app/api/script.py`**

Route to appropriate script generator based on mode:

```python
@router.post("/compose", response_model=ScriptComposeResponse)
async def compose_script(request: ScriptComposeRequest, ...):

    mode = request.mode  # Passed from score endpoint

    if mode == ComicMode.UNKNOWN:
        # Use boilerplate
        script = gemini_service.get_unknown_script(
            detected_name=request.items[0].name if request.items else "snack",
            age=request.age
        )
    elif mode == ComicMode.CELEBRATE:
        # Use celebration prompt
        script = await gemini_service.compose_celebrate_script(
            snacks=request.snacks,
            facts=request.facts,
            age=request.age,
        )
    else:
        # Current educate flow
        script = await gemini_service.compose_script(...)

    return ScriptComposeResponse(script=script, mode=mode)
```

---

## Part 4: Frontend Changes

### 4.1 Update Results Display

**File: `frontend/src/App.jsx` (or equivalent)**

Show different UI based on mode:

```jsx
{mode === "celebrate" && (
  <div className="celebrate-banner">
    Great choice! This snack is tooth-friendly!
  </div>
)}

{mode === "unknown" && (
  <div className="unknown-banner">
    We don't have info on this snack, but here are some tips!
  </div>
)}

{mode === "educate" && (
  <div className="educate-banner">
    Dental Risk Score: {riskScore}/100
  </div>
)}
```

### 4.2 Hide Swaps Section for Non-Educate Modes

```jsx
{mode === "educate" && swaps.length > 0 && (
  <SwapSuggestions swaps={swaps} />
)}
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `data/seeds/seed_data.py` | Add healthy snacks, celebration facts |
| `backend/app/models/api.py` | Add `ComicMode` enum, update response models |
| `backend/app/api/score.py` | Add mode determination logic |
| `backend/app/services/qdrant_service.py` | Add `fact_type` filter, new index |
| `backend/app/services/gemini_service.py` | Add `compose_celebrate_script()`, `get_unknown_script()` |
| `backend/app/api/script.py` | Route to correct script generator |
| `frontend/src/App.jsx` | Mode-based UI display |

---

## Testing Plan

1. **Seed healthy snacks**: Run `seed_data.py`, verify in Qdrant dashboard
2. **Test Celebrate Mode**: Upload apple photo -> expect mode="celebrate", positive comic
3. **Test Unknown Mode**: Upload obscure item -> expect mode="unknown", boilerplate comic
4. **Test Educate Mode**: Upload gummy bears -> expect mode="educate", current behavior
5. **Threshold boundary**: Test items near 40 risk score

---

## Rollback Plan

- Mode logic is additive - if issues, can hard-code `mode = ComicMode.EDUCATE`
- New facts/snacks don't affect existing queries (filtered by `fact_type`)
- Frontend changes are cosmetic only

---

## Section-by-Section Implementation Plan

### Phase 1: Data Layer (Foundation)
**Priority: FIRST - Everything depends on this**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 1.1 | Add `fact_type` field to existing facts (default: "educate") | `seed_data.py` | Small |
| 1.2 | Add 5 healthy snacks with `is_healthy` and `health_benefits` fields | `seed_data.py` | Medium |
| 1.3 | Add 5 celebration facts with `fact_type: "celebrate"` | `seed_data.py` | Medium |
| 1.4 | Add `fact_type` payload index to Qdrant | `qdrant_service.py` | Small |
| 1.5 | Run seed script to populate Qdrant Cloud | Terminal | Small |
| 1.6 | **CHECKPOINT**: Verify data in Qdrant Dashboard | Manual | - |

### Phase 2: API Models (Contracts)
**Priority: SECOND - Define the interface before implementation**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 2.1 | Create `ComicMode` enum | `models/api.py` | Small |
| 2.2 | Add `mode` and `average_risk_score` to `ScoreRetrieveResponse` | `models/api.py` | Small |
| 2.3 | Add `mode` to `ScriptComposeRequest` | `models/api.py` | Small |
| 2.4 | **CHECKPOINT**: Run type checker, ensure no breaks | Terminal | - |

### Phase 3: Qdrant Service (Query Layer)
**Priority: THIRD - Enable filtered queries**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 3.1 | Add `fact_type` parameter to `search_facts()` | `qdrant_service.py` | Medium |
| 3.2 | Update filter logic to include `fact_type` when specified | `qdrant_service.py` | Medium |
| 3.3 | **CHECKPOINT**: Test `search_facts(fact_type="celebrate")` returns only celebration facts | Manual | - |

### Phase 4: Score Endpoint (Mode Logic)
**Priority: FOURTH - The decision point**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 4.1 | Add `HEALTHY_THRESHOLD = 40.0` constant | `api/score.py` | Small |
| 4.2 | Add mode determination logic after scoring | `api/score.py` | Medium |
| 4.3 | Route to appropriate fact search based on mode | `api/score.py` | Medium |
| 4.4 | Return empty swaps for non-educate modes | `api/score.py` | Small |
| 4.5 | **CHECKPOINT**: Test with gummy bears (educate), apple (celebrate), unknown item (unknown) | Manual | - |

### Phase 5: Script Composition (Content Generation)
**Priority: FIFTH - Generate appropriate content per mode**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 5.1 | Add `get_unknown_script()` method (static boilerplate) | `gemini_service.py` | Medium |
| 5.2 | Add `compose_celebrate_script()` method (new prompt) | `gemini_service.py` | Large |
| 5.3 | Update `api/script.py` to route based on mode | `api/script.py` | Medium |
| 5.4 | **CHECKPOINT**: Full pipeline test for all 3 modes | Manual | - |

### Phase 6: Frontend (User Experience)
**Priority: LAST - Polish the presentation**

| Step | Task | File | Estimated Effort |
|------|------|------|------------------|
| 6.1 | Add mode-based banner component | `App.jsx` | Medium |
| 6.2 | Conditionally hide swaps section | `App.jsx` | Small |
| 6.3 | Style celebrate/unknown banners | `styles.css` | Small |
| 6.4 | **CHECKPOINT**: End-to-end test in browser | Manual | - |

---

## Implementation Order Rationale

```
Phase 1 (Data) ──► Phase 2 (Models) ──► Phase 3 (Qdrant) ──► Phase 4 (Score) ──► Phase 5 (Script) ──► Phase 6 (Frontend)
     │                   │                    │                    │                   │                   │
     │                   │                    │                    │                   │                   │
   Data must          Contracts            Queries need         Logic needs         Scripts need       UI needs
   exist first        define API           data + models        queries            mode info          everything
```

**Why this order?**
1. **Data first**: Can't test anything without healthy snacks and celebration facts in Qdrant
2. **Models second**: API contracts must be defined before endpoints use them
3. **Qdrant third**: Query layer must support `fact_type` filter before score endpoint can use it
4. **Score fourth**: Mode determination happens here - central to the feature
5. **Script fifth**: Depends on mode being passed from score endpoint
6. **Frontend last**: Only affects presentation, can be tested once backend is complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Existing tests break | Run tests after each phase checkpoint |
| Gemini prompt quality for celebrate mode | Test with multiple healthy snacks, iterate on prompt |
| Unknown mode feels generic | Can enhance later with more varied boilerplate templates |
| Threshold (40) too high/low | Make it configurable via environment variable |
