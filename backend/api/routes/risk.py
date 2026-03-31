"""
api/routes/risk.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _shim_session_state(session):
    """Mock st.session_state for legacy Python modules that read from it."""
    import sys, types
    st_mock = types.ModuleType('streamlit')
    ns = types.SimpleNamespace()
    ns.conv_answers     = session.conv_answers
    ns.business_profile = session.business_profile
    ns.assessment       = session.assessment
    ns.discovery        = session.discovery
    ns.risk_assessment  = session.risk_assessment
    st_mock.session_state = ns
    sys.modules['streamlit'] = st_mock
    return st_mock


@router.post("/{session_id}/run")
async def run_risk(session_id: str):
    """Run risk assessment. Requires assessment to exist."""
    session = await get_or_create_session(session_id)

    if not session.assessment:
        raise HTTPException(400, "Run AI assessment first")

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _shim_session_state(session)
        from risk_calculator import run_risk_assessment
        result = run_risk_assessment()

        session.risk_assessment   = result
        session.phase_3r_complete = True
        session.current_phase     = "3b"
        await save_session(session)
        return result

    except Exception as e:
        raise HTTPException(500, f"Risk assessment failed: {e}")


@router.get("/{session_id}")
async def get_risk(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.risk_assessment:
        raise HTTPException(404, "No risk assessment found")
    return session.risk_assessment