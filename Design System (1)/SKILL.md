---
name: floras-design-system
description: Master entry point for the Floras AI-driven design system. Read this file first before generating any artifact. It defines what this system is, how it is structured, what rules govern all outputs, and which skill file to load for each artifact type.
---

# Floras Design System
**The AI-driven system for producing consistent, on-brand Floras materials at scale.**

---

## What This System Is

This is not a visual component library. It is a **governed content production system** — a set of rules, knowledge, and reusable skill files that enable an AI agent to produce consistent, recognisable Floras sales and marketing materials from a short brief.

The core principle, borrowed from Floras' own product logic: every output should make it easy for the recipient to understand the value and carry it forward. Don't just make the material impressive. Make it easy to act on.

---

## Folder Structure

```
floras-design-system/
├── SKILL.md                  ← You are here. Read this first, always.
├── style-guide.md            ← Source of truth for all brand expression
└── skills/
    ├── presentation.md       ← Rules for generating sales presentations
    ├── email.md              ← Rules for generating sales emails
    ├── one-pager.md          ← Rules for generating one-pagers and proposals
    └── social-post.md        ← Rules for generating social content
```

Generated outputs are drafts until reviewed by a human. They do not become source of truth unless explicitly approved.

---

## How To Use This System

Every generation task follows this exact order. Do not skip steps.

### Step 1 — Read this file (SKILL.md)
You are doing this now. Understand the system, the rules, and the structure before proceeding.

### Step 2 — Read `style-guide.md`
This is the single source of truth for how Floras looks, sounds, and feels. It must be loaded before any artifact is generated. It defines:
- Brand identity and positioning
- Color tokens and usage rules
- Typography and type scale
- Logo and brand mark usage
- Tone of voice, approved language, and banned phrases
- Layout principles and component patterns
- The Floras currency rules

**Never generate an artifact without reading `style-guide.md` first.**

### Step 3 — Read the relevant skill file
Match the requested artifact type to its skill file:

| Artifact requested | Skill file to load |
|--------------------|--------------------|
| Sales deck, presentation, slides | `skills/presentation.md` |
| Email, outreach, follow-up | `skills/email.md` |
| One-pager, proposal, leave-behind | `skills/one-pager.md` |
| Social post, LinkedIn, caption | `skills/social-post.md` |

Each skill file defines the required inputs, output structure, and format-specific rules for that artifact type.

### Step 4 — Collect the brief
Before generating, confirm you have the minimum required inputs for that artifact type. These are defined in each skill file. If inputs are missing, ask for them or mark them `[NEEDS INPUT]` — never invent them.

### Step 5 — Generate the artifact
Produce the output according to the style guide and the skill file. Apply brand rules consistently. Do not deviate from approved language or introduce visual elements not defined in the style guide.

### Step 6 — Run a consistency check
After generating, review the output against these five questions before delivering:

1. Does it sound like Floras? (tone, vocabulary, sentence structure)
2. Does it use only approved language and avoid banned phrases?
3. Does every claim have a basis — either a sourced statistic or a concrete mechanism? If not, mark it `[NEEDS PROOF]`.
4. Is there a clear next action for the reader?
5. Could the recipient explain the value in two sentences after reading this?

If any answer is no, revise before delivering.

**The consistency check must be shown in the output.** Do not deliver any artifact without displaying the check results explicitly — list each question and whether it passed or failed. A check run silently is not a check.

---

## Core Rules

These apply to every artifact this system produces, regardless of type.

**1. Style guide is law.**
All colors, typography, tone, and language decisions are governed by `style-guide.md`. When in doubt, return to it.

**2. Never invent.**
Do not invent metrics, case studies, client names, product features, or integrations. If a fact cannot be confirmed, mark it `[NEEDS PROOF]`. If an input is missing, mark it `[NEEDS INPUT]`.

**3. Floras is not a carbon offset marketplace.**
Every artifact must reflect what Floras actually is: a supply chain decarbonization engine with a currency at its center. Never describe it as an offset marketplace, a CSR reporting tool, or a generic sustainability platform.

**4. The currency is called Floras.**
Not points, not tokens, not credits. The currency is Floras (capital F). "Floras flow to your wallet" is correct. "Points are added to your account" is not.

**5. Outputs are drafts.**
Every generated artifact is a draft until a human reviews and approves it. Do not treat generated content as source of truth.

**6. Specificity over vagueness.**
Concrete mechanisms beat general claims every time. "Floras turns every transaction into measurable CO₂ reduction" is better than "Floras helps your company become more sustainable." Always prefer the specific.

**7. One clear next action per artifact.**
Every artifact must close with a single, specific next action for the reader. Not "learn more." Something like "Contact us to map your supplier network" or "Allocate your first Floras to a verified project."

**8. Make it carryable.**
The reader should be able to explain the value of Floras in two sentences after reading any artifact this system produces. If they can't, the output is not ready.

**9. Always declare a font fallback stack.**
Never rely solely on Google Fonts. Every artifact must declare `font-family: 'Rubik', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` so the output renders correctly even when the external font fails to load. Wordmark uses `font-weight: 400` minimum — never 300 in HTML artifacts.

**10. Never subscript the number in "Scope 3."**
"Scope 3" is a reporting category, not a chemical formula. Always write it as plain text: "Scope 3." Only CO₂ uses subscript notation.

---

## Audience Reference

Floras has two primary audiences. Every artifact must be written for one of them — never both at once.

### Enterprise buyers
Procurement heads, sustainability directors, supply chain managers, CFOs at mid-to-large companies with complex supplier networks. They care about: compliance, reporting, cost efficiency, measurability, and not adding operational burden. They are skeptical of greenwashing. Speak to mechanisms and outcomes, not values.

### Suppliers
Sales teams, account managers, business development leads at companies selling goods or services to enterprises. They care about: winning and keeping enterprise contracts, differentiating in competitive bids, deepening client relationships. Speak to commercial advantage.

---

## What Good Output Looks Like

A well-generated Floras artifact:
- Opens with the problem or the mechanism — never a company introduction
- Uses short, declarative sentences with active verbs
- Cites at least one concrete figure or mechanism per section
- Never uses the banned phrases listed in `style-guide.md`
- Closes with a single specific next action
- Could be read in full by a procurement director in under 2 minutes and leave them knowing exactly what Floras does and what to do next

---

## What To Do When You Are Unsure

- Unsure about brand rules → re-read `style-guide.md`
- Unsure about output structure → re-read the relevant skill file
- Missing a fact → mark `[NEEDS INPUT]` and ask
- Claim feels unverifiable → mark `[NEEDS PROOF]` and rewrite as a mechanism
- Output doesn't feel like Floras → run the five-question consistency check in Step 6
