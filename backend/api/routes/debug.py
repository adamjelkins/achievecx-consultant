"""
api/routes/debug.py

Development-only endpoints.
Not registered in production (APP_ENV check in main.py).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.session_store import get_or_create_session, save_session
from core.config import settings

router = APIRouter()

# Default flows to confirm if inference returns nothing
DEFAULT_TEST_FLOWS = [
    {"flow_id": "flow_001", "flow_name": "Billing Inquiry",         "category": "Billing",  "confirmed": True, "confidence": 0.95},
    {"flow_id": "flow_002", "flow_name": "Technical Support",       "category": "Support",  "confirmed": True, "confidence": 0.90},
    {"flow_id": "flow_003", "flow_name": "Outage Reporting",        "category": "Support",  "confirmed": True, "confidence": 0.85},
    {"flow_id": "flow_004", "flow_name": "Account Changes",         "category": "Account",  "confirmed": True, "confidence": 0.80},
    {"flow_id": "flow_005", "flow_name": "New Service Activation",  "category": "Sales",    "confirmed": True, "confidence": 0.75},
    {"flow_id": "flow_006", "flow_name": "Retention / Win-back",    "category": "Retention","confirmed": True, "confidence": 0.70},
]


class SeedRequest(BaseModel):
    session_id: str
    conv_answers: dict


@router.post("/seed-session")
async def seed_session(req: SeedRequest):
    """Seed conv_answers and confirmed flows directly."""
    if settings.app_env == "production":
        raise HTTPException(403, "Not available in production")

    session = await get_or_create_session(req.session_id)

    session.conv_answers     = req.conv_answers
    session.conv_complete    = True
    session.phase_2_complete = True
    session.current_phase    = 3

    # Try to confirm from existing discovery flows
    confirmed_names = req.conv_answers.get("flow_confirmation", [])
    if isinstance(confirmed_names, str):
        confirmed_names = [confirmed_names]

    if session.discovery:
        for flow in session.discovery:
            flow["confirmed"] = (
                flow.get("flow_name", "") in confirmed_names
                or flow.get("confirmed", False)
            )
        # If still none confirmed, confirm top 6
        confirmed = [f for f in session.discovery if f.get("confirmed")]
        if not confirmed:
            for flow in session.discovery[:6]:
                flow["confirmed"] = True
    else:
        # No flows from inference — use defaults
        session.discovery = DEFAULT_TEST_FLOWS

    # Ensure business profile has required fields
    if not session.business_profile:
        session.business_profile = {
            "company_name": "AT&T",
            "domain":       "att.com",
            "industry":     "Telecom",
        }

    await save_session(session)

    confirmed_count = len([f for f in session.discovery if f.get("confirmed")])
    return {
        "seeded": True,
        "session_id": session.session_id,
        "confirmed_flows": confirmed_count,
        "discovery_count": len(session.discovery),
    }


@router.get("/session/{session_id}")
async def get_debug_session(session_id: str):
    """Get full session state for debugging."""
    if settings.app_env == "production":
        raise HTTPException(403, "Not available in production")
    session = await get_or_create_session(session_id)
    return session.model_dump()