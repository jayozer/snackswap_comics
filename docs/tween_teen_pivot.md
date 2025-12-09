# SnackSwap Comics: Tween/Teen Pivot - "Roast My Snack"

> **Document Status**: Implementation Plan
> **Created**: 2025-12-08
> **Target Launch**: Hackathon Demo
> **Related**: `docs/new_prompts.md` (prompt specifications)

---

## Executive Summary

SnackSwap Comics is pivoting from a young-kids dental education app to a **tween/teen social content generator** called **"Roast My Snack"** - where **DR. DRIP**, a hype-beast molar tooth, absolutely destroys your snack choices with savage facts and meme-worthy burns.

**Key Changes:**
- Age range: **9-17** (tweens + teens only)
- Two age bands: **9-12** (Tween/Spicy), **13-17** (Teen/Savage)
- New mascot: **DR. DRIP** - hype-beast tooth with gold crown, sunglasses, fresh kicks
- Content tone: Savage roast comedian, TikTok-ready, screenshot-worthy
- Vision detection: "Savage Food Critic" style naming
- No signup required: Inline preferences with localStorage

---

## Part 1: Target Audience

### 1.1 Age Bands

| Band | Ages | Label | Description |
|------|------|-------|-------------|
| **Tween** | 9-12 | "Kid Mode" | Still educational, lighter humor, Captain Sparkle remains |
| **Teen** | 13-17 | "Roast Mode" | Full meme energy, edgy mascot, shareable content |

**Why no 18+?** They're adults. This app is for kids/teens who might still listen to dental health advice if it's delivered in a way they find funny.

**Why no under 9?** Young kids (3-8) don't use apps independently and the meme humor wouldn't land. Parents wanting content for younger kids can use other resources.

### 1.2 User Personas

**Tween User (9-12)**
- Uses app on family tablet or their first phone
- Might share with friends at school
- Still receptive to educational content
- Likes superhero characters
- Parents may be aware of usage

**Teen User (13-17)**
- Has their own phone and social accounts
- Will only engage if content is genuinely funny
- Shares memes with friends on TikTok/Instagram/Snapchat
- Immune to "educational" framing - needs to feel authentic
- Primary driver: "This is actually funny" not "This is good for me"

---

## Part 2: "Roast My Snack" Concept

### 2.1 Core Idea

Transform dental health education into **comedy roast content**. Instead of teaching kids about cavities, we **roast their snack choices** with dental facts delivered as burns.

**Tagline Options:**
- "Roast My Snack" - Your snacks, roasted
- "Your teeth called. They're disappointed."
- "Snack check. Vibe check. Dental wreck."

### 2.2 Content Philosophy

| Old Approach | New Approach |
|--------------|--------------|
| "Sugar is bad for your teeth!" | "Bro really said 'I hate my enamel' with that choice" |
| "Captain Sparkle teaches..." | "Let me tell you why that's a certified L" |
| "Did you know?" facts | "POV: Your dentist seeing this photo" |
| Educational superhero | Sarcastic roast comedian |
| "Great job choosing healthy!" | "Okay I can't even roast this, that's valid" |

### 2.3 Meme Integration Guidelines

**Approved Meme Language (evolves with trends):**
- "POV: [situation]"
- "It's giving [descriptor]"
- "No cap" / "Fr fr"
- "That's not it, bestie"
- "Ratio" (when snack is bad)
- "W choice" / "L choice"
- "Main character energy" (for healthy snacks)
- "NPC behavior" (for mindless bad snacking)
- "Caught in 4K" (snack crimes)

**Avoid:**
- Outdated memes (dab, yeet used unironically)
- Trying too hard (cringe)
- Mean-spirited content (roast ≠ bully)
- Anything that could be body-shaming

---

## Part 3: Mascot Specifications

### 3.1 Tween Mode: DR. DRIP (Spicy Edition)

**For ages 9-12** - Same character, toned down intensity:

- **Visual**: Same Dr. Drip design but slightly friendlier expressions
- **Personality**: Still sassy but less savage
- **Catchphrase**: "That's sus for your teeth!"
- **Tone**: Spicy but age-appropriate burns

