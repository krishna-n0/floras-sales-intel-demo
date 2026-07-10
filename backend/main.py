import json
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

from pitch_feedback import list_pitch_feedback, save_pitch_feedback
from proposal_instructions import build_synthesis_instructions
from entity_type import format_entity_type_for_prompt
from financial_profile import (
    fetch_financial_profile,
    financial_api_configured,
    format_financial_profile_for_prompt,
    has_usable_financial_signal,
)
from kb import (
    enrich_outreach_pitch,
    format_case_for_prompt,
    load_floras_context,
    match_sales_case,
)
from activity_insights import build_management_insights
from activity_log import list_activity, list_reps, log_research_activity
from lead_research import gather_research_context
from quality_reviewer import review_proposal
from research_store import get_research_by_key, list_research_history

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Floras Sales Intelligence Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompanyRequest(BaseModel):
    company_name: str
    industry: Optional[str] = ""
    website: Optional[str] = ""
    notes: Optional[str] = ""
    refresh_research: Optional[bool] = False
    rep_name: Optional[str] = ""


class PitchFeedbackRequest(BaseModel):
    rep_name: str
    company_name: str
    used_pitch: str
    liked_pitch: str
    was_effective: str
    improvements: Optional[str] = ""
    activity_id: Optional[int] = None


class SalesIntelResponse(BaseModel):
    company_name: str
    company_summary: str
    fit_score: int
    fit_level: str
    key_signals: List[str]
    personalized_use_case: str
    suggested_project_types: List[str]
    outreach_pitch: str
    risks_or_unknowns: List[str]
    matched_case_id: Optional[str] = ""
    matched_case_title: Optional[str] = ""
    matched_archetype: Optional[str] = ""
    research_source: Optional[str] = ""
    research_preview: Optional[str] = ""
    research_urls: Optional[List[str]] = []
    quality_rating: Optional[str] = ""
    quality_review: Optional[str] = ""
    review_improvements: Optional[List[str]] = []
    entity_type_id: Optional[str] = ""
    entity_type_label: Optional[str] = ""
    hierarchy_level: Optional[str] = ""
    entity_confidence: Optional[str] = ""
    entity_pitch_focus: Optional[str] = ""
    outreach_target: Optional[str] = ""
    entity_matched_signals: Optional[List[str]] = []
    entity_classification_method: Optional[str] = ""
    entity_llm_rationale: Optional[str] = ""
    financial_available: Optional[bool] = False
    financial_symbol: Optional[str] = ""
    gross_margin_pct: Optional[float] = None
    operating_margin_pct: Optional[float] = None
    roa_pct: Optional[float] = None
    financial_interpretation: Optional[str] = ""
    financial_source: Optional[str] = ""
    financial_fit_level: Optional[str] = ""
    financial_api_configured: Optional[bool] = False
    financial_unavailable_reason: Optional[str] = ""
    company_listing_type: Optional[str] = ""
    public_comp_available: Optional[bool] = False
    public_comp_symbol: Optional[str] = ""
    public_comp_name: Optional[str] = ""
    public_comp_industry_label: Optional[str] = ""
    public_comp_gross_margin_pct: Optional[float] = None
    public_comp_operating_margin_pct: Optional[float] = None
    public_comp_roa_pct: Optional[float] = None
    public_comp_fit_level: Optional[str] = ""
    public_comp_interpretation: Optional[str] = ""
    public_comp_disclaimer: Optional[str] = ""
    public_comp_suggested: Optional[bool] = False
    research_from_cache: Optional[bool] = False
    research_cached_at: Optional[str] = ""
    research_cache_key: Optional[str] = ""
    activity_id: Optional[int] = 0


def parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return json.loads(content)


