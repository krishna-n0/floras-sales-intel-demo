"""Quality Reviewer Agent — critiques the Proposal Agent output in a second LLM step."""

import json
from typing import Optional

from financial_profile import format_financial_profile_for_prompt
from kb import load_floras_context


def parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return json.loads(content)


def review_proposal(
    client,
    proposal: dict,
    research: dict,
    entity_classification: Optional[dict] = None,
    financial_profile: Optional[dict] = None,
) -> dict:
    """Second OpenAI call: review proposal for specificity, grounding, and gaps."""
    floras_context = load_floras_context()
    entity_block = ""
    if entity_classification:
        entity_block = f"""
Lead entity type classification:
- Type: {entity_classification.get('label')} ({entity_classification.get('entity_type_id')})
- Hierarchy: {entity_classification.get('hierarchy_level')}
- Pitch focus: {entity_classification.get('pitch_focus')}
- Outreach target: {entity_classification.get('outreach_target')}
"""
    financial_block = format_financial_profile_for_prompt(financial_profile or {})
    prompt = f"""
You are the Quality Reviewer Agent for Floras Sales Intelligence.

A Proposal Agent drafted this sales intelligence report. Your job is to critique it — not rewrite the whole thing.

Use this Floras company knowledge base to judge whether the proposal correctly represents
what Floras does and whether fit scoring aligns with Floras' ideal customer profile:

FLORAS COMPANY KNOWLEDGE BASE:
{floras_context}
{entity_block}
{financial_block}

Research that was available:
{research.get("context", "")[:2000]}

Proposal to review:
{json.dumps(proposal, indent=2)}

Return ONLY valid JSON with this exact structure:
{{
  "quality_rating": "Good/Fair/Needs Improvement",
  "quality_review": "2-4 sentence overall critique of the proposal",
  "review_improvements": ["specific improvement 1", "specific improvement 2"]
}}

Check for:
- Is the use case specific to this company or generic?
- Are claims grounded in the research or invented?
- Is the pitch aligned with the lead entity type (buyer vs supplier vs financial issuer)?
- If financial data exists: is gross margin reflected in fit_score and outreach (implication, not stat dump)?
- Does outreach_pitch include economic capacity when financials support pursuit?
- Does the proposal use Floras mechanisms (wallet, supplier Floras, project allocation, certificates)?
- Is the fit score justified against Floras' ICP and the research signals?
- What's missing before this is customer-ready?
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a critical B2B sales quality reviewer. Return only valid JSON. Do not use markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    content = completion.choices[0].message.content or ""
    return parse_json_response(content)
