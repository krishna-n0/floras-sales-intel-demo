"""Lead Research Agent — multi-path scrape, Jina extract, Tavily search, notes fallback."""

import os
import re
from typing import Any, List, Optional, Tuple, Union
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from business_research import gather_business_profile_sources
from research_store import get_cached_research, save_research
from entity_type import (
    apply_llm_entity_refinement_if_needed,
    classify_entity_type,
    get_research_config,
    refine_entity_classification,
)
from tavily import TavilyClient

load_dotenv()

WEAK_CONTENT_PATTERNS = (
    "hang tight",
    "sit tight",
    "routing to checkout",
    "please wait",
    "access denied",
    "enable javascript",
    "just a moment",
    "checking your browser",
    "verify you are human",
    "we've got our hands full",
    "automatically refresh",
    "hanging too loose",
    "page is hanging",
)

COMMON_PATHS = (
    "",
    "/sustainability",
    "/about",
    "/our-impact",
    "/impact",
    "/esg",
    "/about-us",
    "/company",
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_weak_content(text: str) -> bool:
    if not text or len(text) < 300:
        return True
    lower = text.lower()
    return any(pattern in lower for pattern in WEAK_CONTENT_PATTERNS)


def site_origin(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_website_html(url: str, max_chars: int = 4000) -> tuple[str, str]:
    try:
        normalized = normalize_url(url)
        if not normalized:
            return "", "No URL provided"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=15.0, follow_redirects=True) as http:
            response = http.get(normalized, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = clean_text(soup.get_text(" ", strip=True))
        if not text:
            return "", "Website returned no readable text"
        if is_weak_content(text):
            return "", "Website returned low-quality or bot-gate content"

        return text[:max_chars], ""
    except Exception as exc:
        return "", str(exc)


def fetch_jina(url: str, max_chars: int = 4000) -> tuple[str, str]:
    """Extract readable page text via Jina Reader API."""
    try:
        normalized = normalize_url(url)
        if not normalized:
            return "", "No URL provided"

        with httpx.Client(timeout=30.0, follow_redirects=True) as http:
            response = http.get(
                f"https://r.jina.ai/{normalized}",
                headers={"Accept": "text/plain"},
            )

        if response.status_code != 200:
            return "", f"Jina returned {response.status_code}"

        text = clean_text(response.text)
        if not text or is_weak_content(text):
            return "", "Jina returned low-quality or bot-gate content"

        return text[:max_chars], ""
    except Exception as exc:
        return "", str(exc)


def dedupe_urls(urls: list[str]) -> list[str]:
    """Return unique URLs, preserving first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        normalized = normalize_url(url).rstrip("/")
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def tavily_search_company(
    company_name: str,
    industry: str = "",
    query_focus: str = "",
    max_results: int = 3,
) -> list[dict]:
    """Search the web via Tavily for company context tuned to entity type."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    focus = query_focus or "sustainability ESG climate commitments impact report"
    query = f"{company_name} {industry} {focus}".strip()

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )
        return [
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "content": result.get("content"),
            }
            for result in response.get("results", [])
        ]
    except Exception:
        return []


def format_tavily_results(results: list[dict]) -> tuple[str, list[str]]:
    snippets = []
    urls = []
    for result in results:
        title = result.get("title") or ""
        content = result.get("content") or ""
        url = result.get("url") or ""
        if content:
            snippets.append(f"[{title}] {content}")
        if url:
            urls.append(url)

    if not snippets:
        return "", []

    return "\n\n".join(snippets)[:6000], urls


def fetch_website_multi_path(
    website: str,
    scrape_paths: Optional[Union[Tuple[str, ...], List[str]]] = None,
) -> tuple[str, str, list[str]]:
    """Try entity-type-specific paths with Jina, then HTML."""
    origin = site_origin(website)
    if not origin or origin == "://":
        return "", "", []

    paths = tuple(scrape_paths) if scrape_paths else COMMON_PATHS
    for path in paths:
        url = origin if not path else f"{origin.rstrip('/')}{path}"

        jina_text, _ = fetch_jina(url)
        if jina_text:
            return jina_text, "jina", [url]

        html_text, _ = fetch_website_html(url)
        if html_text:
            return html_text, "html", [url]

    return "", "", []


