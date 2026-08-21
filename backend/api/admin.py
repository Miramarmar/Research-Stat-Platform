"""
Admin dashboard — usage telemetry ONLY.
Research data, dataset contents, and individual results are NEVER accessible here.
Spec: restricted telemetry view for lab administrators only.

Auth: In production, replace the simple role header check with proper JWT role validation.
"""
from fastapi import APIRouter, Header, HTTPException
from analytics.tracker import get_dashboard_summary, log_feature_event

router = APIRouter()


def _require_admin(role: str):
    """
    Production: decode JWT and check role claim.
    Development: accept 'admin' string header for simplicity.
    """
    if role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail=(
                "Admin access required. "
                "This endpoint is restricted to lab administrators only."
            ),
        )


@router.get("/dashboard")
def get_admin_dashboard(
    session_token: str = Header(...),
    role: str = Header(default=""),
):
    """
    Returns aggregated usage analytics ONLY.
    Privacy guarantees (displayed to admin on every response):
      - No research data, dataset contents, or individual results accessible here.
      - Researchers who chose No-Save Mode are not counted — by design.
      - Only Standard Mode session metadata is tracked.
    """
    _require_admin(role)
    summary = get_dashboard_summary()
    return {
        **summary,
        "privacy_guarantees": {
            "research_data_visible": False,
            "dataset_contents_visible": False,
            "individual_results_visible": False,
            "no_save_mode_tracked": False,
            "note": (
                "This dashboard shows usage patterns only. "
                "No research data, dataset contents, or individual results are "
                "accessible here. Researchers who chose No-Save Mode are not "
                "counted — their sessions leave no trace in the system by design."
            ),
        },
    }


@router.post("/event")
def track_feature_event(
    session_id: str,
    feature_name: str,
    ai_enabled: bool = False,
    role: str = Header(default=""),
):
    """
    Called by frontend when a researcher uses a feature.
    Logs ONLY: feature name, AI toggle state, session ID.
    NO content from the analysis is logged.
    """
    log_feature_event(session_id, feature_name, ai_enabled)
    return {"logged": True}
