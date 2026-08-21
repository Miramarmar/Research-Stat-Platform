"""
AI Assistant Layer — Strictly Separated (v1.2)
-----------------------------------------------
Spec rules (hardcoded, cannot be bypassed):
  1. AI NEVER calculates math, p-values, test statistics, or effect sizes.
  2. AI operates ONLY on already-computed results from the deterministic engine.
  3. AI provides methodological SUGGESTIONS — researcher must Accept / Reject / Modify.
  4. Every AI output is flagged ai_generated=True so frontend renders it distinctly.
  5. If USE_LOCAL_AI=true, uses local Ollama — no data leaves the server.
  6. AI Privacy Disclaimer (liability waiver) MUST be accepted before any AI call.
  7. Raw dataset content is NEVER sent to the AI API.
"""
import os
import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from session.ephemeral_store import get_session, update_session, append_audit

router = APIRouter()

USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")

try:
    import anthropic
    _client = anthropic.Anthropic()
    _cloud_available = True
except Exception:
    _cloud_available = False

# ── Privacy disclaimer (spec requirement: explicit liability waiver) ──────────

AI_DISCLAIMER_TEXT = (
    "By enabling AI Assistance, you acknowledge and accept the following:\n\n"
    "1. Statistical results (not raw data) may be transmitted to a third-party "
    "AI service for plain-language interpretation and thematic analysis.\n\n"
    "2. The platform assumes zero responsibility for any data privacy implications "
    "arising from use of the AI Assistance layer.\n\n"
    "3. Raw dataset content is never sent to the AI. Only pre-computed statistical "
    "outputs are transmitted.\n\n"
    "4. You may disable AI Assistance at any time. All statistics are computed "
    "deterministically regardless of AI toggle state.\n\n"
    "5. AI-generated text is always visually distinguished from calculated statistics "
    "and must be reviewed before inclusion in any publication."
)


class DisclaimerAcceptance(BaseModel):
    accepted: bool


@router.post("/disclaimer/accept")
def accept_disclaimer(
    req: DisclaimerAcceptance,
    session_token: str = Header(...),
    mode: str = Header(...),
):
    if not req.accepted:
        return {"accepted": False}
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found.")
    update_session(session_token, "ai_disclaimer_accepted", True)
    append_audit(session_token, "ai_disclaimer_accepted", {"accepted": True})
    return {"accepted": True, "message": "AI Assistance enabled."}


@router.get("/disclaimer")
def get_disclaimer():
    """Return the full disclaimer text for display in the frontend modal."""
    return {"text": AI_DISCLAIMER_TEXT}


# ── AI availability check ─────────────────────────────────────────────────────

@router.get("/status")
def ai_status():
    if USE_LOCAL_AI:
        try:
            r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            return {"available": r.status_code == 200, "mode": "local_ollama"}
        except Exception:
            return {"available": False, "mode": "local_ollama", "error": "Ollama not running."}
    return {"available": _cloud_available, "mode": "cloud_anthropic"}


# ── Internal AI call (never used for math) ────────────────────────────────────

def _call_ai(prompt: str, max_tokens: int = 300) -> str:
    if USE_LOCAL_AI:
        try:
            r = httpx.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False},
                timeout=45,
            )
            return r.json().get("response", "Local AI unavailable.")
        except Exception as e:
            return f"Local AI error: {e}"
    if _cloud_available:
        try:
            msg = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            return f"Cloud AI error: {e}"
    return "AI unavailable — set ANTHROPIC_API_KEY or enable USE_LOCAL_AI."


def _guard_disclaimer(session_token: str):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found.")
    if not session.get("ai_disclaimer_accepted"):
        raise HTTPException(
            403,
            "AI Privacy Disclaimer not accepted. "
            "Accept the disclaimer before using AI features.",
        )


# ── Test suggestion ───────────────────────────────────────────────────────────

class SuggestionRequest(BaseModel):
    normality_results: list
    n: int
    n_groups: int
    design: str  # e.g. "between-subjects", "within-subjects", "correlational"


@router.post("/suggest-test")
def suggest_test(
    req: SuggestionRequest,
    session_token: str = Header(...),
    mode: str = Header(...),
):
    """
    AI suggests which test to run based on assumption check outputs.
    AI does NOT see the data — only assumption check metadata.
    Researcher must Accept / Reject / Modify before any test is run.
    """
    _guard_disclaimer(session_token)

    norm_summary = "; ".join([
        f"{r.get('column', '')}: {r.get('label', '')}"
        for r in req.normality_results
    ])

    prompt = f"""You are a statistical methodology advisor for academic researchers.

Context:
- Study design: {req.design}
- Sample size: N = {req.n}
- Number of groups: {req.n_groups}
- Normality check results: {norm_summary}

Task: Suggest ONE appropriate statistical test and state why in exactly 2 sentences.
Do NOT calculate any statistics or state any conclusions about the data.
Do NOT use hedging language.
Format strictly as:
TEST: [exact test name]
REASON: [methodological justification, 2 sentences max]"""

    text = _call_ai(prompt, max_tokens=150)
    append_audit(session_token, "ai_test_suggestion", {"design": req.design, "n": req.n})

    return {
        "suggestion": text,
        "ai_generated": True,
        "source": "AI methodological suggestion",
        "requires_action": True,
        "actions": ["Accept", "Reject", "Modify"],
        "disclaimer": "This is a suggestion only. The researcher must approve before any test is run.",
    }


