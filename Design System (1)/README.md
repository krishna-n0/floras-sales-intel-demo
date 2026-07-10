# Floras Design System

An AI-driven content production system for generating consistent, on-brand Floras materials at scale.

---

## What This Is

This is not a visual component library. It is a governed folder of markdown skill files that an AI agent reads to produce finished Floras artifacts — sales presentations, emails, one-pagers, and social posts — from a short content brief.

The system captures Floras-specific rules for tone, language, color, typography, layout, and brand positioning. It marks missing inputs rather than inventing them, runs a consistency check on every output, and ensures that anything produced sounds like Floras.

---

## What's In This Folder

```
floras-design-system/
├── README.md                     ← You are here
├── SKILL.md                      ← Read this first. Master entry point for OpenCode.
├── style-guide.md                ← Source of truth for brand: colors, type, tone, language
├── skills/
│   ├── presentation.md           ← Rules for sales presentations and slide decks
│   ├── email.md                  ← Rules for sales emails (cold, follow-up, post-meeting, re-engagement)
│   ├── one-pager.md              ← Rules for one-pagers and leave-behinds
│   └── social-post.md            ← Rules for LinkedIn and social content
├── artifacts/
│   ├── sales-presentation.html   ← Generated enterprise buyer presentation
│   ├── email-template.html       ← Generated enterprise cold outreach email
│   ├── email-template-supplier.html ← Generated supplier outreach email
│   ├── one-pager.html            ← Generated enterprise one-pager
│   ├── social-post.html          ← Generated LinkedIn post set
│   └── overview.html             ← How this system works, in Floras design
└── consistency-comparison.md     ← Before/after: unguided AI vs. system output
```

---

## How To Use It

### You need
- [OpenCode](https://opencode.ai) installed
- This folder open as your working directory in OpenCode
- A content brief (see below)

### The workflow

1. Open OpenCode with this folder as the project root
2. Give OpenCode a short brief — see examples below
3. OpenCode reads `SKILL.md` → `style-guide.md` → the relevant skill file, then generates
4. Review the output and the displayed consistency check
5. Fill in any `[NEEDS INPUT]` or `[NEEDS PROOF]` markers with real information
6. Approve and send

### Example prompts

**Cold outreach email:**
```
Cold outreach email. Enterprise buyer. Recipient: [Name], [Role], [Company].
Hook: [specific reason this is relevant to them right now].
Desired action: 15-minute call. Sender: Gonzalo.
```

**Sales presentation:**
```
Sales presentation. Enterprise buyer. Company: [Name]. Industry: [sector].
Pain point: [what they care about most]. Presenter: Jeroen.
```

**One-pager:**
```
One-pager, general leave-behind. Supplier audience. Industry: [sector].
Contact: [Name], [email].
```

**LinkedIn post:**
```
Insight post. Topic: [one clear idea]. Anchor stat: [specific figure if available].
Platform: LinkedIn.
```

---

## Key Rules To Know

Before you use the system or review its outputs, know these:

**Floras is not a carbon offset marketplace.** It is a supply chain decarbonization engine with a currency at its center.

**The currency is called Floras.** Not points, not tokens, not credits.

**[NEEDS INPUT]** in an output means the brief was missing something. Fill it in with real information before sending — never delete the marker and leave the gap blank.

**[NEEDS PROOF]** means a claim could not be verified. Replace with a sourced statistic or rewrite as a mechanism statement.

**[ILLUSTRATIVE EXAMPLE]** means a scenario was constructed as a plausible example, not a real case study. Label it clearly if it leaves the system.

**Every output is a draft** until a human reviews and approves it.

---

## Logo Files

Two logo PNG files are used in HTML artifacts:

- `light-logo.png` — white icon, transparent background. Use on dark/green backgrounds.
- `dark-logo.png` — dark icon, transparent background. Use on light/white backgrounds.

Always pair the icon with the FLORAS wordmark in a flex row:
```html
<div style="display:flex; align-items:center; gap:8px;">
  <img src="light-logo.png" alt="" style="height:20px; display:block;">
  <span style="font-size:0.95rem; font-weight:300; letter-spacing:0.15em; color:#fff;">FLORAS</span>
</div>
```

---

## Questions

Contact Gonzalo (gonzalo@floras.io) or Jeroen for questions about brand direction or content.

For questions about the system itself, start with `SKILL.md` — it documents the reasoning behind every rule.
