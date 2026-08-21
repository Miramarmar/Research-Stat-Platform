"""
Admin Usage Analytics Tracker
--------------------------------
Records ONLY: session counts, duration, feature usage, device type, lab ID.
NEVER stores: dataset content, variable names, results, researcher identity.
This module is completely isolated from all research data tables.
"""
import os
from datetime import datetime

try:
    from supabase import create_client
    _sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))
    _db_available = True
except Exception:
    _sb = None
    _db_available = False


def start_session(lab_id: str = "external", device_type: str = "desktop") -> dict:
    if not _db_available:
        return {"session_id": "no-db", "tracked": False}
    try:
        res = _sb.table("usage_sessions").insert({
            "lab_id": lab_id,
            "device_type": device_type,
            "started_at": datetime.now().isoformat(),
        }).execute()
        return {"session_id": res.data[0]["id"], "tracked": True}
    except Exception:
        return {"session_id": "error", "tracked": False}


def end_session(session_id: str, started_at: str):
    if not _db_available or session_id in ("no-db", "error"):
        return
    try:
        start = datetime.fromisoformat(started_at)
        duration = int((datetime.now() - start).total_seconds())
        _sb.table("usage_sessions").update({
            "ended_at": datetime.now().isoformat(),
            "duration_seconds": duration,
        }).eq("id", session_id).execute()
    except Exception:
        pass


def log_feature_event(session_id: str, feature_name: str, ai_enabled: bool = False):
    """Called each time a researcher runs an analysis module."""
    if not _db_available or session_id in ("no-db", "error"):
        return
    try:
        _sb.table("usage_feature_events").insert({
            "session_id": session_id,
            "feature_name": feature_name,
            "ai_enabled": ai_enabled,
            "occurred_at": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


def get_dashboard_summary() -> dict:
    """Admin-only read. Aggregated usage — no research data ever touched."""
    if not _db_available:
        return _mock_summary()
    try:
        res = _sb.rpc("get_dashboard_summary").execute()
        return res.data
    except Exception:
        return _mock_summary()


def _mock_summary() -> dict:
    """Returned when DB is unavailable (dev mode)."""
    return {
        "total_users": 0,
        "sessions_last_30d": 0,
        "avg_session_minutes": 0,
        "ai_adoption_rate": 0,
        "most_used_features": [],
        "daily_active_users": [],
        "note": "Database not connected — showing empty dashboard.",
    }
