"""
blueprint_generator.py

Assembles the CX Blueprint from session state.
Updated: vendor_shortlist added to blueprint context.
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
from datetime import datetime

import openai
from dotenv import load_dotenv

load_dotenv()
_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _call_gpt(prompt: str, max_tokens: int = 300) -> str:
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[blueprint_generator] GPT call failed: {e}")
        return ""


def _get_enriched_context() -> dict:
    bp          = getattr(st.session_state, "business_profile", {})
    answers     = getattr(st.session_state, "conv_answers", {})
    risk_result = st.session_state.get("risk_assessment")

    try:
        from schema_adapter import profile_summary_for_gpt, build_profile_from_session
        if not st.session_state.get("discovery_profile"):
            build_profile_from_session()
        profile_summary = profile_summary_for_gpt()
    except Exception:
        profile_summary = {}

    def _get(schema_key, fallback_key="", fallback_val=""):
        entry = profile_summary.get(schema_key, {})
        if entry and entry.get("value"):
            val = entry["value"]
            return ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)
        if fallback_key:
            raw = answers.get(fallback_key) or bp.get(fallback_key, fallback_val)
            return ", ".join(str(r) for r in raw) if isinstance(raw, list) else str(raw or fallback_val)
        return fallback_val

    top_risk_factor = ""
    if risk_result and risk_result.get("dimension_scores"):
        sorted_dims = sorted(
            risk_result["dimension_scores"].items(),
            key=lambda x: x[1].get("score", 0), reverse=True,
        )
        top_risk_factor = sorted_dims[0][0] if sorted_dims else ""

    # Top vendor for context
    vendors = getattr(st.session_state, "vendor_shortlist", [])
    top_vendor_name = vendors[0]["name"] if vendors else ""

    return {
        "company_name":    bp.get("company_name", ""),
        "domain":          bp.get("domain", ""),
        "industry":        _get("business_context.industry",      "industry",    "Unknown"),
        "company_type":    bp.get("company_type", ""),
        "size":            _get("business_context.business_size",  "size_estimate", ""),
        "regions":         _get("business_context.regions_served", "regions",     ""),
        "channels":        _get("business_context.channels",       "channels",    ""),
        "volume":          _get("business_context.volume_estimate","volume",      ""),
        "pain_points":     _get("business_context.pain_points",    "pain_point",  ""),
        "automation":      _get("business_context.automation_level","automation", ""),
        "primary_goal":    _get("business_context.primary_goal",   "goal",        ""),
        "timeline":        _get("business_context.timeline",       "timeline",    ""),
        "crm":             _get("systems_of_record.crm",           "crm",         ""),
        "cc_platform":     _get("systems_of_record.contact_center_platform",
                                "cc_platform", ""),
        "customer_type":   _get("customer_types.primary_customers", "",          ""),
        "compliance":      _get("compliance.standards",            "",            ""),
        "profile_confidence": profile_summary.get("profile_confidence", 0.0),
        "description":     bp.get("description", ""),
        "has_risk":        risk_result is not None,
        "risk_label":      risk_result.get("program_label", "") if risk_result else "",
        "risk_score":      risk_result.get("program_score", 0) if risk_result else 0,
        "top_risk_factor": top_risk_factor,
        "top_vendor":      top_vendor_name,
    }


def _generate_executive_summary(ctx: dict, assessment: dict, flow_count: int) -> str:
    ai_score    = assessment.get("business_ai_score", 0)
    score_label = assessment.get("score_label", "")
    quick_wins  = assessment.get("quick_wins", [])
    qw_names    = ", ".join(f["flow_name"] for f in quick_wins[:3]) if quick_wins else "none identified"
    platform    = " / ".join(p for p in [ctx["crm"], ctx["cc_platform"]] if p)

    financial_line = ""
    bc_results = st.session_state.get("business_case_results")
    if bc_results:
        b = bc_results["base"]
        sav = b["annual_savings"]
        pay = b["payback_months"]
        def _fmt(v):
            return f"${v/1_000_000:.1f}M" if abs(v) >= 1_000_000 else f"${v:,.0f}"
        if sav > 0:
            financial_line = (
                f"Financial modeling projects {_fmt(sav)} in annual savings "
                f"with a {pay:.1f}-month payback period. "
            )

    risk_line = ""
    if ctx["has_risk"] and ctx["risk_label"]:
        risk_line = (
            f"Implementation risk is assessed as {ctx['risk_label'].lower()}"
            + (f", with {ctx['top_risk_factor'].lower()} as the primary concern. "
               if ctx["top_risk_factor"] else ". ")
        )

    vendor_line = ""
    if ctx["top_vendor"]:
        vendor_line = f"{ctx['top_vendor']} is the top-ranked platform match. "

    prompt = f"""You are a senior CX strategy consultant writing an executive summary
for a CX Blueprint report. Write for a trusted advisor audience.

