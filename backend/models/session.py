"""
models/session.py

Session model — replaces st.session_state across all ported modules.
Stored in Supabase, keyed by session_id (UUID).
All fields optional so partial sessions can be stored/restored.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ConversationMessage(BaseModel):
    role: str           # "assistant" | "user"
    content: str
    step_id: Optional[str] = None
    timestamp: Optional[str] = None


class SessionState(BaseModel):
    """
    Complete session state — mirrors all st.session_state keys
    used across the Streamlit app. Passed as `session` dict to
    all ported business logic functions.
    """

    # ── Identity ──
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # ── Intake ──
    intake_complete: bool = False
    intake_data: dict = Field(default_factory=dict)

    # ── Business profile (from inferencer) ──
    business_profile: dict = Field(default_factory=dict)
    inference_seeded: bool = False

    # ── Phase tracking ──
    current_phase: Any = 1  # int or str ("3r", "3b")
    phase_1_complete: bool = False
    phase_2_complete: bool = False
    phase_3_complete: bool = False
    phase_3r_complete: bool = False
    phase_3b_complete: bool = False
    phase_4_complete: bool = False

    # ── Discovery / conversation ──
    discovery: list = Field(default_factory=list)
    conv_answers: dict = Field(default_factory=dict)
    conv_messages: list[ConversationMessage] = Field(default_factory=list)
    conv_chip_selections: dict = Field(default_factory=dict)
    conv_other_text: dict = Field(default_factory=dict)
    conv_complete: bool = False
    conv_step_idx: int = 0

    # ── Assessment ──
    assessment: dict = Field(default_factory=dict)

    # ── Risk ──
    risk_assessment: dict = Field(default_factory=dict)

    # ── Business case ──
    business_case_results: dict = Field(default_factory=dict)
    business_case_prefilled: bool = False

    # ── Blueprint ──
    blueprint: dict = Field(default_factory=dict)

    # ── Vendor shortlist ──
    vendor_shortlist: list = Field(default_factory=list)

    # ── Discovery profile (schema adapter) ──
    discovery_profile: Optional[dict] = None

    # ── UI state (not persisted, but useful for API responses) ──
    savings_signal_dismissed: bool = False

    def to_dict(self) -> dict:
        """Return as plain dict for passing to ported business logic."""
        return self.model_dump()

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()
