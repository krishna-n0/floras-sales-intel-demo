# Floras One-Pager Skill
**Format:** One-pager / leave-behind / proposal summary
**Reads after:** `SKILL.md` → `style-guide.md` → this file

---

## Purpose

This file governs the generation of Floras one-pagers. These are single-page documents sent as leave-behinds after a meeting, attached to a warm follow-up email, or shared ahead of a proposal conversation. The goal is to give the reader everything they need to understand what Floras does, why it matters to them, and what to do next — in the time it takes to read one page.

A well-built Floras one-pager is dense with meaning, not with words. Every section earns its place. It is not a brochure. It is not a slide deck compressed into a page. It is a self-contained argument that works without a presenter in the room.

---

## Required Inputs

Before generating any one-pager, confirm all of the following. If any are missing, mark `[NEEDS INPUT]` in the relevant section — never invent them.

| Input | Why it's needed |
|-------|----------------|
| **Audience type** | Enterprise buyer or supplier? Determines the value proposition and framing throughout. |
| **Company name** | For personalisation in the header and body. |
| **Industry / sector** | Needed to make the supply chain context specific and credible. |
| **Known pain point or goal** | Determines which value points to lead with. |
| **Any specific stats or projects to feature** | If a verified project rate or impact figure is available, include it. Otherwise mark `[NEEDS INPUT]`. |
| **Contact / next step** | Who should the reader contact and how? What is the one action they should take? |

---

## One-Pager Types

Every Floras one-pager falls into one of two types. Identify the type from the brief before generating.

### General Leave-Behind
A polished, audience-specific summary of what Floras does and why it matters. Used after a first meeting or attached to an outreach email. Not customised to a specific proposal — customised to an audience type and sector.

### Proposal Summary
A focused document tied to a specific conversation or opportunity. References the context of the discussion, addresses the specific pain points raised, and proposes a concrete next step. More personalised than a general leave-behind.

---

## Section Structure

A Floras one-pager contains these sections in this order. All sections are required. Each must fit within the space constraints defined in the Layout Rules section below.

### Header
- Logo, top-left: always pair the icon with the FLORAS wordmark in a flex row. Header is dark so use:
  `<div style="display:flex; align-items:center; gap:8px;"><img src="light-logo.png" alt="" style="height:20px; display:block;"><span style="font-size:0.95rem; font-weight:300; letter-spacing:0.15em; color:#fff;">FLORAS</span></div>`
- Tagline: "Reward The Earth" — beneath the logo
- Document title: audience-specific. Examples: "Supply Chain Decarbonization for [Industry]" / "How [Company] Can Turn Supplier Transactions Into Verified CO₂ Reduction"
- **Background:** `--color-forest` or wallet gradient (`--color-wallet-start` → `--color-wallet-end`, 135deg)
- **Text:** white throughout
- **Wordmark:** white, letter-spacing 0.15em
- **Title:** `--text-h2`, white
- **Tagline:** `--text-label`, ALL CAPS, `rgba(255,255,255,0.7)`

### The Problem
- One short paragraph. Two to three sentences maximum.
- State the problem the audience faces in their own terms. No Floras yet.
- Include one sourced statistic if available. If not, mark `[NEEDS PROOF]` and use a concrete mechanism statement instead.
- **Background:** `--color-bg`
- **Section label:** ALL CAPS, `--text-label`, letter-spacing 0.12em, `--color-text-muted`
- **Body:** `--text-body`, `--color-text`

### How Floras Works
- The mechanism in plain language. Three to four sentences maximum.
- Use the approved flow: transaction occurs → Floras issued to buyer wallet → buyer allocates to verified project → enterprise receives impact certificate.
- Do not introduce features not defined in `style-guide.md`. Do not describe Floras as an offset marketplace or CSR tool.
- **Background:** `--color-surface`
- **Section label:** ALL CAPS, `--text-label`, letter-spacing 0.12em, `--color-text-muted`
- **Body:** `--text-body`, `--color-text`

### Why It Matters To You (Audience-Specific)
This section changes depending on audience type. Generate the correct version — never both.

**If enterprise buyer:**
- Two to three value points. Each is one sentence: mechanism + outcome.
- Lead with the pain point identified in the brief — compliance, measurability, cost, or operational burden.
- Example: "Every transaction generates Floras automatically — no additional procurement budget required."
- No banned phrases. No vague claims.

**If supplier:**
- Two to three value points. Each is one sentence: mechanism + outcome.
- Lead with commercial advantage — winning contracts, differentiating bids, deepening client relationships.
- Example: "Suppliers enrolled in Floras become preferred partners for enterprises with decarbonization mandates."

**Both versions:**
- **Background:** `--color-bg`
- **Section label:** ALL CAPS, `--text-label`, letter-spacing 0.12em, `--color-text-muted`
- **Body:** `--text-body`, `--color-text`