### 3.2 Teen Mascot: DR. DRIP (Full Savage Mode)

**For ages 13-17** - The main character:

#### Visual Design
```
Name: Dr. Drip (or just "Drip")
Species: Hype-beast molar tooth
Vibe: Brutally honest roast master with a PhD in dental destruction

Physical Traits:
- Molar tooth shape (not front tooth)
- Wears dark sunglasses (always on, even indoors)
- GOLD CROWN on top (literal crown, because he's the king)
- Fresh kicks (tiny sneakers - Jordans or Yeezys vibes)
- Confident stance, arms crossed or pointing
- Smug expression by default

Accessories:
- Gold crown (signature piece)
- Sunglasses (never removes except for extreme shock)
- Fresh sneakers
- Optional: tiny chain, microphone for roast moments

Expression Range:
- Default: Smug, arms crossed, judging
- Roasting: Pointing, leaning in, savage smirk
- Shocked (healthy snack): Sunglasses lifted, eyes wide, "Sheesh!"
- Disgusted: Looking away, hand up in "stop"
- Respect: Nod, dap up pose, "W"
```

#### Personality Profile
```
Core Traits:
- SAVAGE but not cruel
- Brutally honest - no sugarcoating (pun intended)
- Hype-beast energy - knows what's cool
- Actually knowledgeable about dental health
- Uses slang CORRECTLY (not cringe adult attempts)

Speech Patterns (CURRENT teen slang):
- "You're COOKED." (signature catchphrase)
- "Get scrubbed." (secondary catchphrase)
- "That's mid." / "That's trash."
- "No cap" (for real)
- "Based" (respectable choice)
- "Cringe" (bad choice)
- "Bro really thought..."
- "Imagine having..."
- "Skill issue"
- "Let him cook" (for healthy snacks)
- "Sheesh!" (impressed)

What Dr. Drip WOULD Say:
- "Bro, you're literally eating a cavity speedrun."
- "That's not a snack, that's a dentist bill with extra steps."
- "50g of sugar? The bacteria in your mouth are throwing a party rn."
- "Your enamel just unfollowed you."
- "That's a stage 5 clinger for your teeth."

What Dr. Drip would NOT Say:
- "Remember to brush your teeth!" (too preachy)
- "Yeet!" "Skibidi!" (dead/cringe memes)
- "You're stupid" (mean, not funny)
- Anything that sounds like a dentist wrote it
```

#### Character Backstory
```
Dr. Drip earned his crown by being the most based tooth in the mouth.
He's seen the cavity wars. He's watched friends get pulled.
Now he uses his platform to expose snack crimes and keep it real.
He's not a hater - he's a truth-teller with immaculate drip.
```

### 3.3 Mode Intensity Matrix

| Scenario | Tween 9-12 (Spicy) | Teen 13-17 (Savage) |
|----------|---------------------|---------------------|
| Bad snack | "That's sus..." | "You're COOKED." |
| Roast intensity | Light burns | Full destruction |
| Slang usage | Mild | Heavy |
| Final verdict | "Not great" | "MID" / "TRASH" |
| Good snack | "Nice!" | "Sheesh! Let him cook." |
| Respect given | High five | Crown ceremony, "GOATED" |

---

## Part 4: Comic Script Structure

> **Full prompt specifications in:** `docs/new_prompts.md`

### 4.1 Teen "Roast" Mode (Educate - Bad Snack)

**Triggered when:** Risk score ≥ 30 AND age 13-17

