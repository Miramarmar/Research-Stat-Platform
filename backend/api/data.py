"""Data import, type detection, cleaning, and variable configuration."""
import io
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd

from session.ephemeral_store import (
    get_session, set_dataframe, get_dataframe,
    update_session, append_audit
)
from stats.engine import detect_column_types, detect_data_issues

router = APIRouter()


@router.post("/import")
async def import_dataset(
    file: UploadFile = File(...),
    session_token: str = Header(...),
    mode: str = Header(...),
):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session not found or expired.")

    contents = await file.read()
    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8-sig")))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    col_types = detect_column_types(df)
    issues = detect_data_issues(df, col_types)

    set_dataframe(session_token, df)
    update_session(session_token, "column_types", col_types)

    append_audit(session_token, "dataset_imported", {
        "filename": file.filename,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "column_types": col_types,
    })

    return {
        "filename": file.filename,
        "n": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "column_types": col_types,
        "data_issues": issues,
        "n_issues": len(issues),
        "preview": df.head(5).fillna("").to_dict(orient="records"),
        "persisted": mode != "ephemeral",
    }


class TypeOverride(BaseModel):
    column: str
    new_type: str  # numerical | categorical | likert | open_ended | pretest | posttest


@router.post("/types/override")
def override_type(req: TypeOverride,
                  session_token: str = Header(...),
                  mode: str = Header(...)):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session expired.")
    types = session.get("column_types", {})
    old_type = types.get(req.column)
    types[req.column] = req.new_type
    update_session(session_token, "column_types", types)
    append_audit(session_token, "type_override", {
        "column": req.column, "from": old_type, "to": req.new_type
    })
    return {"column": req.column, "new_type": req.new_type}


class CleaningDecision(BaseModel):
    issue_type: str       # missing_values | duplicate_rows | impossible_value
    column: Optional[str] = None
    rows: Optional[list] = None
    action: str           # Keep | Exclude | Impute (Mean) | Impute (Median) | Modify
    impute_value: Optional[float] = None


@router.post("/clean")
def apply_cleaning_decision(req: CleaningDecision,
                             session_token: str = Header(...),
                             mode: str = Header(...)):
    """
    Apply ONE researcher-approved cleaning decision.
    NEVER auto-deletes. Every action is recorded in the audit trail.
    """
    df = get_dataframe(session_token)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    rows_affected = 0

    if req.action == "Keep":
        pass  # No change — explicitly kept

    elif req.action == "Exclude":
        if req.rows:
            df = df.drop(index=[i for i in req.rows if i in df.index])
            rows_affected = len(req.rows)
        elif req.issue_type == "duplicate_rows":
            before = len(df)
            df = df.drop_duplicates()
            rows_affected = before - len(df)

    elif req.action.startswith("Impute"):
        if req.column:
            if "Mean" in req.action:
                val = df[req.column].mean()
            elif "Median" in req.action:
                val = df[req.column].median()
            elif "Mode" in req.action:
                val = df[req.column].mode()[0]
            else:
                val = req.impute_value
            n_filled = df[req.column].isna().sum()
            df[req.column] = df[req.column].fillna(val)
            rows_affected = int(n_filled)

    set_dataframe(session_token, df)
    append_audit(session_token, "cleaning_decision", {
        "issue_type": req.issue_type,
        "column": req.column,
        "action": req.action,
        "rows_affected": rows_affected,
    })

    return {
        "action_applied": req.action,
        "rows_affected": rows_affected,
        "new_n": len(df),
    }


class RoleAssignment(BaseModel):
    assignments: dict  # {column: "Independent" | "Dependent" | "Covariate" | "Control"}


@router.post("/roles")
def assign_variable_roles(req: RoleAssignment,
                           session_token: str = Header(...),
                           mode: str = Header(...)):
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session expired.")
    update_session(session_token, "variable_roles", req.assignments)
    append_audit(session_token, "roles_assigned", {"assignments": req.assignments})
    return {"roles": req.assignments}


class CompositeConfig(BaseModel):
    name: str
    columns: list
    reverse_items: Optional[list] = None
    scale_max: Optional[int] = 5


@router.post("/composite")
def create_composite_score(req: CompositeConfig,
                            session_token: str = Header(...),
                            mode: str = Header(...)):
    """Create a composite Likert score. Reverse-coding requires explicit confirmation."""
    df = get_dataframe(session_token)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    from stats.engine import composite_score
    df[req.name] = composite_score(df, req.columns, req.reverse_items, req.scale_max)
    set_dataframe(session_token, df)

    session = get_session(session_token)
    configs = session.get("composite_configs", [])
    configs.append(req.dict())
    update_session(session_token, "composite_configs", configs)

    append_audit(session_token, "composite_created", {
        "name": req.name,
        "items": req.columns,
        "reverse_coded": req.reverse_items or [],
        "scale_max": req.scale_max,
    })
    return {"composite": req.name, "n_items": len(req.columns)}


class FilterConfig(BaseModel):
    column: str
    operator: str   # eq | neq | gt | lt | gte | lte | contains
    value: str


@router.post("/filter")
def apply_global_filter(req: FilterConfig,
                         session_token: str = Header(...),
                         mode: str = Header(...)):
    """Apply dynamic global filter. All downstream stats update automatically."""
    session = get_session(session_token)
    if not session:
        raise HTTPException(404, "Session expired.")
    filters = session.get("filters", [])
    filters.append(req.dict())
    update_session(session_token, "filters", filters)
    append_audit(session_token, "filter_applied", req.dict())
    return {"filters": filters}


@router.delete("/filter")
def clear_filters(session_token: str = Header(...), mode: str = Header(...)):
    update_session(session_token, "filters", [])
    append_audit(session_token, "filters_cleared", {})
    return {"filters": []}
