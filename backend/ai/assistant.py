"""
AI Assistant Layer — Strictly Separated
-----------------------------------------
Rules (hardcoded, cannot be bypassed):
  1. AI NEVER calculates math, p-values, test statistics, or effect sizes.
  2. AI operates ONLY on already-computed results for plain-language translation.
  3. AI provides methodological SUGGESTIONS only — researcher must Accept/Reject/Modify.
  4. Every AI output is flagged ai_generated=True so frontend renders it distinctly.
  5. If USE_LOCAL_AI=true, uses local Ollama — no data leaves the server.
  6. AI Privacy Disclaimer MUST be accepted before any AI call is made.
"""
import os
import httpx

USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

try:
from groq import Groq
_client = Groq()  # reads GROQ_API_KEY from environment
    _cloud_available = True
except Exception:
    _cloud_available = False


def _call_ai(prompt: str, max_tokens: int = 300) -> str:
    if USE_LOCAL_AI:
        try:
            r = httpx.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False},
                timeout=30,
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


def suggest_test(normality_results: list, n: int, n_groups: int, design: str) -> dict:
    """
    Methodological test suggestion based on assumption check outputs.
    AI does NOT see the data — only the assumption check metadata.
    """
    norm_summary = "; ".join([
        f"{r.get('column','')}: {r.get('label','')}" for r in normality_results
    ])
    prompt = f"""You are a statistical methodology advisor for academic researchers.

Context:
- Study design: {design}
- Sample size: N = {n}
- Number of groups: {n_groups}
- Normality check results: {norm_summary}

Task: Suggest ONE appropriate statistical test and state why in exactly 2 sentences.
Do NOT calculate any statistics or state any conclusions about the data.
Do NOT use hedging language like "I think" or "perhaps".
Format your response strictly as:
TEST: [exact test name]
REASON: [methodological justification, 2 sentences max]"""

    text = _call_ai(prompt, max_tokens=150)
    return {
        "suggestion": text,
        "ai_generated": True,
        "source": "AI methodological suggestion",
        "requires_action": True,
        "actions": ["Accept", "Reject", "Modify"],
        "disclaimer": "This is a suggestion only. The researcher must approve before any test is run.",
    }


def interpret_result(result: dict, context: str = "") -> dict:
    """
    Plain-language translation of a COMPLETED statistical result.
    The math is already done — AI only translates to readable prose.
    AI NEVER recalculates or modifies any numbers.
    """
    safe_result = {
        k: v for k, v in result.items()
        if k in ("test", "apa_string", "reject_h0", "frequentist_conclusion",
                  "effect_size_label", "p_value", "cohens_d", "r", "eta_squared")
    }

    prompt = f"""You are an academic writing assistant helping a researcher interpret a statistical result.

Pre-calculated result (do not modify these numbers):
{safe_result}

Additional context: {context}

Write a 2-3 sentence plain-language summary of what this result means for a researcher's paper.
Rules:
- Do NOT recalculate or restate numbers already in the APA string
- Do NOT use causal language ("causes", "leads to", "proves")
- Do NOT claim the hypothesis is "confirmed" or "proven"
- Use past tense academic prose
- Start with "The analysis revealed..." or "Results indicated..."
"""
    text = _call_ai(prompt, max_tokens=200)
    return {
        "interpretation": text,
        "ai_generated": True,
        "source": "AI plain-language interpretation",
        "disclaimer": "AI-generated text. Verify before including in publications.",
        "requires_action": True,
        "actions": ["Accept", "Edit", "Reject"],
    }


def thematic_analysis(responses: list, context: str = "") -> dict:
    """
    Cluster open-ended responses into themes.
    CONSTRAINT: Every theme MUST cite N and % of responses + direct quotes.
    AI must not fabricate themes not present in the data.
    """
    if len(responses) > 100:
        sample = responses[:100]
        truncated = True
    else:
        sample = responses
        truncated = False

    numbered = "\n".join([f"{i+1}. {r}" for i, r in enumerate(sample)])

    prompt = f"""You are a qualitative research assistant performing thematic analysis.

Research context: {context}
Total responses provided: {len(sample)}

Responses:
{numbered}

Instructions:
1. Identify 3-6 recurring themes ONLY from the responses above. Do not invent themes.
2. For each theme, list the exact response numbers (from the numbered list) that support it.
3. Provide 1-2 direct short quotes from the responses as evidence.
4. Return ONLY valid JSON in this exact format:

{{
  "themes": [
    {{
      "theme_name": "string",
      "description": "one sentence description",
      "supporting_response_indices": [1, 4, 7],
      "representative_quotes": ["exact quote from response", "exact quote from response"],
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

    return {
        "themes": parsed.get("themes", []),
        "analyst_note": parsed.get("analyst_note", ""),
        "n_responses_analyzed": len(sample),
        "truncated": truncated,
        "ai_generated": True,
        "source": "AI thematic analysis",
        "disclaimer": "Researcher must verify all themes against source quotes before reporting.",
        "researcher_controls": ["Merge themes", "Split theme", "Rename theme", "Delete theme"],
    }
