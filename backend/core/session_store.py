"""
core/session_store.py

Session persistence layer.
Dev mode: in-memory dict.
Production: Supabase (postgres).

All business logic functions receive session as a plain dict.
This module handles load/save around those calls.
"""

from __future__ import annotations
import json
from typing import Optional
from models.session import SessionState
from core.config import settings

# ── In-memory store (dev / fallback) ──
_memory_store: dict[str, dict] = {}


async def get_session(session_id: str) -> Optional[SessionState]:
    """Load session by ID. Returns None if not found."""
    if settings.app_env == "development" or not settings.supabase_url:
        data = _memory_store.get(session_id)
        if data:
            return SessionState(**data)
        return None

    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_key)
        result = sb.table("sessions").select("*").eq("session_id", session_id).single().execute()
        if result.data:
            state_data = result.data.get("state", {})
            if isinstance(state_data, str):
                state_data = json.loads(state_data)
            return SessionState(**state_data)
    except Exception as e:
        print(f"[session_store] get failed: {e}")

    return None


async def save_session(session: SessionState) -> bool:
    """Persist session. Returns True on success."""
    session.touch()

    if settings.app_env == "development" or not settings.supabase_url:
        _memory_store[session.session_id] = session.model_dump()
        return True

    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_key)
        payload = {
            "session_id": session.session_id,
            "state": session.model_dump_json(),
            "updated_at": session.updated_at,
        }
        sb.table("sessions").upsert(payload).execute()
        return True
    except Exception as e:
        print(f"[session_store] save failed: {e}")
        # Fall back to memory
        _memory_store[session.session_id] = session.model_dump()
        return False


async def create_session() -> SessionState:
    """Create a new session and persist it."""
    session = SessionState()
    await save_session(session)
    return session


async def get_or_create_session(session_id: Optional[str]) -> SessionState:
    """Load existing session or create a new one."""
    if session_id:
        session = await get_session(session_id)
        if session:
            return session
    return await create_session()