**THE ROAST ARC:**
```
PANEL 1: THE FLEX (The Setup)
- Snack enters acting cool, thinking it's delicious
- Snack: "I'm the main character."
- Dr. Drip watches from side, looking skeptical, maybe holding "X" sign
- Visual: Snack looking smug, Drip unimpressed

PANEL 2: THE EXPOSÉ (The Roast Begins)
- Dr. Drip steps in and drops a HARD FACT (cite fact_id)
- "Bro, you're literally just sticky sugar glue."
- Snack starts sweating/panicking
- Visual: Snack glitching out or sweating, Drip pointing

PANEL 3: THE RATIO (The Destruction)
- Dr. Drip doubles down with emotional damage
- "You're stuck in teeth for 6 hours? Stage 5 clinger vibes."
- Another fact if available
- Visual: Snack crying, melting, or defeated ("I just wanted to be loved!")

PANEL 4: THE VIBE CHECK (The Verdict)
- Dr. Drip presents the CHAD SWAP
- "Swap to Apple Slices. High fiber, no cap."
- Dr. Drip poses with the Swap (who looks buff/Chad-like)
- Final verdict overlay: "MID" or "TRASH" or "COOKED"
```

### 4.2 Teen "Based" Mode (Celebrate - Good Snack)

**Triggered when:** Risk score < 30 AND age 13-17

**THE W ARC:**
```
PANEL 1: THE ENTRANCE
- Healthy Snack walks in looking confident (buff arms or sunglasses)
- Dr. Drip: "Hold up... let him cook."
- Visual: Snack with main character energy, Drip intrigued

PANEL 2: THE STATS
- Snack reveals its stats (Fiber, Vitamins, Crunch)
- Dr. Drip is impressed: "No cavity creeps? That's OP."
- Cite fact_id
- Visual: Stats floating around snack like a video game character

PANEL 3: THE GLAZE
- Dr. Drip and Snack engage in handshake or bro-hug
- "Cleans teeth while you eat? Actually cracked strategy."
- Visual: Mutual respect moment, maybe sparkle effects

PANEL 4: THE CROWN
- Dr. Drip puts a literal crown on the snack
- Final Text: "W SNACK" or "BASED" or "GOATED"
- Visual: Coronation ceremony, Drip nodding approval
```

### 4.3 Tween Mode (Ages 9-12)

**Same Dr. Drip but SPICY not SAVAGE:**
- Less intense slang
- Still funny, not baby talk
- "That's sus" instead of "You're COOKED"
- "Not great" instead of "TRASH"
- Same 4-panel structure, lighter burns

---

## Part 5: Technical Implementation

> **Prompt specifications:** All new prompts are defined in `docs/new_prompts.md`

### 5.1 Backend Changes

#### File: `backend/app/models/api.py`

**Change:** Update age validation (9-17 instead of 3-12)

```python
# BEFORE
age: int = Field(..., ge=3, le=12, description="Child's age")

# AFTER
age: int = Field(..., ge=9, le=17, description="User's age (9-17)")
```

Apply to: `ScoreRetrieveRequest`, `ScriptComposeRequest`

---

#### File: `backend/app/services/scoring_service.py`

**Change:** Update `get_age_band()` for 2 bands

```python
def get_age_band(self, age: int) -> str:
    """Convert age to age band: 9-12 (Spicy) or 13-17 (Savage)."""
    if age <= 12:
        return "9-12"  # Tween - Spicy mode
    else:
        return "13-17"  # Teen - Savage mode
```

---

#### File: `backend/app/services/gemini_service.py`

**Changes:** Replace ALL prompts with versions from `docs/new_prompts.md`

| Method | New Prompt From |
|--------|-----------------|
| `detect_items()` | Section 1: Savage Food Critic vision prompt |
| `compose_educate_script()` | Section 2: Dr. Drip Roast prompt |
| `compose_celebrate_script()` | Section 3: Dr. Drip "Based" prompt |

**Key additions:**
1. Add `is_teen = age >= 13` check
2. Teen mode (13-17): Full savage Dr. Drip prompts
3. Tween mode (9-12): Same Dr. Drip, lighter intensity

**Dr. Drip character in prompts:**
```
🎭 RECURRING CHARACTER - DR. DRIP:
A hype-beast molar tooth with sunglasses, a gold crown (literally), and fresh kicks.
Personality: Brutally honest, uses slang (cooked, mid, based, cringe, no cap), unfiltered.
Catchphrase: "You're COOKED." or "Get scrubbed."
```

---

#### File: `backend/app/services/nanobana_service.py`

**Change:** Update image generation prompt (from Section 4 of new_prompts.md)

