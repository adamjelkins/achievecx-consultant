"""
risk_calculator.py

Deterministic implementation risk scoring engine.
One GPT call for mitigation recommendations only.

Overall program risk score: 0-100
  Low      0-39
  Medium   40-59
  High     60-79
  Critical 80-100

Five weighted dimensions:
  Integration Complexity  30%
  Timeline Pressure       20%
  Current Automation      15%
  Contact Volume          15%
  Flow Complexity Mix     20%

Per-flow risk indicators based on category + CWR + flow name keywords.
"""

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
from datetime import datetime

import openai
from dotenv import load_dotenv

load_dotenv()
_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------------------------------------
# Risk labels and colors
# --------------------------------------------------

def _risk_label(score: int) -> str:
    if score >= 80: return "Critical"
    elif score >= 60: return "High"
    elif score >= 40: return "Medium"
    return "Low"


def _risk_color(score: int) -> str:
    if score >= 80: return "#ef4444"
    elif score >= 60: return "#f59e0b"
    elif score >= 40: return "#6366f1"
    return "#22c55e"


def _risk_icon(score: int) -> str:
    if score >= 80: return "🔴"
    elif score >= 60: return "🟠"
    elif score >= 40: return "🟡"
    return "🟢"


# --------------------------------------------------
# Dimension scoring functions (each returns 1-5)
# --------------------------------------------------

def _score_integration(crm: str, cc_platform: str) -> tuple[int, str]:
    """
    Score integration complexity from CRM and CC platform answers.
    Higher = more risky.
    """
    crm_lower = (crm or "").lower()
    cc_lower  = (cc_platform or "").lower()

    # Unknown / custom = highest risk
    if not crm and not cc_platform:
        return 5, "No systems of record identified — integration path unknown."
    if "something else" in crm_lower or "something else" in cc_lower:
        return 4, "Custom or unknown platform requires bespoke integration work."

    # Enterprise stacks with known connectors = lower risk
    known_crm = {"salesforce", "servicenow", "hubspot", "zendesk",
                 "microsoft dynamics", "sap crm", "oracle cx"}
    known_cc  = {"genesys", "nice cxone", "avaya", "five9",
                 "amazon connect", "cisco", "twilio flex"}

    crm_known = any(k in crm_lower for k in known_crm)
    cc_known  = any(k in cc_lower  for k in known_cc)

    if crm_known and cc_known:
        # Both known — check if they're commonly paired
        good_pairs = [
            ("salesforce", "genesys"), ("salesforce", "nice cxone"),
            ("servicenow", "genesys"), ("salesforce", "five9"),
            ("salesforce", "amazon connect"),
        ]
        is_good_pair = any(
            a in crm_lower and b in cc_lower
            for a, b in good_pairs
        )
        if is_good_pair:
            return 1, "Well-documented integration path with native connectors available."
        return 2, "Known platforms — pre-built connectors likely available."
    elif crm_known or cc_known:
        return 3, "One platform is known; the other may require custom integration."
    else:
        return 4, "Integration complexity unclear — discovery sprint recommended."


def _score_timeline(timeline: str) -> tuple[int, str]:
    """Higher = more risky (tighter timeline)."""
    t = (timeline or "").lower()
    if "3" in t and "6" in t:
        return 5, "3–6 month timeline compresses change management and testing."
    elif "6" in t and "12" in t:
        return 3, "6–12 months is achievable with proper planning."
    elif "1+" in t or "year" in t:
        return 2, "12+ month horizon allows for thorough planning and phasing."
    elif "exploring" in t:
        return 1, "No committed timeline — flexibility to phase implementation properly."
    return 3, "Timeline not specified — assume standard 6–12 month window."


def _score_automation(automation: str) -> tuple[int, str]:
    """Lower current automation = higher risk (no muscle memory)."""
    a = (automation or "").lower()
    if "mostly manual" in a:
        return 5, "No existing automation baseline — significant change management required."
    elif "basic ivr" in a:
        return 4, "Basic IVR only — team has limited automation experience."
    elif "some chatbot" in a:
        return 2, "Existing self-service experience reduces change management burden."
    elif "significant" in a:
        return 1, "Mature automation environment — incremental implementation path available."
    return 3, "Automation level unclear — assume moderate change management effort."


