"""Supplementary business-profile research: Wikipedia, SEC EDGAR, business-model web search."""

import re
from functools import lru_cache
from typing import List, Optional, Tuple
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

SEC_USER_AGENT = "FlorasSalesIntelDemo/1.0 (educational demo; contact: demo@floras.local)"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

BUSINESS_MODEL_QUERY = (
    "what does the company do business model customers suppliers products services"
)
# Skip extra Tavily business call when free sources already provide enough text.
MIN_BUSINESS_CONTEXT_CHARS = 500


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _sec_headers() -> dict:
    return {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}


def fetch_wikipedia_summary(company_name: str, max_chars: int = 2500) -> Tuple[str, str]:
    """Return (text, source_url) from Wikipedia REST summary, or empty if not found."""
    name = (company_name or "").strip()
    if not name:
        return "", ""

    try:
        headers = {"User-Agent": SEC_USER_AGENT}
        with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as http:
            search_resp = http.get(
                WIKIPEDIA_API,
                params={
                    "action": "opensearch",
                    "search": name,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
            )
            search_resp.raise_for_status()
            results = search_resp.json()
            if len(results) < 4 or not results[1]:
                return "", ""

            title = results[1][0]
            page_url = results[3][0] if results[3] else ""
            summary_resp = http.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
            )
            if summary_resp.status_code != 200:
                return "", ""

            data = summary_resp.json()
            extract = clean_text(data.get("extract", ""))
            description = clean_text(data.get("description", ""))
            combined = f"{title}"
            if description:
                combined += f" — {description}"
            if extract:
                combined += f". {extract}"
            if not combined:
                return "", ""

            return combined[:max_chars], page_url or data.get("content_urls", {}).get("desktop", {}).get("page", "")
    except Exception:
        return "", ""


@lru_cache(maxsize=1)
def _load_sec_tickers() -> List[dict]:
    try:
        with httpx.Client(timeout=20.0, headers=_sec_headers()) as http:
            response = http.get(SEC_TICKERS_URL)
            response.raise_for_status()
            payload = response.json()
        if isinstance(payload, dict):
            return list(payload.values())
    except Exception:
        pass
    return []


def _match_sec_ticker(company_name: str) -> Optional[str]:
    """Return zero-padded CIK string if a reasonable SEC ticker match is found."""
    name_norm = re.sub(r"[^a-z0-9 ]", "", (company_name or "").lower()).strip()
    if not name_norm:
        return None

    tokens = [t for t in name_norm.split() if len(t) > 2]
    if not tokens:
        return None

    best_cik = None
    best_score = 0
    for entry in _load_sec_tickers():
        title = re.sub(r"[^a-z0-9 ]", "", (entry.get("title") or "").lower())
        if not title:
            continue
        if name_norm in title or title in name_norm:
            return str(entry.get("cik_str", "")).zfill(10)
        overlap = sum(1 for token in tokens if token in title)
        if overlap > best_score:
            best_score = overlap
            best_cik = str(entry.get("cik_str", "")).zfill(10)

    if best_score >= max(1, len(tokens) - 1):
        return best_cik
    return None


def _extract_business_section(text: str, max_chars: int = 3500) -> str:
    """Pull Item 1 Business-ish content from filing text."""
    text = clean_text(text)
    if not text:
        return ""

    patterns = (
        r"item\s*1\.?\s*business[:\s-]*(.*?)(item\s*1a\.|item\s*2\.|$)",
        r"description\s+of\s+business[:\s-]*(.*?)(risk\s+factors|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            section = clean_text(match.group(1))
            if len(section) > 200:
                return section[:max_chars]

    return text[:max_chars]


def fetch_sec_business_profile(company_name: str, max_chars: int = 3500) -> Tuple[str, str]:
    """Fetch latest 10-K business section excerpt for US public companies."""
    cik = _match_sec_ticker(company_name)
    if not cik:
        return "", ""

    try:
        with httpx.Client(timeout=25.0, headers=_sec_headers(), follow_redirects=True) as http:
            submissions_resp = http.get(SEC_SUBMISSIONS_URL.format(cik=cik))
            submissions_resp.raise_for_status()
            submissions = submissions_resp.json()

            recent = submissions.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])

            filing_index = next((i for i, form in enumerate(forms) if form == "10-K"), None)
            if filing_index is None:
                return "", ""

            accession = accessions[filing_index].replace("-", "")
            primary_doc = primary_docs[filing_index]
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession}/{primary_doc}"
            )

            doc_resp = http.get(doc_url, headers={"User-Agent": SEC_USER_AGENT})
            doc_resp.raise_for_status()

            soup = BeautifulSoup(doc_resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            raw_text = clean_text(soup.get_text(" ", strip=True))
            business_text = _extract_business_section(raw_text, max_chars=max_chars)
            if not business_text:
                return "", ""

            company_title = submissions.get("name", company_name)
            return (
                f"SEC EDGAR 10-K business profile ({company_title}, CIK {cik}):\n{business_text}",
                doc_url,
            )
    except Exception:
        return "", ""


def gather_business_profile_sources(
    company_name: str,
    tavily_search_fn,
    industry: str = "",
    *,
    tavily_available: bool = False,
) -> Tuple[str, List[str], List[str]]:
    """
    Collect business hierarchy context with minimal cost:
    1. SEC 10-K Item 1 (free, US public) — tried first
    2. Wikipedia (free) — only if SEC misses
    3. Tavily business query — same TAVILY_API_KEY as ESG search; only if still thin

    tavily_search_fn: callable(company_name, industry, query_focus, max_results) -> list[dict]
    """
    parts: List[str] = []
    urls: List[str] = []
    methods: List[str] = []

    sec_text, sec_url = fetch_sec_business_profile(company_name)
    if sec_text:
        parts.append(sec_text)
        if sec_url:
            urls.append(sec_url)
        methods.append("sec_edgar")

    wiki_text, wiki_url = "", ""
    if not sec_text:
        wiki_text, wiki_url = fetch_wikipedia_summary(company_name)
        if wiki_text:
            parts.append(f"Wikipedia company summary:\n{wiki_text}")
            if wiki_url:
                urls.append(wiki_url)
            methods.append("wikipedia")

    business_chars = len(sec_text) + len(wiki_text)
    need_tavily_business = (
        tavily_available
        and company_name
        and tavily_search_fn
        and business_chars < MIN_BUSINESS_CONTEXT_CHARS
    )

    if need_tavily_business:
        biz_results = tavily_search_fn(
            company_name,
            industry,
            BUSINESS_MODEL_QUERY,
            max_results=3,
        )
        snippets = []
        for result in biz_results:
            title = result.get("title") or ""
            content = result.get("content") or ""
            url = result.get("url") or ""
            if content:
                snippets.append(f"[{title}] {content}")
            if url:
                urls.append(url)
        if snippets:
            parts.append("Business model web search (Tavily):\n" + "\n\n".join(snippets)[:3000])
            methods.append("tavily_business")

    if not parts:
        return "", [], []

    return "\n\n".join(parts), urls, methods