```
STYLE: Modern "Webtoon" or "Adult Swim" animation style. Edgy, high-contrast, expressive.

VISUAL STYLE RULES:
- Thick, gritty ink lines (street art/underground comics)
- Saturated, neon-accented color palette (Cyberpunk lite / Graffiti vibes)
- EXAGGERATED expressions (anime shock, meme faces, intense crying, smug smirk)
- Dr. Drip looks COOL: Sunglasses, gold tooth cap, sneakers. NOT a baby superhero.
- Backgrounds: Halftone dots, speed lines, abstract gradients
```

---

#### File: `backend/data/seeds/seed_data.py`

**Changes needed:**

1. Update all `age_band` values from old system to new:
   - "3-5" → "9-12" (or remove if too young)
   - "6-8" → "9-12"
   - "9-12" → "9-12" (keep)
   - Add new "13-17" variants

2. Add teen-appropriate facts written in roastable format:

```python
# Example teen facts to add
{
    "fact_id": "teen_sugar_bacteria",
    "text": "Sugar literally feeds the bacteria in your mouth - they produce acid that eats through enamel in about 20 minutes after you eat",
    "age_band": "13-17",
    "fact_type": "educate",
    "topic": ["sugar", "bacteria", "acid"],
    "risk_tags": ["sugary"],
    "roast_hook": "bacteria throwing a party",  # NEW: helps with roast generation
},
{
    "fact_id": "teen_sticky_time",
    "text": "Sticky candy stays on teeth for hours, giving bacteria an all-you-can-eat buffet of sugar",
    "age_band": "13-17",
    "fact_type": "educate",
    "topic": ["sticky", "candy", "time"],
    "risk_tags": ["sticky"],
    "roast_hook": "all-you-can-eat bacteria buffet",
},
{
    "fact_id": "teen_acid_erosion",
    "text": "Sour candy is double trouble - the sugar feeds bacteria AND the acid directly dissolves enamel",
    "age_band": "13-17",
    "fact_type": "educate",
    "topic": ["sour", "acid", "enamel"],
    "risk_tags": ["acidic"],
    "roast_hook": "speedrunning enamel destruction",
},
# Celebration facts for healthy snacks
{
    "fact_id": "teen_cheese_neutral",
    "text": "Cheese actually neutralizes acid in your mouth and has calcium that strengthens enamel",
    "age_band": "13-17",
    "fact_type": "celebrate",
    "topic": ["cheese", "calcium", "acid"],
    "roast_hook": "dentist-approved moves",
},
{
    "fact_id": "teen_apple_clean",
    "text": "Crunchy fruits like apples literally scrub your teeth while you eat them - nature's toothbrush",
    "age_band": "13-17",
    "fact_type": "celebrate",
    "topic": ["apple", "crunchy", "cleaning"],
    "roast_hook": "multitasking legend",
},
```

3. **Re-seed Qdrant** after changes with:
```bash
cd backend && ./seed_data.sh
```

---

### 5.2 Frontend Changes

#### File: `frontend/src/components/AgeSelector.tsx`

**Changes:**

1. Update age range from 3-12 to 9-17
2. Update age groups to 2 bands
3. Update labels and emojis

```typescript
// BEFORE
const ageGroups = [
  { min: 3, max: 5, emoji: '🧒', label: 'Little' },
  { min: 6, max: 8, emoji: '👦', label: 'Kid' },
  { min: 9, max: 12, emoji: '🧑', label: 'Tween' },
];

// AFTER
const ageGroups = [
  { min: 9, max: 12, emoji: '😎', label: 'Tween' },
  { min: 13, max: 17, emoji: '🔥', label: 'Teen' },
];
```

Update slider min/max:
```typescript
// BEFORE
<input type="range" min={3} max={12} ...

// AFTER
<input type="range" min={9} max={17} ...
```

Update default age in parent component from 7 to 12.

---

#### New File: `frontend/src/components/AllergenSelector.tsx`

