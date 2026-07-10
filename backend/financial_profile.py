"""Optional financial profile for public companies — FMP or Alpha Vantage."""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

load_dotenv()

FMP_SEARCH_URL = "https://financialmodelingprep.com/stable/search-name"
FMP_INCOME_URL = "https://financialmodelingprep.com/stable/income-statement"
FMP_BALANCE_URL = "https://financialmodelingprep.com/stable/balance-sheet-statement"
ALPHA_OVERVIEW_URL = "https://www.alphavantage.co/query"

FMP_SEARCH_SYMBOL_URL = "https://financialmodelingprep.com/stable/search-symbol"

US_EXCHANGES = frozenset({"NASDAQ", "NYSE", "AMEX", "NASDAQ GLOBAL SELECT", "NYSE ARCA", "BATS"})
NEGATIVE_NAME_TERMS = (
    "etf",
    "bond fund",
    " bdc",
    "mutual fund",
    "trust",
    "wisdomtree",
    "high yield",
    "instl",
    "physical gold",
    "fund class",
    "tracker fund",
    "equity insights",
)

KNOWN_TICKERS = {
    "pepsi": "PEP",
    "pepsico": "PEP",
    "salesforce": "CRM",
    "goldman sachs": "GS",
    "goldman": "GS",
    "nike": "NKE",
    "unilever": "UL",
    "maersk": "AMKBY",
}

# Public peer comps when the lead has no ticker (private / non-US) — keyed by industry signals.
INDUSTRY_PUBLIC_COMPS: Tuple[Dict[str, Any], ...] = (
    {
        "bucket": "apparel",
        "label": "Apparel & outdoor",
        "keywords": ("apparel", "outdoor", "fashion", "clothing", "footwear", "sportswear", "retail brand"),
        "symbol": "COLM",
        "name": "Columbia Sportswear",
    },
    {
        "bucket": "cpg_retail",
        "label": "CPG & retail",
        "keywords": ("food", "beverage", "consumer goods", "cpg", "fmcg", "grocery", "supermarket", "snack"),
        "symbol": "KO",
        "name": "Coca-Cola",
    },
    {
        "bucket": "packaging_supplier",
        "label": "Packaging & industrial suppliers",
        "keywords": ("packaging", "container", "can manufacturer", "industrial supplier", "b2b supplier"),
        "symbol": "BLL",
        "name": "Ball Corporation",
    },
    {
        "bucket": "logistics",
        "label": "Logistics & freight",
        "keywords": ("logistics", "freight", "shipping", "3pl", "carrier", "transportation", "maritime"),
        "symbol": "FDX",
        "name": "FedEx",
    },
    {
        "bucket": "travel",
        "label": "Travel & aviation",
        "keywords": ("aviation", "airline", "hotel", "hospitality", "travel", "saf"),
        "symbol": "DAL",
        "name": "Delta Air Lines",
    },
    {
        "bucket": "software",
        "label": "Enterprise software",
        "keywords": ("software", "saas", "cloud", "enterprise software", "technology platform"),
        "symbol": "CRM",
        "name": "Salesforce",
    },
    {
        "bucket": "finance",
        "label": "Financial services",
        "keywords": ("bank", "financial services", "fintech", "investment", "capital markets", "insurance"),
        "symbol": "GS",
        "name": "Goldman Sachs",
    },
    {
        "bucket": "beauty",
        "label": "Beauty & personal care",
        "keywords": ("beauty", "cosmetic", "skincare", "personal care", "refill"),
        "symbol": "EL",
        "name": "Estée Lauder",
    },
)


def _financial_fit_level(gross_margin: Optional[float]) -> str:
    if gross_margin is None:
        return "unknown"
    if gross_margin >= 40:
        return "strong"
    if gross_margin >= 25:
        return "moderate"
    return "weak"


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "" or value == "None":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round((numerator / denominator) * 100, 1)


def _margin_interpretation(gross_margin: Optional[float], *, is_comp: bool = False) -> str:
    prefix = "Peer comp gross margin — " if is_comp else ""
    if gross_margin is None:
        return "Margin data unavailable — do not infer financial fit from revenue alone."
    if gross_margin >= 40:
        return (
            prefix
            + "Strong gross margin — sector peers likely able to absorb transaction-embedded Floras costs."
        )
    if gross_margin >= 25:
        return prefix + "Moderate gross margin — Floras fit depends on volume and procurement leverage."
    return prefix + "Lower gross margin — prioritize high-volume transaction use cases if pursuing."


def _norm_haystack(*parts: str) -> str:
    return re.sub(r"\s+", " ", " ".join(parts).lower()).strip()


