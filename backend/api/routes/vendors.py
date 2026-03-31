"""
api/routes/vendors.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _shim_session_state(session):
    import sys, types
    st_mock = types.ModuleType('streamlit')
    ns = types.SimpleNamespace()
    ns.discovery        = session.discovery
    ns.conv_answers     = session.conv_answers
    ns.business_profile = session.business_profile
    ns.assessment       = session.assessment
    st_mock.session_state = ns
    sys.modules['streamlit'] = st_mock


@router.post("/{session_id}/score")
async def score_vendors(session_id: str):
    session = await get_or_create_session(session_id)

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _shim_session_state(session)
        from vendor_catalog import run_vendor_shortlist
        result = run_vendor_shortlist()

        session.vendor_shortlist = result
        await save_session(session)
        return result

    except Exception as e:
        raise HTTPException(500, f"Vendor scoring failed: {e}")


@router.get("/{session_id}")
async def get_vendors(session_id: str):
    session = await get_or_create_session(session_id)
    return session.vendor_shortlist or []