def _score_volume(volume: str) -> tuple[int, str]:
    """Higher volume = higher stakes if something goes wrong."""
    v = (volume or "").lower()
    if "50,000+" in v or "50000" in v:
        return 5, "High volume — any deployment issues affect a large customer base."
    elif "10,000" in v:
        return 3, "Moderate volume — staged rollout strongly recommended."
    elif "1,000" in v:
        return 2, "Manageable volume for phased deployment approach."
    elif "under" in v:
        return 1, "Low volume limits blast radius of any deployment issues."
    return 3, "Volume not specified — assume moderate risk."


def _score_flow_complexity(quick_wins: list, walk_flows: list,
                            crawl_flows: list) -> tuple[int, str]:
    """
    Run-heavy portfolio = higher risk (full automation, no fallback).
    Crawl-heavy = lower risk (foundational work).
    """
    total = len(quick_wins) + len(walk_flows) + len(crawl_flows)
    if total == 0:
        return 3, "No flows scored yet."

    run_pct   = len(quick_wins) / total
    crawl_pct = len(crawl_flows) / total

    if run_pct >= 0.6:
        return 5, "Run-heavy portfolio — high automation ambition increases deployment risk."
    elif run_pct >= 0.4:
        return 4, "Mixed Run/Walk portfolio — careful sequencing and fallback planning required."
    elif crawl_pct >= 0.5:
        return 2, "Crawl-heavy portfolio — foundational work is lower risk."
    else:
        return 3, "Balanced portfolio — moderate complexity across phases."


# --------------------------------------------------
# Per-flow risk scoring
# --------------------------------------------------

# Keywords that elevate flow risk regardless of CWR
HIGH_RISK_KEYWORDS = {
    "identity", "authentication", "verification", "payment",
    "fraud", "compliance", "regulatory", "hipaa", "pci",
    "credit card", "security", "password", "account access",
}

MEDIUM_RISK_KEYWORDS = {
    "billing", "refund", "dispute", "escalation",
    "complaint", "legal", "contract",
}


def _flow_risk_factors(flow: dict) -> list[str]:
    """Return list of risk factor strings for a specific flow."""
    name     = (flow.get("flow_name") or "").lower()
    category = (flow.get("category") or "").lower()
    cwr      = flow.get("crawl_walk_run", "Crawl")
    factors  = []

    # Keyword-based factors
    if any(k in name for k in HIGH_RISK_KEYWORDS):
        factors.append("Regulatory or security exposure — low error tolerance")
    if any(k in name for k in MEDIUM_RISK_KEYWORDS):
        factors.append("Financial or dispute handling — requires careful validation")

    # CWR-based factors
    if cwr == "Run":
        factors.append("Full automation target — fallback handling essential")
    elif cwr == "Walk":
        factors.append("Agent handoff logic required — CRM integration dependency")

    # Category factors
    if "authentication" in category or "security" in category:
        factors.append("Authentication complexity increases testing scope")
    if "payment" in category or "billing" in category:
        factors.append("Financial data handling requires compliance review")

    # Positive factors (lower risk indicators)
    if not factors:
        factors.append("Well-defined intent — standard implementation path")
    if cwr == "Crawl":
        factors.append("Foundational phase — lower deployment complexity")

    return factors[:3]  # cap at 3 for readability


def _score_flow_risk(flow: dict) -> int:
    """Return 0-100 risk score for a single flow."""
    name     = (flow.get("flow_name") or "").lower()
    cwr      = flow.get("crawl_walk_run", "Crawl")
    base     = {"Run": 50, "Walk": 35, "Crawl": 20}.get(cwr, 30)

    # Keyword modifiers
    if any(k in name for k in HIGH_RISK_KEYWORDS):
        base += 25
    elif any(k in name for k in MEDIUM_RISK_KEYWORDS):
        base += 12

    return min(base, 95)


# --------------------------------------------------
# GPT narrative and inaction risk
# --------------------------------------------------

