"""
api/routes/sessions.py

Session management endpoints.
The frontend creates a session on first load and stores the
session_id in localStorage. All subsequent requests include it.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.session_store import get_session, save_session, create_session, get_or_create_session
from models.session import SessionState

router = APIRouter()


class SessionResponse(BaseModel):
    session_id: str
    current_phase: object
    phase_flags: dict
    intake_complete: bool


@router.post("/", response_model=SessionResponse)
async def new_session():
    """Create a new session. Called on first app load."""
    session = await create_session()
    return _session_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_info(session_id: str):
    """Get session status. Called on page reload to restore state."""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_response(session)


@router.get("/{session_id}/full")
async def get_full_session(session_id: str):
    """Get complete session state. Used for debug/admin."""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.delete("/{session_id}")
async def reset_session(session_id: str):
    """Reset session — creates fresh state with same ID."""
    session = SessionState(session_id=session_id)
    await save_session(session)
    return {"session_id": session_id, "reset": True}


def _session_response(session: SessionState) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        current_phase=session.current_phase,
        intake_complete=session.intake_complete,
        phase_flags={
            "phase_1": session.phase_1_complete,
            "phase_2": session.phase_2_complete,
            "phase_3": session.phase_3_complete,
            "phase_3r": session.phase_3r_complete,
            "phase_3b": session.phase_3b_complete,
            "phase_4": session.phase_4_complete,
        },
    )
