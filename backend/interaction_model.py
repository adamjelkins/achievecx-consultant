"""
interaction_model.py

Renders CX Interaction Model cards for confirmed flows.
Used in two locations:
  - Blueprint > Flow Designs tab
  - Phase 2 > Design Preview section

Each card shows:
  Entry Channels     how the customer initiates contact
  Intents            what the AI detects and handles
  Data Sources       systems powering the interaction
  Human Role         where/if a human is involved
  Output Actions     what the AI does (inform, transact, route, etc.)
  Authentication     what proof of identity is required
  Containment        target % or engagement metric

Loads from flow_templates.json (project root).
Falls back to inference from flow category + CWR if template not found.
"""

import json
import os
import streamlit as st
from pathlib import Path


# --------------------------------------------------
# Load templates
# --------------------------------------------------

_TEMPLATES_PATH = Path(__file__).parent / "data" / "flow_templates.json"
_templates_cache: dict | None = None


def _load_templates() -> dict:
    global _templates_cache
    if _templates_cache is not None:
        return _templates_cache
    try:
        with open(_TEMPLATES_PATH, "r") as f:
            _templates_cache = json.load(f)
    except Exception as e:
        print(f"[interaction_model] Failed to load flow_templates.json: {e}")
        _templates_cache = {}
    return _templates_cache


# --------------------------------------------------
# Fallback inference from flow metadata
# --------------------------------------------------

def _infer_template(flow: dict, scored: dict) -> dict:
    """
    Build a best-effort template from flow metadata when
    no entry exists in flow_templates.json.
    """
    flow_name = flow.get("flow_name", "")
    category  = (flow.get("category") or
                 scored.get("category") or "").lower()
    cwr       = scored.get("crawl_walk_run", "Crawl")

    # Channel inference from category
    channels = ["Phone", "Web", "Chat"]
    if "outbound" in category or "notification" in category:
        channels = ["SMS", "Email", "App Push"]
    elif "field" in category or "dispatch" in category:
        channels = ["Phone", "Web", "Mobile App"]

    # Data source inference
    data_sources = ["CRM", "Knowledge Base"]
    if "billing" in category or "payment" in category:
        data_sources = ["Billing System", "CRM", "Payment Gateway"]
    elif "order" in category:
        data_sources = ["OMS", "CRM"]
    elif "technical" in category or "support" in category:
        data_sources = ["Knowledge Base", "CRM", "ITSM"]
    elif "health" in category or "medical" in category:
        data_sources = ["EHR", "CRM", "Scheduling System"]
    elif "field" in category:
        data_sources = ["Field Service System", "CRM", "Scheduling"]

    # Human role from CWR
    human_role = {
        "Run":   "Escalation",
        "Walk":  "Collaborative",
        "Crawl": "In-Loop",
    }.get(cwr, "Escalation")

    # Containment from AI score
    ai_score   = scored.get("ai_score", 50)
    containment = min(int(ai_score * 0.9), 90)

    return {
        "flow_id":          flow.get("flow_id", ""),
        "flow_name":        flow_name,
        "category":         flow.get("category", ""),
        "entry_channels":   channels,
        "intents":          ["Primary intent", "Secondary intent"],
        "data_sources":     data_sources,
        "human_role":       human_role,
        "human_role_detail": "Based on flow complexity and automation level.",
        "output_actions":   ["Inform", "Escalate"],
        "authentication":   "Standard verification",
        "containment_target": containment,
        "containment_type": "standard",
        "complexity":       scored.get("complexity", "Medium"),
        "notes":            "Template inferred from flow metadata.",
    }


# --------------------------------------------------
# Color helpers
# --------------------------------------------------

def _human_role_color(role: str) -> tuple[str, str]:
    """Returns (bg_color, text_color) for human role badge."""
    return {
        "None":          ("rgba(34,197,94,0.1)",  "#22c55e"),
        "Escalation":    ("rgba(99,102,241,0.1)", "#818cf8"),
        "In-Loop":       ("rgba(245,158,11,0.1)", "#f59e0b"),
        "Post-Review":   ("rgba(99,102,241,0.1)", "#a78bfa"),
        "Collaborative": ("rgba(245,158,11,0.1)", "#fbbf24"),
    }.get(role, ("rgba(82,82,91,0.1)", "#71717a"))


def _containment_color(pct: int) -> str:
    if pct >= 80: return "#22c55e"
    elif pct >= 60: return "#6366f1"
    elif pct >= 40: return "#f59e0b"
    return "#71717a"


def _complexity_color(complexity: str) -> str:
    return {
        "Low":    "#22c55e",
        "Medium": "#f59e0b",
        "High":   "#ef4444",
    }.get(complexity, "#71717a")


