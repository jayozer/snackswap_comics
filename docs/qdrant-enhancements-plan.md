# Qdrant Query Enhancements Plan

> **Status**: Planning
> **Created**: 2025-12-07
> **Branch**: `qdrant-features`

## Overview

Two enhancements to improve the relevance and quality of Qdrant searches:

| Enhancement | Description | Impact |
|------------|-------------|--------|
| **Panel-aware retrieval** | Blend scene/mood context into search queries | Facts match comic panel tone |
| **Cross-collection joins** | Use snack metadata to refine fact searches | Facts align with specific snack characteristics |

---

## Enhancement 1: Panel-Aware Fact/Snack Retrieval

### Goal
Make fact retrieval context-aware so facts match the intended panel mood and scene.

### Current State (score.py:98-105)
```python
# Generic fact query - no panel context
fact_query = f"dental health, {item.category}, sugar, acidity"
fact_embedding = await gemini_service.generate_query_embedding(fact_query)

fact_results = await qdrant_service.search_facts(
    fact_embedding,
    age_band=age_band,
    limit=4,
)
```

### Proposed Approach: Query Augmentation

Blend panel context into the query text before generating embeddings. This is the simplest approach that requires **no schema changes**.

```python
# Panel context passed from script composition stage
panel_context = {
    "panel_number": 1,  # 1-4
    "scene": "playground",  # kitchen, dentist, school, playground
    "mood": "funny",  # funny, dramatic, educational, celebratory
    "narrative_beat": "intro"  # intro, conflict, revelation, resolution
}

# Augmented fact query
fact_query = f"dental health, {item.category}, {panel_context['mood']} tone, {panel_context['narrative_beat']}"
# Example: "dental health, candy, funny tone, intro"
```

### Implementation Steps

#### Step 1.1: Define Panel Context Model
**File**: `backend/app/models/api.py`

```python
from pydantic import BaseModel
from typing import Optional

class PanelContext(BaseModel):
    """Context for panel-aware retrieval."""
    panel_number: int = 1  # 1-4
    scene: Optional[str] = None  # playground, kitchen, dentist, school
    mood: str = "educational"  # funny, dramatic, educational, celebratory
    narrative_beat: str = "intro"  # intro, conflict, revelation, resolution
```

#### Step 1.2: Update search_facts Signature
**File**: `backend/app/services/qdrant_service.py`

```python
async def search_facts(
    self,
    query_vector: list[float],
    age_band: str,
    limit: int = 8,
    clinic_approved_only: bool = True,
    panel_context: dict | None = None,  # NEW
) -> list[models.ScoredPoint]:
    """
    Search for relevant facts with optional panel context filtering.

    Panel context is used at embedding generation time, not here.
    This parameter is for future metadata filtering if we add
    mood/scene tags to facts.
    """
```

#### Step 1.3: Create Context-Aware Query Builder
**File**: `backend/app/services/query_builder.py` (NEW)

```python
"""Query builder for context-aware Qdrant searches."""

from typing import Optional

class QueryBuilder:
    """Builds context-enriched query strings for embedding generation."""

    @staticmethod
    def build_fact_query(
        snack_category: str,
        snack_traits: list[str],
        panel_context: Optional[dict] = None,
    ) -> str:
        """
        Build a fact search query enriched with panel context.

        Args:
            snack_category: Category of detected snack (candy, chips, etc.)
            snack_traits: Risk traits from snack (sticky, sugary, acidic)
            panel_context: Optional panel mood/scene context

        Returns:
            Query string optimized for fact retrieval
        """
        base_query = f"dental health, {snack_category}"

        # Add snack traits
        if snack_traits:
            base_query += f", {', '.join(snack_traits)}"

        # Add panel context if provided
        if panel_context:
            mood = panel_context.get("mood", "educational")
            beat = panel_context.get("narrative_beat", "")

            # Mood-specific query augmentation
            mood_keywords = {
                "funny": "fun fact, surprising, amusing",
                "dramatic": "serious consequence, warning, danger",
                "educational": "learning, science, explanation",
                "celebratory": "positive, healthy, good choice",
            }

            if mood in mood_keywords:
                base_query += f", {mood_keywords[mood]}"

            # Narrative beat augmentation
            beat_keywords = {
                "intro": "introduction, discovery",
                "conflict": "problem, consequence, risk",
                "revelation": "surprise, revelation, science",
                "resolution": "solution, recommendation, tip",
            }

            if beat in beat_keywords:
                base_query += f", {beat_keywords[beat]}"

        return base_query

    @staticmethod
    def build_snack_query(
        detected_name: str,
        brand_guess: str | None,
        category: str,
    ) -> str:
        """Build a snack search query."""
        return f"brand={brand_guess or 'generic'}, type={category}, name={detected_name}"
```

#### Step 1.4: Integrate into Score Endpoint
**File**: `backend/app/api/score.py`