Business: {ctx['company_name']} | Industry: {ctx['industry']}
Channels: {ctx['channels']} | Volume: {ctx['volume']}/month
Pain point: {ctx['pain_points']} | Goal: {ctx['primary_goal']}
Platform: {platform or 'not specified'}
Flows: {flow_count} confirmed | AI Score: {ai_score}/100 ({score_label})
Quick wins: {qw_names}
{financial_line}{risk_line}{vendor_line}

Write a single paragraph (90-110 words). Specific to industry and pain points.
Mention AI score. Include financial, risk, and vendor context if provided.
Confident consulting tone. No bullets, no headers, plain prose."""

    result = _call_gpt(prompt, max_tokens=220)
    if not result:
        result = (
            f"{ctx['company_name']} has a CX AI Opportunity Score of {ai_score}/100, "
            f"indicating a {score_label.lower()} for AI-enabled CX transformation. "
            + (financial_line if financial_line else "")
            + f"Based on {flow_count} confirmed interaction flows, this assessment "
            f"identifies clear automation opportunities to reduce contact volume "
            f"and improve resolution rates."
        )
    return result


def _generate_next_steps(ctx: dict, assessment: dict) -> list:
    quick_wins = assessment.get("quick_wins", [])
    walk_flows = assessment.get("walk_flows", [])
    qw_names   = [f["flow_name"] for f in quick_wins[:2]]
    ai_score   = assessment.get("business_ai_score", 0)
    platform   = ctx["crm"] or ctx["cc_platform"] or "existing platform"
    qw_first   = qw_names[0] if qw_names else "highest-volume inbound flows"

    risk_context = ""
    if ctx["has_risk"] and ctx["risk_label"]:
        risk_context = (
            f"Overall implementation risk: {ctx['risk_label']}. "
            f"Top risk factor: {ctx['top_risk_factor']}. "
        )

    vendor_context = ""
    if ctx["top_vendor"]:
        vendor_context = f"Top recommended platform: {ctx['top_vendor']}. "

    prompt = f"""You are a senior CX strategy consultant.

Company: {ctx['company_name']} | Industry: {ctx['industry']}
Platform: {platform} | Goal: {ctx['primary_goal']}
Timeline: {ctx['timeline']} | AI Score: {ai_score}/100
Quick wins: {qw_names} | Compliance: {ctx['compliance']}
{risk_context}{vendor_context}

Write exactly 4 next-step recommendations. Each: one sentence, max 22 words,
specific and actionable for {ctx['industry']}.

