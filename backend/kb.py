"""Load Floras company knowledge and sales case patterns for prompts."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

KB_DIR = Path(__file__).parent / "kb"
FLORAS_OVERVIEW_PATH = KB_DIR / "floras_overview.txt"
CASES_DIR = KB_DIR / "cases"

MIN_CASE_MATCH_SCORE = 2


@lru_cache(maxsize=1)
def load_floras_context() -> str:
    """Return Floras company overview text for prompt injection."""
    if not FLORAS_OVERVIEW_PATH.exists():
        return ""
    return FLORAS_OVERVIEW_PATH.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def load_cases() -> Tuple[Dict[str, Any], ...]:
    """Load all sales case JSON files from kb/cases/."""
    if not CASES_DIR.exists():
        return ()
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        try:
            cases.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return tuple(cases)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _count_haystack_matches(needles: list, haystack: str) -> Tuple[int, List[str]]:
    """Count how many trigger phrases appear in haystack; return score and matched phrases."""
    matched = []
    for needle in needles:
        term = _normalize(needle)
        if term and term in haystack:
            matched.append(needle)
    return len(matched), matched


def match_sales_case(
    research_context: str = "",
    industry: str = "",
    notes: str = "",
    entity_classification: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return the best-matching sales case, or None if no strong match."""
    cases = load_cases()
    if not cases:
        return None

    haystack = _normalize(" ".join([research_context, industry, notes]))
    industry_norm = _normalize(industry)

    preferred_ids = set((entity_classification or {}).get("preferred_case_ids") or [])
    discouraged_ids = set((entity_classification or {}).get("discouraged_case_ids") or [])

    best_case = None
    best_score = 0
    best_matched_triggers: List[str] = []

    for case in cases:
        case_id = case.get("case_id", "")
        trigger_score, matched_triggers = _count_haystack_matches(
            case.get("lead_triggers", []), haystack
        )
        pain_score, matched_pains = _count_haystack_matches(
            case.get("pain_signals", []), haystack
        )
        sector_score = 0
        matched_sectors: List[str] = []
        for sector in case.get("sectors", []):
            sector_norm = _normalize(sector)
            if sector_norm and (
                sector_norm in haystack or sector_norm in industry_norm
            ):
                sector_score += 1
                matched_sectors.append(sector)

        score = trigger_score * 2 + pain_score + min(sector_score, 2)

        if case_id in preferred_ids:
            score += 3
        if case_id in discouraged_ids:
            score -= 4

        if score > best_score:
            best_score = score
            best_case = case
            best_matched_triggers = matched_triggers + matched_pains + matched_sectors

    if best_case is None or best_score < MIN_CASE_MATCH_SCORE:
        return None

    return {
        **best_case,
        "_match_score": best_score,
        "_matched_triggers": best_matched_triggers,
    }


def format_case_for_prompt(case: Dict[str, Any]) -> str:
    """Format a matched sales case for injection into the Proposal Agent prompt."""
    templates = case.get("output_templates", {})
    objections = case.get("objections_and_responses", [])
    objection_lines = "\n".join(
        f'- "{item.get("objection", "")}" → {item.get("response", "")}'
        for item in objections
    )

    return f"""
MATCHED SALES CASE PATTERN (use this to shape use case, project types, and outreach pitch):
- Case ID: {case.get("case_id", "")}
- Title: {case.get("title", "")}
- Archetype: {case.get("archetype", "")}
- Maturity: {case.get("maturity_level", "")}
- Matched signals: {", ".join(case.get("_matched_triggers", [])[:8]) or "general sector/trigger overlap"}

Floras mechanism for this pattern:
{case.get("floras_mechanism", "")}

Buyer personas: {", ".join(case.get("buyer_personas", []))}
Budget source: {case.get("budget_source", "")}

Safe claims (may use when consistent with research):
{chr(10).join("- " + c for c in case.get("safe_claims", []))}

Conditional claims (only if research supports):
{chr(10).join("- " + c for c in case.get("conditional_claims", []))}

Avoid claims:
{chr(10).join("- " + c for c in case.get("avoid_claims", []))}

Case project types to prefer: {", ".join(case.get("suggested_project_types", []))}

Pitch templates (personalize with company name; do not copy verbatim if research contradicts):
- One-liner: {templates.get("one_liner", "")}
- Short pitch: {templates.get("short_pitch", "")}

Objections and responses (use at most one if clearly relevant):
{objection_lines}
"""


def _paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


def _similar_enough(a: str, b: str) -> bool:
    """Rough check whether two paragraphs say the same thing."""
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if not a_norm or not b_norm:
        return False
    if a_norm == b_norm:
        return True
    shorter, longer = (a_norm, b_norm) if len(a_norm) <= len(b_norm) else (b_norm, a_norm)
    if shorter in longer:
        return True
    # Avoid flagging a short AI hook as duplicate of a long case template.
    if len(shorter) < 120 or len(longer) < 120:
        return False
    a_words = set(a_norm.split())
    b_words = set(b_norm.split())
    overlap = len(a_words & b_words) / min(len(a_words), len(b_words))
    return overlap >= 0.65


def enrich_outreach_pitch(
    ai_pitch: str,
    case: Optional[Dict[str, Any]],
    company_name: str,
) -> str:
    """Extend outreach pitch with case content when it adds substance—not filler."""
    base = (ai_pitch or "").strip()
    if not case:
        return base

    paragraphs = _paragraphs(base)
    templates = case.get("output_templates", {})
    company = company_name or "your company"

    short_pitch = templates.get("short_pitch", "").replace("{company_name}", company).strip()
    if short_pitch and not any(_similar_enough(short_pitch, p) for p in paragraphs):
        paragraphs.append(short_pitch)

    if len(paragraphs) < 3:
        objections = case.get("objections_and_responses", [])
        if objections:
            response = objections[0].get("response", "").strip()
            if response and not any(_similar_enough(response, p) for p in paragraphs):
                paragraphs.append(response)

    return "\n\n".join(paragraphs)