```python
from app.services.query_builder import QueryBuilder

# In score_retrieve(), replace:
# fact_query = f"dental health, {item.category}, sugar, acidity"

# With:
snack_traits = []
if matched_snack.get("stickiness", 0) > 0.5:
    snack_traits.append("sticky")
if matched_snack.get("added_sugar_g", 0) > 20:
    snack_traits.append("sugary")
if matched_snack.get("acidity_tag") == "high":
    snack_traits.append("acidic")

fact_query = QueryBuilder.build_fact_query(
    snack_category=item.category,
    snack_traits=snack_traits,
    panel_context=request.panel_context,  # Optional, passed from frontend
)
```

---

## Enhancement 2: Cross-Collection Joins at Query Time

### Goal
Ensure facts are specifically relevant to the matched snack's characteristics, not just generic dental facts.

### Current State
```
User uploads: gummy bears
  ↓
Snack search → "Gummy Bears" (sticky=0.8, sugary, acidic=medium)
  ↓
Fact search → generic "dental health, candy, sugar, acidity"
  ↓
Result: May return generic facts not specific to sticky candy
```

### Proposed State (Two-Stage Search)
```
User uploads: gummy bears
  ↓
Stage 1: Snack search → "Gummy Bears" (sticky=0.8, sugary, acidic=medium)
  ↓
Stage 2: Extract snack traits → Build targeted fact query
  - Query: "sticky candy dental damage, sugar bacteria, chewy residue"
  - Filters: age_band, clinic_approved, risk_tags=["sticky", "sugary"]
  ↓
Result: Facts specifically about sticky/sugary candy damage
```

### Implementation Steps

#### Step 2.1: Add Risk Tags to Facts (Seed Data)
**File**: `data/seeds/seed_data.py`

Add `risk_tags` to existing facts to enable filtering:

```python
facts = [
    {
        "fact_id": "F001",
        "text": "Sugar feeds bacteria in your mouth...",
        "topic": ["sugar", "bacteria"],
        "age_band": "6-8",
        "clinic_approved": True,
        "risk_tags": ["sugary"],  # NEW: Tags for cross-collection filtering
    },
    {
        "fact_id": "F002",
        "text": "Sticky foods like gummy candies stay on your teeth longer...",
        "topic": ["stickiness", "sugar"],
        "age_band": "6-8",
        "clinic_approved": True,
        "risk_tags": ["sticky", "sugary"],  # NEW
    },
    {
        "fact_id": "F004",
        "text": "Acidic drinks like soda can soften your tooth enamel...",
        "topic": ["acidity", "enamel"],
        "age_band": "9-12",
        "clinic_approved": True,
        "risk_tags": ["acidic"],  # NEW
    },
    # ... add risk_tags to all facts
]
```

#### Step 2.2: Add Payload Index for risk_tags
**File**: `backend/app/services/qdrant_service.py`

```python
async def _ensure_payload_indexes(self) -> None:
    indexes_config = {
        self.FACTS_COLLECTION: [
            ("clinic_approved", models.PayloadSchemaType.BOOL),
            ("age_band", models.PayloadSchemaType.KEYWORD),
            ("risk_tags", models.PayloadSchemaType.KEYWORD),  # NEW
        ],
        # ... existing indexes
    }
```

#### Step 2.3: Update search_facts to Accept Risk Tags Filter
**File**: `backend/app/services/qdrant_service.py`

```python
async def search_facts(
    self,
    query_vector: list[float],
    age_band: str,
    limit: int = 8,
    clinic_approved_only: bool = True,
    risk_tags: list[str] | None = None,  # NEW
) -> list[models.ScoredPoint]:
    """
    Search for relevant facts with optional risk tag filtering.

    Args:
        query_vector: Query embedding vector
        age_band: Target age band (3-5, 6-8, 9-12, all)
        limit: Maximum number of results
        clinic_approved_only: Only return clinic-approved facts
        risk_tags: Filter facts that mention these risk types (sticky, sugary, acidic)
    """
    must_conditions = [
        models.Filter(
            should=[
                models.FieldCondition(
                    key="age_band",
                    match=models.MatchValue(value=age_band),
                ),
                models.FieldCondition(
                    key="age_band",
                    match=models.MatchValue(value="all"),
                ),
            ]
        ),
    ]

    if clinic_approved_only:
        must_conditions.append(
            models.FieldCondition(
                key="clinic_approved",
                match=models.MatchValue(value=True),
            )
        )

    # NEW: Add risk_tags filter using "should" (OR logic)
    if risk_tags:
        risk_should = [
            models.FieldCondition(
                key="risk_tags",
                match=models.MatchValue(value=tag),
            )
            for tag in risk_tags
        ]
        must_conditions.append(models.Filter(should=risk_should))

    query_filter = models.Filter(must=must_conditions)
    # ... rest of search
```

#### Step 2.4: Extract Risk Tags from Matched Snack
**File**: `backend/app/services/scoring_service.py`