def _cwr_color(cwr: str) -> str:
    return {"Run": "#22c55e", "Walk": "#f59e0b", "Crawl": "#6b7280"}.get(cwr, "#6b7280")


# --------------------------------------------------
# Single card renderer
# --------------------------------------------------

def render_interaction_card(
    flow: dict,
    scored: dict,
    expanded: bool = False,
) -> None:
    """
    Render one CX Interaction Model card.

    Args:
        flow:     Discovery flow dict (flow_id, flow_name, category, source)
        scored:   Assessment scored flow dict (ai_score, crawl_walk_run, rationale)
        expanded: Whether to show full detail or compact view
    """
    templates = _load_templates()
    fid       = flow.get("flow_id", "")
    template  = templates.get(fid) or _infer_template(flow, scored)

    flow_name       = template["flow_name"]
    category        = template.get("category", flow.get("category", ""))
    entry_channels  = template.get("entry_channels", [])
    intents         = template.get("intents", [])
    data_sources    = template.get("data_sources", [])
    human_role      = template.get("human_role", "Escalation")
    human_detail    = template.get("human_role_detail", "")
    output_actions  = template.get("output_actions", [])
    authentication  = template.get("authentication", "")
    containment     = template.get("containment_target")
    contain_type    = template.get("containment_type", "standard")
    eng_metric      = template.get("engagement_metric", "")
    eng_target      = template.get("engagement_target", "")
    complexity      = template.get("complexity", "Medium")
    notes           = template.get("notes", "")

    cwr       = scored.get("crawl_walk_run", "")
    ai_score  = scored.get("ai_score", 0)
    rationale = scored.get("rationale", "")

    hr_bg, hr_color   = _human_role_color(human_role)
    cwr_color         = _cwr_color(cwr)
    complexity_color  = _complexity_color(complexity)

    # ── Card container ──
    st.markdown(
        '<div style="background:#141414;border:1px solid #1f1f1f;'
        'border-radius:12px;padding:18px 20px;margin-bottom:14px;">'

        # Header
        '<div style="display:flex;justify-content:space-between;'
        'align-items:flex-start;margin-bottom:14px;">'
        '<div>'
        '<div style="font-size:15px;font-weight:700;color:#f1f5f9;'
        'letter-spacing:-0.02em;margin-bottom:3px;">' + flow_name + '</div>'
        '<div style="font-size:11px;color:#52525b;">' + category + '</div>'
        '</div>'
        '<div style="display:flex;align-items:center;gap:8px;">'
        + (
            '<span style="font-size:11px;font-weight:600;color:' + cwr_color + ';'
            'background:' + cwr_color + '18;border:1px solid ' + cwr_color + '33;'
            'border-radius:4px;padding:2px 8px;">' + cwr + '</span>'
            if cwr else ""
        )
        + (
            '<span style="font-size:12px;font-weight:700;color:#6366f1;">'
            + str(ai_score) + '</span>'
            if ai_score else ""
        )
        + '</div></div>',
        unsafe_allow_html=True,
    )

    # ── Two-column detail grid ──
    col1, col2 = st.columns(2)

    with col1:
        # Entry Channels
        if entry_channels:
            channels_html = " · ".join(
                '<span style="background:#1e1e1e;border:1px solid #2a2a2a;'
                'border-radius:4px;padding:1px 7px;font-size:11px;color:#a1a1aa;">'
                + c + '</span>'
                for c in entry_channels
            )
            st.markdown(
                '<div style="margin-bottom:12px;">'
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
                'Entry Channels</div>'
                '<div style="display:flex;flex-wrap:wrap;gap:4px;">'
                + channels_html + '</div></div>',
                unsafe_allow_html=True,
            )

        # Intents
        if intents:
            intents_html = "".join(
                '<div style="display:flex;align-items:flex-start;gap:6px;'
                'margin-bottom:3px;">'
                '<span style="color:#6366f1;font-size:11px;flex-shrink:0;'
                'margin-top:1px;">◆</span>'
                '<span style="font-size:12px;color:#c4c4c8;line-height:1.4;">'
                + intent + '</span></div>'
                for intent in intents
            )
            st.markdown(
                '<div style="margin-bottom:12px;">'
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
                'Intents Detected</div>'
                + intents_html + '</div>',
                unsafe_allow_html=True,
            )

    with col2:
        # Data Sources
        if data_sources:
            ds_html = "".join(
                '<div style="display:flex;align-items:center;gap:6px;'
                'margin-bottom:3px;">'
                '<span style="color:#f59e0b;font-size:10px;flex-shrink:0;">⬡</span>'
                '<span style="font-size:12px;color:#c4c4c8;">' + ds + '</span></div>'
                for ds in data_sources
            )
            st.markdown(
                '<div style="margin-bottom:12px;">'
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
                'Data Sources</div>'
                + ds_html + '</div>',
                unsafe_allow_html=True,
            )

        # Output Actions
        if output_actions:
            actions_html = " · ".join(
                '<span style="font-size:11px;color:#a1a1aa;">' + a + '</span>'
                for a in output_actions
            )
            st.markdown(
                '<div style="margin-bottom:12px;">'
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
                'Output Actions</div>'
                '<div>' + actions_html + '</div></div>',
                unsafe_allow_html=True,
            )

    # ── Human Role + Containment row ──
    st.markdown(
        '<div style="height:1px;background:#1f1f1f;margin:4px 0 12px;"></div>',
        unsafe_allow_html=True,
    )

    col_hr, col_auth, col_contain = st.columns([2, 2, 2])

    with col_hr:
        st.markdown(
            '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
            'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
            'Human Role</div>'
            '<span style="font-size:12px;font-weight:600;color:' + hr_color + ';'
            'background:' + hr_bg + ';border:1px solid ' + hr_color + '33;'
            'border-radius:6px;padding:3px 10px;">' + human_role + '</span>',
            unsafe_allow_html=True,
        )

    with col_auth:
        if authentication:
            st.markdown(
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:6px;">'
                'Authentication</div>'
                '<div style="font-size:11px;color:#a1a1aa;line-height:1.4;">'
                + authentication + '</div>',
                unsafe_allow_html=True,
            )

    with col_contain:
        st.markdown(
            '<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
            'text-transform:uppercase;color:#52525b;margin-bottom:6px;">',
            unsafe_allow_html=True,
        )

        if contain_type == "engagement":
            # Proactive/outbound flows — show engagement metric
            st.markdown(
                'Engagement Target</div>'
                '<div style="font-size:20px;font-weight:700;color:#6366f1;'
                'letter-spacing:-0.02em;line-height:1;">' + eng_target + '</div>'
                '<div style="font-size:10px;color:#52525b;margin-top:2px;">'
                + eng_metric + '</div>',
                unsafe_allow_html=True,
            )
        elif contain_type == "ai_assisted":
            # Complaint/fraud flows — AI-assisted framing
            st.markdown(
                'AI Role</div>'
                '<span style="font-size:12px;font-weight:600;color:#f59e0b;'
                'background:rgba(245,158,11,0.1);border:1px solid #f59e0b33;'
                'border-radius:6px;padding:3px 10px;">AI-Assisted</span>'
                '<div style="font-size:10px;color:#52525b;margin-top:4px;">'
                'Triage, capture & route</div>',
                unsafe_allow_html=True,
            )
        else:
            # Standard containment
            contain_color = _containment_color(containment or 0)
            contain_str   = str(containment) + "%" if containment else "—"
            st.markdown(
                'Containment Target</div>'
                '<div style="font-size:20px;font-weight:700;color:'
                + contain_color + ';letter-spacing:-0.02em;line-height:1;">'
                + contain_str + '</div>'
                + (
                    '<div style="height:3px;background:#1f1f1f;border-radius:2px;'
                    'margin-top:6px;overflow:hidden;">'
                    '<div style="height:3px;width:' + str(containment) + '%;'
                    'background:' + contain_color + ';border-radius:2px;"></div></div>'
                    if containment else ""
                ),
                unsafe_allow_html=True,
            )

    # ── Human role detail + complexity + notes ──
    if human_detail or complexity or rationale or notes:
        st.markdown(
            '<div style="height:1px;background:#1f1f1f;margin:12px 0 10px;"></div>',
            unsafe_allow_html=True,
        )

    if human_detail:
        st.markdown(
            '<div style="font-size:11px;color:#71717a;line-height:1.5;'
            'margin-bottom:8px;font-style:italic;">'
            '🔄 ' + human_detail + '</div>',
            unsafe_allow_html=True,
        )

    footer_items = []
    if complexity:
        comp_color = _complexity_color(complexity)
        footer_items.append(
            '<span style="font-size:10px;color:' + comp_color + ';'
            'background:' + comp_color + '15;border:1px solid ' + comp_color + '30;'
            'border-radius:4px;padding:1px 7px;">● ' + complexity + ' complexity</span>'
        )
    if rationale:
        footer_items.append(
            '<span style="font-size:11px;color:#52525b;">' + rationale + '</span>'
        )
    if notes and notes != "Template inferred from flow metadata.":
        footer_items.append(
            '<span style="font-size:10px;color:#3f3f46;font-style:italic;">'
            '📌 ' + notes + '</span>'
        )

    if footer_items:
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">'
            + " ".join(footer_items) + '</div>',
            unsafe_allow_html=True,
        )

    # Close card div
    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------
