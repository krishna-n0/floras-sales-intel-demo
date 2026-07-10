"""Unified instructions for how the Proposal Agent synthesizes all intelligence layers."""

from typing import Any, Dict, Optional


def build_synthesis_instructions(
    entity_classification: Optional[Dict[str, Any]] = None,
    financial_profile: Optional[Dict[str, Any]] = None,
    has_matched_case: bool = False,
) -> str:
    entity = entity_classification or {}
    financial = financial_profile or {}
    entity_id = entity.get("entity_type_id", "unknown")
    has_direct = bool(financial.get("available"))
    comp = financial.get("public_comp") or {}
    has_comp = bool(comp.get("available"))
    has_financials = has_direct or has_comp
    listing = financial.get("company_listing_type", "unknown")

    lines = [
        "HOW TO SYNTHESIZE ALL INPUTS (read in this order):",
        "",
        "1) LEAD ENTITY TYPE — decides WHO you are pitching and WHICH Floras mechanism:",
        "   - enterprise_buyer → enterprise wallet from procurement/supplier transactions",
        "   - supplier_to_enterprises → embed Floras in products/invoices to win enterprise accounts",
        "   - financial_product_issuer → cards, loans, or payment-product differentiation",
        "   - poor_fit_entity → default Low fit; only pursue a narrow sub-use-case if research proves it",
        "   - dual_buyer_and_supplier → acknowledge both; supplier-embed angle often comes first",
        "",
        "2) RESEARCH (website, SEC 10-K, Wikipedia, Tavily) — supplies FACTS only:",
        "   - SEC/Wikipedia describe what the company does (buyer vs supplier language)",
        "   - Sustainability snippets support ESG urgency, not financial capacity",
        "   - Never invent facts missing from research",
        "",
    ]

    if has_direct:
        gm = financial.get("gross_margin_pct")
        om = financial.get("operating_margin_pct")
        roa = financial.get("roa_pct")
        fit_lvl = financial.get("financial_fit_level", "unknown")
        lines.extend(
            [
                f"3) FINANCIAL PROFILE (public company, listing: {listing}) — economic plausibility:",
                f"   - Gross margin: {gm}% (primary BD signal; fit level: {fit_lvl})",
                f"   - Operating margin: {om}% | ROA: {roa}%",
                f"   - Interpretation: {financial.get('interpretation', '')}",
                "   - Use gross margin in fit_score: strong (≥40%) supports High when entity + sustainability align;",
                "     moderate (25–40%) → Medium unless huge procurement volume; weak (<25%) → cap at Medium unless",
                "     high-transaction retail/CPG with clear supplier leverage",
                "   - Add one key_signal citing gross margin when available",
                "   - In outreach_pitch: weave ONE sentence on economic capacity — do NOT dump raw percentages",
                "",
            ]
        )
    elif has_comp:
        gm = comp.get("gross_margin_pct")
        om = comp.get("operating_margin_pct")
        roa = comp.get("roa_pct")
        fit_lvl = comp.get("financial_fit_level", "unknown")
        lines.extend(
            [
                f"3) FINANCIAL PROFILE (listing: private — use PUBLIC PEER COMP ONLY):",
                f"   - Peer: {comp.get('name')} ({comp.get('symbol')}) — {comp.get('industry_label', '')}",
                f"   - {comp.get('disclaimer', '')}",
                f"   - Peer gross margin: {gm}% (fit level: {fit_lvl}) | Operating: {om}% | ROA: {roa}%",
                f"   - Interpretation: {comp.get('interpretation', '')}",
                "   - Use peer margin as SECTOR capacity signal — never claim these are the target's financials",
                "   - Note in risks_or_unknowns that direct financials unavailable and peer comp was used",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"3) FINANCIAL PROFILE (listing: {listing}) — direct margins unavailable; do not invent margins",
                "   - Note in risks_or_unknowns if financial capacity is unknown",
                "",
            ]
        )

    if has_matched_case:
        lines.extend(
            [
                "4) MATCHED SALES CASE — shapes pitch structure, safe claims, and project types",
                "   - Case mechanism must align with entity type (do not pitch buyer wallet to a supplier)",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "4) No matched sales case — use Floras KB + entity type only; keep pitch conservative",
                "",
            ]
        )

    lines.extend(
        [
            "5) OUTPUT RULES:",
            "   - company_summary: what they do + sustainability posture + entity role (buyer/supplier/etc.)",
            "   - key_signals: mix research facts, entity type, and financial signal (if any)",
            "   - personalized_use_case: Floras mechanism matched to entity type",
            "   - outreach_pitch: hook from research → Floras mechanism → optional financial capacity line",
            "     → clear CTA; 2–4 short paragraphs if case matched, else 1–2 sentences",
            "   - risks_or_unknowns: thin research, entity ambiguity, missing financials, or poor fit flags",
            "",
            f"Current entity type for this lead: {entity.get('label', 'Unknown')} ({entity_id})",
        ]
    )

    if entity_id == "supplier_to_enterprises":
        lines.append(
            "   PITCH REMINDER: This is a SUPPLIER — lead with differentiation for their enterprise customers, "
            "not a buyer wallet accumulation story."
        )
    elif entity_id == "poor_fit_entity":
        lines.append(
            "   PITCH REMINDER: Deprioritize broad outreach; fit_score should be Low unless a narrow exception is proven."
        )

    return "\n".join(lines)
