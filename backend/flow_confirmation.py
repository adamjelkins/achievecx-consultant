"""
flow_confirmation.py

Flow Confirmation UI — Tab 1 of the discovery experience.

Responsibilities:
  - Display pre-suggested flows (from inference) as pre-confirmed
  - Display conversation-discovered flows as unconfirmed
  - Allow user to confirm / dismiss any flow
  - Allow user to add a flow via free text → GPT maps to canonical flow_id
  - Write confirmed state back to st.session_state.discovery

State contract:
  Each flow dict in st.session_state.discovery must have:
    flow_id, flow_name, category, confidence, reasons, confirmed, source
  source: "inferred" | "discovered" | "user_added"
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
from rapidfuzz import fuzz

FLOWS_FILE = os.path.join(Path.cwd(), "data", "flows.json")


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _load_flows() -> list:
    try:
        with open(FLOWS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _confidence_color(confidence: float) -> str:
    if confidence >= 0.80:
        return "#22c55e"
    elif confidence >= 0.60:
        return "#6366f1"
    elif confidence >= 0.40:
        return "#f59e0b"
    else:
        return "#52525b"


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.80:
        return "Strong"
    elif confidence >= 0.60:
        return "Good"
    elif confidence >= 0.40:
        return "Possible"
    else:
        return "Weak"


def _source_badge(source: str) -> tuple:
    """Returns (label, color) for the source badge."""
    if source == "inferred":
        return "AI Pre-suggested", "#6366f1"
    elif source == "discovered":
        return "From Conversation", "#f59e0b"
    elif source == "user_added":
        return "Added by You", "#22c55e"
    else:
        return "Detected", "#52525b"


# --------------------------------------------------
# GPT flow mapping for "Add a flow"
# --------------------------------------------------

def _map_text_to_flow(user_text: str, flows: list) -> dict | None:
    """
    Try to map free-text input to a canonical flow using two strategies:
    1. Fuzzy match against flow names and keywords (fast, no API cost)
    2. If no strong fuzzy match, use GPT to interpret intent

    Returns the matched flow dict from flows.json, or None.
    """
    user_lower = user_text.lower().strip()

    # Strategy 1: fuzzy match
    best_score = 0
    best_flow = None
    for flow in flows:
        # Match against flow name
        name_score = fuzz.token_sort_ratio(user_lower, flow["flow_name"].lower())
        # Match against keywords
        kw_score = max(
            (fuzz.partial_ratio(user_lower, kw.lower()) for kw in flow.get("keywords", [])),
            default=0,
        )
        score = max(name_score, kw_score)
        if score > best_score:
            best_score = score
            best_flow = flow

    if best_score >= 65:
        return best_flow

    # Strategy 2: GPT mapping
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        catalog = [
            {"flow_id": f["flow_id"], "flow_name": f["flow_name"],
             "category": f.get("category", ""), "keywords": f.get("keywords", [])}
            for f in flows
        ]

        prompt = f"""A user wants to add this customer interaction flow to their CX design:
"{user_text}"

From the following catalog, identify the best matching flow.
Return ONLY a JSON object with the matching flow_id and flow_name, or null if no match:
{json.dumps(catalog, indent=2)}

Return exactly: {{"flow_id": "flow_xxx", "flow_name": "..."}}
Or if no match: null"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()

        # Parse response
        if raw.lower() == "null" or not raw:
            return None

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(
                l for l in cleaned.splitlines()
                if not l.strip().startswith("```")
            ).strip()

        parsed = json.loads(cleaned)
        if not parsed or "flow_id" not in parsed:
            return None

        # Look up in flows
        known = {f["flow_id"]: f for f in flows}
        return known.get(parsed["flow_id"])

    except Exception as e:
        print(f"[flow_confirmation] GPT mapping failed: {e}")
        return None


# --------------------------------------------------
# Session state helpers
# --------------------------------------------------