### Impact & Proof
- Lead with the strongest available number or credential.
- If a verified project rate is available, display it as a stat: `X kg CO₂e / Flora` — label in `--text-label`, value in `--text-stat`, `--color-text`.
- Include partner logos (Berkeley SkyDeck, Puro Earth, Aclymate, Anew) as a single row — grayscale, 24–48px height, equal spacing.
- If no hard numbers are available, mark `[NEEDS PROOF]` and replace with a mechanism statement.
- **Background:** `--color-surface`
- **Section label:** ALL CAPS, `--text-label`, letter-spacing 0.12em, `--color-text-muted`
- **Body:** `--text-body`, `--color-text`
- **Stat label:** `--text-label`, `--color-text-muted`
- **Stat value:** `--text-stat`, `--color-text`

### Next Step
- One specific action. Not "learn more." Not "visit our website."
- Examples: "Book a 30-minute call to map your supplier network." / "Contact [Name] to discuss your Q[X] procurement cycle."
- Contact name, role, email or LinkedIn.
- **Background:** `--color-forest` or wallet gradient — mirrors the header.
- **Text:** white throughout
- **CTA text:** `--text-h3`, white
- **Contact details:** `--text-body-sm`, `rgba(255,255,255,0.8)`
- Logo bottom-left: `<div style="display:flex; align-items:center; gap:8px;"><img src="light-logo.png" alt="" style="height:20px; display:block;"><span style="font-size:0.95rem; font-weight:300; letter-spacing:0.15em; color:#fff;">FLORAS</span></div>`

---

## Layout Rules

A one-pager is a single page. Every section must fit. These constraints are hard limits — if content exceeds them, cut copy, not sections.

### Page Dimensions & Margins
- **Page size:** A4 (210 × 297mm) or US Letter (8.5 × 11in) — match the brief or default to A4
- **Margins:** 24px all sides minimum
- **Max content width:** Full page width minus margins

### Section Space Allocation (approximate)
| Section | Approximate height share |
|---------|--------------------------|
| Header | 15–18% of page |
| The Problem | 12–15% |
| How Floras Works | 15–18% |
| Why It Matters To You | 15–18% |
| Impact & Proof | 18–20% |
| Next Step | 10–11% |

These are guides, not hard pixel values. The total must fit on one page. If a section runs long, cut words — do not overflow onto a second page and do not reduce font size below `--text-body-sm` (0.875rem).

### Typography on One-Pagers
- **Document title (header):** `--text-h2`, white
- **Section labels:** `--text-label` (0.72rem, weight 700), ALL CAPS, letter-spacing 0.12em
- **Body copy:** `--text-body` (1rem, weight 400) — never go smaller than `--text-body-sm` (0.875rem)
- **Stat values:** `--text-stat` (2.4rem, weight 800) — use sparingly, one stat maximum
- **CTA text in footer:** `--text-h3` (1.2rem, weight 600)

### Color Usage on One-Pagers
- **Header and Next Step sections:** `--color-forest` or wallet gradient, white text
- **Body sections:** alternate `--color-bg` and `--color-surface` — do not use the same background for two consecutive sections
- **Section labels:** `--color-text-muted` on light backgrounds
- **Headings and emphasis:** `--color-brand-text` on light backgrounds
- **Never use pure white as the page background** — always `--color-bg` for body sections

### Dividers
- Use `--color-border-soft` for section dividers where a visual break is needed
- Do not use decorative rules, drop shadows, or heavy borders between sections

---

## Tone Notes for One-Pagers

A one-pager is read alone, without a presenter. Every word must do its job unassisted.

- **Lead with the audience's problem, not with Floras.** The reader should see themselves in the first section before they encounter the product.
- **Be ruthless with word count.** If a sentence can be cut without losing meaning, cut it. Dense prose does not read well at one-pager scale.
- **Every section ends with either a proof point or a forward motion.** No section should end on a vague claim.
- **The Next Step section is a commitment, not a sign-off.** It should feel like the natural conclusion of a well-made case — not an afterthought.
- **No taglines or slogans in the body.** "Reward The Earth" belongs in the header only. The body is for mechanisms and outcomes.

---

## Consistency Check (One-Pager-Specific)

Run these in addition to the five questions in `SKILL.md` Step 6:

1. Does the one-pager fit on a single page without reducing body copy below `--text-body-sm`?
2. Does the Problem section open on the audience's problem — not on Floras?
3. Is the Why It Matters section written for the correct audience type (buyer vs. supplier)?
4. Is every claim in the Impact & Proof section either sourced or marked `[NEEDS PROOF]`?
5. Does the Next Step section close with a single specific action and a named contact?
6. Do the header and Next Step section use a dark background — mirroring each other to frame the document?
