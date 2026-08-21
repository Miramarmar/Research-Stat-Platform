"""Session management — Standard (DB) and Ephemeral (RAM-only) modes."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from session.ephemeral_store import (
    create_ephemeral_session, get_session,
    update_session, destroy_session, export_config
)
from analytics.tracker import start_session, end_session

router = APIRouter()


class StartRequest(BaseModel):
    mode: str  # "standard" | "ephemeral"
    lab_id: Optional[str] = "external"
    device_type: Optional[str] = "desktop"


@router.post("/start")
def start(req: StartRequest):
    if req.mode == "ephemeral":
        token = create_ephemeral_session()
        return {
            "session_token": token,
            "mode": "ephemeral",
            "persisted": False,
            "message": (
                "No-Save Mode active. Nothing will be written to any database or disk. "
                "All data exists in server RAM only and is cleared when you end this session."
            ),
        }
    else:
        # Standard mode — track usage (no research data)
        tracking = start_session(req.lab_id, req.device_type)
        return {
            "session_token": tracking.get("session_id"),
            "mode": "standard",
            "persisted": True,
            "tracking_id": tracking.get("session_id"),
        }


class EndRequest(BaseModel):
    session_token: str
    mode: str
    started_at: Optional[str] = None


@router.post("/end")
def end(req: EndRequest):
    if req.mode == "ephemeral":
        destroy_session(req.session_token)
    else:
        if req.started_at:
            end_session(req.session_token, req.started_at)
    return {"ended": True}


class SettingsUpdate(BaseModel):
    alpha: Optional[float] = None
    confidence_level: Optional[int] = None
    show_equations: Optional[bool] = None
    ai_enabled: Optional[bool] = None
    ai_disclaimer_accepted: Optional[bool] = None


@router.patch("/settings")
def update_settings(req: SettingsUpdate,
                    session_token: str = Header(...),
                    mode: str = Header(...)):
    if mode == "ephemeral":
        session = get_session(session_token)
        if not session:
            raise HTTPException(404, "Session not found or expired.")
        for field, val in req.dict(exclude_none=True).items():
            update_session(session_token, field, val)
    return {"updated": True}


@router.get("/config/export")
def export_config_snapshot(session_token: str = Header(...),
                            mode: str = Header(...)):
    """Export reproducibility snapshot — raw data never included."""
    if mode == "ephemeral":
        config = export_config(session_token)
        return config
    return {"error": "Config export for standard mode not yet implemented."}