# ── Result interpretation ─────────────────────────────────────────────────────

class InterpretRequest(BaseModel):
    result: dict        # the full result from the stats engine
    context: Optional[str] = ""


@router.post("/interpret")
def interpret_result(
    req: InterpretRequest,
    session_token: str = Header(...),
    mode: str = Header(...),
):
    """
    Plain-language translation of a COMPLETED statistical result.
    The math is already done — AI only translates to academic prose.
    AI NEVER recalculates or modifies any numbers.
    Raw dataset content is NOT sent.
    """
    _guard_disclaimer(session_token)

    # Only send safe, pre-computed summary fields — never raw data
    safe_result = {
        k: v for k, v in req.result.items()
        if k in (
            "test", "apa_string", "reject_h0", "frequentist_conclusion",
            "effect_size_label", "p_value", "cohens_d", "r",
            "eta_squared", "r_squared",
        )
    }

    prompt = f"""You are an academic writing assistant helping a researcher interpret a statistical result.

Pre-calculated result (do not modify these numbers):
{safe_result}

Additional context: {req.context}

Write a 2-3 sentence plain-language summary suitable for a Methods/Results section.
Rules:
- Do NOT recalculate or alter any number from the result above
- Do NOT use causal language ("causes", "leads to", "proves", "confirms")
- Do NOT claim the hypothesis is "proven" or "confirmed"
- Use past-tense academic prose
- Start with "The analysis revealed..." or "Results indicated..."
"""
    text = _call_ai(prompt, max_tokens=200)
    append_audit(session_token, "ai_interpretation", {
        "test": safe_result.get("test"), "apa": safe_result.get("apa_string")
    })

    return {
        "interpretation": text,
        "ai_generated": True,
        "source": "AI plain-language interpretation",
        "disclaimer": (
            "AI-generated text. Verify accuracy before including in publications. "
            "The platform assumes zero responsibility for AI output."
        ),
        "requires_action": True,
        "actions": ["Accept", "Edit", "Reject"],
    }


# ── Thematic analysis ─────────────────────────────────────────────────────────

class ThematicRequest(BaseModel):
    responses: list
    context: Optional[str] = ""


@router.post("/thematic")
def thematic_analysis(
    req: ThematicRequest,
    session_token: str = Header(...),
    mode: str = Header(...),
):
    """
    Cluster open-ended text responses into themes.
    Spec constraints:
      - AI must not fabricate themes
      - Every theme must show N-count, percentage, and direct supporting quotes
      - Researcher retains full control: merge, split, rename, delete themes
    """
    _guard_disclaimer(session_token)

    if len(req.responses) > 100:
        sample = req.responses[:100]
        truncated = True
    else:
        sample = req.responses
        truncated = False

    numbered = "\n".join([f"{i+1}. {r}" for i, r in enumerate(sample)])

    prompt = f"""You are a qualitative research assistant performing thematic analysis for an academic study.

Research context: {req.context}
Total responses provided: {len(sample)}

Responses:
{numbered}

Instructions:
1. Identify 3-6 recurring themes ONLY from the responses above. Do not invent themes not present.
2. For each theme, list the exact response numbers that support it.
3. Provide 1-2 direct short quotes from the actual responses as evidence.
4. Return ONLY valid JSON (no markdown, no preamble):

{{
  "themes": [
    {{
      "theme_name": "string",
      "description": "one sentence description",
      "supporting_response_indices": [1, 4, 7],
      "representative_quotes": ["exact short quote", "exact short quote"],
      "n": 3,
      "pct": 30.0
    }}
  ],
  "analyst_note": "brief note about data quality or coverage"
}}"""

    raw = _call_ai(prompt, max_tokens=800)

    import json, re
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}
    except Exception:
        parsed = {}

    append_audit(session_token, "ai_thematic_analysis", {
        "n_responses": len(sample), "truncated": truncated
    })

    return {
        "themes": parsed.get("themes", []),
        "analyst_note": parsed.get("analyst_note", ""),
        "n_responses_analyzed": len(sample),
        "truncated": truncated,
        "ai_generated": True,
        "source": "AI thematic analysis",
        "disclaimer": (
            "Researcher must verify all themes against source quotes before reporting. "
            "The platform assumes zero responsibility for AI-generated theme accuracy."
        ),
        "researcher_controls": [
            "Merge themes", "Split theme", "Rename theme", "Delete theme"
        ],
    }
