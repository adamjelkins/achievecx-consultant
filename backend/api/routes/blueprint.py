"""
api/routes/blueprint.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _shim_session_state(session):
    import sys, types

    class DictNamespace(dict):
        def __getattr__(self, k): return self.get(k)
        def __setattr__(self, k, v): self[k] = v

    st_mock = types.ModuleType('streamlit')
    st_mock.spinner = lambda x: __import__('contextlib').nullcontext()
    st_mock.error   = lambda x: None
    st_mock.warning = lambda x: None
    st_mock.info    = lambda x: None

    ns = DictNamespace()
    ns['business_profile']      = session.business_profile or {}
    ns['discovery']             = session.discovery or []
    ns['conv_answers']          = session.conv_answers or {}
    ns['assessment']            = session.assessment or {}
    ns['risk_assessment']       = session.risk_assessment or {}
    ns['business_case_results'] = session.business_case_results or {}
    ns['intake_profile']        = session.intake_data or {
        'first_name':   'John',
        'last_name':    'Doe',
        'email':        'john.doe@att.com',
        'company_name': (session.business_profile or {}).get('company_name', ''),
    }
    ns['vendor_shortlist']      = session.vendor_shortlist or []
    ns['discovery_profile']     = session.discovery_profile or {}

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
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Blueprint generation failed: {e}")


@router.get("/{session_id}")
async def get_blueprint(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.blueprint:
        raise HTTPException(404, "No blueprint found — generate it first")
    return session.blueprint