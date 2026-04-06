"""
api/routes/assessment.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _mock_streamlit(session):
    """Mock st.session_state before importing streamlit-dependent modules."""
    import sys, types
    if 'streamlit' not in sys.modules:
        st_mock = types.ModuleType('streamlit')
        st_mock.session_state = types.SimpleNamespace()
        # Mock other streamlit functions used in modules
        st_mock.spinner = lambda x: __import__('contextlib').nullcontext()
        st_mock.error   = lambda x: None
        st_mock.warning = lambda x: None
        st_mock.info    = lambda x: None
        sys.modules['streamlit'] = st_mock
    import streamlit as st
    if session:
        st.session_state.business_profile = session.business_profile
        st.session_state.discovery        = session.discovery
        st.session_state.conv_answers     = session.conv_answers
        st.session_state.assessment       = session.assessment


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
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _mock_streamlit(session)
        from maturity_assessment import run_assessment as _run
        result = _run(confirmed, session.business_profile)

        session.assessment       = result
        session.phase_3_complete = True
        session.current_phase    = "3r"
        await save_session(session)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Assessment failed: {e}")


@router.get("/{session_id}")
async def get_assessment(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.assessment:
        raise HTTPException(404, "No assessment found — run it first")
    return session.assessment