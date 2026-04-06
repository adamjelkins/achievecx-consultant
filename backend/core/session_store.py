"""
core/session_store.py

Session persistence layer.
Dev mode: JSON files on disk (shared across processes).
Production: Supabase.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional
from models.session import SessionState
from core.config import settings

# Dev: store sessions as JSON files in a temp directory
_DEV_STORE_DIR = Path(__file__).parent.parent / ".sessions"


def _dev_path(session_id: str) -> Path:
    _DEV_STORE_DIR.mkdir(exist_ok=True)
    return _DEV_STORE_DIR / f"{session_id}.json"


async def get_session(session_id: str) -> Optional[SessionState]:
    """Load session by ID. Returns None if not found."""
    if settings.app_env != "production" or not settings.supabase_url:
        path = _dev_path(session_id)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return SessionState(**data)
            except Exception as e:
                print(f"[session_store] Read failed: {e}")
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
        print(f"[session_store] Supabase get failed: {e}")

    return None


async def save_session(session: SessionState) -> bool:
    """Persist session. Returns True on success."""
    session.touch()

    if settings.app_env != "production" or not settings.supabase_url:
        try:
            path = _dev_path(session.session_id)
            path.write_text(session.model_dump_json())
            return True
        except Exception as e:
            print(f"[session_store] Write failed: {e}")
            return False

    try:
        from supabase import create_client
        sb = create_client(settings.supabase_url, settings.supabase_service_key)
        payload = {
            "session_id": session.session_id,
            "state":      session.model_dump_json(),
            "updated_at": session.updated_at,
        }
        sb.table("sessions").upsert(payload).execute()
        return True
    except Exception as e:
        print(f"[session_store] Supabase save failed: {e}")
        # Fall back to file
        try:
            _dev_path(session.session_id).write_text(session.model_dump_json())
        except Exception:
            pass
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