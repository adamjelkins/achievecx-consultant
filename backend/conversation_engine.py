"""
conversation_engine.py

10-step structured discovery conversation.
Change: systems step split into crm (Step 7) and cc_platform (Step 8).
"""

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


# --------------------------------------------------
# Step definitions (10 steps)
# --------------------------------------------------

STEPS = [
    {
        "id":         "flow_confirmation",
        "title":      "Flow Confirmation",
        "question":   None,
        "type":       "chip_multi",
        "options":    None,
        "schema_key": "confirmed_flows",
        "required":   True,
    },
    {
        "id":         "regions",
        "title":      "Regions Served",
        "question":   "Which regions does your business primarily serve?",
        "type":       "chip_multi",
        "options":    [
            "United States", "Canada", "United Kingdom",
            "Europe", "Latin America", "Asia Pacific",
            "Middle East & Africa", "Global",
        ],
        "schema_key": "regions_served",
        "required":   True,
    },
    {
        "id":         "channels",
        "title":      "Customer Channels",
        "question":   "How do your customers reach you? Select all that apply.",
        "type":       "chip_multi",
        "options":    [
            "Phone", "Live Chat", "Email", "Web / Self-service",
            "SMS", "Social Media", "In-Person",
        ],
        "schema_key": "channels",
        "required":   True,
    },
    {
        "id":         "volume",
        "title":      "Contact Volume",
        "question":   "Roughly how many customer contacts do you handle per month?",
        "type":       "chip_single",
        "options":    [
            "Under 1,000", "1,000 – 10,000",
            "10,000 – 50,000", "50,000+", "Not sure yet",
        ],
        "schema_key": "volume_estimate",
        "required":   True,
    },
    {
        "id":         "pain_point",
        "title":      "Biggest Pain Point",
        "question":   "What's driving the most contact volume right now?",
        "type":       "chip_or_text",
        "options":    [
            "Order issues", "Returns & refunds", "Billing questions",
            "Technical support", "Appointment scheduling",
            "Account access", "Something else...",
        ],
        "schema_key": "pain_points",
        "required":   True,
    },
    {
        "id":         "automation",
        "title":      "Current Automation",
        "question":   "What's your current level of automation in customer service?",
        "type":       "chip_single",
        "options":    [
            "Mostly manual — agents handle everything",
            "Basic IVR — press 1 for sales, etc.",
            "Some chatbot or self-service",
            "Significant automation already in place",
        ],
        "schema_key": "automation_level",
        "required":   True,
    },
    {
        "id":         "crm",
        "title":      "CRM Platform",
        "question":   "What CRM system do you use to manage customer data?",
        "type":       "chip_or_text",
        "options":    [
            "Salesforce", "HubSpot", "Microsoft Dynamics",
            "ServiceNow", "Zendesk", "SAP CRM",
            "Oracle CX", "Something else...",
        ],
        "schema_key": "crm_platform",
        "required":   False,
    },
    {
        "id":         "cc_platform",
        "title":      "Contact Center Platform",
        "question":   "What contact center platform or telephony system do you use?",
        "type":       "chip_or_text",
        "options":    [
            "Genesys", "NICE CXone", "Avaya", "Five9",
            "Amazon Connect", "Cisco", "Twilio Flex",
            "Something else...",
        ],
        "schema_key": "contact_center_platform",
        "required":   False,
    },
    {
        "id":         "goal",
        "title":      "Primary AI Goal",
        "question":   "What's the #1 thing you want AI to do for your customer experience?",
        "type":       "chip_or_text",
        "options":    [
            "Reduce call / contact volume",
            "Faster issue resolution",
            "Cut operational costs",
            "Improve customer satisfaction (CSAT)",
            "Enable 24/7 availability",
            "Better agent productivity",
            "Something else...",
        ],
        "schema_key": "primary_goal",
        "required":   True,
    },
    {
        "id":         "timeline",
        "title":      "Implementation Timeline",
        "question":   "When are you looking to implement AI-enabled CX improvements?",
        "type":       "chip_single",
        "options":    [
            "Just exploring for now",
            "Within 3 – 6 months",
            "6 – 12 months",
            "1+ year horizon",
        ],
        "schema_key": "timeline",
        "required":   True,
    },
]