def build_prompt(
    req: CompanyRequest,
    research: dict,
    matched_case: Optional[dict] = None,
    entity_classification: Optional[dict] = None,
    financial_profile: Optional[dict] = None,
) -> str:
    floras_context = load_floras_context()
    entity_section = ""
    if entity_classification:
        entity_section = format_entity_type_for_prompt(entity_classification)
    financial_section = format_financial_profile_for_prompt(financial_profile or {})
    synthesis_section = build_synthesis_instructions(
        entity_classification,
        financial_profile,
        has_matched_case=bool(matched_case),
    )
    case_section = ""
    pitch_guidance = (
        "Write outreach_pitch as 1-2 sentences — concise, specific, aligned with entity type."
    )
    if matched_case:
        case_section = format_case_for_prompt(matched_case)
        pitch_guidance = (
            "Write outreach_pitch as 2-4 short paragraphs separated by blank lines:\n"
            "1) Hook from specific research (sustainability, procurement, or sector signal)\n"
            "2) Floras mechanism aligned to ENTITY TYPE and matched case — wallet, supplier embed, "
            "or product feature as appropriate\n"
            "3) If FINANCIAL PROFILE exists: one sentence on economic capacity (implication only, "
            "not a table of percentages) — e.g. unit economics that can support transaction-embedded Floras\n"
            "4) Optional: certificates/reporting value if research supports it\n"
            "Use matched case safe claims. No generic filler. Shorter if research is thin."
        )
    elif has_usable_financial_signal(financial_profile or {}):
        pitch_guidance = (
            "Write outreach_pitch as 2-3 sentences: research hook + Floras mechanism for entity type + "
            "one line on financial capacity (gross margin implication, not raw stats)."
        )

    return f"""
You are the Proposal Agent for Floras Sales Intelligence.

Use the Floras company knowledge base below to understand what Floras is, who it serves,
and how to judge lead fit. Compare the researched company against Floras' ideal customer
profile, use cases, and mechanisms (transaction-embedded climate value, enterprise wallet,
supplier integration, verified project allocation, certificates/reporting).

FLORAS COMPANY KNOWLEDGE BASE:
{floras_context}

{entity_section}
{financial_section}

{synthesis_section}
{case_section}

You are drafting a sales intelligence report for a prospective lead.
A Lead Research Agent has already gathered context below.
Ground your answer in the research. If research is thin, say so in risks_or_unknowns.
Do not invent specific sustainability claims that are not supported by the research.
Frame the use case in Floras terms (wallet, supplier-embedded Floras, project allocation,
certificates) — not generic carbon-offset language unless the research supports it.
CRITICAL: Match your pitch to the LEAD ENTITY TYPE above. A supplier company needs a
supplier-differentiation story, not a buyer wallet story. A financial issuer needs a
product story, not procurement. If entity type is poor_fit_entity, default to Low fit
unless research shows a narrow exception.

Company name: {req.company_name}
Industry: {req.industry}
Website: {req.website or "Not provided"}

Lead Research Agent findings:
{research["context"]}

Return ONLY valid JSON with this exact structure:
{{
  "company_name": "...",
  "company_summary": "...",
  "fit_score": 0,
  "fit_level": "Low/Medium/High",
  "key_signals": ["...", "..."],
  "personalized_use_case": "...",
  "suggested_project_types": ["...", "..."],
  "outreach_pitch": "...",
  "risks_or_unknowns": ["...", "..."]
}}

Outreach pitch guidance:
{pitch_guidance}

Fit scoring — combine entity type, research, and financial profile (when available):
- High fit (75-100): entity type aligns + strong sustainability/procurement signals + gross margin
  strong/moderate OR huge implied transaction volume (CPG/retail)
- Medium fit (45-74): partial alignment, moderate margins, or software-like entity with narrow angle
- Low fit (0-44): poor_fit_entity, weak mechanism fit, or no leverage unless exception documented
Justify fit_score using entity type, research facts, and financial_fit_level when present.
"""


def fallback_review(exc: Exception) -> dict:
    return {
        "quality_rating": "Fair",
        "quality_review": "Quality review could not run; proposal shown without reviewer pass.",
        "review_improvements": [f"Reviewer step failed: {str(exc)}"],
    }


def _attach_activity_log(req: CompanyRequest, data: dict) -> dict:
    try:
        activity_id = log_research_activity(
            req.rep_name or "",
            req.company_name,
            req.industry or "",
            req.website or "",
            req.notes or "",
            data,
        )
        data["activity_id"] = activity_id
    except Exception:
        data["activity_id"] = 0
    return data


