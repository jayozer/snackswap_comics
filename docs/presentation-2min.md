# Roast My Snack (SnackSwap Comics) — 2 Minute Presentation

> **Total time**: 2:00  
> **Format**: 1 live demo + 1 instant “reveal” tab  
> **Goal**: Entertaining demo that clearly hits the judging rubric (creative, search/RAG, guardrails, UX, real-world fit, innovation)

---

## Pre-Demo Setup (do this before you walk up)

- Open 3 browser tabs:
  - **Tab A (Live)**: `http://localhost:3000` on the idle screen
  - **Tab B (Celebrate reveal)**: Pre-generated **CELEBRATE** result (apple) sitting on **Results** or **Comic**
  - **Tab C (Roast backup)**: Pre-generated **EDUCATE** result (gummy bears) sitting on **Results**
- Desktop-ready images (drag & drop):
  - `gummy_bears.jpg` (roast demo)
  - `apple.jpg` (celebrate demo)
- Tab A controls set for the demo:
  - Age at **11** (Spicy) so you can quickly slide to **15** (Savage)
  - Tap **Peanuts** in allergies (so you can mention swap filtering)

---

## Script + On-Screen Actions (time-coded)

### 0:00–0:12 — Hook (Problem + Thesis)
**On screen**: Logo + DR. HAWLEY + speech bubble (idle screen)  
**Say**
> “This is **Roast My Snack**. We turn a snack photo into a 4‑panel comic where **Dr. Hawley**—a Gen‑Z molar—judges the snack’s *aesthetic threat level* to your smile.  
> Teens don’t respond to ‘cavities’… they respond to **looking good**. We use **vanity as a force for good**.”

### 0:12–0:22 — Age-Adaptive Personality (Innovation + Guardrails)
**On screen**: Slide age from **11 → 15** and point to the mode label under the speech bubble  
**Say**
> “Same character, different intensity: **Spicy** for tweens, **Savage** for teens—developmentally appropriate.  
> And the rule is: **we roast the snack, never the kid**.”

### 0:22–0:27 — Personalization (Real-World Fit)
**On screen**: Click **Peanuts 🥜** in the allergen chips  
**Say**
> “Quick personalization: allergies. Any swap suggestions we recommend will avoid these.”

### 0:27–1:05 — Live Roast Demo (Creative + UX + Search/RAG)
**On screen**: Drag `gummy_bears.jpg` into the upload zone; point at the 5-step progress overlay as it advances  
**Say (match the on-screen step labels)**
> “While it runs, here’s the pipeline:  
> **Scanning snack**: Gemini Vision detects and **groups** what’s in the photo.  
> **Checking aesthetic threat**: we do **semantic search in Qdrant Cloud** to match snacks + pull **clinic‑approved facts** and better swaps, then score risk from **sugar, acidity, stickiness, residue**.  
> **Writing vanity roast**: Gemini Pro writes the script with a **24k thinking budget**, then we run it through guardrails.  
> **Creating glow up comic**: Nano‑Banana generates the art, and we add our own **emotion speech bubbles** + export formats.”

### 1:05–1:20 — Results (Search/Similarity + Behavior Change)
**On screen**: Results panel (risk score + facts + swap ideas)  
**Say**
> “Here’s the **risk score**, the **tooth facts** we retrieved, and **taste‑matched swap ideas**—filtered to avoid peanuts.”

### 1:20–1:40 — Comic + Export (Creative Polish + UX)
**On screen**: Click **SEE MY COMIC!**, point to bubble shapes, toggle **Reel / Story**, click **DOWNLOAD COMIC**  
**Say**
> “And here’s the comic: 4 panels, with **emotion‑matched bubbles**.  
> One tap export in **Reel** or **Story** format—built to be shared.”

