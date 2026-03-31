"""
api/routes/inference.py

Business inference endpoints.
Called after intake form submission — runs GPT domain inference
and flow pre-suggestion, returns business profile.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.session_store import get_or_create_session, save_session

router = APIRouter()


class IntakeRequest(BaseModel):
    session_id: str
    email: str
    first_name: str
    last_name: str
    company_name: str = ""
    phone: str = ""


class InferenceResponse(BaseModel):
    session_id: str
    business_profile: dict
    suggested_flows: list
    inference_seeded: bool


@router.post("/run", response_model=InferenceResponse)
async def run_inference(req: IntakeRequest):
    """
    Run full business inference from email domain.
    Stores result in session. Returns business profile + suggested flows.
    """
    session = await get_or_create_session(req.session_id)

    # Store intake data
    session.intake_complete = True
    session.intake_data = {
        "email":        req.email,
        "first_name":   req.first_name,
        "last_name":    req.last_name,
        "company_name": req.company_name,
        "phone":        req.phone,
    }

    try:
        # Import and run the existing business inferencer
        # We pass session as a dict to avoid st.session_state dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from business_inferencer import run_full_inference
        result = run_full_inference(req.email)

        # Override company name if provided in intake
        if req.company_name and result.get("business_profile"):
            result["business_profile"]["company_name"] = req.company_name

        session.business_profile   = result.get("business_profile", {})
        session.discovery          = result.get("suggested_flows", [])
        session.inference_seeded   = True
        session.phase_1_complete   = True
        session.current_phase      = 2

    except Exception as e:
        print(f"[inference] Failed: {e}")
        # Minimal fallback profile
        domain = req.email.split("@")[-1].split(".")[0] if "@" in req.email else "unknown"
        session.business_profile = {
            "company_name": req.company_name or domain,
            "domain":       req.email.split("@")[-1] if "@" in req.email else "",
            "industry":     "Unknown",
        }
        session.inference_seeded = True
        session.phase_1_complete = True
        session.current_phase    = 2

    await save_session(session)

    return InferenceResponse(
        session_id      = session.session_id,
        business_profile= session.business_profile,
        suggested_flows = session.discovery,
        inference_seeded= session.inference_seeded,
    )