def gather_research_context(
    company_name: str,
    industry: str,
    website: str,
    notes: str,
    openai_client: Any = None,
    force_refresh: bool = False,
) -> dict:
    """Gather lead research from website paths, Tavily search, and user notes."""
    company_name = (company_name or "").strip()
    industry = (industry or "").strip()
    website = (website or "").strip()
    notes = (notes or "").strip()

    if not force_refresh:
        cached = get_cached_research(company_name, industry, website, notes)
        if cached:
            research = dict(cached["research"])
            research["from_cache"] = True
            research["cache_key"] = cached["cache_key"]
            research["cached_at"] = cached["cached_at"]
            research["last_used_at"] = cached["last_used_at"]
            research["cache_hit_count"] = cached["hit_count"]
            return research

    preview_entity = classify_entity_type(company_name, industry, notes)
    research_config = get_research_config(preview_entity)

    parts: list[str] = []
    source_urls: list[str] = []
    methods: list[str] = []

    entity_header = (
        f"Entity type preview (pre-scrape): {preview_entity.get('label')} "
        f"[{preview_entity.get('entity_type_id')}, confidence {preview_entity.get('confidence')}]"
    )
    parts.append(entity_header)
    methods.append("entity_preview")

    # Step 1: website scrape (paths tuned to entity type)
    web_method = ""
    if website:
        web_text, web_method, web_urls = fetch_website_multi_path(
            website,
            scrape_paths=research_config.get("scrape_paths"),
        )
        if web_text and not is_weak_content(web_text):
            label = "Jina Reader" if web_method == "jina" else "HTML scrape"
            parts.append(f"Website content via {label} ({web_urls[0]}):\n{web_text}")
            source_urls.extend(web_urls)
            methods.append(f"website_{web_method}")

    # Step 2: Tavily search tuned to entity type
    if company_name:
        tavily_results = tavily_search_company(
            company_name,
            industry,
            query_focus=research_config.get("tavily_query_focus", ""),
        )
        tavily_text, tavily_urls = format_tavily_results(tavily_results)
        if tavily_text:
            parts.append(f"Web search results (Tavily — sustainability focus):\n{tavily_text}")
            source_urls.extend(tavily_urls)
            methods.append("tavily")

    # Step 2b: business profile — SEC (free) → Wikipedia (free) → Tavily business (only if thin)
    if company_name:
        biz_text, biz_urls, biz_methods = gather_business_profile_sources(
            company_name,
            tavily_search_company,
            industry=industry,
            tavily_available=bool(os.getenv("TAVILY_API_KEY", "").strip()),
        )
        if biz_text:
            parts.append(biz_text)
            source_urls.extend(biz_urls)
            methods.extend(biz_methods)

    # Step 3: user notes
    if notes:
        parts.append(f"User-provided notes:\n{notes}")
        methods.append("notes")

    source_urls = dedupe_urls(source_urls)

    if len(parts) <= 1:
        source = "minimal"
        context = (
            "No website content, web search results, or user notes available. "
            "Use company name and industry only."
        )
        entity_classification = preview_entity
    else:
        context = "\n\n".join(parts)
        source = "_and_".join(methods) if methods else "minimal"
        full_entity = classify_entity_type(
            company_name,
            industry,
            notes,
            research_context=context,
        )
        entity_classification = refine_entity_classification(preview_entity, full_entity)

        # LLM refinement when rules are uncertain (low confidence or close runner-up)
        research_body = context
        entity_classification = apply_llm_entity_refinement_if_needed(
            openai_client,
            company_name,
            industry,
            notes,
            research_body,
            entity_classification,
        )

        method_label = entity_classification.get("classification_method", "rules")
        entity_summary = (
            f"Entity type (final — {method_label}): {entity_classification.get('label')} "
            f"[{entity_classification.get('entity_type_id')}, confidence "
            f"{entity_classification.get('confidence')}] — "
            f"{entity_classification.get('pitch_focus', '')}"
        )
        if entity_classification.get("llm_rationale"):
            entity_summary += f"\nLLM rationale: {entity_classification['llm_rationale']}"
        context = entity_summary + "\n\n" + context

    preview = context[:300] + "..." if len(context) > 300 else context
    result = {
        "source": source,
        "context": context,
        "preview": preview,
        "fetch_method": methods[0] if methods else "",
        "research_urls": source_urls[:12],
        "entity_classification": entity_classification,
        "entity_research_config": research_config,
        "from_cache": False,
    }
    cache_key = save_research(company_name, industry, website, notes, result)
    result["cache_key"] = cache_key
    return result


if __name__ == "__main__":
    print(tavily_search_company("Patagonia", "apparel"))
