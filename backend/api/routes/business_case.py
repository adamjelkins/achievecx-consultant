"""
api/routes/business_case.py
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.session_store import get_or_create_session, save_session

router = APIRouter()


class BusinessCaseRunRequest(BaseModel):
    session_id: str
    inputs: Optional[dict] = None   # None = use prefilled defaults


@router.post("/run")
async def run_business_case(req: BusinessCaseRunRequest):
    session = await get_or_create_session(req.session_id)

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from business_case_calculator import run_business_case as _run, prefill_from_session, BusinessCaseInputs

        if req.inputs:
            inputs = BusinessCaseInputs(**req.inputs)
        else:
            inputs = prefill_from_session(session.to_dict())

        result = _run(inputs)

        session.business_case_results = result
        session.phase_3b_complete     = True
        session.current_phase         = 4
        await save_session(session)
        return result

    except Exception as e:
        raise HTTPException(500, f"Business case failed: {e}")


@router.get("/{session_id}/prefill")
async def get_prefill(session_id: str):
    """Get prefilled business case inputs from session data."""
    session = await get_or_create_session(session_id)

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from business_case_calculator import prefill_from_session
        inputs = prefill_from_session(session.to_dict())
        return inputs.__dict__
    except Exception as e:
        raise HTTPException(500, f"Prefill failed: {e}")


@router.get("/{session_id}")
async def get_business_case(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.business_case_results:
        raise HTTPException(404, "No business case found")
    return session.business_case_results