def _get_confirmed_ids() -> set:
    return {
        f["flow_id"]
        for f in st.session_state.get("discovery", [])
        if f.get("confirmed")
    }


def _get_dismissed_ids() -> set:
    return set(st.session_state.get("dismissed_flow_ids", []))


def _dismiss_flow(flow_id: str) -> None:
    """Mark a flow as dismissed — remove from discovery, track ID."""
    dismissed = list(st.session_state.get("dismissed_flow_ids", []))
    if flow_id not in dismissed:
        dismissed.append(flow_id)
    st.session_state.dismissed_flow_ids = dismissed

    # Remove from discovery
    st.session_state.discovery = [
        f for f in st.session_state.get("discovery", [])
        if f["flow_id"] != flow_id
    ]


def _confirm_flow(flow_id: str) -> None:
    """Set confirmed=True for a flow in discovery."""
    for f in st.session_state.get("discovery", []):
        if f["flow_id"] == flow_id:
            f["confirmed"] = True
            break


def _unconfirm_flow(flow_id: str) -> None:
    """Set confirmed=False for a flow in discovery."""
    for f in st.session_state.get("discovery", []):
        if f["flow_id"] == flow_id:
            f["confirmed"] = False
            break


# --------------------------------------------------
# CSS
# --------------------------------------------------

CONFIRMATION_CSS = """
<style>
    /* Flow card */
    .flow-card {
        background: #141414;
        border: 1px solid #1f1f1f;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 8px;
        transition: border-color 0.15s ease;
    }
    .flow-card.confirmed {
        border-color: #1a2e1a;
        background: #0f1a0f;
    }
    .flow-card.dismissed {
        opacity: 0.4;
    }

    /* Section header label */
    .section-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #52525b;
        margin: 20px 0 10px;
    }

    /* Confirm/dismiss button overrides inside flow cards */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #2a2a2a !important;
        color: #71717a !important;
        border-radius: 6px !important;
        font-size: 12px !important;
        padding: 4px 10px !important;
        transition: all 0.15s ease !important;
        min-height: unset !important;
        height: 28px !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #3f3f46 !important;
        color: #f1f5f9 !important;
    }

    /* Continue button */
    .continue-btn button {
        background: #6366f1 !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        padding: 12px 24px !important;
        transition: background 0.15s ease, transform 0.1s ease !important;
    }
    .continue-btn button:hover {
        background: #4f46e5 !important;
        transform: translateY(-1px) !important;
    }

    /* Add flow input */
    div[data-testid="stTextInput"] input {
        background: #1c1c1c !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        font-size: 13px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
</style>
"""


# --------------------------------------------------
# Flow card renderer
# --------------------------------------------------

