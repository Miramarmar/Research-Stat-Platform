"""
Ephemeral (No-Save) Session Store
----------------------------------
All data lives in Python process RAM only.
Nothing is written to disk, database, or logs.
Sessions auto-expire after 4 hours of inactivity.
"""
import json
import secrets
import threading
from datetime import datetime, timedelta

import pandas as pd

SESSION_TTL_HOURS = 4

_store: dict = {}
_lock = threading.Lock()


def create_ephemeral_session() -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        _store[token] = {
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now(),
            "dataframe": None,
            "column_types": {},
            "variable_roles": {},
            "composite_configs": [],
            "hypotheses": [],
            "results": [],
            "audit": [],
            "filters": [],
            "alpha": 0.05,
            "confidence_level": 95,
            "show_equations": True,
            "ai_enabled": False,
            "ai_disclaimer_accepted": False,
        }
    return token


def get_session(token: str) -> dict | None:
    with _lock:
        session = _store.get(token)
        if not session:
            return None
        if datetime.now() - session["last_active"] > timedelta(hours=SESSION_TTL_HOURS):
            del _store[token]
            return None
        session["last_active"] = datetime.now()
        return session


def set_dataframe(token: str, df: pd.DataFrame):
    with _lock:
        if token in _store:
            _store[token]["dataframe"] = df


def get_dataframe(token: str) -> pd.DataFrame | None:
    with _lock:
        s = _store.get(token)
        return s["dataframe"] if s else None


def update_session(token: str, key: str, value):
    with _lock:
        if token in _store:
            _store[token][key] = value
            _store[token]["last_active"] = datetime.now()


def append_audit(token: str, action: str, details: dict):
    with _lock:
        if token in _store:
            _store[token]["audit"].append({
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details,
            })


def append_result(token: str, result: dict):
    with _lock:
        if token in _store:
            _store[token]["results"].append(result)


def export_config(token: str) -> dict:
    """
    Export a reproducibility snapshot.
    Raw data (dataframe) is NEVER included — only analysis configuration.
    This allows another researcher to re-run the exact same analysis environment.
    """
    with _lock:
        s = _store.get(token)
        if not s:
            return {"error": "Session not found."}
        return {
            "export_version": "1.1",
            "exported_at": datetime.now().isoformat(),
            "session_mode": "ephemeral",
            "note": "Raw dataset not included. Re-import your data to reproduce this analysis.",
            "configuration": {
                "alpha": s.get("alpha", 0.05),
                "confidence_level": s.get("confidence_level", 95),
                "show_equations": s.get("show_equations", True),
                "column_types": s.get("column_types", {}),
                "variable_roles": s.get("variable_roles", {}),
                "composite_configs": s.get("composite_configs", []),
                "filters": s.get("filters", []),
            },
            "hypotheses": [
                {k: v for k, v in h.items() if k != "linked_result"}
                for h in s.get("hypotheses", [])
            ],
            "results_summary": [
                {k: v for k, v in r.items()
                 if k in ("test", "apa_string", "reject_h0",
                           "frequentist_conclusion", "p_value")}
                for r in s.get("results", [])
                if isinstance(r, dict) and "apa_string" in r
            ],
            "audit_trail": s.get("audit", []),
        }


def destroy_session(token: str):
    """Explicitly overwrite sensitive fields then delete — belt and suspenders."""
    with _lock:
        if token in _store:
            _store[token]["dataframe"] = None
            _store[token]["results"] = []
            _store[token]["audit"] = []
            _store[token]["hypotheses"] = []
            del _store[token]


def cleanup_expired() -> int:
    with _lock:
        expired = [
            t for t, s in _store.items()
            if datetime.now() - s["last_active"] > timedelta(hours=SESSION_TTL_HOURS)
        ]
        for t in expired:
            del _store[t]
    return len(expired)


def active_count() -> int:
    with _lock:
        return len(_store)