### 1:40–1:52 — Celebrate Reveal (Second Demo, No Waiting)
**On screen**: Switch to **Tab B** (apple) and point to the green CELEBRATE header / meter  
**Say**
> “It’s not all roasting—when a snack is tooth‑friendly, we flip to **Celebrate mode**. Same pipeline, totally different tone: positive reinforcement and glow‑up energy.”

### 1:52–2:00 — Close (Real-World Fit + Brand)
**On screen**: Point to **Poppy Kids** logo/link in the footer  
**Say**
> “We built this with **Poppy Kids Pediatric Dentistry**. Roast My Snack makes dental education something kids actually want to share—because it’s about the **glow‑up**.”

---

## Rubric Coverage (what you hit, without sounding like a checklist)

- **Creative Quality**: DR. HAWLEY mascot + comics + emotion bubbles + polish
- **Search & Similarity**: Qdrant semantic search + clinic-approved RAG facts + swap retrieval
- **Guardrails**: age-banding + “roast snack, not kid” + profanity filtering + audit logs (mention if asked)
- **UX & Tradeoffs**: 5-step progress, fast vision vs high-quality writing, export formats
- **Real-World Fit**: Poppy Kids partnership + share-ready outputs + allergy-aware swaps
- **Innovation**: vanity framing + age-adaptive personality + multi-stage pipeline

---

## Backup Lines (if something goes wrong)

- **If the live run is slow**: “While this finishes, here’s a pre-generated example.” → jump to **Tab C**.
- **If the image gets ‘unknown’**: “We fail gracefully: we switch to general dental glow‑up tips.” (Unknown mode.)
- **If asked about stack (10 seconds)**: “FastAPI + Next.js, Gemini Flash for vision, Gemini Pro for scripts with thinking, Gemini image for comics, Qdrant Cloud for semantic search, plus custom guardrails.”

---

## Key Phrases (memorize)

1. “**Vanity as a force for good.**”
2. “**Same character, developmentally appropriate intensity.**”
3. “**Roast the snack, never the kid.**”

---

## Rehearsal Checklist (5 minutes before you present)

- Confirm backend + frontend are running (`localhost:8000` + `localhost:3000`).
- Run the two “setup” generations and park tabs:
  - Tab B: apple (CELEBRATE) on Results/Comic
  - Tab C: gummy bears (EDUCATE) on Results
- Do one dry run with a timer and hard cut anything that pushes you past 2:00.
- Practice the two tab switches (Tab A → Tab B) so it’s instant and confident.
- If swaps don’t appear for your roast snack, delete the one line about swaps and just point at facts + risk score.

---

## If Judges Ask “Why This Works?”

- Teens care about appearance; this makes dental health feel immediate (“white teeth / yellow teeth”), not abstract (“cavities later”).
- The output is shareable (Reel/Story), so education travels socially instead of being a lecture.

**The Problem with Traditional Messaging:**
- "Brush or you'll get cavities" → Abstract future harm, low urgency
- "Sugar rots your teeth" → Sounds like a lecture, triggers defiance

**The SnackSwap Approach:**
- "That snack is gonna turn your smile yellow" → Immediate, visual, vanity-driven
- "Your teeth are losing followers" → Social currency language
- Humor creates positive association with dental awareness

### Why Positivity Matters

**Shame-Free Education:**
- Studies show shame-based health messaging backfires for adolescents
- Creates anxiety and avoidance, not behavior change
- DR. HAWLEY roasts the SNACK, celebrates the PERSON

**Lifelong Habit Formation:**
- Positive associations with dental health create lasting habits
- Kids who enjoy learning about oral health visit dentists more regularly
- Shareable content creates peer-to-peer education

---

## Final Checklist Before Presenting

- [ ] Browser at localhost:3000
- [ ] Age slider at 10
- [ ] Gummy bear photo on desktop
- [ ] Apple photo as backup
- [ ] Screenshot of completed comic (backup)
- [ ] Timer visible or memorized cues
- [ ] Deep breath, you've got this