def _generate_narrative(
    ctx: dict,
    program_score: int,
    program_label: str,
    dimension_scores: dict,
) -> str:
    """
    Generate a plain-English 2-3 sentence narrative explaining WHY
    this client's implementation risk is what it is — specific to
    their CRM, CC platform, timeline, and automation baseline.
    """
    top_dims = sorted(
        dimension_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True,
    )[:2]

    dim_lines = "\n".join(
        f"- {name}: {d['label']} — {d['reason']}"
        for name, d in top_dims
    )

    prompt = f"""You are a senior CX implementation consultant writing a briefing for a client.

Client: {ctx.get('company_name', 'this company')}
Industry: {ctx.get('industry', 'Unknown')}
CRM: {ctx.get('crm', 'Unknown')}
Contact Center: {ctx.get('cc_platform', 'Unknown')}
Timeline: {ctx.get('timeline', 'Unknown')}
Current Automation: {ctx.get('automation', 'Unknown')}
Overall Implementation Risk: {program_label} ({program_score}/100)

Top risk drivers:
{dim_lines}

Write 2-3 sentences explaining why this client's implementation risk is {program_label}.
Be specific — reference their actual CRM, CC platform, timeline, and automation level.
Do NOT use hedge words like "may" or "could". Be direct and factual.
Write for a trusted advisor audience, not a sales pitch.
Return only the narrative text, no labels or formatting."""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[risk_calculator] Narrative generation failed: {e}")
        # Deterministic fallback
        top_name, top_dim = top_dims[0] if top_dims else ("complexity", {"reason": ""})
        return (
            f"Implementation risk is {program_label} primarily due to {top_name.lower()}. "
            f"{top_dim.get('reason', '')} "
            f"A phased rollout approach starting with lower-complexity flows is recommended."
        )


def _generate_inaction_risk(ctx: dict) -> list[dict]:
    """
    Generate 3-4 inaction risk items — the cost of staying the same.
    Each item has: dimension, headline, body (1-2 sentences).
    Specific to the client's industry, stack, and automation level.
    """
    prompt = f"""You are a senior CX transformation advisor briefing a client on the risks of NOT modernizing their customer experience.

Client: {ctx.get('company_name', 'this company')}
Industry: {ctx.get('industry', 'Unknown')}
CRM: {ctx.get('crm', 'Unknown')}
Contact Center: {ctx.get('cc_platform', 'Unknown')}
Current Automation Level: {ctx.get('automation', 'Unknown')}
Contact Volume: {ctx.get('volume', 'Unknown')}
Primary Pain Point: {ctx.get('pain_point', 'Unknown')}

Write exactly 4 inaction risk items covering:
1. Technology obsolescence (their current stack vs market direction)
2. Competitive displacement (what AI-enabled competitors can do that they can't)
3. Customer experience drift (rising customer expectations they won't meet)
4. Cost trajectory (how manual costs compound while AI costs deflate)

For each item, be specific to this client's industry and stack. Do not be generic.

Return ONLY a JSON array with this structure:
[
  {{
    "dimension": "Technology Obsolescence",
    "headline": "Short punchy headline (max 8 words)",
    "body": "1-2 specific sentences about why staying put is costly for THIS client."
  }},
  ...
]"""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        import json as _json
        start = raw.find("["); end = raw.rfind("]") + 1
        if start != -1 and end > 0:
            items = _json.loads(raw[start:end])
            if isinstance(items, list) and items:
                return items[:4]
    except Exception as e:
        print(f"[risk_calculator] Inaction risk generation failed: {e}")

    # Deterministic fallback
    industry = ctx.get("industry", "your industry")
    crm      = ctx.get("crm", "your CRM")
    cc       = ctx.get("cc_platform", "your contact center platform")
    return [
        {
            "dimension": "Technology Obsolescence",
            "headline":  "Your stack is falling behind the market",
            "body":      f"{crm} and {cc} are increasingly behind platforms with native AI capabilities. "
                         f"Every quarter without modernization widens the gap."
        },
        {
            "dimension": "Competitive Displacement",
            "headline":  "AI-enabled competitors are pulling ahead",
            "body":      f"Competitors in {industry} with AI-enabled CX resolve issues faster, "
                         f"at lower cost, and with higher CSAT — making it harder to retain customers on price or service alone."
        },
        {
            "dimension": "Customer Experience Drift",
            "headline":  "Customer expectations are outpacing your capabilities",
            "body":      "Customers now expect instant, accurate, 24/7 resolution. "
                         "Each year without AI-assisted handling increases the gap between expectation and experience."
        },
        {
            "dimension": "Cost Trajectory",
            "headline":  "Manual handling costs compound; AI costs deflate",
            "body":      "Agent hiring, training, and attrition costs rise annually. "
                         "AI implementation costs are falling. The longer you wait, the wider the ROI gap becomes."
        },
    ]


