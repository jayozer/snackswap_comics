# Roast My Snack — Presentation Script

> **Total time**: ~3-4 minutes (adjustable)
> **Format**: Storytelling + 2 live demos (gummies + fruit plate)
> **Vibe**: Entertaining, personal, technically impressive

---

## Pre-Demo Setup

**Browser Tabs:**
- **Tab A (Live)**: `http://localhost:3000` - fresh start
- **Tab B (Backup Roast)**: Pre-generated gummy bears result
- **Tab C (Backup Celebrate)**: Pre-generated fruit plate result

**Desktop Ready:**
- `gummy_bears.jpg` (roast demo)
- `fruit_plate.jpg` (celebrate demo - the one with watermelon, grapes, strawberries)

**Settings:**
- Age slider at **14** (Savage mode)
- One allergen selected (e.g., Peanuts)

---

## The Script (TIGHT 2-MINUTE VERSION)

### 🎬 HOOK + INTRO (0:00-0:25)

**[App on screen with DR. HAWLEY]**

> "Tell a kid 'brush or you'll get cavities'... they don't care. But tell them their snack is gonna turn their smile yellow? Now you've got their attention.
>
> This is **Roast My Snack** — snap a photo of any snack, and **Dr. Hawley** — a Gen-Z molar with no chill — roasts its 'aesthetic threat level' to your smile.
>
> **Vanity as a force for good.**
>
> Quick origin story: Dr. Hawley is named after my golden retriever puppy, who's named after the Hawley retainer. Tooth mascot, named after a dog, named after dental equipment. **Turtles all the way down.**"

---

### 🔥 PERSONALITY + TONE (0:25-0:45)

**[Show age toggle]**

> "Two modes: **Spicy** for tweens — 'sus', 'mid'. **Savage** for teens — 'cooked', 'L + ratio'. Same character, **developmentally appropriate intensity**.
>
> The comedy comes from **30 Adult Swim transcripts** I used to build a roast corpus. Rick and Morty, Smiling Friends energy — not generic AI output.
>
> And we **roast the snack, never the kid**."

---

### 🎯 LIVE DEMO — Gummy Bears (0:45-1:30)

**[Drag gummy_bears.jpg]**

> "Let's roast some gummy bears."

**[While processing — keep it brief]**

> "**Gemini Vision** detects the snack. **Qdrant semantic search** matches it to our database and pulls clinic-approved facts. **Gemini Pro** writes the script through guardrails. **Nano-Banana** generates the art — but here's the thing:
>
> AI-generated text looks terrible. So Nano-Banana makes the art, **PIL draws clean bubbles**, **Freepik adds the background**. Best of both worlds."

**[Results appear]**

> "**74 risk score**. Sugar, stickiness — the works. Dr. Hawley does not hold back."

---

### 🍎 CELEBRATE MODE + WIFE SHOUTOUT (1:30-2:00)

**[Drag fruit_plate.jpg OR show pre-loaded Tab]**

> "But it's not all roasting. Healthy snack? **Celebrate mode**."

**[While processing / showing result]**

> "Quick shoutout to my wife **Dr. Andrea at Poppy Kids Pediatric Dentistry** — she reviewed every risk score in our database. Sugar weights, acidity factors — that's **clinic-validated science** behind the roasts.
>
> *'Goated. Actually goated with the sauce.'* — I learned that phrase making this app. Now I say it constantly."

---

### 🏁 CLOSE (2:00-2:10)

> "Portrait for Stories, Reel for TikTok — **shareable dental education**.
>
> **Roast My Snack** — making dental health about the glow up, one roast at a time."

---

## Rubric Coverage Checklist

| Rubric Criteria | How We Hit It |
|-----------------|---------------|
| **Creative Quality** | DR. HAWLEY character, Adult Swim corpus, Freepik backgrounds, vanity roasting concept |
| **Search & Similarity** | Qdrant semantic search, transparent risk scoring, taste-matched swaps, risk_tags filtering |
| **Guardrails** | 50+ blocked terms, teen slang allowlist, audit logs, "roast snack not kid" philosophy |
| **UX & Tradeoffs** | 5-step progress, PIL text overlay (not Nano-Banana), localStorage persistence, export formats |
| **Real-World Fit** | Poppy Kids partnership, clinic-validated scores, shareable social formats |
| **Innovation** | Vanity framing, age-adaptive personality, Adult Swim corpus, smart plate detection |

---

## Key Phrases to Memorize

1. **"Vanity as a force for good."**
2. **"Roast the snack, never the kid."**
3. **"Same character, developmentally appropriate intensity."**
4. **"Adult Swim energy, tuned for dental health."**
5. **"Best of both worlds: AI art + professional backgrounds + pixel-perfect typography."**

---

## Personal Story Beats (Quick Hits)

- 🐕 **"Turtles all the way down"** — puppy → retainer → mascot
- 📺 **"Adult Swim energy"** — 30 transcripts, roast corpus
- 👩‍⚕️ **"Clinic-validated"** — wife reviewed every score
- 🎨 **"Best of both worlds"** — Nano-Banana art + PIL text + Freepik backgrounds

---

## Backup Lines

**If live demo is slow:**
> "While this finishes, let me show you a pre-generated example." → Switch to Tab B/C

**If detection fails:**
> "We fail gracefully — switches to Unknown mode with generic glow-up tips."

**If asked about stack (quick version):**
> "FastAPI + Next.js, Gemini Flash for vision, Gemini Pro for scripts with thinking mode, Nano-Banana for images, Qdrant Cloud for semantic search, PIL for text overlay, and custom guardrails."

**If asked about the corpus:**
> "The roast examples are in `drhawley_roast_corpus.py` — 50+ few-shot examples extracted from Adult Swim dialogue patterns."

---

## Rehearsal Checklist

- [ ] Backend running (`localhost:8000`)
- [ ] Frontend running (`localhost:3000`)
- [ ] Tab B: Gummy bears pre-generated (backup)
- [ ] Tab C: Fruit plate pre-generated (backup)
- [ ] Gummy bears image on desktop
- [ ] Fruit plate image on desktop
- [ ] Age at 14 (Savage mode)
- [ ] One dry run with timer
- [ ] Practice the puppy joke delivery
- [ ] Deep breath — you've got this 🦷✨