def _financial_fields(financial_profile: dict) -> dict:
    comp = financial_profile.get("public_comp") or {}
    direct = bool(financial_profile.get("available"))
    return {
        "financial_available": direct,
        "financial_symbol": financial_profile.get("symbol", "") or "",
        "gross_margin_pct": financial_profile.get("gross_margin_pct"),
        "operating_margin_pct": financial_profile.get("operating_margin_pct"),
        "roa_pct": financial_profile.get("roa_pct"),
        "financial_interpretation": financial_profile.get("interpretation", "") or "",
        "financial_source": financial_profile.get("source", "") or "",
        "financial_fit_level": financial_profile.get("financial_fit_level", "") or "",
        "financial_api_configured": financial_api_configured(),
        "financial_unavailable_reason": (
            "" if direct else (financial_profile.get("reason") or "")
        ),
        "company_listing_type": financial_profile.get("company_listing_type", "") or "",
        "public_comp_available": bool(comp.get("available")),
        "public_comp_symbol": comp.get("symbol", "") or "",
        "public_comp_name": comp.get("name", "") or "",
        "public_comp_industry_label": comp.get("industry_label", "") or "",
        "public_comp_gross_margin_pct": comp.get("gross_margin_pct"),
        "public_comp_operating_margin_pct": comp.get("operating_margin_pct"),
        "public_comp_roa_pct": comp.get("roa_pct"),
        "public_comp_fit_level": comp.get("financial_fit_level", "") or "",
        "public_comp_interpretation": comp.get("interpretation", "") or "",
        "public_comp_disclaimer": comp.get("disclaimer", "") or "",
        "public_comp_suggested": bool(
            not direct and comp.get("symbol") and not comp.get("available")
        ),
    }


@app.get("/")
def root():
    return {"message": "Floras Sales Intelligence backend is running"}


@app.post("/pitch-feedback")
def submit_pitch_feedback(req: PitchFeedbackRequest):
    """Rep feedback: did you use the pitch, was it effective, what to improve."""
    feedback_id = save_pitch_feedback(
        req.rep_name,
        req.company_name,
        req.used_pitch,
        req.liked_pitch,
        req.was_effective,
        req.improvements or "",
        activity_id=req.activity_id,
    )
    return {"ok": True, "feedback_id": feedback_id}


@app.get("/pitch-feedback")
def get_pitch_feedback(limit: int = 50, rep_name: Optional[str] = None):
    """Recent pitch feedback for managers."""
    return {"items": list_pitch_feedback(limit=limit, rep_name=rep_name)}


@app.get("/activity/management")
def team_activity_management(limit: int = 500):
    """Manager view: grouped activity, themes, duplicates, and takeaways."""
    return build_management_insights(limit=limit)


@app.get("/activity")
def team_activity(limit: int = 50, rep_name: Optional[str] = None):
    """Who researched which companies — team activity log."""
    return {
        "items": list_activity(limit=limit, rep_name=rep_name),
        "reps": list_reps(),
    }


@app.get("/research-history")
def research_history(limit: int = 50):
    """List recent saved research runs (scrapes + sources) for audit / management."""
    return {"items": list_research_history(limit=limit)}


@app.get("/research-history/{cache_key}")
def research_history_detail(cache_key: str):
    """Full saved research blob for a prior run."""
    entry = get_research_by_key(cache_key)
    if not entry:
        return {"error": "not_found", "cache_key": cache_key}
    return entry


