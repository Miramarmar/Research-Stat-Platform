"""Hypothesis management — H0/H1 definition, mapping, and evaluation."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from session.ephemeral_store import get_session, update_session, append_audit

router = APIRouter()


class Hypothesis(BaseModel):
    id: Optional[str] = None
    h1: str  # Alternative hypothesis statement
    h0: str  # Null hypothesis statement
    variable_iv: Optional[str] = None
    variable_dv: Optional[str] = None
    expected_direction: Optional[str] = None  # positive | negative | any
    test_type: Optional[str] = None  # ttest | anova | correlation | regression
    status: Optional[str] = "pending"  # pending | reject_h0 | fail_to_reject


@router.post("/")
def add_hypothesis(hyp: Hypothesis,
                   session_token: str = Header(...), mode: str = Header(...)):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found.")
    import uuid
    hyp.id = str(uuid.uuid4())
    hypotheses = session.get("hypotheses", [])
    hypotheses.append(hyp.dict())
    update_session(session_token, "hypotheses", hypotheses)
    append_audit(session_token, "hypothesis_added", {"h1": hyp.h1, "h0": hyp.h0})
    return {"id": hyp.id, "added": True}


@router.get("/")
def list_hypotheses(session_token: str = Header(...), mode: str = Header(...)):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found.")
    return {"hypotheses": session.get("hypotheses", [])}


class EvaluationRequest(BaseModel):
    hypothesis_id: str
    statistical_result: dict  # the full result from the stats engine


@router.post("/evaluate")
def evaluate_hypothesis(req: EvaluationRequest,
                         session_token: str = Header(...), mode: str = Header(...)):
    """
    Link a completed statistical test result to a hypothesis.
    Uses strict frequentist language — never 'proven' or 'confirmed'.
    """
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found.")

    hypotheses = session.get("hypotheses", [])
    hyp = next((h for h in hypotheses if h["id"] == req.hypothesis_id), None)
    if not hyp:
        raise HTTPException(404, "Hypothesis not found.")

    reject = req.statistical_result.get("reject_h0", False)
    p = req.statistical_result.get("p_value")
    alpha = session.get("alpha", 0.05)

    # Strict frequentist conclusion — hardcoded, never from AI
    if reject:
        formal_conclusion = "There is sufficient statistical evidence to reject the null hypothesis."
        status = "reject_h0"
        verdict_label = "Reject H₀"
    else:
        formal_conclusion = "There is insufficient evidence to reject the null hypothesis."
        status = "fail_to_reject"
        verdict_label = "Fail to Reject H₀"

    hyp["status"] = status
    hyp["verdict_label"] = verdict_label
    hyp["formal_conclusion"] = formal_conclusion
    hyp["linked_result"] = req.statistical_result
    hyp["p_value"] = p
    hyp["alpha_used"] = alpha
    hyp["apa_string"] = req.statistical_result.get("apa_string", "")
    hyp["plain_language"] = req.statistical_result.get("plain_language", "")

    update_session(session_token, "hypotheses", hypotheses)
    append_audit(session_token, "hypothesis_evaluated", {
        "id": req.hypothesis_id,
        "status": status,
        "apa": hyp["apa_string"],
    })

    return {
        "hypothesis_id": req.hypothesis_id,
        "status": status,
        "verdict_label": verdict_label,
        "formal_conclusion": formal_conclusion,
        "apa_string": hyp["apa_string"],
        "plain_language": hyp["plain_language"],
        "p_value": p,
        "alpha": alpha,
    }