```python
def extract_risk_tags(self, snack_payload: dict) -> list[str]:
    """
    Extract risk tags from snack payload for cross-collection filtering.

    Args:
        snack_payload: Matched snack data

    Returns:
        List of risk tags (sticky, sugary, acidic, hard)
    """
    tags = []

    if snack_payload.get("stickiness", 0) > 0.5:
        tags.append("sticky")

    if snack_payload.get("added_sugar_g", 0) > 15:
        tags.append("sugary")

    acidity = snack_payload.get("acidity_tag", "low")
    if acidity in ("medium", "high"):
        tags.append("acidic")

    if snack_payload.get("crunch_hardness", 0) > 0.7:
        tags.append("hard")

    return tags
```

#### Step 2.5: Update Score Endpoint with Two-Stage Search
**File**: `backend/app/api/score.py`

```python
# After matching snack (line 79-82)
matched_snack = scoring_service.match_snack_to_payload(item, snack_results)

if not matched_snack:
    continue

# Calculate dental risk
risk_score = scoring_service.calculate_dental_risk(matched_snack)

# NEW: Extract risk tags for cross-collection filtering
risk_tags = scoring_service.extract_risk_tags(matched_snack)

# Build context-aware fact query
snack_traits = []
if "sticky" in risk_tags:
    snack_traits.append("sticky residue teeth")
if "sugary" in risk_tags:
    snack_traits.append("sugar bacteria cavity")
if "acidic" in risk_tags:
    snack_traits.append("acid enamel erosion")

fact_query = QueryBuilder.build_fact_query(
    snack_category=matched_snack["category"],
    snack_traits=snack_traits,
    panel_context=request.panel_context,
)

fact_embedding = await gemini_service.generate_query_embedding(fact_query)

# Search facts with risk tag filtering
fact_results = await qdrant_service.search_facts(
    fact_embedding,
    age_band=age_band,
    limit=4,
    risk_tags=risk_tags if risk_tags else None,  # NEW
)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/models/api.py` | Add `PanelContext` model |
| `backend/app/services/query_builder.py` | NEW: Context-aware query builder |
| `backend/app/services/qdrant_service.py` | Add `risk_tags` filter to `search_facts()` |
| `backend/app/services/scoring_service.py` | Add `extract_risk_tags()` method |
| `backend/app/api/score.py` | Integrate two-stage search with context |
| `data/seeds/seed_data.py` | Add `risk_tags` to all facts |

---

## Implementation Order

```
Phase 1: Data Layer
├── 1.1 Add risk_tags to facts in seed_data.py
├── 1.2 Add risk_tags payload index
└── 1.3 Re-seed Qdrant Cloud

Phase 2: Service Layer
├── 2.1 Create query_builder.py
├── 2.2 Add extract_risk_tags() to scoring_service.py
└── 2.3 Update search_facts() with risk_tags filter

Phase 3: API Layer
├── 3.1 Add PanelContext model
├── 3.2 Update ScoreRetrieveRequest to accept panel_context
└── 3.3 Integrate into score endpoint

Phase 4: Testing
├── 4.1 Test sticky snack → sticky facts alignment
├── 4.2 Test sugary snack → sugar facts alignment
├── 4.3 Test panel mood affects fact tone
└── 4.4 End-to-end comic generation test
```

---

## Example: Before vs After

### Before (Generic Facts)
```
Input: Gummy Bears photo
Snack Match: candy_gummy (sticky=0.8, sugar=46g, acidity=medium)

Fact Query: "dental health, candy, sugar, acidity"
Facts Retrieved:
- F003: "Brushing your teeth twice a day helps..." (generic)
- F015: "Drinking plain water is the best drink..." (not relevant)
- F007: "Eating cheese or yogurt after a sugary snack..." (somewhat relevant)
```

### After (Targeted Facts)
```
Input: Gummy Bears photo
Snack Match: candy_gummy (sticky=0.8, sugar=46g, acidity=medium)
Risk Tags: ["sticky", "sugary", "acidic"]

Fact Query: "dental health, candy, sticky residue teeth, sugar bacteria cavity, fun fact, introduction"
Filters: risk_tags IN ["sticky", "sugary", "acidic"]

Facts Retrieved:
- F002: "Sticky foods like gummy candies stay on your teeth longer..." (perfect match)
- F001: "Sugar feeds bacteria in your mouth that make acid..." (relevant)
- F004: "Acidic drinks like soda can soften your tooth enamel..." (relevant to acidity)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Empty results with strict filters | Fall back to vector-only search if filtered results < 2 |
| risk_tags missing from old facts | Default to empty list, gradually add tags |
| Query augmentation reduces accuracy | A/B test augmented vs original queries |
| Re-seeding loses data | Export existing data before re-seed |

---

## Success Criteria

1. **Sticky snack → sticky facts**: Gummy bears returns F002 (sticky fact) in top 3
2. **Panel mood affects tone**: "funny" mood returns lighter, surprising facts
3. **No regression**: Existing flow works identically when panel_context is None
4. **Performance**: Search latency < 200ms (no significant increase)
