"""Aggregate team research activity into manager-facing insights and sections."""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from activity_log import init_activity_db, list_reps
from research_store import DB_PATH, _connect


INDUSTRY_BUCKETS: List[Tuple[str, str, Tuple[str, ...]]] = [
    ("cpg_retail", "CPG & retail", ("cpg", "consumer goods", "fmcg", "food", "beverage", "grocery", "retail", "supermarket")),
    ("apparel", "Apparel & fashion", ("apparel", "fashion", "clothing", "outdoor", "footwear")),
    ("finance", "Bank & fintech", ("financial", "bank", "fintech", "investment", "capital markets", "asset management", "insurance")),
    ("logistics", "Logistics & freight", ("logistics", "freight", "shipping", "3pl", "carrier", "transportation", "last mile")),
    ("travel", "Travel & aviation", ("aviation", "airline", "travel", "hotel", "hospitality", "saf")),
    ("supplier", "Suppliers & packaging", ("packaging", "supplier", "ingredient", "co-manufacturer", "industrial", "b2b")),
    ("software", "Software & SaaS", ("software", "saas", "cloud", "technology", "enterprise software")),
]

THEME_RULES: List[Tuple[str, str, Tuple[str, ...]]] = [
    ("supplier_emissions", "Supplier emissions & Scope 3", ("scope 3", "supplier", "procurement", "supply chain", "sourcing", "vendor")),
    ("consumer_loyalty", "Consumer loyalty & rewards", ("loyalty", "rewards", "miles", "points", "cashback", "card rewards")),
    ("sustainability_reporting", "Sustainability reporting", ("csrd", "cdp", "disclosure", "reporting", "assurance", "sec climate", "esg report")),
    ("climate_commitments", "Climate commitments", ("net zero", "carbon neutral", "climate target", "science based", "sustainability goal", "emissions target")),
    ("procurement_pain", "Procurement pain points", ("procurement", "purchasing", "sourcing program", "supplier engagement", "category management")),
    ("payment_integration", "Payment & reward integration", ("credit card", "payment", "fintech", "wallet", "transaction", "embed")),
]

ENTITY_SECTION_LABELS = {
    "enterprise_buyer": "Enterprise buyers",
    "supplier_to_enterprises": "Supplier-side companies",
    "financial_product_issuer": "Bank & fintech issuers",
    "poor_fit_entity": "Poor-fit entities",
    "dual_buyer_and_supplier": "Dual buyer & supplier",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _norm_company(name: str) -> str:
    return _norm(re.sub(r"[^a-z0-9\s]", "", _norm(name)))


def _fit_bucket(fit_level: str, fit_score: Optional[int]) -> str:
    level = _norm(fit_level)
    if "high" in level:
        return "high"
    if "low" in level:
        return "low"
    if fit_score is not None:
        if fit_score >= 75:
            return "high"
        if fit_score < 45:
            return "low"
    return "medium"


def classify_industry(industry: str, notes: str = "", company_name: str = "") -> str:
    haystack = _norm(" ".join([industry, notes, company_name]))
    for bucket_id, _label, keywords in INDUSTRY_BUCKETS:
        if any(kw in haystack for kw in keywords):
            return bucket_id
    return "other"


def industry_label(bucket_id: str) -> str:
    for bid, label, _ in INDUSTRY_BUCKETS:
        if bid == bucket_id:
            return label
    return "Other industries"


def detect_themes(item: Dict[str, Any]) -> List[str]:
    haystack = _norm(
        " ".join(
            [
                item.get("industry", ""),
                item.get("notes", ""),
                item.get("company_name", ""),
                item.get("matched_case_title", ""),
                item.get("entity_type_label", ""),
            ]
        )
    )
    matched = []
    for theme_id, _label, keywords in THEME_RULES:
        if any(kw in haystack for kw in keywords):
            matched.append(theme_id)
    return matched


def _fetch_all_activity(limit: int = 500) -> List[Dict[str, Any]]:
    init_activity_db()
    limit = max(1, min(limit, 500))
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, rep_name, company_name, industry, website, notes,
                   fit_score, fit_level, entity_type_id, entity_type_label,
                   matched_case_title, research_source, research_from_cache,
                   research_cache_key, created_at
            FROM research_activity
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "rep_name": row["rep_name"],
                "company_name": row["company_name"],
                "industry": row["industry"],
                "website": row["website"],
                "notes": row["notes"],
                "fit_score": row["fit_score"],
                "fit_level": row["fit_level"],
                "entity_type_id": row["entity_type_id"],
                "entity_type_label": row["entity_type_label"],
                "matched_case_title": row["matched_case_title"],
                "research_source": row["research_source"],
                "research_from_cache": bool(row["research_from_cache"]),
                "created_at": row["created_at"],
                "fit_bucket": _fit_bucket(row["fit_level"], row["fit_score"]),
                "industry_bucket": classify_industry(
                    row["industry"], row["notes"], row["company_name"]
                ),
                "themes": [],
            }
        )
    for item in items:
        item["themes"] = detect_themes(item)
    return items


