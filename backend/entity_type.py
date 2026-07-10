"""Classify leads by position in the Floras GTM hierarchy (buyer, supplier, financial issuer, etc.)."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

KB_DIR = Path(__file__).parent / "kb"
ENTITY_TYPES_PATH = KB_DIR / "entity_types.json"

DEFAULT_SCRAPE_PATHS = (
    "",
    "/sustainability",
    "/about",
    "/our-impact",
    "/impact",
    "/esg",
    "/about-us",
    "/company",
)


@lru_cache(maxsize=1)
def load_entity_types_kb() -> Dict[str, Any]:
    if not ENTITY_TYPES_PATH.exists():
        return {"entity_types": [], "classification_rules": {}}
    return json.loads(ENTITY_TYPES_PATH.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _score_entity_type(
    entity: Dict[str, Any],
    haystack: str,
    industry_norm: str,
) -> tuple[int, List[str], List[str]]:
    """Return score, matched positive signals, matched negative signals."""
    matched_positive: List[str] = []
    matched_negative: List[str] = []
    score = 0

    for signal in entity.get("industry_signals", []):
        term = _normalize(signal)
        if term and (term in haystack or term in industry_norm):
            score += 2
            matched_positive.append(signal)

    for signal in entity.get("text_signals", []):
        term = _normalize(signal)
        if term and term in haystack:
            score += 1
            matched_positive.append(signal)

    for signal in entity.get("negative_signals", []):
        term = _normalize(signal)
        if term and term in haystack:
            score -= 2
            matched_negative.append(signal)

    return score, matched_positive, matched_negative


def _score_all(
    haystack: str,
    industry: str,
) -> List[Dict[str, Any]]:
    kb = load_entity_types_kb()
    industry_norm = _normalize(industry)
    results: List[Dict[str, Any]] = []

    for entity in kb.get("entity_types", []):
        score, matched_positive, matched_negative = _score_entity_type(
            entity, haystack, industry_norm
        )
        results.append(
            {
                **entity,
                "_score": score,
                "_matched_signals": matched_positive,
                "_negative_hits": matched_negative,
            }
        )

    results.sort(key=lambda item: item["_score"], reverse=True)
    return results


def _detect_dual_role(scored: List[Dict[str, Any]], rules: Dict[str, Any]) -> bool:
    by_id = {item["entity_type_id"]: item["_score"] for item in scored}
    buyer_min = rules.get("dual_role_min_buyer_score", 2)
    supplier_min = rules.get("dual_role_min_supplier_score", 2)
    return (
        by_id.get("enterprise_buyer", 0) >= buyer_min
        and by_id.get("supplier_to_enterprises", 0) >= supplier_min
    )


def _entity_by_id(entity_type_id: str) -> Optional[Dict[str, Any]]:
    kb = load_entity_types_kb()
    return next(
        (e for e in kb.get("entity_types", []) if e.get("entity_type_id") == entity_type_id),
        None,
    )


def _build_classification(
    entity: Dict[str, Any],
    *,
    phase: str,
    score: int,
    matched_signals: List[str],
    negative_hits: List[str],
    runner_up: Optional[Dict[str, str]],
    classification_method: str = "rules",
    rule_based_entity_type_id: str = "",
    llm_rationale: str = "",
    llm_evidence: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "entity_type_id": entity.get("entity_type_id", "unknown"),
        "label": entity.get("label", "Unknown"),
        "hierarchy_level": entity.get("hierarchy_level", "unknown"),
        "summary": entity.get("summary", ""),
        "pitch_focus": entity.get("pitch_focus", ""),
        "outreach_target": entity.get("outreach_target", ""),
        "confidence": _confidence_label(score),
        "classification_phase": phase,
        "classification_method": classification_method,
        "rule_based_entity_type_id": rule_based_entity_type_id,
        "llm_rationale": llm_rationale,
        "llm_evidence": llm_evidence or [],
        "score": score,
        "matched_signals": matched_signals[:12],
        "negative_hits": negative_hits[:8],
        "preferred_case_ids": entity.get("preferred_case_ids", []),
        "discouraged_case_ids": entity.get("discouraged_case_ids", []),
        "pitch_note": entity.get("pitch_note", ""),
        "fit_cap_note": entity.get("fit_cap_note", ""),
        "runner_up": runner_up,
    }


def _unknown_classification(
    phase: str,
    scored: List[Dict[str, Any]],
    best: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    unknown = _entity_by_id("unknown") or {
        "entity_type_id": "unknown",
        "label": "Unknown / needs more data",
        "hierarchy_level": "unknown",
        "summary": "Insufficient signals to classify buyer vs supplier vs financial issuer.",
        "pitch_focus": "Gather more research before choosing a Floras narrative.",
        "outreach_target": "Unknown",
    }
    return _build_classification(
        unknown,
        phase=phase,
        score=best["_score"] if best else 0,
        matched_signals=best["_matched_signals"][:12] if best else [],
        negative_hits=best["_negative_hits"][:8] if best else [],
        runner_up=_runner_up(scored, "unknown"),
        classification_method="rules",
    )


def needs_llm_entity_refinement(classification: Dict[str, Any]) -> bool:
    """True when rule-based classification is uncertain and LLM should arbitrate."""
    kb = load_entity_types_kb()
    rules = kb.get("classification_rules", {})
    margin = rules.get("llm_refinement_score_margin", 2)

    if classification.get("entity_type_id") == "unknown":
        return bool(rules.get("llm_refinement_on_unknown", True))

    if classification.get("confidence") == "low":
        return True

    runner_up = classification.get("runner_up")
    if runner_up:
        try:
            winner_score = int(classification.get("score", 0))
            runner_score = int(runner_up.get("score", 0))
            if runner_score > 0 and (winner_score - runner_score) <= margin:
                return True
        except (TypeError, ValueError):
            pass

    return False


def _parse_json_response(content: str) -> dict:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return json.loads(content)


def _entity_options_for_llm() -> str:
    lines = []
    for entity in load_entity_types_kb().get("entity_types", []):
        lines.append(
            f"- {entity.get('entity_type_id')}: {entity.get('label')} — {entity.get('summary', '')}"
        )
    lines.append(
        "- unknown: Insufficient evidence to classify (use only if research is too thin)"
    )
    return "\n".join(lines)


def llm_refine_entity_classification(
    client: "OpenAI",
    company_name: str,
    industry: str,
    notes: str,
    research_context: str,
    rule_classification: Dict[str, Any],
) -> Dict[str, Any]:
    """Second-pass entity classification using LLM on research text."""
    valid_ids = {
        e.get("entity_type_id")
        for e in load_entity_types_kb().get("entity_types", [])
    }
    valid_ids.add("unknown")

    runner_up = rule_classification.get("runner_up") or {}
    prompt = f"""