def _render_flow_card(flow: dict) -> None:
    """Render a single flow card with confirm/dismiss controls."""
    flow_id = flow["flow_id"]
    flow_name = flow.get("flow_name", flow_id)
    confidence = float(flow.get("confidence", 0.0))
    confirmed = flow.get("confirmed", False)
    source = flow.get("source", "discovered")
    reasons = [r for r in flow.get("reasons", []) if r]

    color = _confidence_color(confidence)
    conf_label = _confidence_label(confidence)
    src_label, src_color = _source_badge(source)
    pct = int(confidence * 100)

    # Card container styling via markdown
    card_bg = "#0f1a0f" if confirmed else "#141414"
    card_border = "#1e3a1e" if confirmed else "#1f1f1f"

    st.markdown(
        f'<div style="background:{card_bg};border:1px solid {card_border};'
        f'border-radius:10px;padding:14px 16px;margin-bottom:8px;">',
        unsafe_allow_html=True,
    )

    col_info, col_actions = st.columns([3, 1])

    with col_info:
        # Flow name + source badge
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
            f'<span style="font-size:14px;font-weight:600;color:#f1f5f9;'
            f'letter-spacing:-0.02em;">{flow_name}</span>'
            f'<span style="font-size:10px;font-weight:600;color:{src_color};'
            f'background:rgba(99,102,241,0.08);border:1px solid {src_color}33;'
            f'border-radius:4px;padding:1px 6px;letter-spacing:0.04em;">'
            f'{src_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Confidence bar + label
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            f'<div style="flex:1;height:3px;background:#1f1f1f;border-radius:2px;">'
            f'<div style="width:{pct}%;height:3px;background:{color};'
            f'border-radius:2px;"></div></div>'
            f'<span style="font-size:11px;font-weight:600;color:{color};'
            f'white-space:nowrap;">{conf_label} · {pct}%</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Reasons (collapsed by default)
        if reasons:
            with st.expander("Why this flow?", expanded=False):
                for r in reasons:
                    st.markdown(
                        f'<div style="font-size:12px;color:#52525b;'
                        f'padding:2px 0;">· {r}</div>',
                        unsafe_allow_html=True,
                    )

    with col_actions:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if confirmed:
            if st.button("✓ Confirmed", key=f"unconfirm_{flow_id}",
                         help="Click to unconfirm"):
                _unconfirm_flow(flow_id)
                st.rerun()
        else:
            if st.button("+ Confirm", key=f"confirm_{flow_id}"):
                _confirm_flow(flow_id)
                st.rerun()

        if st.button("✕ Dismiss", key=f"dismiss_{flow_id}"):
            _dismiss_flow(flow_id)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# Add a flow
# --------------------------------------------------

def _render_add_flow_section(flows: list) -> None:
    """Free-text flow addition with GPT canonical mapping."""
    st.markdown(
        '<div style="font-size:10px;font-weight:600;letter-spacing:0.12em;'
        'text-transform:uppercase;color:#52525b;margin:20px 0 10px;">'
        'Add a Flow</div>',
        unsafe_allow_html=True,
    )

    existing_ids = {f["flow_id"] for f in st.session_state.get("discovery", [])}
    dismissed_ids = _get_dismissed_ids()

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        user_text = st.text_input(
            label="add_flow_input",
            label_visibility="collapsed",
            placeholder="Describe a flow, e.g. 'customers asking about store hours'",
            key="add_flow_text",
        )
    with col_btn:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        add_clicked = st.button("+ Add", key="add_flow_btn",
                                use_container_width=True)

    if add_clicked and user_text.strip():
        with st.spinner("Mapping to canonical flow..."):
            matched = _map_text_to_flow(user_text.strip(), flows)

        if matched is None:
            st.warning(
                "Couldn't match that to a known flow. "
                "Try rephrasing — e.g. 'order tracking', 'billing question', 'password reset'."
            )
        elif matched["flow_id"] in existing_ids:
            st.info(
                f"**{matched['flow_name']}** is already in your flow list."
            )
        elif matched["flow_id"] in dismissed_ids:
            # Re-add dismissed flow
            discovery = st.session_state.get("discovery", [])
            discovery.append({
                "flow_id": matched["flow_id"],
                "flow_name": matched["flow_name"],
                "category": matched.get("category", "Unknown"),
                "confidence": 0.75,
                "reasons": [f"Added by user: '{user_text}'"],
                "confirmed": True,
                "source": "user_added",
            })
            dismissed = st.session_state.get("dismissed_flow_ids", [])
            st.session_state.dismissed_flow_ids = [
                d for d in dismissed if d != matched["flow_id"]
            ]
            st.session_state.discovery = discovery
            st.success(f"Re-added **{matched['flow_name']}**.")
            st.rerun()
        else:
            discovery = st.session_state.get("discovery", [])
            discovery.append({
                "flow_id": matched["flow_id"],
                "flow_name": matched["flow_name"],
                "category": matched.get("category", "Unknown"),
                "confidence": 0.75,
                "reasons": [f"Added by user: '{user_text}'"],
                "confirmed": True,
                "source": "user_added",
            })
            st.session_state.discovery = discovery
            st.success(f"Added **{matched['flow_name']}**.")
            st.rerun()


