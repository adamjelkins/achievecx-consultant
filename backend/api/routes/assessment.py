"""
api/routes/assessment.py
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.session_store import get_or_create_session, save_session

router = APIRouter()


@router.post("/{session_id}/run")
async def run_assessment(session_id: str):
    """Run AI maturity assessment. Caches result in session."""
    session = await get_or_create_session(session_id)

    confirmed = [f for f in session.discovery if f.get("confirmed")]
    if not confirmed:
        raise HTTPException(400, "No confirmed flows to assess")

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from maturity_assessment import run_assessment as _run
        result = _run(confirmed, session.business_profile)

        session.assessment        = result
        session.phase_3_complete  = True
        session.current_phase     = "3r"
        await save_session(session)
        return result

    except Exception as e:
        raise HTTPException(500, f"Assessment failed: {e}")


@router.get("/{session_id}")
async def get_assessment(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.assessment:
        raise HTTPException(404, "No assessment found — run it first")
    return session.assessment
