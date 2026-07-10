# Floras Sales Intelligence Demo

Proof-of-concept sales intelligence tool for Floras: research a lead, classify where they sit in the value chain, score fit (including financials), and generate a personalized outreach pitch.

**Project location:** `~/Desktop/floras-sales-intel-demo`

## Overview

**What it is:** A proof-of-concept sales tool for Floras that takes a company name (plus industry, website, notes) and produces a tailored sales intelligence report: business hierarchy (buyer vs supplier vs bank), financial profile, fit score, use case, outreach pitch, and risks.

**How it works:**

1. **Lead Research (code)** — Classifies entity type (preview), then gathers evidence: website scrape (Jina/HTML, paths tuned to entity type), Tavily ESG search, SEC EDGAR 10-K Item 1 Business (US public), Wikipedia (fallback), optional Tavily business search (only if SEC/Wikipedia are thin), and your notes. Rules re-classify entity type on full research; GPT refines entity type only when confidence is low or ambiguous.
2. **Financial profile (FMP)** — Optional: gross margin, operating margin, ROA for public companies when `FMP_API_KEY` is set.
3. **Case matching (code)** — Scores 12 sales playbooks against research; entity type boosts/penalizes cases; highest score wins.
4. **Proposal Agent (GPT)** — Drafts the report using Floras KB, entity type, financials, synthesis instructions, matched case, and research.
5. **Quality Reviewer (GPT)** — Critiques grounding, entity/pitch alignment, financials in fit, and Floras mechanism usage.

**What Floras context it uses:**

- **Floras knowledge base** (`floras_overview.txt`) — climate-fintech, transaction-linked climate value, enterprise wallet, supplier embed, verified projects, ICP.
- **Entity types KB** (`entity_types.json`) — buyer / supplier / financial issuer / poor fit / dual role; drives scrape paths, Tavily queries, case preferences, and pitch angle.
- **12 sales cases** (`kb/cases/`) — e.g. CPG procurement, corporate travel/SAF, supplier differentiation, logistics/freight, CSRD disclosure, credit card rewards, financial services low-fit; best match shapes pitch templates and safe claims.

**What you get:**

- **Business hierarchy** — entity type, confidence, pitch focus, outreach target, matched signals (LLM rationale if refined)
- **Financial profile** — gross/operating margin, ROA, financial fit level (when FMP available)
- **Fit score** (High/Medium/Low), company summary, key sales signals
- **Personalized Floras use case**, suggested project types, **outreach pitch**
- **Research sources/URLs** (SEC, Wikipedia, Tavily, website, etc.)
- **Matched sales case** badge, **quality review** with improvement suggestions

**Stack & run:** Plain HTML frontend + FastAPI backend + OpenAI + Tavily (+ optional FMP for financials). Backend on port **8000**, frontend on **5173**, open **http://127.0.0.1:5173**. Demo/POC — AI-estimated fit, no live Floras project catalog or CRM integration.

**Good test companies:** PepsiCo (great fit, CPG), Ball Corporation (supplier differentiation), Goldman Sachs (poor fit), Unilever (CSRD + CPG), Maersk (logistics), Salesforce (medium fit, software).

## Stack

- **Frontend:** plain HTML (`frontend/index.html`)
- **Backend:** FastAPI + OpenAI + Tavily + optional FMP (`backend/`)
- **Pipeline:** Lead Research (code) → Financial profile (FMP) → Case match (code) → Proposal Agent (OpenAI) → Quality Reviewer (OpenAI)

## Setup (first time or after moving the folder)

```bash
cd ~/Desktop/floras-sales-intel-demo
./scripts/setup.sh
```

Or manually:

```bash
cd ~/Desktop/floras-sales-intel-demo/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
OPENAI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here

# Optional — financial margins (see below)
# FMP_API_KEY=your_fmp_key
# ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

### Optional: financial margins (FMP or Alpha Vantage)

BD cares about **gross margin**, operating margin, and ROA. Add **one** of these to `backend/.env`:

**Option A — Financial Modeling Prep (recommended)**  
1. Sign up at [financialmodelingprep.com](https://site.financialmodelingprep.com/developer/docs) (free tier available).  
2. Copy your API key into `.env`: `FMP_API_KEY=...`  
3. Works with **company names** (e.g. `PepsiCo` → ticker lookup automatic).

**Option B — Alpha Vantage**  
1. Get a free key at [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key).  
2. Add `ALPHA_VANTAGE_API_KEY=...` to `.env`.  
3. Best when the form input is a **ticker** (e.g. `PEP`, `CRM`) — free tier is rate-limited (5 calls/min).

No code changes needed after adding the key — restart the backend. The report shows a **Financial Profile** section when data is available.

> **Research cost notes:** SEC EDGAR and Wikipedia are free. Tavily business search uses your existing `TAVILY_API_KEY` and only runs when SEC/Wikipedia did not return enough business context (saves API calls).

> If you moved the project, recreate the virtualenv — the old `venv` has hardcoded paths to the previous folder.

## Run

**Terminal 1 — backend**

```bash
cd ~/Desktop/floras-sales-intel-demo/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Or: `./scripts/start-backend.sh`

