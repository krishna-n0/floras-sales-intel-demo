# Floras Presentation Skill
**Format:** Sales presentation / slide deck
**Reads after:** `SKILL.md` → `style-guide.md` → this file

---

## Purpose

This file governs the generation of Floras sales presentations. These are slide decks used by Gonzalo, Jeroen, or the Floras team to pitch to enterprise buyers or suppliers. The goal of every presentation is not to impress — it is to leave the audience with a clear understanding of what Floras does, why it matters to them specifically, and one concrete next step.

A well-built Floras presentation feels like a calm, well-reasoned argument. Not a pitch. Not a product demo. A structured case.

---

## Required Inputs

Before generating any slide deck, confirm all of the following. If any are missing, mark `[NEEDS INPUT]` in the relevant slide — never invent them.

| Input | Why it's needed |
|-------|----------------|
| **Audience type** | Enterprise buyer or supplier? This determines framing, terminology, and the value proposition emphasized. |
| **Company name** | Personalization on the title slide and throughout. |
| **Industry / sector** | Needed to make the supply chain context specific and credible. |
| **Known pain point or goal** | What does this audience care about most? Compliance? Cost? Contract differentiation? |
| **Presenter name** | For the closing / contact slide. |
| **Any specific projects or stats to feature** | If Floras has a verified project or stat relevant to this audience, include it. Otherwise mark `[NEEDS INPUT]`. |

---

## Slide Structure

Every Floras presentation follows this sequence. Slide count is a guide, not a hard limit — slides can be split if content is dense, but the order and section presence are mandatory.

### Title Slide
- **FLORAS** wordmark, centered or left-aligned
- Tagline: "Reward The Earth"
- Deck title: e.g. "Supply Chain Decarbonization for [Company Name]" — always specific, never generic
- Presenter name and date
- **Background:** `--color-forest` or wallet card gradient (`--color-wallet-start` → `--color-wallet-end`, 135deg)
- **Text:** white throughout
- **No subheadings, no bullet points. Clean.**

### Problem Slide
- Open with the problem, not Floras. The audience needs to see themselves in it before they care about the solution.
- One headline. Max 3 sentences of body copy.
- Include one sourced statistic if available. Example: "Supply chains account for over 80% of enterprise greenhouse gas emissions." If no sourced stat is available, mark `[NEEDS PROOF]` and use a mechanism statement instead.
- **Background:** `--color-bg`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Body:** `--text-body`, `--color-text`

### Mechanism Slide
- Explain how Floras works in plain language. One clear mechanism, not a feature list.
- Suggested flow: Transaction occurs → Floras currency issued to buyer's wallet → Buyer allocates Floras to a verified climate project → Enterprise receives a verified impact certificate.
- Can use a simple 3–4 step flow diagram. No illustrations. Simple line connectors between labeled boxes are acceptable.
- Do not introduce new terminology not defined in `style-guide.md`.
- **Split permitted:** If the flow diagram and explanatory copy feel crowded on one slide, this may be split into two slides.
- **Background:** `--color-surface`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Step labels:** ALL CAPS, `--text-label`, `--color-brand-text`
- **Step descriptions:** `--text-body`, `--color-text`

### Value Proposition Slide (Audience-Specific)
This slide changes depending on audience. Generate the correct version — never both.

**If enterprise buyer:**
- Headline: lead with compliance, measurability, or cost efficiency — whichever matches the known pain point
- Three value points maximum. Each is one sentence: mechanism + outcome.
- Example: "Every transaction generates Floras — no additional budget required."
- Do not use: "going green," "eco-friendly," "carbon footprint," or any banned phrase from the style guide.

**If supplier:**
- Headline: lead with commercial advantage — winning contracts, differentiating in bids
- Three value points maximum. Each one sentence.
- Example: "Suppliers enrolled in Floras become preferred partners for enterprises with decarbonization mandates."

**Both versions:**
- **Background:** `--color-bg`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Body:** `--text-body`, `--color-text`
- Section label must be generic — use "Why It Matters" for enterprise buyer and "Your Advantage" for supplier. Never use `[NEEDS INPUT]` in a structural label.

### Flow Slide — How It Works in Practice
- A concrete, step-by-step scenario. Use a real or plausible industry example relevant to the audience's sector.
- Format: numbered steps, not bullets. 4–6 steps max.
- Each step is one sentence. Active voice. Subject + verb + outcome.
- If a real case study exists, use it and name the partner. If not, construct a plausible scenario and mark it `[ILLUSTRATIVE EXAMPLE — NOT A CASE STUDY]`.
- **Split permitted:** If the scenario runs to more than 6 steps or the content feels dense, this may be split into two slides.
- **Background:** `--color-bg`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Step numbers:** `--color-leaf`, weight 700
- **Step text:** `--text-body`, `--color-text`

### Impact & Proof Slide
- Lead with the most credible number or outcome available.
- If a verified project rate is available: display it as a stat card — `X kg CO₂e / Flora` in `--text-stat`, `--color-text`, with the label "IMPACT RATE" in `--text-label`, `--color-text-muted`.
- Include partner logos (Berkeley SkyDeck, Puro Earth, Aclymate, Anew) as social proof — grayscale, 24–48px height, equal spacing, light background only.
- If no hard impact numbers are available, mark `[NEEDS PROOF]` and replace with a mechanism: "Every Flora allocated funds a certified project — traceability guaranteed."
- Never add "independently verified" or "auditable" to the impact rate description unless explicitly sourced. If unverified, mark `[NEEDS PROOF]` and remove the claim entirely.
- **Split permitted:** If both a stat callout and partner logos are present, this may be split into two slides.
- **Background:** `--color-surface`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Body:** `--text-body`, `--color-text`
- **Stat values:** `--text-stat`, `--color-text` (or white if on `--color-balance-bg`)

