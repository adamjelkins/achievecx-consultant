"""
api/routes/conversation.py

Discovery conversation endpoints.
The CX Explorer component calls these as the advisor
progresses through the 10-step conversation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from core.session_store import get_or_create_session, save_session

router = APIRouter()


class AnswerRequest(BaseModel):
    session_id: str
    step_id: str
    answer: Any                    # str | list[str] depending on step type
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


@router.get("/{session_id}/state", response_model=ConversationStateResponse)
async def get_conversation_state(session_id: str):
    """Get current conversation state — called on CX Explorer mount."""
    session = await get_or_create_session(session_id)

    steps = _get_steps()
    idx   = session.conv_step_idx
    step  = steps[idx] if idx < len(steps) else None

    return ConversationStateResponse(
        session_id      = session.session_id,
        messages        = [m.model_dump() for m in session.conv_messages],
        current_step    = step,
        current_step_idx= idx,
        progress_pct    = _progress_pct(idx, len(steps)),
        is_complete     = session.conv_complete,
        answers         = session.conv_answers,
        discovery       = session.discovery,
    )


@router.post("/answer", response_model=ConversationStateResponse)
async def record_answer(req: AnswerRequest):
    """
    Record an answer and advance the conversation.
    Returns updated conversation state including any new messages.
    """
    session = await get_or_create_session(req.session_id)

    if session.conv_complete:
        raise HTTPException(400, "Conversation already complete")

    steps = _get_steps()
    idx   = session.conv_step_idx

    if idx >= len(steps):
        raise HTTPException(400, "No more steps")

    step = steps[idx]

    # Store the answer
    session.conv_answers[req.step_id]         = req.answer
    session.conv_chip_selections[req.step_id] = req.chip_selections
    session.conv_other_text[req.step_id]      = req.other_text

    # Add user message
    from models.session import ConversationMessage
    from datetime import datetime
    answer_str = _answer_to_str(req.answer, req.chip_selections, req.other_text)
    session.conv_messages.append(ConversationMessage(
        role      = "user",
        content   = answer_str,
        step_id   = req.step_id,
        timestamp = datetime.utcnow().isoformat(),
    ))

    # Advance step
    next_idx = idx + 1
    session.conv_step_idx = next_idx

    # Add acknowledgment + next question
    ack = _get_acknowledgment(req.step_id, answer_str)
    if ack:
        session.conv_messages.append(ConversationMessage(
            role    = "assistant",
            content = ack,
            step_id = req.step_id,
        ))

    if next_idx < len(steps):
        next_step = steps[next_idx]
        session.conv_messages.append(ConversationMessage(
            role    = "assistant",
            content = next_step["question"],
            step_id = next_step["id"],
        ))
    else:
        # Conversation complete
        session.conv_complete    = True
        session.phase_2_complete = True
        session.current_phase    = 3
        session.conv_messages.append(ConversationMessage(
            role    = "assistant",
            content = _summary_message(session.conv_answers, session.business_profile),
        ))

    # Update discovery flows based on channel answer
    if req.step_id == "channels" and session.discovery:
        session.discovery = _filter_flows_by_channels(
            session.discovery, req.answer
        )

    await save_session(session)

    next_step_data = steps[next_idx] if next_idx < len(steps) else None

    return ConversationStateResponse(
        session_id      = session.session_id,
        messages        = [m.model_dump() for m in session.conv_messages],
        current_step    = next_step_data,
        current_step_idx= next_idx,
        progress_pct    = _progress_pct(next_idx, len(steps)),
        is_complete     = session.conv_complete,
        answers         = session.conv_answers,
        discovery       = session.discovery,
    )


@router.post("/{session_id}/confirm-flow")
async def confirm_flow(session_id: str, flow_id: str, confirmed: bool = True):
    """Toggle flow confirmation from the diagram."""
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
        # Already initialized
        return await get_conversation_state(session_id)

    from models.session import ConversationMessage
    steps = _get_steps()

    bp          = session.business_profile
    company     = bp.get("company_name", "your company")
    first_name  = session.intake_data.get("first_name", "")

    greeting = (
        f"Great to meet you{', ' + first_name if first_name else ''}. "
        f"I've already researched {company} and identified some likely customer interaction flows. "
        f"Let me ask you a few quick questions to sharpen the picture."
    )

    session.conv_messages.append(ConversationMessage(
        role="assistant", content=greeting
    ))

    if steps:
        session.conv_messages.append(ConversationMessage(
            role    = "assistant",
            content = steps[0]["question"],
            step_id = steps[0]["id"],
        ))

    await save_session(session)
    return await get_conversation_state(session_id)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _get_steps() -> list:
    """Return the 10 conversation steps."""
    # Import from the existing conversation engine
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from conversation_engine import STEPS
        return STEPS
    except Exception:
        return []


def _progress_pct(idx: int, total: int) -> int:
    if total == 0:
        return 0
    return min(int((idx / total) * 100), 100)


def _answer_to_str(answer: Any, chips: list, other: str) -> str:
    if chips:
        parts = list(chips)
        if other:
            parts.append(other)
        return ", ".join(parts)
    if isinstance(answer, list):
        return ", ".join(str(a) for a in answer)
    return str(answer) if answer is not None else ""


def _get_acknowledgment(step_id: str, answer: str) -> str:
    acks = {
        "flow_confirmation": "Good — I've noted those flows.",
        "regions":           "Got it.",
        "channels":          "Good to know. Multi-channel coverage is key for modern CX.",
        "volume":            f"Understood. {answer} contacts sets the scale.",
        "pain_point":        "That's a common challenge — we'll address it in the assessment.",
        "automation":        "Good baseline to work from.",
        "crm":               "Noted.",
        "cc_platform":       "Good.",
        "goal":              "Clear. That'll shape our recommendations.",
        "timeline":          "Understood.",
    }
    return acks.get(step_id, "")


def _summary_message(answers: dict, bp: dict) -> str:
    company = bp.get("company_name", "your company")
    return (
        f"Thanks — I now have a complete picture of {company}'s CX environment. "
        f"Your platform diagram is ready. Click any use case to explore it, "
        f"then continue to your AI Maturity Assessment when ready."
    )


def _filter_flows_by_channels(discovery: list, channels: Any) -> list:
    """Keep all flows — channel filtering happens at diagram render time."""
    return discovery