def _pick_public_comp(industry: str, company_name: str) -> Optional[Dict[str, Any]]:
    haystack = _norm_haystack(industry, company_name)
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for comp in INDUSTRY_PUBLIC_COMPS:
        score = sum(1 for kw in comp["keywords"] if kw in haystack)
        if score > best_score:
            best_score = score
            best = comp
    return best if best_score > 0 else None


def _infer_listing_type(api_configured: bool, direct: Dict[str, Any]) -> str:
    if direct.get("available"):
        return "public"
    if not api_configured:
        return "unknown"
    reason = (direct.get("reason") or "").lower()
    if "402" in reason or "rate cap" in reason or "rate limit" in reason:
        return "unknown"
    if "no ticker" in reason or "no income" in reason:
        return "private"
    return "unknown"


def financial_api_configured() -> bool:
    return bool(
        os.getenv("FMP_API_KEY", "").strip()
        or os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    )


def _score_search_item(item: dict, name_norm: str) -> int:
    symbol = str(item.get("symbol") or "")
    item_name = re.sub(r"[^a-z0-9 ]", "", (item.get("name") or "").lower())
    exchange = (item.get("exchange") or item.get("exchangeFullName") or "").upper()
    tokens = [t for t in name_norm.split() if len(t) > 2]
    token_hits = sum(1 for t in tokens if t in item_name)

    score = 0
    if name_norm and (name_norm in item_name or item_name in name_norm):
        score += 5
    score += token_hits * 2
    if len(tokens) >= 2 and token_hits < 2:
        score -= 5
    if exchange in US_EXCHANGES or "NASDAQ" in exchange or "NYSE" in exchange:
        score += 4
    if symbol and "." not in symbol and len(symbol) <= 5:
        score += 3
    if any(term in item_name for term in NEGATIVE_NAME_TERMS):
        score -= 6
    return score


def _fmp_search(company_name: str, api_key: str) -> List[dict]:
    results: List[dict] = []
    name = (company_name or "").strip()
    if not name:
        return results

    try:
        with httpx.Client(timeout=12.0) as http:
            by_name = http.get(
                FMP_SEARCH_URL,
                params={"query": name, "apikey": api_key},
            )
            by_name.raise_for_status()
            if isinstance(by_name.json(), list):
                results.extend(by_name.json())

            tickerish = re.fullmatch(r"[A-Za-z]{1,5}", name)
            symbol_queries = []
            if tickerish:
                symbol_queries.append(name.upper())
            else:
                parts = name.split()
                if parts:
                    symbol_queries.append(parts[0])
                if len(parts) >= 2:
                    symbol_queries.append(" ".join(parts[:2]))

            for symbol_query in symbol_queries:
                by_symbol = http.get(
                    FMP_SEARCH_SYMBOL_URL,
                    params={"query": symbol_query, "apikey": api_key},
                )
                if by_symbol.status_code == 200 and isinstance(by_symbol.json(), list):
                    results.extend(by_symbol.json())
    except Exception:
        pass

    seen = set()
    unique: List[dict] = []
    for item in results:
        symbol = item.get("symbol")
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        unique.append(item)
    return unique


def _resolve_fmp_symbol(company_name: str, api_key: str) -> Optional[str]:
    name_norm = re.sub(r"[^a-z0-9 ]", "", company_name.lower()).strip()
    if name_norm in KNOWN_TICKERS:
        return KNOWN_TICKERS[name_norm]

    results = _fmp_search(company_name, api_key)
    if not results:
        return None

    ranked = sorted(results, key=lambda item: _score_search_item(item, name_norm), reverse=True)
    best = ranked[0]
    if _score_search_item(best, name_norm) < 4:
        return None
    return str(best.get("symbol")) if best.get("symbol") else None


def _margins_from_fmp_rows(income: dict, balance: dict) -> Dict[str, Any]:
    revenue = _safe_float(income.get("revenue"))
    gross_profit = _safe_float(income.get("grossProfit"))
    operating_income = _safe_float(income.get("operatingIncome"))
    net_income = _safe_float(income.get("netIncome"))
    total_assets = _safe_float(balance.get("totalAssets"))

    gross_margin = _pct(gross_profit, revenue)
    operating_margin = _pct(operating_income, revenue)
    roa = _pct(net_income, total_assets)

    return {
        "fiscal_period": income.get("date") or income.get("calendarYear") or "",
        "revenue": revenue,
        "gross_margin_pct": gross_margin,
        "operating_margin_pct": operating_margin,
        "roa_pct": roa,
        "financial_fit_level": _financial_fit_level(gross_margin),
    }


