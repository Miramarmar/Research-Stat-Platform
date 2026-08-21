"""Central API router — all endpoint groups registered here."""
from fastapi import APIRouter
from api import sessions, data, statistics, hypotheses, ai_assistant, reports, admin

api_router = APIRouter()
api_router.include_router(sessions.router,     prefix="/sessions",    tags=["Sessions"])
api_router.include_router(data.router,         prefix="/data",        tags=["Data"])
api_router.include_router(statistics.router,   prefix="/stats",       tags=["Statistics"])
api_router.include_router(hypotheses.router,   prefix="/hypotheses",  tags=["Hypotheses"])
api_router.include_router(ai_assistant.router, prefix="/ai",          tags=["AI Assistant"])
api_router.include_router(reports.router,      prefix="/reports",     tags=["Reports"])
api_router.include_router(admin.router,        prefix="/admin",       tags=["Admin"])