### Why Now Slide
- One clear reason the timing is right. Regulatory pressure, procurement mandates, competitor movement — whatever is most relevant to this audience.
- One headline. Two sentences max.
- Do not manufacture urgency. If a real regulatory or market driver exists, name it specifically. If not, mark `[NEEDS INPUT]`.
- **Background:** `--color-bg`
- **Headline:** `--text-h1`, `--color-brand-text`
- **Body:** `--text-body`, `--color-text`

### Closing Slide — The Ask / Next Step
- Single, specific next action. Not "learn more." Not "get in touch."
- Examples: "Map your supplier network with us — book a 30-minute call." / "Allocate your first Floras to a verified project this quarter."
- Contact details for the presenter.
- **Background:** `--color-forest` or gradient — mirror the title slide.
- **Text:** white throughout
- Logo bottom-left: icon only, no text wordmark. `<img src="light-logo.png" alt="" style="height:20px; display:block;">`
- The CTA text, contact line, and tagline must be vertically and horizontally centered on the slide. Do not use `margin-top: auto` on the closing CTA — it pushes content to the bottom instead of centering it.

---

## Slide Design Rules

### Layout
- One idea per slide. If a slide needs two ideas, split it.
- Max one headline + one supporting visual or max 3–4 body sentences per slide. Never both a visual and dense copy.
- All text left-aligned unless the slide is a title or closing slide (centered acceptable there).
- No decorative borders, gradients on text, or drop shadows on type.

### Color Usage in Slides
- **Dark slides** (title, closing): wallet gradient (`--color-wallet-start` → `--color-wallet-end` at 135deg) background, white text. The gradient runs from warm yellow-olive to dark forest green.
- **Slide background sequence (mandatory):** Title: dark gradient → Problem: `--color-bg` → Mechanism: `--color-surface` → Value Proposition: `--color-bg` → Flow: `--color-surface` → Impact & Proof: `--color-bg` → Why Now: `--color-surface` → Closing: dark gradient
- **Light slides** (body content): follow the mandatory sequence above. Never use the same background for two consecutive slides.
- **Emphasis:** use `--color-brand-text` for headings and key terms on light slides. Never use `--color-leaf` for body text.
- **Flow node backgrounds:** `--color-surface-sage` background with `--color-brand-text` text and a `--color-leaf` left border (4px). Section dividers between section label and headline use `--color-leaf` (2px line, 40px wide).
- **Stat callouts:** `--color-balance-bg` background, white text, Rubik 800 — use sparingly, one per deck maximum unless the deck is data-heavy.
- **Step numbers and list markers:** `--color-leaf`, weight 700.

### Typography in Slides
- **Slide headline:** `--text-h1` (2.2rem, weight 700), `--color-brand-text` on light / white on dark
- **Section label above headline:** ALL CAPS, `--text-label`, letter-spacing 0.12em, `--color-text-muted` on light / `rgba(255,255,255,0.6)` on dark
- **Body copy:** `--text-body` (1rem, weight 400), `--color-text` — never smaller than 0.875rem
- **Stat values:** `--text-stat` (2.4rem, weight 800)
- **Step numbers / list markers:** `--color-leaf`, weight 700 — the only place `--color-leaf` appears in slide text
- **Wordmark font stack:** always declare `font-family: 'Rubik', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` to ensure fallback rendering. Wordmark uses `font-weight: 400` minimum — never 300 in HTML artifacts.

### Logo
- Every slide: Floras logo in the top-left corner (or bottom-left on closing slide)
- Always pair the icon with the FLORAS wordmark in a flex row — never use the icon alone
- Light slides:
  `<div style="display:flex; align-items:center; gap:8px;"><img src="dark-logo.png" alt="" style="height:20px; display:block;"><span style="font-size:0.95rem; font-weight:300; letter-spacing:0.15em; color:var(--color-text);">FLORAS</span></div>`
- Dark slides:
  `<div style="display:flex; align-items:center; gap:8px;"><img src="light-logo.png" alt="" style="height:20px; display:block;"><span style="font-size:0.95rem; font-weight:300; letter-spacing:0.15em; color:#fff;">FLORAS</span></div>`
- Never resize, stretch, or recolor outside these two treatments

### What Not to Include
- No clip art, stock illustrations, or decorative icons not defined in the style guide
- No transition animations specified in this file — those are a presenter decision
- No tables with more than 4 columns — if data is that complex, summarize it
- No more than one stat callout card per slide

---

## Tone Notes for Presentations

Presentations are the highest-stakes Floras artifact — they are delivered live, in front of decision-makers. The tone must be particularly disciplined.

- **Open on the problem, not on Floras.** The audience will disengage if the first slide is a company introduction.
- **Never oversell.** One strong, verified claim beats three vague ones. If a claim can't be backed up, cut it or mark `[NEEDS PROOF]`.
- **Avoid the word "solution."** Floras is a mechanism, not a solution. Say what it does.
- **Every slide should be passable in 20 seconds.** If the presenter has to read from the slide, the slide has too much copy.
- **The closing slide is an action, not a thank you.** End with what you want the audience to do next — not "Thank you for your time."

---

## Consistency Check (Presentation-Specific)

Run these in addition to the five questions in `SKILL.md` Step 6:

1. Does the Problem slide open on the audience's problem — not on Floras?
2. Is every claim on the Impact & Proof slide either sourced or marked `[NEEDS PROOF]`?
3. Is the Value Proposition slide written for the correct audience type (buyer vs. supplier)?
4. Does the closing slide end with a single specific action — not a generic CTA?
5. Is the FLORAS wordmark present on every slide in the correct color for that background?