You classify B2B leads for Floras sales intelligence by their position in the value chain.

Valid entity_type_id values:
{_entity_options_for_llm()}

Company: {company_name}
Industry: {industry or "Not provided"}
User notes: {notes or "None"}

Rule-based classification (may be wrong on edge cases):
- entity_type_id: {rule_classification.get("entity_type_id")}
- label: {rule_classification.get("label")}
- confidence: {rule_classification.get("confidence")}
- score: {rule_classification.get("score")}
- matched signals: {", ".join(rule_classification.get("matched_signals") or [])}
- runner-up: {runner_up.get("label", "none")} (score {runner_up.get("score", "0")})

Research excerpt:
{(research_context or "")[:4500]}

Choose the best entity_type_id based on what the company actually DOES:
- enterprise_buyer: large brand that purchases from suppliers at scale
- supplier_to_enterprises: B2B vendor selling into enterprise supply chains
- financial_product_issuer: bank/fintech with cards, loans, or payment products
- poor_fit_entity: asset manager / advisory-heavy financial firm without product surface
- dual_buyer_and_supplier: clearly both buys at scale AND sells B2B into enterprises
- unknown: only if evidence is truly insufficient

Return ONLY valid JSON:
{{
  "entity_type_id": "...",
  "confidence": "high/medium/low",
  "rationale": "1-2 sentences citing specific evidence from research",
  "evidence_signals": ["short evidence 1", "short evidence 2"]
}}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You classify companies for B2B sales routing. "
                    "Return only valid JSON. Prefer evidence from business descriptions over sustainability marketing."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = completion.choices[0].message.content or ""
    data = _parse_json_response(content)
    chosen_id = data.get("entity_type_id", "unknown")
    if chosen_id not in valid_ids:
        chosen_id = rule_classification.get("entity_type_id", "unknown")

    entity = _entity_by_id(chosen_id)
    if not entity:
        return {
            **rule_classification,
            "classification_method": "rules",
            "llm_rationale": "LLM returned invalid entity type; kept rule-based result.",
        }

    llm_confidence = str(data.get("confidence", "medium")).lower()
    if llm_confidence not in {"high", "medium", "low"}:
        llm_confidence = "medium"

    evidence = [str(item) for item in (data.get("evidence_signals") or []) if item][:8]
    merged_signals = list(
        dict.fromkeys((rule_classification.get("matched_signals") or []) + evidence)
    )[:12]

    refined = _build_classification(
        entity,
        phase=rule_classification.get("classification_phase", "full"),
        score=rule_classification.get("score", 0),
        matched_signals=merged_signals,
        negative_hits=rule_classification.get("negative_hits", []),
        runner_up=rule_classification.get("runner_up"),
        classification_method="llm",
        rule_based_entity_type_id=rule_classification.get("entity_type_id", ""),
        llm_rationale=str(data.get("rationale", "")).strip(),
        llm_evidence=evidence,
    )
    refined["confidence"] = llm_confidence
    return refined