def _compact_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item["id"],
        "rep_name": item["rep_name"],
        "company_name": item["company_name"],
        "industry": item["industry"],
        "fit_score": item["fit_score"],
        "fit_level": item["fit_level"],
        "entity_type_label": item["entity_type_label"],
        "matched_case_title": item["matched_case_title"],
        "industry_bucket": item["industry_bucket"],
        "industry_label": industry_label(item["industry_bucket"]),
        "created_at": item["created_at"],
        "notes_preview": (item.get("notes") or "")[:120],
    }


def _group_items(items: List[Dict[str, Any]], key_fn) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        buckets[key_fn(item)].append(item)

    groups = []
    for key in sorted(buckets.keys(), key=lambda k: (-len(buckets[k]), k)):
        group_items = buckets[key]
        companies = [i["company_name"] for i in group_items]
        reps = sorted({i["rep_name"] for i in group_items})
        groups.append(
            {
                "key": key,
                "count": len(group_items),
                "companies": companies,
                "reps": reps,
                "items": [_compact_item(i) for i in group_items],
            }
        )
    return groups


def _duplicated_companies(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_company: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        key = _norm_company(item["company_name"])
        if key:
            by_company[key].append(item)

    dupes = []
    for _key, rows in by_company.items():
        reps = sorted({r["rep_name"] for r in rows})
        if len(reps) > 1 or len(rows) > 1:
            dupes.append(
                {
                    "company_name": rows[0]["company_name"],
                    "search_count": len(rows),
                    "reps": reps,
                    "last_searched": rows[0]["created_at"],
                }
            )
    dupes.sort(key=lambda d: (-d["search_count"], d["company_name"].lower()))
    return dupes


def _rep_focus_lines(by_rep: List[Dict[str, Any]]) -> List[str]:
    lines = []
    for group in by_rep:
        rep = group["key"]
        industry_counts = Counter(i["industry_label"] for i in group["items"])
        top_industries = ", ".join(
            f"{label} ({count})" for label, count in industry_counts.most_common(3)
        )
        companies = ", ".join(group["companies"][:5])
        if len(group["companies"]) > 5:
            companies += f" +{len(group['companies']) - 5} more"
        lines.append(
            f"{rep} ran {group['count']} search(es) — focus: {top_industries or 'mixed'}. "
            f"Companies: {companies}."
        )
    return lines


def _manager_takeaways(
    items: List[Dict[str, Any]],
    dupes: List[Dict[str, Any]],
    high_fit: List[Dict[str, Any]],
    industry_groups: List[Dict[str, Any]],
) -> List[str]:
    if not items:
        return ["No team searches logged yet. Reps should enter their name and run reports."]

    takeaways = []
    reps = list_reps()
    takeaways.append(
        f"{len(reps)} rep(s) active · {len(items)} total searches · "
        f"{len({i['company_name'].lower() for i in items})} unique companies."
    )

    if high_fit:
        names = ", ".join(i["company_name"] for i in high_fit[:6])
        takeaways.append(f"High-fit accounts to prioritize: {names}.")

    promising = [g for g in industry_groups if g["count"] >= 2][:3]
    if promising:
        verticals = ", ".join(f"{g['key']} ({g['count']})" for g in promising)
        takeaways.append(f"Most active verticals: {verticals}.")

    if dupes:
        dupe_names = ", ".join(d["company_name"] for d in dupes[:4])
        takeaways.append(f"Possible duplicate work on: {dupe_names} — align before outreach.")

    supplier_count = sum(
        1 for i in items if i.get("entity_type_id") == "supplier_to_enterprises"
    )
    buyer_count = sum(1 for i in items if i.get("entity_type_id") == "enterprise_buyer")
    if supplier_count > buyer_count:
        takeaways.append("Team is leaning supplier-side — good for embed/differentiation plays.")
    elif buyer_count > supplier_count:
        takeaways.append("Team is leaning enterprise buyers — wallet/procurement plays dominate.")

    return takeaways


def build_management_insights(limit: int = 500) -> Dict[str, Any]:
    items = _fetch_all_activity(limit=limit)
    reps = list_reps()

    high_fit = [i for i in items if i["fit_bucket"] == "high"]
    medium_fit = [i for i in items if i["fit_bucket"] == "medium"]
    low_fit = [i for i in items if i["fit_bucket"] == "low"]

    dupes = _duplicated_companies(items)

    by_rep = _group_items(items, lambda i: i["rep_name"])
    for g in by_rep:
        g["title"] = f"{g['key']}'s searches"

    by_industry = _group_items(
        items, lambda i: industry_label(i["industry_bucket"])
    )
    for g in by_industry:
        g["title"] = g["key"]

    by_entity = _group_items(
        items,
        lambda i: ENTITY_SECTION_LABELS.get(
            i.get("entity_type_id") or "", i.get("entity_type_label") or "Unclassified"
        ),
    )
    for g in by_entity:
        g["title"] = g["key"]

    by_playbook = _group_items(
        items, lambda i: i.get("matched_case_title") or "No matched playbook"
    )
    for g in by_playbook:
        g["title"] = g["key"]

    theme_map: Dict[str, Dict[str, Any]] = {}
    for item in items:
        for theme_id in item["themes"]:
            label = next(l for tid, l, _ in THEME_RULES if tid == theme_id)
            if theme_id not in theme_map:
                theme_map[theme_id] = {
                    "theme_id": theme_id,
                    "label": label,
                    "count": 0,
                    "companies": [],
                    "reps": set(),
                }
            theme_map[theme_id]["count"] += 1
            theme_map[theme_id]["companies"].append(item["company_name"])
            theme_map[theme_id]["reps"].add(item["rep_name"])

    themes = []
    for theme in sorted(theme_map.values(), key=lambda t: -t["count"]):
        themes.append(
            {
                "theme_id": theme["theme_id"],
                "label": theme["label"],
                "count": theme["count"],
                "companies": list(dict.fromkeys(theme["companies"]))[:12],
                "reps": sorted(theme["reps"]),
            }
        )

    sections = [
        {
            "section_id": "by_rep",
            "title": "By rep",
            "description": "Who researched which companies and their focus areas.",
            "groups": by_rep,
        },
        {
            "section_id": "high_fit",
            "title": "High-fit companies",
            "description": "Accounts that scored High — prioritize for outreach.",
            "groups": [
                {
                    "key": "high_fit",
                    "title": "High fit",
                    "count": len(high_fit),
                    "companies": [i["company_name"] for i in high_fit],
                    "reps": sorted({i["rep_name"] for i in high_fit}),
                    "items": [_compact_item(i) for i in high_fit],
                }
            ]
            if high_fit
            else [],
        },
        {
            "section_id": "by_industry",
            "title": "By industry vertical",
            "description": "CPG, apparel, finance, logistics, travel, suppliers, and more.",
            "groups": by_industry,
        },
        {
            "section_id": "by_entity",
            "title": "By company role",
            "description": "Buyer vs supplier vs bank vs poor fit.",
            "groups": by_entity,
        },
        {
            "section_id": "by_playbook",
            "title": "By use case / playbook",
            "description": "Matched GTM cases: CSRD, supplier embed, SAF, logistics, etc.",
            "groups": by_playbook,
        },
    ]

    return {
        "summary": {
            "total_searches": len(items),
            "unique_companies": len({_norm_company(i["company_name"]) for i in items if i["company_name"]}),
            "unique_reps": len(reps),
            "high_fit_count": len(high_fit),
            "medium_fit_count": len(medium_fit),
            "low_fit_count": len(low_fit),
            "duplicated_companies": dupes,
        },
        "manager_takeaways": _manager_takeaways(items, dupes, high_fit, by_industry),
        "rep_focus": _rep_focus_lines(by_rep),
        "themes": themes,
        "sections": sections,
        "recent": [_compact_item(i) for i in items[:20]],
        "reps": reps,
    }