TOTAL_STEPS = len(STEPS)


# --------------------------------------------------
# Helper
# --------------------------------------------------

def _answer_to_str(answer) -> str:
    if isinstance(answer, list):
        return ", ".join(str(a) for a in answer if a)
    if answer is None:
        return ""
    return str(answer)


# --------------------------------------------------
# Init
# --------------------------------------------------

def init_conversation() -> None:
    if "conv_step" not in st.session_state:
        st.session_state.conv_step = 0
    if "conv_answers" not in st.session_state:
        st.session_state.conv_answers = {}
    if "conv_messages" not in st.session_state:
        st.session_state.conv_messages = []
    if "conv_complete" not in st.session_state:
        st.session_state.conv_complete = False
    if "conv_chip_selections" not in st.session_state:
        st.session_state.conv_chip_selections = {}
    if "conv_other_text" not in st.session_state:
        st.session_state.conv_other_text = {}

    if not st.session_state.conv_messages:
        _seed_opening_message()


# --------------------------------------------------
# Opening message
# --------------------------------------------------

def _seed_opening_message() -> None:
    profile      = st.session_state.get("intake_profile", {})
    bp           = st.session_state.get("business_profile", {})
    first_name   = profile.get("first_name", "there")
    company_name = bp.get("company_name", "your business")
    industry     = bp.get("industry", "")

    industry_line = (
        f" — a {industry.lower()} business"
        if industry and industry not in ("Unknown", "")
        else ""
    )

    content = (
        f"Hi {first_name}! I've researched **{company_name}**{industry_line} "
        f"and pre-loaded some likely customer interaction flows. "
        f"I'll ask you a few quick questions to make sure I have the right picture. "
        f"This takes about 2 minutes."
    )

    st.session_state.conv_messages.append({
        "role": "assistant", "content": content,
        "message_type": "text", "step_id": None,
        "options": None, "answered": True,
    })
    _queue_step_message(0)


# --------------------------------------------------
# Step message builder
# --------------------------------------------------

def _queue_step_message(step_idx: int) -> None:
    if step_idx >= TOTAL_STEPS:
        return

    step = STEPS[step_idx]

    if step["id"] == "flow_confirmation":
        bp           = st.session_state.get("business_profile", {})
        company_name = bp.get("company_name", "your business")
        discovery    = st.session_state.get("discovery", [])
        options      = [f["flow_name"] for f in discovery]
        question     = (
            f"Based on what I know about {company_name}, "
            f"these are the customer interaction flows I'd expect. "
            f"Select the ones that apply — deselect any that don't fit."
        )
    else:
        question = step["question"]
        options  = step["options"]

    st.session_state.conv_messages.append({
        "role": "assistant", "content": question,
        "message_type": step["type"], "step_id": step["id"],
        "options": options, "answered": False,
    })


# --------------------------------------------------
# Answer handling
# --------------------------------------------------

def record_answer(step_id: str, answer) -> None:
    st.session_state.conv_answers[step_id] = answer

    step_idx = next(
        (i for i, s in enumerate(STEPS) if s["id"] == step_id), None
    )
    if step_idx is None:
        return

    # User echo message
    st.session_state.conv_messages.append({
        "role": "user", "content": _answer_to_str(answer),
        "message_type": "text", "step_id": step_id,
        "options": None, "answered": True,
    })

    # Mark question answered
    for msg in st.session_state.conv_messages:
        if msg.get("step_id") == step_id and msg["role"] == "assistant":
            msg["answered"] = True

    _persist_answer(step_id, answer)

    next_idx = step_idx + 1
    st.session_state.conv_step = next_idx

    if next_idx >= TOTAL_STEPS:
        st.session_state.conv_complete = True
        _queue_summary_message()
    else:
        _queue_acknowledgment(step_id)
        _queue_step_message(next_idx)