# --------------------------------------------------
# Main render function
# --------------------------------------------------

def render_flow_confirmation() -> None:
    """
    Main entry point. Renders the full flow confirmation UI.
    Call this from Tab 1 in main.py.
    """
    st.markdown(CONFIRMATION_CSS, unsafe_allow_html=True)

    discovery = st.session_state.get("discovery", [])
    bp = st.session_state.get("business_profile", {})
    company_name = bp.get("company_name", "your business")

    flows = _load_flows()

    # Header
    confirmed_count = sum(1 for f in discovery if f.get("confirmed"))
    total_count = len(discovery)

    st.markdown(
        f'<div style="margin-bottom:4px;">'
        f'<span style="font-size:20px;font-weight:650;color:#f1f5f9;'
        f'letter-spacing:-0.03em;">Flow Confirmation</span>'
        f'</div>'
        f'<div style="font-size:13px;color:#52525b;margin-bottom:20px;">'
        f'We identified {total_count} likely flows for '
        f'<span style="color:#a1a1aa;">{company_name}</span>. '
        f'Confirm the ones that apply — dismiss the rest.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Confirmed count badge
    if confirmed_count > 0:
        st.markdown(
            f'<div style="display:inline-flex;align-items:center;gap:6px;'
            f'background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);'
            f'border-radius:6px;padding:4px 12px;margin-bottom:16px;">'
            f'<span style="font-size:12px;color:#22c55e;font-weight:600;">'
            f'✓ {confirmed_count} flow{"s" if confirmed_count != 1 else ""} confirmed'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    if not discovery:
        st.info(
            "No flows detected yet. Describe your business in the chat "
            "or add flows manually below."
        )
    else:
        # Split into inferred vs discovered
        inferred = [f for f in discovery if f.get("source") == "inferred"]
        discovered = [f for f in discovery
                      if f.get("source") not in ("inferred", "user_added")]
        user_added = [f for f in discovery if f.get("source") == "user_added"]

        # --- Pre-suggested flows ---
        if inferred:
            st.markdown(
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.12em;'
                'text-transform:uppercase;color:#52525b;margin-bottom:10px;">'
                'AI Pre-suggested</div>',
                unsafe_allow_html=True,
            )
            for flow in inferred:
                _render_flow_card(flow)

        # --- Conversation-discovered flows ---
        if discovered:
            st.markdown(
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.12em;'
                'text-transform:uppercase;color:#52525b;margin:20px 0 10px;">'
                'Also Detected</div>',
                unsafe_allow_html=True,
            )
            for flow in discovered:
                _render_flow_card(flow)

        # --- User-added flows ---
        if user_added:
            st.markdown(
                '<div style="font-size:10px;font-weight:600;letter-spacing:0.12em;'
                'text-transform:uppercase;color:#52525b;margin:20px 0 10px;">'
                'Added by You</div>',
                unsafe_allow_html=True,
            )
            for flow in user_added:
                _render_flow_card(flow)

    # Add a flow section
    st.markdown(
        '<div style="height:1px;background:#1f1f1f;margin:20px 0;"></div>',
        unsafe_allow_html=True,
    )
    _render_add_flow_section(flows)

    # Continue button
    st.markdown(
        '<div style="height:1px;background:#1f1f1f;margin:24px 0 20px;"></div>',
        unsafe_allow_html=True,
    )

    if confirmed_count == 0:
        st.markdown(
            '<div style="font-size:12px;color:#52525b;margin-bottom:12px;">'
            'Confirm at least one flow to continue.</div>',
            unsafe_allow_html=True,
        )

    col_spacer, col_btn = st.columns([2, 1])
    with col_btn:
        continue_disabled = confirmed_count == 0
        if st.button(
            "Continue to Assessment →",
            key="continue_to_assessment",
            disabled=continue_disabled,
            use_container_width=True,
            type="primary",
        ):
            st.session_state.flows_confirmed = True
            st.rerun()