```typescript
'use client';

import { motion } from 'framer-motion';

const ALLERGENS = [
  { id: 'dairy', label: 'Dairy', emoji: '🥛' },
  { id: 'nuts', label: 'Tree Nuts', emoji: '🌰' },
  { id: 'peanuts', label: 'Peanuts', emoji: '🥜' },
  { id: 'gluten', label: 'Gluten', emoji: '🌾' },
  { id: 'eggs', label: 'Eggs', emoji: '🥚' },
  { id: 'soy', label: 'Soy', emoji: '🫘' },
  { id: 'sesame', label: 'Sesame', emoji: '🌱' },
  { id: 'shellfish', label: 'Shellfish', emoji: '🦐' },
];

interface AllergenSelectorProps {
  selected: string[];
  onChange: (allergens: string[]) => void;
}

export default function AllergenSelector({ selected, onChange }: AllergenSelectorProps) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter(a => a !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="space-y-2">
      <label className="font-display text-sm text-brand-dark">
        ALLERGIES (we'll skip these in swaps)
      </label>
      <div className="flex flex-wrap gap-2">
        {ALLERGENS.map((allergen) => (
          <motion.button
            key={allergen.id}
            type="button"
            onClick={() => toggle(allergen.id)}
            className={`
              px-3 py-1.5 rounded-full text-sm font-comic
              border-2 transition-all
              ${selected.includes(allergen.id)
                ? 'bg-brand-orange/20 border-brand-orange text-brand-dark'
                : 'bg-white border-brand-subtle text-brand-mid hover:border-brand-blue'
              }
            `}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {allergen.emoji} {allergen.label}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
```

---

#### New File: `frontend/src/hooks/usePreferences.ts`

```typescript
'use client';

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'snackswap_prefs';

interface Preferences {
  age: number;
  allergens: string[];
}

const DEFAULT_PREFS: Preferences = {
  age: 12,  // Default to tween
  allergens: [],
};

export function usePreferences() {
  const [age, setAge] = useState(DEFAULT_PREFS.age);
  const [allergens, setAllergens] = useState<string[]>(DEFAULT_PREFS.allergens);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const prefs = JSON.parse(stored) as Preferences;
        setAge(prefs.age);
        setAllergens(prefs.allergens);
      }
    } catch {
      // Ignore parse errors, use defaults
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ age, allergens }));
    }
  }, [age, allergens, isLoaded]);

  return {
    age,
    setAge,
    allergens,
    setAllergens,
    isLoaded,
  };
}
```

---

#### File: `frontend/src/app/page.tsx`

**Changes:**

1. Import new components and hook
2. Replace local age state with preferences hook
3. Add AllergenSelector to UI
4. Pass allergens to API calls

```typescript
// Add imports
import AllergenSelector from '@/components/AllergenSelector';
import { usePreferences } from '@/hooks/usePreferences';

// In Home component, replace:
// const [age, setAge] = useState(7);

// With:
const { age, setAge, allergens, setAllergens, isLoaded } = usePreferences();

// Update score API call (around line 100-107):
// Change: allergies: []
// To: allergies: allergens

// Add AllergenSelector in JSX (below AgeSelector):
<AllergenSelector selected={allergens} onChange={setAllergens} />
```

---

### 5.3 Qdrant Changes

#### Update Payload Indexes

Add/update indexes for new age bands in `data/create_indexes.py`:

```python
# Ensure age_band index supports new values
# Values: "9-12", "13-17"
```

#### Re-seed Required

After all seed data changes:
```bash
cd backend
source .venv/bin/activate
python -m data.seeds.seed_data  # Or ./seed_data.sh
```

---

## Part 6: Visual/Art Direction

### 6.1 Chompy Character Sheet

For image generation prompts (Nano-Banana/Gemini):