def _queue_acknowledgment(step_id: str) -> None:
    acks = {
        "flow_confirmation": "Got it — I've confirmed those flows.",
        "regions":           "Understood — regional context helps shape the solution.",
        "channels":          "Good to know. Multi-channel coverage is key for modern CX.",
        "volume":            "Understood — that helps me calibrate the AI opportunity.",
        "pain_point":        "That's a common driver. AI can make a real dent there.",
        "automation":        "Clear picture — I know exactly where you're starting from.",
        "crm":               "Noted — CRM integration is central to any AI deployment.",
        "cc_platform":       "Good — that shapes the integration path significantly.",
        "goal":              "That's a strong focus. I'll make sure the roadmap reflects it.",
        "timeline":          "Perfect — I'll factor that into the recommendations.",
    }
    st.session_state.conv_messages.append({
        "role": "assistant", "content": acks.get(step_id, "Got it, thanks."),
        "message_type": "text", "step_id": None,
        "options": None, "answered": True,
    })


def _queue_summary_message() -> None:
    answers      = st.session_state.conv_answers
    bp           = st.session_state.get("business_profile", {})
    company      = bp.get("company_name", "your business")

    confirmed_flows = answers.get("flow_confirmation", [])
    flow_count      = len(confirmed_flows) if isinstance(confirmed_flows, list) else 0
    goal_lower      = _answer_to_str(answers.get("goal", "")).lower() or "CX transformation"
    timeline_display = _answer_to_str(answers.get("timeline", ""))

    content = (
        f"That's everything I need. Here's what I've captured for "
        f"**{company}**: {flow_count} confirmed interaction flow"
        f"{'s' if flow_count != 1 else ''}, "
        f"with a focus on _{goal_lower}_."
        + (f" Timeline: _{timeline_display}_." if timeline_display else "")
        + "\n\nReview your confirmed flows below, then continue to your AI Assessment."
    )

    st.session_state.conv_messages.append({
        "role": "assistant", "content": content,
        "message_type": "text", "step_id": "summary",
        "options": None, "answered": True,
    })


# --------------------------------------------------
# Schema persistence
# --------------------------------------------------

def _persist_answer(step_id: str, answer) -> None:
    if "collected_data" not in st.session_state:
        st.session_state.collected_data = {}

    st.session_state.collected_data[step_id] = {
        "value": answer,
        "collected_at": datetime.utcnow().isoformat(),
    }

    if step_id == "flow_confirmation" and isinstance(answer, list):
        discovery = st.session_state.get("discovery", [])
        for flow in discovery:
            flow["confirmed"] = flow["flow_name"] in answer
        st.session_state.discovery = discovery

    try:
        from schema_adapter import build_profile_from_session
        build_profile_from_session()
    except Exception as e:
        print(f"[conversation_engine] Schema update failed: {e}")


# --------------------------------------------------
# Getters
# --------------------------------------------------

def current_step_idx() -> int:
    return st.session_state.get("conv_step", 0)


def current_step() -> dict | None:
    idx = current_step_idx()
    return STEPS[idx] if idx < TOTAL_STEPS else None


def is_complete() -> bool:
    return st.session_state.get("conv_complete", False)


def progress_pct() -> int:
    answered = len([
        s for s in STEPS
        if s["id"] in st.session_state.get("conv_answers", {})
    ])
    return min(int((answered / TOTAL_STEPS) * 100), 100)


def get_messages() -> list:
    return st.session_state.get("conv_messages", [])


def get_answers() -> dict:
    return st.session_state.get("conv_answers", {})


def get_chip_selections(step_id: str) -> list:
    return st.session_state.get("conv_chip_selections", {}).get(step_id, [])


def set_chip_selection(step_id: str, selections: list) -> None:
    if "conv_chip_selections" not in st.session_state:
        st.session_state.conv_chip_selections = {}
    st.session_state.conv_chip_selections[step_id] = selections


def get_other_text(step_id: str) -> str:
    return st.session_state.get("conv_other_text", {}).get(step_id, "")


def set_other_text(step_id: str, text: str) -> None:
    if "conv_other_text" not in st.session_state:
        st.session_state.conv_other_text = {}
    st.session_state.conv_other_text[step_id] = text


def reset_conversation() -> None:
    for key in [
        "conv_step", "conv_answers", "conv_messages",
        "conv_complete", "conv_chip_selections",
        "conv_other_text", "discovery_profile",
    ]:
        st.session_state.pop(key, None)