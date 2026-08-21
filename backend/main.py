"""
Research-Grade Statistical & AI-Assisted Analysis Platform
Backend Entry Point — FastAPI

Architecture:
  - Deterministic engine: SciPy / StatsModels / Pandas ONLY (LLM never calculates math)
  - AI layer: optional, toggleable — thematic analysis + plain-language translation only
  - Session modes: "standard" (Supabase-persisted) | "ephemeral" (RAM-only, zero persistence)
  - Admin dashboard: usage telemetry only — never touches research data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import threading, time, os

load_dotenv()

from api.router import api_router
from session.ephemeral_store import cleanup_expired

app = FastAPI(
    title="ResearchStat Platform",
    description=(
        "Academic statistical analysis platform. "
        "Deterministic engine + optional, strictly-separated AI assistance. "
        "Built for HCI, psychology, education, and social science researchers."
    ),
    version="1.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")

# ── Background cleanup: expire idle ephemeral sessions every 30 min ──────────
def _cleanup_loop():
    while True:
        time.sleep(1800)
        n = cleanup_expired()
        if n:
            print(f"[cleanup] Expired {n} ephemeral session(s).")

threading.Thread(target=_cleanup_loop, daemon=True).start()

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    from session.ephemeral_store import active_count
    return {
        "status": "ok",
        "version": "1.1.0",
        "ephemeral_sessions_active": active_count(),
    }