```
CHOMPY - Teen Mascot Character Sheet

BASE DESCRIPTION:
A cartoon molar tooth character with attitude. Off-white color (realistic tooth shade),
slightly chipped corner suggesting experience. Small rectangular black sunglasses.
Tiny crossed arms or expressive hand gestures. One eyebrow always slightly raised
in skepticism. Compact, cute but edgy design.

EXPRESSIONS TO SUPPORT:
1. Skeptical (default) - Eyebrow raised, slight frown, arms crossed
2. Shocked - Sunglasses tilted, eyes wide, mouth open
3. Roasting - Smirking, finger pointing, confident pose
4. Dramatic - Over-the-top shocked, hands on face
5. Respect - Subtle smile, small nod, maybe fist bump pose
6. Disappointed - Head shake, looking down, sighing

STYLE NOTES:
- Clean cartoon style, works at small sizes
- Bold outlines for clarity
- Expressions should be readable in comic panels
- Should feel like a character teens would find cool, not cringe
- NOT too cute/kawaii - has edge
- NOT scary/horror - still friendly underneath
```

### 6.2 Comic Panel Style (Teen Mode)

```
TEEN COMIC STYLE:

Layout: 1x4 vertical strip (optimized for phone screens/stories)

Color Palette:
- Background: Gradient purples, dark teals, neon accents
- Text: White with subtle glow/shadow
- Chompy: Off-white tooth, black sunglasses, subtle highlights

Typography:
- Dialogue: Bold sans-serif, ALL CAPS for emphasis
- Sound effects: Graffiti/street art style
- Meme text: Impact font or similar (ironic usage)

Panel Borders:
- Slightly rough/hand-drawn edges
- Can break borders for dramatic effect
- Neon glow accents on key panels

Vibe Reference:
- Adult Swim bumpers
- TikTok/Instagram story aesthetics
- Meme formats but elevated
- NOT: Corporate, sterile, "educational material"
```

---

## Part 7: Example Scripts

### 7.1 Teen Roast Example: Gummy Bears (THE ROAST ARC)

```json
{
  "title": "Roast My Snack: Gummy Bears",
  "mode": "roast",
  "panels": [
    {
      "panel_number": 1,
      "scene": "Gummy Bear enters looking smug, Dr. Drip watching from side with skeptical look",
      "character": "dr_drip",
      "snack_dialogue": "I'm literally the main character of snack time.",
      "drip_dialogue": "*holds up X sign*",
      "emotion": "flex_setup"
    },
    {
      "panel_number": 2,
      "scene": "Dr. Drip steps forward pointing, Gummy Bear starts sweating",
      "character": "dr_drip",
      "dialogue": "Bro, you're literally just sticky sugar glue. 50g of sugar? The bacteria in your mouth are throwing a PARTY rn.",
      "fact_citation": "sugar_bacteria_01",
      "emotion": "expose"
    },
    {
      "panel_number": 3,
      "scene": "Gummy Bear crying/melting, bacteria visible partying on tooth in background",
      "character": "dr_drip",
      "dialogue": "You're stuck in teeth for 6 hours? Stage 5 clinger vibes. Skill issue fr.",
      "snack_dialogue": "I just wanted to be loved!",
      "emotion": "ratio"
    },
    {
      "panel_number": 4,
      "scene": "Dr. Drip posing with buff Apple character, Gummy Bear defeated in corner",
      "character": "dr_drip",
      "dialogue": "Swap to Apple Slices. High fiber, cleans teeth while you eat. No cap.",
      "verdict_overlay": "COOKED",
      "emotion": "vibe_check"
    }
  ]
}
```

### 7.2 Teen Celebrate Example: Apple (THE W ARC)

```json
{
  "title": "Roast My Snack: Apple",
  "mode": "based",
  "panels": [
    {
      "panel_number": 1,
      "scene": "Apple walks in with sunglasses and buff arms, Dr. Drip intrigued",
      "character": "dr_drip",
      "dialogue": "Hold up... let him cook.",
      "emotion": "entrance"
    },
    {
      "panel_number": 2,
      "scene": "Apple revealing stats floating around it like RPG character, Dr. Drip impressed",
      "character": "dr_drip",
      "dialogue": "No cavity creeps? High fiber? That's actually OP.",
      "apple_stats": "+5 Fiber, +3 Crunch, -100% Cavity Risk",
      "fact_citation": "apple_clean_01",
      "emotion": "stats"
    },
    {
      "panel_number": 3,
      "scene": "Dr. Drip and Apple doing elaborate handshake/bro-hug",
      "character": "dr_drip",
      "dialogue": "Cleans teeth while you eat? Actually cracked strategy. Sheesh!",
      "emotion": "glaze"
    },
    {
      "panel_number": 4,
      "scene": "Dr. Drip placing gold crown on Apple, coronation ceremony vibes",
      "character": "dr_drip",
      "dialogue": "Real recognizes real.",
      "verdict_overlay": "GOATED",
      "emotion": "crown"
    }
  ]
}
```