Return ONLY a JSON array:
["Step one.", "Step two.", "Step three.", "Step four."]"""

    raw = _call_gpt(prompt, max_tokens=250)
    try:
        start = raw.find("["); end = raw.rfind("]") + 1
        if start != -1 and end > 0:
            steps = json.loads(raw[start:end])
            if isinstance(steps, list) and steps:
                return [s for s in steps if isinstance(s, str)][:4]
    except Exception:
        pass

    return [
        f"Deploy IVA automation for {qw_first} to achieve immediate containment gains.",
        f"Integrate {platform} with contact center to enable AI-assisted agent workflows.",
        "Establish KPI baselines (FCR, AHT, containment) across all priority flows.",
        f"Schedule a 90-day implementation planning session aligned to your "
        f"{ctx['timeline'] or '6-12 month'} timeline.",
    ]


def _build_flow_cards(confirmed_flows: list, assessment: dict) -> list:
    score_map = {f["flow_id"]: f for f in assessment.get("scored_flows", [])}
    cards = []
    for flow in confirmed_flows:
        fid    = flow["flow_id"]
        scored = score_map.get(fid, {})
        cards.append({
            "flow_id":              fid,
            "flow_name":            flow.get("flow_name", fid),
            "category":             flow.get("category", "Unknown"),
            "source":               flow.get("source", "discovered"),
            "ai_score":             scored.get("ai_score", 0),
            "crawl_walk_run":       scored.get("crawl_walk_run", "Crawl"),
            "quick_win":            scored.get("quick_win", False),
            "rationale":            scored.get("rationale", ""),
            "automation_potential": scored.get("automation_potential", 0),
        })
    cards.sort(key=lambda x: x["ai_score"], reverse=True)
    return cards


def generate_blueprint() -> dict:
    assessment      = getattr(st.session_state, "assessment", {})
    discovery       = getattr(st.session_state, "discovery", [])
    intake_profile  = getattr(st.session_state, "intake_profile", {})
    confirmed_flows = [f for f in discovery if f.get("confirmed")]
    ctx             = _get_enriched_context()

    # Issue 3 fix: auto-run risk assessment if not already in session
    # so blueprint always has risk context even if advisor skipped the panel
    if not st.session_state.get("risk_assessment") and confirmed_flows:
        try:
            from risk_calculator import run_risk_assessment
            run_risk_assessment()
        except Exception as e:
            print(f"[blueprint_generator] Auto risk assessment failed: {e}")

    # Run vendor shortlist if not already cached
    try:
        from vendor_catalog import get_or_run_vendor_shortlist
        vendors = get_or_run_vendor_shortlist()
    except Exception:
        vendors = []

    exec_summary = _generate_executive_summary(ctx, assessment, len(confirmed_flows))
    next_steps   = _generate_next_steps(ctx, assessment)
    flow_cards   = _build_flow_cards(confirmed_flows, assessment)

    # Business case
    bc_results = st.session_state.get("business_case_results")
    bc_data    = {}
    if bc_results:
        b = bc_results["base"]
        bc_data = {
            "has_data":             True,
            "annual_savings":       b["annual_savings"],
            "payback_months":       b["payback_months"],
            "impl_cost":            b["impl_cost"],
            "npv_3yr":              b["npv"][3],
            "npv_5yr":              b["npv"][5],
            "savings_by_driver":    b["savings_by_driver"],
            "current_total":        b["current"]["total_cost"],
            "proposed_total":       b["proposed"]["total_cost"],
            "current_cpc":          b["current"]["cost_per_contact"],
            "proposed_cpc":         b["proposed"]["cost_per_contact"],
            "current_agents":       b["current"]["agent_count"],
            "proposed_agents":      b["proposed_agent_count"],
            "automation_pct":       b["effective_automation"],
            "conservative_savings": bc_results["conservative"]["annual_savings"],
            "optimistic_savings":   bc_results["optimistic"]["annual_savings"],
        }
    else:
        bc_data = {"has_data": False}

    # Risk assessment
    risk_result = st.session_state.get("risk_assessment")
    if risk_result:
        risk_data = {
            "has_data":         True,
            "program_score":    risk_result.get("program_score", 0),
            "program_label":    risk_result.get("program_label", ""),
            "program_color":    risk_result.get("program_color", "#52525b"),
            "program_icon":     risk_result.get("program_icon", ""),
            "dimension_scores": risk_result.get("dimension_scores", {}),
            "flow_risks":       risk_result.get("flow_risks", []),
            "top_risk_flows":   risk_result.get("top_risk_flows", []),
            "mitigations":      risk_result.get("mitigations", []),
        }
    else:
        risk_data = {"has_data": False}

    # Vendor shortlist — store lightweight version in blueprint
    vendor_data = [
        {
            "rank":        i + 1,
            "vendor_id":   v["vendor_id"],
            "name":        v["name"],
            "tier":        v["tier"],
            "featured":    v.get("featured", False),
            "feat_label":  v.get("featured_label"),
            "fit_score":   v["fit_score"],
            "description": v["description"],
            "fit_reasons": v.get("fit_reasons", []),
            "website":     v.get("website", ""),
            "logo_domain": v.get("logo_domain", ""),
        }
        for i, v in enumerate(vendors)
    ]

    blueprint = {
        "generated_at":         datetime.utcnow().isoformat(),
        "generated_for":        f"{intake_profile.get('first_name','')} {intake_profile.get('last_name','')}".strip(),
        "generated_email":      intake_profile.get("email", ""),
        "company_name":         ctx["company_name"],
        "domain":               ctx["domain"],
        "industry":             ctx["industry"],
        "company_type":         ctx["company_type"],
        "size_estimate":        ctx["size"],
        "regions":              ctx["regions"],
        "channels":             ctx["channels"],
        "crm":                  ctx["crm"],
        "cc_platform":          ctx["cc_platform"],
        "primary_goal":         ctx["primary_goal"],
        "timeline":             ctx["timeline"],
        "business_ai_score":    assessment.get("business_ai_score", 0),
        "score_label":          assessment.get("score_label", ""),
        "score_color":          assessment.get("score_color", "#52525b"),
        "profile_confidence":   ctx["profile_confidence"],
        "confirmed_flow_count": len(confirmed_flows),
        "quick_win_count":      len(assessment.get("quick_wins", [])),
        "flow_cards":           flow_cards,
        "quick_wins":           assessment.get("quick_wins", []),
        "walk_flows":           assessment.get("walk_flows", []),
        "crawl_flows":          assessment.get("crawl_flows", []),
        "executive_summary":    exec_summary,
        "next_steps":           next_steps,
        "business_case":        bc_data,
        "risk_assessment":      risk_data,
        "vendor_shortlist":     vendor_data,
    }

    st.session_state.blueprint = blueprint
    return blueprint


def get_or_generate_blueprint() -> dict:
    existing      = st.session_state.get("blueprint")
    discovery     = getattr(st.session_state, "discovery", [])
    confirmed_ids = sorted(f["flow_id"] for f in discovery if f.get("confirmed"))

    if existing:
        existing_ids = sorted(c["flow_id"] for c in existing.get("flow_cards", []))
        # Issue 4 fix: also invalidate if vendor shortlist flow IDs differ
        vendor_flow_ids = getattr(st.session_state, "vendor_shortlist_flow_ids", [])
        if existing_ids == confirmed_ids and vendor_flow_ids == confirmed_ids:
            return existing

    return generate_blueprint()