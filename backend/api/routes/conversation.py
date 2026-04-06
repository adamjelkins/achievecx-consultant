"""
api/routes/conversation.py

Discovery conversation endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

from core.session_store import get_or_create_session, save_session

router = APIRouter()

# ── Streamlit mock (must happen before any import of conversation_engine) ──

def _ensure_streamlit_mocked():
    import sys, types
    if 'streamlit' not in sys.modules:
        st_mock = types.ModuleType('streamlit')
        st_mock.spinner = lambda x: __import__('contextlib').nullcontext()
        st_mock.error   = lambda x: None
        st_mock.warning = lambda x: None
        st_mock.info    = lambda x: None
        st_mock.session_state = types.SimpleNamespace()
        sys.modules['streamlit'] = st_mock


def _get_steps() -> list:
    """Return the 10 conversation steps from conversation_engine."""
    try:
        import sys
        from pathlib import Path
        _ensure_streamlit_mocked()
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from conversation_engine import STEPS
        return STEPS
    except Exception as e:
        print(f"[conversation] Failed to load STEPS: {e}")
        import traceback; traceback.print_exc()
        return _fallback_steps()


def _fallback_steps() -> list:
    """Minimal fallback steps if conversation_engine fails to import."""
    return [
        {"id": "flow_confirmation", "title": "Use Cases",     "question": "Which of these customer interaction types apply to your business?", "type": "multi_select",  "options": ["Billing Inquiry", "Technical Support", "Outage Reporting", "Account Changes", "New Service Activation", "Retention / Win-back", "Payments", "Order Status", "Appointment Scheduling", "FAQ / General Inquiries"]},
        {"id": "regions",           "title": "Regions",       "question": "Which regions do you primarily serve?",                              "type": "single_select", "options": ["North America", "Europe", "Asia-Pacific", "Latin America", "Global"]},
        {"id": "channels",          "title": "Channels",      "question": "Which customer contact channels are you currently using?",           "type": "multi_select",  "options": ["Phone", "Live Chat", "Web / Self-service", "SMS", "Email", "Mobile App", "IVR"]},
        {"id": "volume",            "title": "Volume",        "question": "What is your approximate monthly contact volume?",                   "type": "single_select", "options": ["Under 1,000", "1,000 – 10,000", "10,000 – 50,000", "50,000+"]},
        {"id": "pain_point",        "title": "Pain Points",   "question": "What is your biggest customer experience challenge right now?",      "type": "text",          "options": []},
        {"id": "automation",        "title": "Automation",    "question": "What is your current level of automation in customer interactions?",  "type": "single_select", "options": ["None", "Basic IVR only", "Some chatbots", "Mature automation"]},
        {"id": "crm",               "title": "CRM",           "question": "Which CRM platform are you using?",                                  "type": "single_select", "options": ["Salesforce", "Microsoft Dynamics", "HubSpot", "ServiceNow", "Oracle", "SAP", "Other", "None"]},
        {"id": "cc_platform",       "title": "Contact Center","question": "Which contact center platform are you using?",                       "type": "single_select", "options": ["Genesys", "NICE CXone", "Avaya", "Cisco", "Five9", "Amazon Connect", "Twilio", "Other", "None"]},
        {"id": "goal",              "title": "Goal",          "question": "What is your primary goal for this AI initiative?",                  "type": "single_select", "options": ["Reduce cost per contact", "Improve CSAT / NPS", "Increase containment", "Reduce agent workload", "Faster resolution", "All of the above"]},
        {"id": "timeline",          "title": "Timeline",      "question": "What is your target timeline for implementation?",                   "type": "single_select", "options": ["0-3 months", "3-6 months", "6-12 months", "12+ months", "No firm timeline"]},
    ]


# ── Request/Response models ────────────────────────────────────

class AnswerRequest(BaseModel):
    session_id: str
    step_id: str
    answer: Any
    chip_selections: list = []
    other_text: str = ""


class ConversationStateResponse(BaseModel):
    session_id: str
    messages: list
    current_step: Optional[dict]
    current_step_idx: int
    progress_pct: int
    is_complete: bool
    answers: dict
    discovery: list


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/{session_id}/state", response_model=ConversationStateResponse)
async def get_conversation_state(session_id: str):
    """Get current conversation state."""
    session = await get_or_create_session(session_id)
    steps   = _get_steps()
    idx     = session.conv_step_idx
    step    = steps[idx] if idx < len(steps) else None

    return ConversationStateResponse(
        session_id       = session.session_id,
        messages         = [m.model_dump() for m in session.conv_messages],
        current_step     = _enrich_step(step, session) if step else None,
        current_step_idx = idx,
        progress_pct     = _progress_pct(idx, len(steps)),
        is_complete      = session.conv_complete,
        answers          = session.conv_answers,
        discovery        = session.discovery,
    )


@router.post("/answer", response_model=ConversationStateResponse)
async def record_answer(req: AnswerRequest):
    """Record an answer and advance the conversation."""
    session = await get_or_create_session(req.session_id)

    if session.conv_complete:
        raise HTTPException(400, "Conversation already complete")

    steps = _get_steps()
    idx   = session.conv_step_idx

    if idx >= len(steps):
        raise HTTPException(400, "No more steps")

    from models.session import ConversationMessage

    # Store the answer
    session.conv_answers[req.step_id]         = req.answer
    session.conv_chip_selections[req.step_id] = req.chip_selections
    session.conv_other_text[req.step_id]      = req.other_text

    # Handle flow_confirmation — mark selected flows as confirmed
    if req.step_id == "flow_confirmation":
        selected_names = req.chip_selections or (
            req.answer if isinstance(req.answer, list) else [req.answer] if req.answer else []
        )
        if session.discovery:
            # Mark existing discovery flows confirmed/unconfirmed
            for flow in session.discovery:
                flow["confirmed"] = flow.get("flow_name", "") in selected_names
        else:
            # No flows from inference — create from selected names
            session.discovery = [
                {
                    "flow_id":   f"flow_{i:03d}",
                    "flow_name": name,
                    "category":  "General",
                    "confirmed": True,
                    "confidence": 0.8,
                    "cwr":       "Walk",
                    "cwr_label": "AI Assisted",
                    "cwr_color": "#fbbf24",
                }
                for i, name in enumerate(selected_names)
            ]

    # Add user message
    answer_str = _answer_to_str(req.answer, req.chip_selections, req.other_text)
    session.conv_messages.append(ConversationMessage(
        role      = "user",
        content   = answer_str or "(no answer)",
        step_id   = req.step_id,
        timestamp = datetime.utcnow().isoformat(),
    ))

    # Advance
    next_idx = idx + 1
    session.conv_step_idx = next_idx

    # Acknowledgment
    ack = _get_acknowledgment(req.step_id, answer_str)
    if ack:
        session.conv_messages.append(ConversationMessage(
            role="assistant", content=ack, step_id=req.step_id,
        ))

    if next_idx < len(steps):
        next_step = steps[next_idx]
        q = next_step.get("question") or ""
        if q:
            session.conv_messages.append(ConversationMessage(
                role="assistant", content=q, step_id=next_step["id"],
            ))
    else:
        session.conv_complete    = True
        session.phase_2_complete = True
        session.current_phase    = 3
        session.conv_messages.append(ConversationMessage(
            role="assistant",
            content=_summary_message(session.conv_answers, session.business_profile),
        ))

    await save_session(session)

    next_step_data = _enrich_step(steps[next_idx], session) if next_idx < len(steps) else None
    return ConversationStateResponse(
        session_id       = session.session_id,
        messages         = [m.model_dump() for m in session.conv_messages],
        current_step     = next_step_data,
        current_step_idx = next_idx,
        progress_pct     = _progress_pct(next_idx, len(steps)),
        is_complete      = session.conv_complete,
        answers          = session.conv_answers,
        discovery        = session.discovery,
    )


@router.post("/{session_id}/confirm-flow")
async def confirm_flow(session_id: str, flow_id: str, confirmed: bool = True):
    """Toggle flow confirmation."""
    session = await get_or_create_session(session_id)
    for flow in session.discovery:
        if flow.get("flow_id") == flow_id:
            flow["confirmed"] = confirmed
            break
    await save_session(session)
    return {"flow_id": flow_id, "confirmed": confirmed}


@router.post("/{session_id}/init")
async def init_conversation(session_id: str):
    """Initialize conversation with opening message."""
    session = await get_or_create_session(session_id)

    if session.conv_messages:
        return await get_conversation_state(session_id)

    from models.session import ConversationMessage
    steps = _get_steps()

    bp         = session.business_profile or {}
    company    = bp.get("company_name", "your company")
    first_name = (session.intake_data or {}).get("first_name", "")

    greeting = (
        f"Great to meet you{', ' + first_name if first_name else ''}. "
        f"I've already researched {company} and identified some likely customer interaction flows. "
        f"Let me ask you a few quick questions to sharpen the picture."
    )

    session.conv_messages.append(ConversationMessage(
        role="assistant", content=greeting
    ))

    if steps:
        first_q = steps[0].get("question") or ""
        if first_q:
            session.conv_messages.append(ConversationMessage(
                role    = "assistant",
                content = first_q,
                step_id = steps[0]["id"],
            ))

    await save_session(session)
    return await get_conversation_state(session_id)


# ── Helpers ────────────────────────────────────────────────────

def _progress_pct(idx: int, total: int) -> int:
    if total == 0: return 0
    return min(int((idx / total) * 100), 100)


def _answer_to_str(answer: Any, chips: list, other: str) -> str:
    if chips:
        parts = list(chips)
        if other and other.strip():
            parts.append(other.strip())
        return ", ".join(parts)
    if isinstance(answer, list):
        return ", ".join(str(a) for a in answer)
    return str(answer) if answer is not None else ""


def _get_acknowledgment(step_id: str, answer: str) -> str:
    acks = {
        "flow_confirmation": "Got it — I've noted those use cases.",
        "regions":           "Understood.",
        "channels":          "Good to know — multi-channel coverage shapes the platform design.",
        "volume":            f"Understood. {answer} contacts sets the scale for this program.",
        "pain_point":        "That's a common challenge — we'll address it directly in the assessment.",
        "automation":        "Good baseline to work from.",
        "crm":               "Noted.",
        "cc_platform":       "Good.",
        "goal":              "Clear — that'll shape our recommendations.",
        "timeline":          "Understood.",
    }
    return acks.get(step_id, "")


def _summary_message(answers: dict, bp: dict) -> str:
    company = (bp or {}).get("company_name", "your company")
    return (
        f"Thanks — I now have a complete picture of {company}'s CX environment. "
        f"Your platform diagram is ready. Click any use case to explore it, "
        f"then continue to your AI Maturity Assessment when ready."
    )


def _enrich_step(step: dict, session) -> dict:
    """
    Enrich a step with dynamic content.
    flow_confirmation options come from discovery flows.
    """
    if not step or step.get("id") != "flow_confirmation":
        return step

    bp          = session.business_profile or {}
    company     = bp.get("company_name", "your business")
    discovery   = session.discovery or []
    options     = [f["flow_name"] for f in discovery] if discovery else [
        "Billing Inquiry", "Technical Support", "Outage Reporting",
        "Account Changes", "New Service Activation", "Retention / Win-back",
        "Payments", "Order Status", "Appointment Scheduling", "FAQ / General Inquiries",
    ]
    question = (
        f"Based on what I know about {company}, "
        f"these are the customer interaction flows I'd expect. "
        f"Select the ones that apply — deselect any that don't fit."
    )
    return {**step, "question": question, "options": options}