# Multi-card renderer
# --------------------------------------------------

def render_interaction_model(
    confirmed_flows: list,
    assessment: dict,
    show_header: bool = True,
) -> None:
    """
    Render interaction model cards for all confirmed flows.

    Args:
        confirmed_flows: List of flow dicts from st.session_state.discovery
        assessment:      Assessment dict from st.session_state.assessment
        show_header:     Whether to show the section header
    """
    if not confirmed_flows:
        st.info("No confirmed flows yet. Complete the discovery conversation to see interaction models.")
        return

    score_map = {
        f["flow_id"]: f
        for f in assessment.get("scored_flows", [])
    }

    if show_header:
        flow_count = len(confirmed_flows)
        st.markdown(
            '<div style="font-size:10px;font-weight:600;letter-spacing:0.12em;'
            'text-transform:uppercase;color:#71717a;margin-bottom:6px;">'
            'Interaction Models</div>'
            '<div style="font-size:12px;color:#52525b;margin-bottom:16px;">'
            + str(flow_count) + ' confirmed use case'
            + ('s' if flow_count != 1 else '') +
            ' — entry channels, intents, data sources, human role, '
            'and containment targets.</div>',
            unsafe_allow_html=True,
        )

    # Group by CWR for visual organization
    cwr_order  = ["Run", "Walk", "Crawl"]
    cwr_labels = {
        "Run":   ("🟢 Run — Full Automation", "#22c55e"),
        "Walk":  ("⚡ Walk — AI-Assisted",     "#f59e0b"),
        "Crawl": ("🔧 Crawl — Foundation",     "#6b7280"),
    }

    grouped: dict[str, list] = {"Run": [], "Walk": [], "Crawl": [], "Unknown": []}
    for flow in confirmed_flows:
        fid    = flow["flow_id"]
        scored = score_map.get(fid, {})
        cwr    = scored.get("crawl_walk_run", "Unknown")
        grouped.setdefault(cwr, []).append((flow, scored))

    for cwr in cwr_order:
        flows_in_group = grouped.get(cwr, [])
        if not flows_in_group:
            continue

        label, color = cwr_labels[cwr]
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;'
            'margin:20px 0 12px;">'
            '<span style="font-size:12px;font-weight:600;color:' + color + ';">'
            + label + ' (' + str(len(flows_in_group)) + ')</span>'
            '<div style="flex:1;height:1px;background:#1f1f1f;"></div></div>',
            unsafe_allow_html=True,
        )

        for flow, scored in flows_in_group:
            render_interaction_card(flow, scored)

    # Unknown CWR (unscored flows)
    for flow, scored in grouped.get("Unknown", []):
        render_interaction_card(flow, scored)