def _fetch_fmp_by_symbol(symbol: str, api_key: str) -> Dict[str, Any]:
    try:
        with httpx.Client(timeout=15.0) as http:
            income_resp = http.get(
                FMP_INCOME_URL,
                params={"symbol": symbol, "limit": 1, "apikey": api_key},
            )
            balance_resp = http.get(
                FMP_BALANCE_URL,
                params={"symbol": symbol, "limit": 1, "apikey": api_key},
            )
            income_resp.raise_for_status()
            balance_resp.raise_for_status()
            income_rows = income_resp.json()
            balance_rows = balance_resp.json()

        if not income_rows:
            return {"available": False, "source": "fmp", "symbol": symbol, "reason": "No income statement"}

        income = income_rows[0]
        balance = balance_rows[0] if balance_rows else {}
        margins = _margins_from_fmp_rows(income, balance)

        return {
            "available": True,
            "source": "fmp",
            "symbol": symbol,
            **margins,
            "interpretation": _margin_interpretation(margins.get("gross_margin_pct")),
        }
    except Exception as exc:
        reason = str(exc)
        if "402" in reason:
            reason = "FMP plan limit or rate cap reached (402). Retry later or check your FMP subscription."
        return {"available": False, "source": "fmp", "reason": reason}


def _fetch_fmp_profile(company_name: str, api_key: str) -> Dict[str, Any]:
    symbol = _resolve_fmp_symbol(company_name, api_key)
    if not symbol:
        return {"available": False, "source": "fmp", "reason": "No ticker match — likely private or non-US listed"}
    return _fetch_fmp_by_symbol(symbol, api_key)


def _fetch_alpha_vantage_profile(company_name: str, api_key: str) -> Dict[str, Any]:
    symbol = company_name.upper().strip()
    if not re.fullmatch(r"[A-Z.\-]{1,8}", symbol):
        return {"available": False, "source": "alpha_vantage", "reason": "Pass ticker for Alpha Vantage"}

    try:
        with httpx.Client(timeout=15.0) as http:
            response = http.get(
                ALPHA_OVERVIEW_URL,
                params={"function": "OVERVIEW", "symbol": symbol, "apikey": api_key},
            )
            response.raise_for_status()
            data = response.json()

        if not data or data.get("Symbol") is None:
            return {"available": False, "source": "alpha_vantage", "reason": "No overview data"}

        gross_profit = _safe_float(data.get("GrossProfitTTM"))
        revenue = _safe_float(data.get("RevenueTTM"))
        operating_margin = _safe_float(data.get("OperatingMarginTTM"))
        if operating_margin is not None:
            operating_margin = round(operating_margin * 100, 1)

        gross_margin_pct = _pct(gross_profit, revenue)

        roa_pct = _safe_float(data.get("ReturnOnAssetsTTM"))
        if roa_pct is not None:
            roa_pct = round(roa_pct * 100, 1)

        return {
            "available": True,
            "source": "alpha_vantage",
            "symbol": data.get("Symbol"),
            "fiscal_period": data.get("LatestQuarter") or "",
            "revenue": revenue,
            "gross_margin_pct": gross_margin_pct,
            "operating_margin_pct": operating_margin,
            "roa_pct": roa_pct,
            "financial_fit_level": _financial_fit_level(gross_margin_pct),
            "interpretation": _margin_interpretation(gross_margin_pct),
        }
    except Exception as exc:
        return {"available": False, "source": "alpha_vantage", "reason": str(exc)}


def _build_public_comp(
    company_name: str,
    industry: str,
    fmp_key: str,
) -> Dict[str, Any]:
    comp = _pick_public_comp(industry, company_name)
    if not comp or not fmp_key:
        return {"available": False}

    profile = _fetch_fmp_by_symbol(comp["symbol"], fmp_key)
    if not profile.get("available"):
        return {"available": False, "reason": profile.get("reason", "")}

    return {
        "available": True,
        "bucket": comp["bucket"],
        "industry_label": comp["label"],
        "symbol": comp["symbol"],
        "name": comp["name"],
        "gross_margin_pct": profile.get("gross_margin_pct"),
        "operating_margin_pct": profile.get("operating_margin_pct"),
        "roa_pct": profile.get("roa_pct"),
        "financial_fit_level": profile.get("financial_fit_level"),
        "interpretation": _margin_interpretation(profile.get("gross_margin_pct"), is_comp=True),
        "disclaimer": (
            f"Public peer benchmark ({comp['name']}, {comp['symbol']}) — "
            f"NOT actual financials for {company_name}. Use for sector capacity signal only."
        ),
    }


