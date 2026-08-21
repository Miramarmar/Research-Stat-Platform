"""
Statistics endpoints — all math via deterministic engine only.
Spec additions v1.2: ANCOVA endpoint, mixed-methods crosstab endpoint.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from session.ephemeral_store import (
    get_dataframe, get_session, append_result, append_audit
)
from stats.engine import (
    descriptive_stats, run_all_assumptions,
    independent_ttest, paired_ttest,
    mann_whitney, wilcoxon_signed_rank, kruskal_wallis, one_way_anova, ancova,
    correlation, linear_regression, logistic_regression,
    cronbach_alpha, mcdonald_omega, learning_gain,
    word_frequency, ngram_frequency, mixed_methods_crosstab,
)

router = APIRouter()


def _get_df(token):
    df = get_dataframe(token)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")
    return df


def _apply_filters(df, session):
    import pandas as pd
    for f in session.get("filters", []):
        col, op, val = f["column"], f["operator"], f["value"]
        if col not in df.columns:
            continue
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                num = float(val)
                ops = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "eq": "==", "neq": "!="}
                if op == "gt":  df = df[df[col] > num]
                elif op == "lt":  df = df[df[col] < num]
                elif op == "gte": df = df[df[col] >= num]
                elif op == "lte": df = df[df[col] <= num]
                elif op == "eq":  df = df[df[col] == num]
                elif op == "neq": df = df[df[col] != num]
            else:
                if op == "eq":       df = df[df[col].astype(str) == val]
                elif op == "neq":    df = df[df[col].astype(str) != val]
                elif op == "contains": df = df[df[col].astype(str).str.contains(val, na=False)]
        except Exception:
            continue
    return df


# ── Descriptive ──────────────────────────────────────────────────────────────

@router.get("/descriptive/{column}")
def get_descriptive(column: str,
                     session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    if column not in df.columns:
        raise HTTPException(400, f"Column '{column}' not found.")
    result = descriptive_stats(df, column)
    append_result(session_token, {"type": "descriptive", "column": column, **result})
    return result


@router.get("/descriptive")
def get_all_descriptive(session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    return {col: descriptive_stats(df, col) for col in df.columns}


# ── Assumption checks ────────────────────────────────────────────────────────

class AssumptionRequest(BaseModel):
    columns: List[str]
    test_type: str = "comparison"  # comparison | regression


@router.post("/assumptions")
def check_assumptions(req: AssumptionRequest,
                       session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    result = run_all_assumptions(df, req.columns, req.test_type)
    append_audit(session_token, "assumptions_checked", {
        "columns": req.columns, "all_satisfied": result["all_satisfied"]
    })
    return result


# ── T-tests ──────────────────────────────────────────────────────────────────

class TTestRequest(BaseModel):
    type: str                          # independent | paired
    column1: str
    column2: str
    group_col: Optional[str] = None
    group1_value: Optional[str] = None
    group2_value: Optional[str] = None
    alpha: Optional[float] = 0.05
    tails: Optional[int] = 2
    equal_var: Optional[bool] = True


@router.post("/ttest")
def run_ttest(req: TTestRequest,
               session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    alpha = req.alpha or session.get("alpha", 0.05)

    if req.type == "independent":
        if req.group_col and req.group1_value and req.group2_value:
            g1 = df[df[req.group_col].astype(str) == req.group1_value][req.column1]
            g2 = df[df[req.group_col].astype(str) == req.group2_value][req.column1]
            result = independent_ttest(g1, g2, req.group1_value, req.group2_value,
                                        alpha, req.tails, req.equal_var)
        else:
            result = independent_ttest(df[req.column1], df[req.column2],
                                        req.column1, req.column2,
                                        alpha, req.tails, req.equal_var)
    else:
        result = paired_ttest(df[req.column1], df[req.column2],
                               alpha, req.tails, req.column1, req.column2)

    append_result(session_token, result)
    append_audit(session_token, "ttest_run", {
        "type": req.type, "apa": result.get("apa_string")
    })
    return result


# ── ANOVA ────────────────────────────────────────────────────────────────────

class ANOVARequest(BaseModel):
    group_column: str
    value_column: str
    alpha: Optional[float] = 0.05


@router.post("/anova")
def run_anova(req: ANOVARequest,
               session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    groups_df = df.groupby(req.group_column)[req.value_column]
    groups = [g for _, g in groups_df]
    labels = [str(n) for n, _ in groups_df]
    alpha = req.alpha or session.get("alpha", 0.05)
    result = one_way_anova(groups, labels, alpha)
    append_result(session_token, result)
    append_audit(session_token, "anova_run", {"apa": result.get("apa_string")})
    return result


# ── ANCOVA (spec addition) ───────────────────────────────────────────────────

class ANCOVARequest(BaseModel):
    dependent: str
    group_column: str
    covariates: List[str]
    alpha: Optional[float] = 0.05


@router.post("/ancova")
def run_ancova(req: ANCOVARequest,
                session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    alpha = req.alpha or session.get("alpha", 0.05)
    result = ancova(df, req.dependent, req.group_column, req.covariates, alpha)
    append_result(session_token, result)
    append_audit(session_token, "ancova_run", {
        "dependent": req.dependent,
        "covariates": req.covariates,
        "apa": result.get("apa_string"),
    })
    return result


# ── Non-parametric ───────────────────────────────────────────────────────────

class NonParamRequest(BaseModel):
    test: str  # mann_whitney | wilcoxon | kruskal
    column1: str
    column2: Optional[str] = None
    group_col: Optional[str] = None
    alpha: Optional[float] = 0.05


@router.post("/nonparametric")
def run_nonparametric(req: NonParamRequest,
                       session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    alpha = req.alpha or session.get("alpha", 0.05)

    if req.test == "mann_whitney":
        if req.group_col:
            grp = df.groupby(req.group_col)[req.column1]
            g_list = [g for _, g in grp]
            labels = [str(n) for n, _ in grp]
            result = mann_whitney(g_list[0], g_list[1], labels[0], labels[1], alpha)
        else:
            result = mann_whitney(df[req.column1], df[req.column2],
                                   req.column1, req.column2, alpha)
    elif req.test == "wilcoxon":
        result = wilcoxon_signed_rank(df[req.column1], df[req.column2], alpha)
    else:
        grp = df.groupby(req.group_col)[req.column1]
        result = kruskal_wallis([g for _, g in grp], [str(n) for n, _ in grp], alpha)

    append_result(session_token, result)
    return result


# ── Correlation ──────────────────────────────────────────────────────────────

class CorrelationRequest(BaseModel):
    x_column: str
    y_column: str
    method: str = "pearson"  # pearson | spearman | kendall
    alpha: Optional[float] = 0.05


@router.post("/correlation")
def run_correlation(req: CorrelationRequest,
                     session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    result = correlation(df[req.x_column], df[req.y_column],
                          req.method, req.alpha or session.get("alpha", 0.05))
    append_result(session_token, result)
    return result


# ── Regression ───────────────────────────────────────────────────────────────

class RegressionRequest(BaseModel):
    type: str = "linear"       # linear | logistic
    dependent: str
    predictors: List[str]
    show_equation: Optional[bool] = True


@router.post("/regression")
def run_regression(req: RegressionRequest,
                    session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    show_eq = req.show_equation
    if show_eq is None:
        show_eq = session.get("show_equations", True)

    result = (
        logistic_regression(df, req.dependent, req.predictors)
        if req.type == "logistic"
        else linear_regression(df, req.dependent, req.predictors, show_eq)
    )
    append_result(session_token, result)
    return result


# ── Reliability ──────────────────────────────────────────────────────────────

class ReliabilityRequest(BaseModel):
    columns: List[str]
    compute_omega: Optional[bool] = True


@router.post("/reliability")
def run_reliability(req: ReliabilityRequest,
                     session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    alpha_result = cronbach_alpha(df, req.columns)
    result = {"cronbach": alpha_result}
    if req.compute_omega and len(req.columns) >= 3:
        result["omega"] = mcdonald_omega(df, req.columns)
    append_result(session_token, result)
    return result


# ── Learning gain ────────────────────────────────────────────────────────────

class LearningGainRequest(BaseModel):
    pre_column: str
    post_column: str


@router.post("/learning-gain")
def run_learning_gain(req: LearningGainRequest,
                       session_token: str = Header(...), mode: str = Header(...)):
    df = _get_df(session_token)
    result = learning_gain(df, req.pre_column, req.post_column)
    append_result(session_token, result)
    return result


# ── Text / Qualitative (AI-OFF deterministic mode) ───────────────────────────

class TextAnalysisRequest(BaseModel):
    column: str
    top_n: Optional[int] = 20
    ngram_n: Optional[int] = 2


@router.post("/text/deterministic")
def run_text_analysis(req: TextAnalysisRequest,
                       session_token: str = Header(...), mode: str = Header(...)):
    """Deterministic NLP — runs with AI OFF. Supports Arabic, French, English responses."""
    df = _get_df(session_token)
    responses = df[req.column].dropna().astype(str).tolist()
    return {
        "column": req.column,
        "word_frequency": word_frequency(responses, req.top_n),
        "ngrams": ngram_frequency(responses, req.ngram_n),
        "n_responses": len(responses),
        "ai_generated": False,
    }


# ── Mixed-methods cross-tabulation (spec addition) ───────────────────────────

class MixedMethodsRequest(BaseModel):
    group_column: str
    theme_column: str


@router.post("/mixed-methods/crosstab")
def run_mixed_methods(req: MixedMethodsRequest,
                       session_token: str = Header(...), mode: str = Header(...)):
    """
    Cross-tabulate qualitative themes against quantitative groups.
    Spec: visualise qualitative themes against quantitative group outcomes.
    """
    df = _get_df(session_token)
    session = get_session(session_token)
    df = _apply_filters(df, session)
    result = mixed_methods_crosstab(df, req.group_column, req.theme_column)
    append_result(session_token, result)
    return result