# --------------------------------------------------
# Single flow card by ID (for clickable diagram nodes)
# --------------------------------------------------

def render_single_card(flow_id: str, assessment: dict) -> None:
    """
    Render an interaction model card for a single flow by flow_id.
    Used by the clickable platform diagram node panel.

    Args:
        flow_id:    canonical flow_id (e.g. "flow_001")
        assessment: maturity assessment dict from session state
    """
    discovery = st.session_state.get("discovery", [])
    score_map = {
        f["flow_id"]: f
        for f in assessment.get("scored_flows", [])
    }

    # Find the flow in discovery
    flow = next(
        (f for f in discovery if f.get("flow_id") == flow_id),
        None,
    )

    if not flow:
        # Flow not in discovery — build minimal stub from template
        templates = _load_templates()
        tmpl = templates.get(flow_id, {})
        if not tmpl:
            st.info(f"No data available for flow {flow_id}.")
            return
        flow = {
            "flow_id":   flow_id,
            "flow_name": tmpl.get("flow_name", flow_id),
            "category":  tmpl.get("category", ""),
            "source":    "template",
            "confirmed": False,
        }

    scored = score_map.get(flow_id, {})
    render_interaction_card(flow, scored)


def get_flow_name(flow_id: str) -> str:
    """Return display name for a flow_id from templates or discovery."""
    templates = _load_templates()
    if flow_id in templates:
        return templates[flow_id].get("flow_name", flow_id)
    discovery = st.session_state.get("discovery", [])
    match = next(
        (f for f in discovery if f.get("flow_id") == flow_id),
        None,
    )
    return match.get("flow_name", flow_id) if match else flow_id