### 7.3 Tween Example (Spicy Mode - Age 9-12)

```json
{
  "title": "Roast My Snack: Sour Patch Kids",
  "mode": "roast_spicy",
  "panels": [
    {
      "panel_number": 1,
      "character": "dr_drip",
      "dialogue": "Hmm, let's see what we got here...",
      "emotion": "curious"
    },
    {
      "panel_number": 2,
      "character": "dr_drip",
      "dialogue": "That's kinda sus for your teeth. Sour candy = acid attack!",
      "emotion": "concerned"
    },
    {
      "panel_number": 3,
      "character": "dr_drip",
      "dialogue": "Your enamel is NOT having a good time rn.",
      "emotion": "dramatic"
    },
    {
      "panel_number": 4,
      "character": "dr_drip",
      "dialogue": "Maybe try some cheese instead? Way better vibes.",
      "verdict_overlay": "Not great",
      "emotion": "suggesting"
    }
  ]
}
```

---

## Part 8: Implementation Checklist

### Phase 1: Backend Core (Do First)
- [ ] Update `api.py` age validation (9-17)
- [ ] Update `scoring_service.py` age bands (9-12, 13-17)
- [ ] Add teen prompt methods to `gemini_service.py`
- [ ] Update script composition routing based on age

### Phase 2: Content & Data
- [ ] Add teen facts to `seed_data.py`
- [ ] Update existing fact age_bands
- [ ] Re-seed Qdrant with new data
- [ ] Test fact retrieval for both age bands

### Phase 3: Frontend
- [ ] Update `AgeSelector.tsx` (9-17, 2 groups)
- [ ] Create `AllergenSelector.tsx`
- [ ] Create `usePreferences.ts` hook
- [ ] Integrate into `page.tsx`
- [ ] Test localStorage persistence

### Phase 4: Polish & Test
- [ ] Generate test comics for both age bands
- [ ] Verify Chompy character appears correctly for 13-17
- [ ] Verify Captain Sparkle for 9-12
- [ ] Test allergen filtering in swaps
- [ ] End-to-end flow testing

---

## Part 9: Success Metrics

**Would a teen actually share this?**
- [ ] Comics are genuinely funny (not cringe)
- [ ] Dialogue sounds natural for gen-z
- [ ] Visual style is cool, not corporate
- [ ] Meme references land
- [ ] Format works for Instagram/TikTok stories

**Does it still educate?**
- [ ] Dental facts are accurate
- [ ] Facts are integrated into humor (not tacked on)
- [ ] Healthy snacks are celebrated
- [ ] Swaps are suggested naturally

---

## Appendix: Meme Reference Guide

Keep updated as trends evolve:

| Meme/Phrase | Usage | Example |
|-------------|-------|---------|
| POV: | Perspective setup | "POV: Your enamel watching you eat this" |
| It's giving | Describes vibe | "It's giving cavity energy" |
| No cap / Fr fr | Emphasis (serious) | "That sugar content is wild, no cap" |
| Bestie | Addressing user | "Bestie, we need to talk" |
| Ratio | Bad outcome | "Your tooth to cavity ratio after this" |
| W / L | Win/Loss | "W choice" or "That's an L for your teeth" |
| Main character | Compliment | "Main character energy with that apple" |
| NPC behavior | Mindless action | "NPC snacking right here" |
| Caught in 4K | Caught doing something | "Caught your bacteria in 4K celebrating" |
| Speedrun | Doing fast | "Cavity speedrun any%" |
| The vibes are off | Something wrong | "The vibes in your mouth are off rn" |
