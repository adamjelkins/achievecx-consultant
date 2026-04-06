"""
maturity_assessment.py

AI Maturity Assessment engine.

Architecture:
  - Rules-based scoring: deterministic, defensible, consistent across runs
  - GPT rationale: one call for all flows, produces plain-English narrative
  - Session state: results cached under st.session_state.assessment

Scoring model (each axis 0-100):
  automation_potential  — how automatable is this flow type?
  volume_impact         — how much contact volume does it typically represent?
  effort_score          — inverse of implementation effort (easier = higher)

  flow_ai_score = weighted average of the three axes
  business_ai_score = average of all confirmed flow scores

Crawl / Walk / Run:
  Run   >= 70   Full AI automation opportunity
  Walk  40-69   AI-assisted, partial automation
  Crawl  < 40   Manual today, foundational work needed
"""

import json
import os
try:
    import streamlit as st
except ImportError:
    import types, sys
    st = types.ModuleType('streamlit')
    st.session_state = types.SimpleNamespace()
    st.spinner = lambda x: __import__('contextlib').nullcontext()
    st.error = lambda x: None
    st.warning = lambda x: None
    st.info = lambda x: None
    sys.modules['streamlit'] = st
from pathlib import Path
from datetime import datetime

import openai
from dotenv import load_dotenv

load_dotenv()

_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------------------------------------
# Rules tables
# --------------------------------------------------

# Automation potential by flow category (0-100)
CATEGORY_AUTOMATION = {
    "Orders":        88,
    "Notifications": 92,
    "Billing":       72,
    "Support":       60,
    "Scheduling":    78,
    "Account":       80,
    "Healthcare":    55,
    "Financial":     62,
    "Sales":         58,
    "Marketing":     85,
    "Unknown":       60,
}

# Volume impact by flow category — how common is this in a contact center?
CATEGORY_VOLUME = {
    "Orders":        85,
    "Notifications": 70,
    "Billing":       78,
    "Support":       90,
    "Scheduling":    65,
    "Account":       72,
    "Healthcare":    68,
    "Financial":     75,
    "Sales":         60,
    "Marketing":     55,
    "Unknown":       60,
}

# Implementation effort by category — inverse (easier = higher score)
CATEGORY_EFFORT = {
    "Orders":        82,
    "Notifications": 90,
    "Billing":       65,
    "Support":       58,
    "Scheduling":    75,
    "Account":       70,
    "Healthcare":    45,
    "Financial":     48,
    "Sales":         62,
    "Marketing":     80,
    "Unknown":       60,
}

# Industry modifiers — some industries are further ahead on AI
INDUSTRY_MODIFIER = {
    "Retail":                 1.05,
    "Technology":             1.10,
    "Financial Services":     1.00,
    "Telecom":                1.08,
    "Healthcare":             0.85,
    "Insurance":              0.90,
    "Hospitality":            0.95,
    "Logistics":              1.02,
    "Education":              0.88,
    "Government":             0.80,
    "Manufacturing":          0.92,
    "Professional Services":  0.95,
    "Other":                  1.00,
    "Unknown":                1.00,
}

# Score weights
W_AUTOMATION = 0.45
W_VOLUME     = 0.30
W_EFFORT     = 0.25


# --------------------------------------------------
# Rules scoring
# --------------------------------------------------

def _score_flow(flow: dict, industry: str) -> dict:
    """
    Score a single flow using the rules tables.
    Returns a scored flow dict.
    """
    category = flow.get("category", "Unknown")
    confidence = float(flow.get("confidence", 0.7))

    automation = CATEGORY_AUTOMATION.get(category, 60)
    volume     = CATEGORY_VOLUME.get(category, 60)
    effort     = CATEGORY_EFFORT.get(category, 60)

    # Apply industry modifier
    modifier = INDUSTRY_MODIFIER.get(industry, 1.0)

    # Weighted composite
    raw_score = (
        automation * W_AUTOMATION +
        volume     * W_VOLUME +
        effort     * W_EFFORT
    ) * modifier

    # Confidence nudge — higher confidence in detection = slight boost
    confidence_boost = (confidence - 0.5) * 8  # -4 to +4 range
    ai_score = min(100, max(0, round(raw_score + confidence_boost)))

    # Crawl / Walk / Run
    if ai_score >= 70:
        cwr = "Run"
    elif ai_score >= 40:
        cwr = "Walk"
    else:
        cwr = "Crawl"

    return {
        "flow_id":             flow["flow_id"],
        "flow_name":           flow.get("flow_name", flow["flow_id"]),
        "category":            category,
        "crawl_walk_run":      cwr,
        "ai_score":            ai_score,
        "automation_potential": round(automation * modifier),
        "volume_impact":       round(volume * modifier),
        "effort_score":        round(effort * modifier),
        "quick_win":           cwr == "Run" and effort >= 70,
        "rationale":           "",   # filled by GPT call
    }


def _score_all_flows(confirmed_flows: list, industry: str) -> list:
    """Score all confirmed flows."""
    return [_score_flow(f, industry) for f in confirmed_flows]


def _business_ai_score(scored_flows: list) -> int:
    """Weighted average of all flow AI scores."""
    if not scored_flows:
        return 0
    total = sum(f["ai_score"] for f in scored_flows)
    return round(total / len(scored_flows))