def apply_llm_entity_refinement_if_needed(
    client: Optional["OpenAI"],
    company_name: str,
    industry: str,
    notes: str,
    research_context: str,
    rule_classification: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply LLM refinement only when rules are uncertain and a client is available."""
    if not client or not research_context.strip():
        rule_classification["classification_method"] = "rules"
        return rule_classification
    if not needs_llm_entity_refinement(rule_classification):
        rule_classification["classification_method"] = "rules"
        return rule_classification
    try:
        return llm_refine_entity_classification(
            client,
            company_name,
            industry,
            notes,
            research_context,
            rule_classification,
        )
    except Exception as exc:
        return {
            **rule_classification,
            "classification_method": "rules",
            "llm_rationale": f"LLM refinement skipped: {exc}",
        }


def classify_entity_type(
    company_name: str = "",
    industry: str = "",
    notes: str = "",
    research_context: str = "",
) -> Dict[str, Any]:
    """
    Classify entity type from industry, notes, company name, and optional research text.
    When research_context is empty, this acts as a preview for scraping configuration.
    """
    kb = load_entity_types_kb()
    rules = kb.get("classification_rules", {})
    min_score = rules.get("min_score", 2)

    preview_haystack = _normalize(" ".join([company_name, industry, notes]))
    full_haystack = _normalize(" ".join([preview_haystack, research_context]))

    preview_scored = _score_all(preview_haystack, industry)
    full_scored = _score_all(full_haystack, industry)

    phase = "full" if research_context.strip() else "preview"
    scored = full_scored if phase == "full" else preview_scored
    best = scored[0] if scored else None

    if _detect_dual_role(full_scored if research_context.strip() else preview_scored, rules):
        dual = _entity_by_id("dual_buyer_and_supplier")
        if dual:
            buyer = next(e for e in scored if e["entity_type_id"] == "enterprise_buyer")
            supplier = next(e for e in scored if e["entity_type_id"] == "supplier_to_enterprises")
            combined_score = buyer["_score"] + supplier["_score"]
            return _build_classification(
                dual,
                phase=phase,
                score=combined_score,
                matched_signals=list(
                    dict.fromkeys(buyer["_matched_signals"] + supplier["_matched_signals"])
                ),
                negative_hits=list(
                    dict.fromkeys(buyer["_negative_hits"] + supplier["_negative_hits"])
                ),
                runner_up=_runner_up(scored, dual["entity_type_id"]),
                classification_method="rules",
            )

    if best is None or best["_score"] < min_score:
        return _unknown_classification(phase, scored, best)

    return _build_classification(
        best,
        phase=phase,
        score=best["_score"],
        matched_signals=best["_matched_signals"],
        negative_hits=best["_negative_hits"],
        runner_up=_runner_up(scored, best["entity_type_id"]),
        classification_method="rules",
    )


def _confidence_label(score: int) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _runner_up(scored: List[Dict[str, Any]], winner_id: str) -> Optional[Dict[str, str]]:
    for item in scored:
        if item["entity_type_id"] != winner_id and item["_score"] > 0:
            return {
                "entity_type_id": item["entity_type_id"],
                "label": item["label"],
                "score": str(item["_score"]),
            }
    return None


def get_research_config(entity_classification: Dict[str, Any]) -> Dict[str, Any]:
    """Return scrape paths and Tavily query focus for the classified entity type."""
    entity_type_id = entity_classification.get("entity_type_id", "unknown")
    kb = load_entity_types_kb()

    entity = next(
        (e for e in kb.get("entity_types", []) if e["entity_type_id"] == entity_type_id),
        None,
    )
    if not entity:
        return {
            "scrape_paths": list(DEFAULT_SCRAPE_PATHS),
            "tavily_query_focus": "sustainability ESG climate commitments impact",
        }

    paths = entity.get("scrape_paths") or list(DEFAULT_SCRAPE_PATHS)
    return {
        "scrape_paths": paths,
        "tavily_query_focus": entity.get(
            "tavily_query_focus",
            "sustainability ESG climate commitments impact",
        ),
    }


def refine_entity_classification(
    preview: Dict[str, Any],
    full: Dict[str, Any],
) -> Dict[str, Any]:
    """Prefer full research classification; keep preview metadata when full is unknown."""
    if full.get("entity_type_id") != "unknown":
        full["preview_entity_type_id"] = preview.get("entity_type_id")
        full["preview_label"] = preview.get("label")
        return full
    preview["classification_phase"] = "preview_only"
    return preview


def format_entity_type_for_prompt(classification: Dict[str, Any]) -> str:
    """Format entity classification for Proposal Agent prompt injection."""
    lines = [
        "LEAD ENTITY TYPE (business hierarchy — shapes pitch angle and fit scoring):",
        f"- Entity type: {classification.get('label', 'Unknown')} ({classification.get('entity_type_id', 'unknown')})",
        f"- Hierarchy level: {classification.get('hierarchy_level', 'unknown')}",
        f"- Confidence: {classification.get('confidence', 'low')} (score {classification.get('score', 0)})",
        f"- Classification method: {classification.get('classification_method', 'rules')}",
    ]

    if classification.get("rule_based_entity_type_id") and classification.get("classification_method") == "llm":
        lines.append(
            f"- Rule-based guess (overridden): {classification.get('rule_based_entity_type_id')}"
        )

    if classification.get("llm_rationale"):
        lines.append(f"- LLM rationale: {classification['llm_rationale']}")

    lines.extend(
        [
            f"- Summary: {classification.get('summary', '')}",
            f"- Pitch focus: {classification.get('pitch_focus', '')}",
            f"- Outreach target: {classification.get('outreach_target', '')}",
        ]
    )

    signals = classification.get("matched_signals") or []
    if signals:
        lines.append(f"- Matched signals: {', '.join(signals[:10])}")

    negatives = classification.get("negative_hits") or []
    if negatives:
        lines.append(f"- Conflicting signals: {', '.join(negatives[:6])}")

    runner_up = classification.get("runner_up")
    if runner_up:
        lines.append(
            f"- Runner-up type: {runner_up.get('label')} (score {runner_up.get('score')}) — resolve in risks if ambiguous"
        )

    if classification.get("pitch_note"):
        lines.append(f"- IMPORTANT: {classification['pitch_note']}")

    if classification.get("fit_cap_note"):
        lines.append(f"- Fit guidance: {classification['fit_cap_note']}")

    lines.extend(
        [
            "",
            "Entity-type pitch rules:",
            "- Enterprise buyer: pitch wallet accumulation from procurement — NOT supplier differentiation.",
            "- Supplier to enterprises: pitch embedding Floras to win enterprise accounts — NOT buyer wallet as primary story.",
            "- Financial product issuer: pitch cards/loans/payments — NOT supply-chain procurement.",
            "- Poor fit entity: default Low fit unless a narrow exception is evidenced in research.",
            "- Dual role: acknowledge both angles; note BD may target supplier side first.",
        ]
    )

    return "\n".join(lines)