def fetch_financial_profile(company_name: str, industry: str = "") -> Dict[str, Any]:
    """
    Fetch financial margins for public companies via FMP/AV.
    When no ticker match (likely private), suggest a public peer comp by industry.
    """
    name = (company_name or "").strip()
    industry = (industry or "").strip()
    api_ok = financial_api_configured()

    if not name:
        return {
            "available": False,
            "company_listing_type": "unknown",
            "reason": "No company name",
            "public_comp": {"available": False},
        }

    fmp_key = os.getenv("FMP_API_KEY", "").strip()
    direct: Dict[str, Any] = {"available": False, "reason": ""}
    fmp_last_reason = ""

    if fmp_key:
        direct = _fetch_fmp_profile(name, fmp_key)
        if direct.get("available"):
            return {
                **direct,
                "company_listing_type": "public",
                "public_comp": {"available": False},
            }
        fmp_last_reason = direct.get("reason", "")

    alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    if alpha_key:
        direct = _fetch_alpha_vantage_profile(name, alpha_key)
        if direct.get("available"):
            return {
                **direct,
                "company_listing_type": "public",
                "public_comp": {"available": False},
            }
        fmp_last_reason = fmp_last_reason or direct.get("reason", "")

    listing_type = _infer_listing_type(api_ok, direct)
    reason = fmp_last_reason or direct.get("reason", "")

    industry_comp = _pick_public_comp(industry, name)
    no_ticker = "no ticker" in reason.lower()
    rate_limited = "402" in reason or "rate cap" in reason.lower()

    # Peer comp: private companies, no ticker match, or rate-limited direct lookup with industry context
    should_try_comp = bool(
        fmp_key
        and industry_comp
        and not direct.get("available")
        and (listing_type == "private" or no_ticker or (rate_limited and industry))
    )
    public_comp = _build_public_comp(name, industry, fmp_key) if should_try_comp else {"available": False}

    if should_try_comp and not public_comp.get("available") and industry_comp:
        public_comp = {
            "available": False,
            "symbol": industry_comp["symbol"],
            "name": industry_comp["name"],
            "industry_label": industry_comp["label"],
            "disclaimer": (
                f"Suggested public peer for {name}: {industry_comp['name']} ({industry_comp['symbol']}). "
                "Margin fetch failed — may be FMP rate limit (402). Retry later."
            ),
            "reason": public_comp.get("reason", ""),
        }
        if listing_type != "public":
            listing_type = "private"

    if public_comp.get("available") and listing_type != "public":
        listing_type = "private"

    return {
        "available": False,
        "company_listing_type": listing_type,
        "reason": reason
        or "No financial API key configured (optional: FMP_API_KEY or ALPHA_VANTAGE_API_KEY)",
        "public_comp": public_comp,
    }


def has_usable_financial_signal(profile: Dict[str, Any]) -> bool:
    return bool(profile.get("available") or (profile.get("public_comp") or {}).get("available"))


def format_financial_profile_for_prompt(profile: Dict[str, Any]) -> str:
    if profile.get("available"):
        revenue = profile.get("revenue")
        revenue_str = f"${revenue:,.0f}" if isinstance(revenue, (int, float)) else "N/A"
        return f"""
FINANCIAL PROFILE (direct public company data from {profile.get("source", "API")}, symbol {profile.get("symbol", "N/A")}):
- Listing type: public
- Fiscal period: {profile.get("fiscal_period") or "N/A"}
- Revenue: {revenue_str}
- Gross margin: {profile.get("gross_margin_pct") or "N/A"}%
- Operating margin: {profile.get("operating_margin_pct") or "N/A"}%
- Return on assets (ROA): {profile.get("roa_pct") or "N/A"}%
- Financial fit level: {profile.get("financial_fit_level", "unknown")}
- BD interpretation: {profile.get("interpretation", "")}

Use gross margin as a primary signal for fit_score and outreach_pitch (implication, not raw stats in pitch).
"""

    comp = profile.get("public_comp") or {}
    if comp.get("available"):
        return f"""
FINANCIAL PROFILE — TARGET IS LIKELY PRIVATE (no public ticker). PUBLIC PEER BENCHMARK ONLY:
- Listing type: private (no direct margins for this company)
- Peer comp: {comp.get("name")} ({comp.get("symbol")}) — {comp.get("industry_label", "")}
- {comp.get("disclaimer", "")}
- Gross margin (peer): {comp.get("gross_margin_pct") or "N/A"}%
- Operating margin (peer): {comp.get("operating_margin_pct") or "N/A"}%
- ROA (peer): {comp.get("roa_pct") or "N/A"}%
- Financial fit level (peer): {comp.get("financial_fit_level", "unknown")}
- BD interpretation: {comp.get("interpretation", "")}

Use peer margins as a SECTOR capacity signal only — never state they are the target's financials.
Note in risks_or_unknowns that direct financials are unavailable and peer comp was used.
"""

    listing = profile.get("company_listing_type", "unknown")
    if listing == "private":
        return f"""
FINANCIAL PROFILE — Listing type: private (no public ticker match).
- Direct margins unavailable. No industry peer comp matched from industry/company text.
- Note in risks_or_unknowns; do not invent margins.
"""
    return ""