def _score_label(score: int) -> tuple:
    """Returns (label, color) for a business AI score."""
    if score >= 80:
        return "Exceptional Opportunity", "#22c55e"
    elif score >= 65:
        return "Strong Opportunity",      "#6366f1"
    elif score >= 50:
        return "Good Opportunity",        "#f59e0b"
    elif score >= 35:
        return "Emerging Opportunity",    "#f97316"
    else:
        return "Early Stage",             "#52525b"


# --------------------------------------------------
# GPT rationale (one call for all flows)
# --------------------------------------------------

def _fetch_rationale(scored_flows: list, business_profile: dict) -> dict:
    """
    Single GPT call to generate plain-English quick-win rationale
    for Run-classified flows only (highest value, lowest verbosity).

    Returns dict keyed by flow_id → rationale string.
    """
    run_flows = [f for f in scored_flows if f["crawl_walk_run"] == "Run"]
    if not run_flows:
        # Fall back to all Walk flows if no Run flows
        run_flows = [f for f in scored_flows if f["crawl_walk_run"] == "Walk"]
    if not run_flows:
        return {}

    company     = business_profile.get("company_name", "this company")
    industry    = business_profile.get("industry", "Unknown")
    description = business_profile.get("description", "")

    flows_summary = "\n".join([
        f"- {f['flow_name']} (score: {f['ai_score']}, category: {f['category']})"
        for f in run_flows
    ])

    prompt = f"""You are a CX AI strategy consultant.

Business context:
- Company: {company}
- Industry: {industry}
- Description: {description}

These customer interaction flows scored highest for AI automation opportunity:
{flows_summary}

For each flow, write ONE concise sentence (max 20 words) explaining the key AI opportunity.
Be specific to {industry}. Avoid generic phrases like "improves efficiency."

Return ONLY a valid JSON object keyed by exact flow name:
{{
  "Order Inquiry": "IVA with real-time order lookup can contain 80% of inquiries without agent involvement.",
  "Return Process": "..."
}}

Return ONLY the JSON. No markdown."""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()

        # Strip fences
        if raw.startswith("```"):
            raw = "\n".join(
                l for l in raw.splitlines()
                if not l.strip().startswith("```")
            ).strip()

        # Find JSON object
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return {}

        parsed = json.loads(raw[start:end])
        # Key by flow_name → rationale
        return {k: v for k, v in parsed.items() if isinstance(v, str)}

    except Exception as e:
        print(f"[maturity_assessment] GPT rationale failed: {e}")
        return {}


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def run_assessment(confirmed_flows: list, business_profile: dict) -> dict:
    """
    Run the full maturity assessment.

    Args:
        confirmed_flows: list of flow dicts with flow_id, flow_name, category
        business_profile: dict from st.session_state.business_profile

    Returns:
        {
            "scored_flows": [...],
            "business_ai_score": int,
            "score_label": str,
            "score_color": str,
            "quick_wins": [...],
            "walk_flows": [...],
            "crawl_flows": [...],
            "assessed_at": str,
        }
    """
    industry = business_profile.get("industry", "Unknown")

    # Step 1 — rules scoring
    scored_flows = _score_all_flows(confirmed_flows, industry)

    # Step 2 — GPT rationale for top flows
    rationale_map = _fetch_rationale(scored_flows, business_profile)

    # Inject rationale into scored flows
    for f in scored_flows:
        f["rationale"] = rationale_map.get(f["flow_name"], "")

    # Step 3 — aggregate score
    biz_score = _business_ai_score(scored_flows)
    label, color = _score_label(biz_score)

    # Sort scored flows by ai_score descending
    scored_flows.sort(key=lambda x: x["ai_score"], reverse=True)

    return {
        "scored_flows":      scored_flows,
        "business_ai_score": biz_score,
        "score_label":       label,
        "score_color":       color,
        "quick_wins":        [f for f in scored_flows if f["quick_win"]],
        "walk_flows":        [f for f in scored_flows if f["crawl_walk_run"] == "Walk"],
        "crawl_flows":       [f for f in scored_flows if f["crawl_walk_run"] == "Crawl"],
        "run_flows":         [f for f in scored_flows if f["crawl_walk_run"] == "Run"],
        "assessed_at":       datetime.utcnow().isoformat(),
    }


# --------------------------------------------------
# Session state helpers
# --------------------------------------------------

def get_assessment() -> dict | None:
    return st.session_state.get("assessment")


def assessment_is_stale(confirmed_flow_ids: list) -> bool:
    """
    Returns True if the assessment needs to be re-run because
    the confirmed flow set has changed since last assessment.
    """
    assessment = get_assessment()
    if not assessment:
        return True
    assessed_ids = [
        f["flow_id"] for f in assessment.get("scored_flows", [])
    ]
    return sorted(assessed_ids) != sorted(confirmed_flow_ids)


def run_and_cache_assessment() -> dict:
    """
    Run assessment and cache in session state.
    Re-runs if confirmed flows have changed.
    Returns the assessment dict.
    """
    confirmed_flows = [
        f for f in st.session_state.get("discovery", [])
        if f.get("confirmed")
    ]
    confirmed_ids = [f["flow_id"] for f in confirmed_flows]

    if assessment_is_stale(confirmed_ids):
        bp = st.session_state.get("business_profile", {})
        assessment = run_assessment(confirmed_flows, bp)
        st.session_state.assessment = assessment

    return st.session_state.assessment