# GPT mitigation recommendations
# --------------------------------------------------

def _generate_mitigations(
    ctx: dict,
    program_score: int,
    dimension_scores: dict,
    top_risk_flows: list,
) -> list[str]:
    """Generate 4-5 specific mitigation recommendations via GPT."""

    top_dims = sorted(
        dimension_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True,
    )[:3]

    dim_lines = "\n".join(
        f"- {name}: {d['label']} ({d['score']}/100) — {d['reason']}"
        for name, d in top_dims
    )

    flow_lines = "\n".join(
        f"- {f['flow_name']}: {_risk_label(f['risk_score'])} risk"
        for f in top_risk_flows[:3]
    )

    prompt = f"""You are a senior CX implementation consultant.

Client: {ctx.get('company_name', 'this company')}
Industry: {ctx.get('industry', 'Unknown')}
CRM: {ctx.get('crm', 'Unknown')}
Contact Center: {ctx.get('cc_platform', 'Unknown')}
Timeline: {ctx.get('timeline', 'Unknown')}
Overall Program Risk: {_risk_label(program_score)} ({program_score}/100)

Top risk dimensions:
{dim_lines}

Highest-risk flows:
{flow_lines}

Write exactly 4 mitigation recommendations for this specific client.
Each must be:
- One sentence, max 20 words
- Specific and actionable
- Address a real risk identified above
- Written for a trusted advisor audience

Return ONLY a JSON array:
["Mitigation one.", "Mitigation two.", "Mitigation three.", "Mitigation four."]"""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        raw = response.choices[0].message.content.strip()
        import json
        start = raw.find("["); end = raw.rfind("]") + 1
        if start != -1 and end > 0:
            items = json.loads(raw[start:end])
            if isinstance(items, list) and items:
                return [s for s in items if isinstance(s, str)][:4]
    except Exception as e:
        print(f"[risk_calculator] GPT call failed: {e}")

    # Deterministic fallback
    fallbacks = []
    if dimension_scores.get("Integration Complexity", {}).get("score", 0) >= 60:
        fallbacks.append(
            f"Conduct an integration discovery sprint with {ctx.get('crm','your CRM')} "
            f"before committing to timeline."
        )
    if dimension_scores.get("Timeline Pressure", {}).get("score", 0) >= 60:
        fallbacks.append(
            "Implement a phased rollout starting with lowest-risk flows "
            "to validate the platform before full deployment."
        )
    if dimension_scores.get("Current Automation", {}).get("score", 0) >= 60:
        fallbacks.append(
            "Invest in change management and agent training before go-live "
            "to reduce adoption resistance."
        )
    fallbacks.append(
        "Establish clear rollback procedures and fallback routing "
        "for all automated flows before cutover."
    )
    return fallbacks[:4]


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def run_risk_assessment() -> dict:
    """
    Run the full risk assessment from session state.
    Caches result in st.session_state.risk_assessment.
    Returns risk assessment dict.
    """
    answers    = getattr(st.session_state, "conv_answers", {})
    bp         = getattr(st.session_state, "business_profile", {})
    assessment = getattr(st.session_state, "assessment", {})

    crm         = answers.get("crm", "") or ""
    cc_platform = answers.get("cc_platform", "") or ""
    timeline    = answers.get("timeline", "") or ""
    automation  = answers.get("automation", "") or ""
    volume      = answers.get("volume", "") or ""

    quick_wins  = assessment.get("quick_wins", [])
    walk_flows  = assessment.get("walk_flows", [])
    crawl_flows = assessment.get("crawl_flows", [])

    # Score each dimension (1-5 raw, then scaled to 0-100)
    int_score,  int_reason  = _score_integration(crm, cc_platform)
    tl_score,   tl_reason   = _score_timeline(timeline)
    auto_score, auto_reason = _score_automation(automation)
    vol_score,  vol_reason  = _score_volume(volume)
    flow_score, flow_reason = _score_flow_complexity(
        quick_wins, walk_flows, crawl_flows
    )

    # Scale raw 1-5 to 0-100
    def _scale(raw): return int((raw - 1) / 4 * 100)

    dimension_scores = {
        "Integration Complexity": {
            "score":  _scale(int_score),
            "raw":    int_score,
            "reason": int_reason,
            "label":  _risk_label(_scale(int_score)),
            "color":  _risk_color(_scale(int_score)),
            "weight": 0.30,
        },
        "Timeline Pressure": {
            "score":  _scale(tl_score),
            "raw":    tl_score,
            "reason": tl_reason,
            "label":  _risk_label(_scale(tl_score)),
            "color":  _risk_color(_scale(tl_score)),
            "weight": 0.20,
        },
        "Current Automation": {
            "score":  _scale(auto_score),
            "raw":    auto_score,
            "reason": auto_reason,
            "label":  _risk_label(_scale(auto_score)),
            "color":  _risk_color(_scale(auto_score)),
            "weight": 0.15,
        },
        "Contact Volume": {
            "score":  _scale(vol_score),
            "raw":    vol_score,
            "reason": vol_reason,
            "label":  _risk_label(_scale(vol_score)),
            "color":  _risk_color(_scale(vol_score)),
            "weight": 0.15,
        },
        "Flow Complexity Mix": {
            "score":  _scale(flow_score),
            "raw":    flow_score,
            "reason": flow_reason,
            "label":  _risk_label(_scale(flow_score)),
            "color":  _risk_color(_scale(flow_score)),
            "weight": 0.20,
        },
    }

    # Weighted program score
    program_score = int(sum(
        d["score"] * d["weight"]
        for d in dimension_scores.values()
    ))

    # Per-flow risk
    discovery = getattr(st.session_state, "discovery", [])
    confirmed = [f for f in discovery if f.get("confirmed")]

    # Merge CWR from assessment into confirmed flows
    score_map = {
        f["flow_id"]: f
        for f in assessment.get("scored_flows", [])
    }
    flow_risks = []
    for flow in confirmed:
        fid    = flow["flow_id"]
        scored = score_map.get(fid, {})
        merged = {**flow, **scored}
        risk_s = _score_flow_risk(merged)
        flow_risks.append({
            "flow_id":    fid,
            "flow_name":  flow.get("flow_name", fid),
            "category":   flow.get("category", ""),
            "cwr":        scored.get("crawl_walk_run", "Crawl"),
            "ai_score":   scored.get("ai_score", 0),
            "risk_score": risk_s,
            "risk_label": _risk_label(risk_s),
            "risk_color": _risk_color(risk_s),
            "risk_icon":  _risk_icon(risk_s),
            "factors":    _flow_risk_factors(merged),
        })

    flow_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    top_risk_flows = [f for f in flow_risks if f["risk_score"] >= 60]

    # Context for GPT
    ctx = {
        "company_name": bp.get("company_name", ""),
        "industry":     bp.get("industry", ""),
        "crm":          crm,
        "cc_platform":  cc_platform,
        "timeline":     timeline,
        "automation":   automation,
        "volume":       volume,
        "pain_point":   answers.get("pain_point", ""),
    }

    # GPT narrative — plain-English "why" explanation
    narrative = _generate_narrative(
        ctx, program_score, _risk_label(program_score), dimension_scores
    )

    # GPT inaction risk — cost of staying the same
    inaction_risks = _generate_inaction_risk(ctx)

    # GPT mitigation recommendations
    mitigations = _generate_mitigations(
        ctx, program_score, dimension_scores, top_risk_flows
    )

    result = {
        "assessed_at":      datetime.utcnow().isoformat(),
        "program_score":    program_score,
        "program_label":    _risk_label(program_score),
        "program_color":    _risk_color(program_score),
        "program_icon":     _risk_icon(program_score),
        "dimension_scores": dimension_scores,
        "flow_risks":       flow_risks,
        "top_risk_flows":   top_risk_flows,
        "narrative":        narrative,
        "inaction_risks":   inaction_risks,
        "mitigations":      mitigations,
    }

    st.session_state.risk_assessment = result
    return result


def get_or_run_risk_assessment() -> dict:
    """Return cached risk assessment or run fresh."""
    existing  = getattr(st.session_state, "risk_assessment", None)
    discovery = getattr(st.session_state, "discovery", [])
    confirmed_ids = sorted(
        f["flow_id"] for f in discovery if f.get("confirmed")
    )

    if existing:
        # Invalidate if flows have changed
        assessed_ids = sorted(
            f["flow_id"] for f in existing.get("flow_risks", [])
        )
        if assessed_ids == confirmed_ids:
            return existing

    return run_risk_assessment()