**Terminal 2 — frontend**

```bash
cd ~/Desktop/floras-sales-intel-demo/frontend
python3 -m http.server 5173
```

Or: `./scripts/start-frontend.sh`

Open **http://127.0.0.1:5173** in your browser.

## Shared hosted demo (Option 1 — one link for the team)

Use this when BD should open **one URL**, share **run history + research cache**, and **not** need API keys on their laptops.

Keys live only in the host’s environment (e.g. Render). Never commit `backend/.env`.

### What you get

- One link: UI + API on the same server  
- Shared SQLite on a persistent disk → management view / cache / pitch feedback for everyone  
- You push to GitHub → Render can auto-redeploy  

### Deploy on Render (recommended)

1. Push the latest code to GitHub (including `render.yaml`).
2. Go to [render.com](https://render.com) → sign up with GitHub.
3. **New** → **Blueprint** → select `krishna-n0/floras-sales-intel-demo` (or **Web Service** and paste settings from `render.yaml`).
4. Set secret env vars in the Render dashboard (do not put these in GitHub):
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`
   - `FMP_API_KEY` (optional)
5. Confirm a **Disk** is mounted at `/var/data` (Blueprint sets this; needed so cache/history survive restarts).
   - Shared history needs a **Starter** (or higher) plan — free web services don’t keep a persistent disk.
6. Deploy. When live, open your service URL, e.g. `https://floras-sales-intel.onrender.com`.
7. Send that URL to the team. They enter their name and run companies — everyone sees the same Management view.

### Local vs hosted

| | Local | Hosted |
|--|-------|--------|
| Open | http://127.0.0.1:5173 | Your Render URL |
| Keys | Your `backend/.env` | Render env vars |
| Cache / history | Only on your Mac | Shared for everyone |

### Free-tier note

Render **free** web services sleep after idle and **don’t keep a persistent disk**, so cache/history can reset. Use **Starter** (~$7/mo) with the Blueprint disk for a real shared demo. First visit after sleep can take ~30–60s on free.

## Test examples

| Goal | Company | Industry | Notes |
|------|---------|----------|-------|
| Great fit, CPG + financials | PepsiCo | food and beverage | CPG, supplier network, Scope 3 procurement |
| Supplier embed story | Ball Corporation | packaging | B2B supplier to beverage brands, key accounts |
| Poor fit (finserv) | Goldman Sachs | financial services | Investment bank, asset management |
| CSRD / disclosure | Unilever | consumer goods | CSRD, CDP, Scope 3 procurement |
| Logistics / freight | Maersk | logistics | Freight, 3PL, Scope 3 transportation |
| Medium fit, software | Salesforce | software | SaaS, asset-light, limited suppliers |
| Travel / SAF case | Delta Air Lines | aviation | Corporate travel, SAF, Scope 3 aviation |

Patagonia (apparel, sustainability notes) works for general supply-chain research without a strong case match.

## Project structure

```
floras-sales-intel-demo/
├── frontend/index.html
├── backend/
│   ├── main.py
│   ├── lead_research.py
│   ├── business_research.py
│   ├── entity_type.py
│   ├── financial_profile.py
│   ├── proposal_instructions.py
│   ├── quality_reviewer.py
│   ├── kb.py
│   ├── kb/
│   │   ├── floras_overview.txt
│   │   ├── entity_types.json
│   │   └── cases/          # 12 sales playbooks
│   └── requirements.txt
└── scripts/
    ├── setup.sh
    ├── start-backend.sh
    └── start-frontend.sh
```

## After moving the folder

1. **Reopen in Cursor:** File → Open Folder → `~/Desktop/floras-sales-intel-demo`
2. **Recreate venv:** `./scripts/setup.sh` (old venv points at the previous path)
3. **Stop old servers** still running from `~/floras-sales-intel-demo` (Ctrl+C in those terminals)
4. **Restart:** `./scripts/start-backend.sh` and `./scripts/start-frontend.sh`