@app.post("/analyze-company", response_model=SalesIntelResponse)
def analyze_company(req: CompanyRequest):
    research = gather_research_context(
        req.company_name,
        req.industry or "",
        req.website or "",
        req.notes or "",
        openai_client=client,
        force_refresh=bool(req.refresh_research),
    )
    entity_classification = research.get("entity_classification") or {}
    financial_profile = fetch_financial_profile(req.company_name, req.industry or "")
    matched_case = match_sales_case(
        research.get("context", ""),
        req.industry or "",
        req.notes or "",
        entity_classification=entity_classification,
    )
    prompt = build_prompt(req, research, matched_case, entity_classification, financial_profile)

    try:
        # Step 1: Proposal Agent
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise B2B sales intelligence analyst. "
                        "Return only valid JSON. Do not use markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        content = completion.choices[0].message.content or ""
        data = parse_json_response(content)
        data["outreach_pitch"] = enrich_outreach_pitch(
            data.get("outreach_pitch", ""),
            matched_case,
            req.company_name,
        )
        data["matched_case_id"] = matched_case.get("case_id", "") if matched_case else ""
        data["matched_case_title"] = matched_case.get("title", "") if matched_case else ""
        data["matched_archetype"] = matched_case.get("archetype", "") if matched_case else ""
        data["research_source"] = research["source"]
        data["research_preview"] = research["preview"]
        data["research_urls"] = research.get("research_urls", [])
        data["entity_type_id"] = entity_classification.get("entity_type_id", "")
        data["entity_type_label"] = entity_classification.get("label", "")
        data["hierarchy_level"] = entity_classification.get("hierarchy_level", "")
        data["entity_confidence"] = entity_classification.get("confidence", "")
        data["entity_pitch_focus"] = entity_classification.get("pitch_focus", "")
        data["outreach_target"] = entity_classification.get("outreach_target", "")
        data["entity_matched_signals"] = entity_classification.get("matched_signals", [])
        data["entity_classification_method"] = entity_classification.get(
            "classification_method", "rules"
        )
        data["entity_llm_rationale"] = entity_classification.get("llm_rationale", "")
        data["research_from_cache"] = bool(research.get("from_cache"))
        data["research_cached_at"] = research.get("cached_at", "") or ""
        data["research_cache_key"] = research.get("cache_key", "") or ""
        data.update(_financial_fields(financial_profile))

        # Step 2: Quality Reviewer Agent (second OpenAI call)
        try:
            review = review_proposal(
                client, data, research, entity_classification, financial_profile
            )
            data["quality_rating"] = review.get("quality_rating", "")
            data["quality_review"] = review.get("quality_review", "")
            data["review_improvements"] = review.get("review_improvements", [])
        except Exception as review_exc:
            data.update(fallback_review(review_exc))

        return _attach_activity_log(req, data)

    except Exception as exc:
        data = {
            "company_name": req.company_name,
            "company_summary": "Demo fallback: Unable to call AI service, but backend endpoint is working.",
            "fit_score": 70,
            "fit_level": "Medium",
            "key_signals": [
                "Company may have sustainability relevance",
                "Potential climate storytelling opportunity",
                "Could benefit from verified climate project recommendations",
            ],
            "personalized_use_case": "Floras could help this company connect business activity to verified climate projects and create a clearer customer-facing impact story.",
            "suggested_project_types": [
                "Reforestation",
                "Carbon removal",
                "Biodiversity protection",
            ],
            "outreach_pitch": "Floras can help your company turn climate goals into transparent, project-backed action.",
            "matched_case_id": matched_case.get("case_id", "") if matched_case else "",
            "matched_case_title": matched_case.get("title", "") if matched_case else "",
            "matched_archetype": matched_case.get("archetype", "") if matched_case else "",
            "risks_or_unknowns": [
                f"AI call failed or response was not valid JSON: {str(exc)}"
            ],
            "research_source": research["source"],
            "research_preview": research["preview"],
            "research_urls": research.get("research_urls", []),
            "entity_type_id": entity_classification.get("entity_type_id", ""),
            "entity_type_label": entity_classification.get("label", ""),
            "hierarchy_level": entity_classification.get("hierarchy_level", ""),
            "entity_confidence": entity_classification.get("confidence", ""),
            "entity_pitch_focus": entity_classification.get("pitch_focus", ""),
            "outreach_target": entity_classification.get("outreach_target", ""),
            "entity_matched_signals": entity_classification.get("matched_signals", []),
            "entity_classification_method": entity_classification.get(
                "classification_method", "rules"
            ),
            "entity_llm_rationale": entity_classification.get("llm_rationale", ""),
            "research_from_cache": bool(research.get("from_cache")),
            "research_cached_at": research.get("cached_at", "") or "",
            "research_cache_key": research.get("cache_key", "") or "",
        }
        data.update(_financial_fields(financial_profile))
        data.update(fallback_review(exc))
        return _attach_activity_log(req, data)
