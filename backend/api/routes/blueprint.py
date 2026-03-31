"""
api/routes/blueprint.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _shim_session_state(session):
    import sys, types
    st_mock = types.ModuleType('streamlit')
    ns = types.SimpleNamespace()
    ns.business_profile      = session.business_profile
    ns.discovery             = session.discovery
    ns.conv_answers          = session.conv_answers
    ns.assessment            = session.assessment
    ns.risk_assessment       = session.risk_assessment
    ns.business_case_results = session.business_case_results
    st_mock.session_state = ns
    sys.modules['streamlit'] = st_mock
    return st_mock


@router.post("/{session_id}/generate")
async def generate_blueprint(session_id: str):
    session = await get_or_create_session(session_id)

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _shim_session_state(session)
        from blueprint_generator import generate_blueprint as _generate
        result = _generate()

        session.blueprint        = result
        session.phase_4_complete = True
        await save_session(session)
        return result

    except Exception as e:
        raise HTTPException(500, f"Blueprint generation failed: {e}")


@router.get("/{session_id}")
async def get_blueprint(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.blueprint:
        raise HTTPException(404, "No blueprint found — generate it first")
    return session.blueprint