"""
Deterministic Statistical Engine — v1.2
=========================================
ALL mathematical calculations happen here — SciPy, StatsModels, Pandas ONLY.
The LLM is NEVER permitted to calculate math, p-values, or test statistics.

Spec alignment (v1.2):
  - Pre/post-test pair detection by column naming
  - ANCOVA added
  - Composite score with explicit reverse-coding confirmation
  - Mixed-methods cross-tabulation
  - APA formatting hardcoded — never from AI
  - Strict frequentist phrasing: "Reject H₀" / "Fail to Reject H₀"
  - Correlation ≠ causation caution always appended
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import (
    shapiro, levene, kstest, mannwhitneyu,
    wilcoxon, kruskal, f_oneway
)
import statsmodels.api as sm
import warnings
warnings.filterwarnings("ignore")


# ══════════════════════════════════════════════════════════════════════════════
# VARIABLE TYPE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_column_types(df: pd.DataFrame) -> dict:
    """
    Auto-detect: Numerical, Categorical, Likert, Open-Ended, PreTest, PostTest.
    PreTest/PostTest pairs detected by column naming patterns.
    Returns dict of {column_name: detected_type}.
    """
    types = {}
    cols_lower = {c: c.lower() for c in df.columns}

    pre_markers  = ("pre", "pre_", "pretest", "pre-test", "before", "t1", "t0", "_pre", "-pre")
    post_markers = ("post", "post_", "posttest", "post-test", "after", "t2", "_post", "-post")

    for col in df.columns:
        cl = cols_lower[col]
        series = df[col].dropna()

        if any(cl.startswith(m) or cl.endswith(m) for m in pre_markers):
            types[col] = "pretest"
        elif any(cl.startswith(m) or cl.endswith(m) for m in post_markers):
            types[col] = "posttest"
        elif not pd.api.types.is_numeric_dtype(series):
            unique_ratio = series.nunique() / max(len(series), 1)
            avg_len = series.astype(str).str.len().mean()
            types[col] = "open_ended" if (unique_ratio > 0.4 or avg_len > 40) else "categorical"
        elif series.nunique() <= 7 and series.min() >= 1 and series.max() <= 7:
            types[col] = "likert"
        else:
            types[col] = "numerical"

    return types


def detect_data_issues(df: pd.DataFrame, column_types: dict,
                        likert_max: dict = None) -> list:
    """
    Surface data quality issues — NEVER auto-deletes.
    Returns flags for researcher review with [Keep|Exclude|Modify|Impute] options.
    Every decision must be logged in the audit trail.
    """
    issues = []
    likert_max = likert_max or {}

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append({
            "type": "duplicate_rows",
            "count": int(dup_count),
            "description": f"{dup_count} duplicate row(s) detected.",
            "rows": df[df.duplicated()].index.tolist(),
            "options": ["Keep", "Exclude", "Review"],
        })

    for col, ctype in column_types.items():
        # Missing values
        missing = df[col].isna().sum()
        if missing > 0:
            issues.append({
                "type": "missing_values",
                "column": col,
                "count": int(missing),
                "pct": round(100 * missing / len(df), 1),
                "description": (
                    f"Column '{col}' has {missing} missing value(s) "
                    f"({round(100*missing/len(df),1)}%)."
                ),
                "options": ["Keep", "Exclude", "Impute (Mean)",
                            "Impute (Median)", "Impute (Mode)"],
            })

        # Impossible Likert values
        if ctype == "likert":
            scale_max = likert_max.get(col, 5)
            out_of_range = df[
                (df[col] < 1) | (df[col] > scale_max)
            ][col].dropna()
            if len(out_of_range) > 0:
                issues.append({
                    "type": "impossible_value",
                    "column": col,
                    "count": int(len(out_of_range)),
                    "description": (
                        f"Column '{col}' has {len(out_of_range)} value(s) "
                        f"outside the 1–{scale_max} scale."
                    ),
                    "rows": out_of_range.index.tolist(),
                    "options": ["Keep", "Exclude", "Modify"],
                })

    return issues


# ══════════════════════════════════════════════════════════════════════════════
# DESCRIPTIVE STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def descriptive_stats(df: pd.DataFrame, column: str) -> dict:
    """
    Full descriptive output: N, Mean, Median, SD, Variance, Min, Max,
    Skewness, Kurtosis, SE, IQR, and 95% CI of the mean.
    Frequencies and valid percentages for categorical/Likert data.
    """
    col = df[column].dropna()

    if not pd.api.types.is_numeric_dtype(col):
        freq = col.value_counts()
        return {
            "column": column,
            "type": "categorical",
            "n": int(col.count()),
            "missing": int(df[column].isna().sum()),
            "missing_pct": round(100 * df[column].isna().sum() / max(len(df), 1), 1),
            "unique_values": int(col.nunique()),
            "frequencies": freq.to_dict(),
            "valid_percentages": (freq / len(col) * 100).round(1).to_dict(),
        }

    q1 = float(col.quantile(0.25))
    q3 = float(col.quantile(0.75))
    sem_val = float(stats.sem(col))
    mean_val = float(col.mean())

    return {
        "column": column,
        "type": "numerical",
        "n": int(col.count()),
        "missing": int(df[column].isna().sum()),
        "missing_pct": round(100 * df[column].isna().sum() / max(len(df), 1), 1),
        "mean": round(mean_val, 4),
        "median": round(float(col.median()), 4),
        "sd": round(float(col.std()), 4),
        "variance": round(float(col.var()), 4),
        "se": round(sem_val, 4),
        "min": round(float(col.min()), 4),
        "max": round(float(col.max()), 4),
        "range": round(float(col.max() - col.min()), 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(q3 - q1, 4),
        "skewness": round(float(stats.skew(col)), 4),
        "kurtosis": round(float(stats.kurtosis(col)), 4),
        "ci_95": [
            round(mean_val - 1.96 * sem_val, 4),
            round(mean_val + 1.96 * sem_val, 4),
        ],
    }


def learning_gain(df: pd.DataFrame, pre_col: str, post_col: str) -> dict:
    """Auto-calculate post − pre gain when pre/post pair is defined by researcher."""
    pairs = df[[pre_col, post_col]].dropna()
    gains = pairs[post_col] - pairs[pre_col]
    return {
        "pre_column": pre_col,
        "post_column": post_col,
        "n_pairs": len(pairs),
        "mean_pre": round(float(pairs[pre_col].mean()), 4),
        "mean_post": round(float(pairs[post_col].mean()), 4),
        "mean_gain": round(float(gains.mean()), 4),
        "sd_gain": round(float(gains.std(ddof=1)), 4),
        "min_gain": round(float(gains.min()), 4),
        "max_gain": round(float(gains.max()), 4),
        "pct_improved": round(100 * (gains > 0).sum() / len(gains), 1),
        "pct_declined": round(100 * (gains < 0).sum() / len(gains), 1),
    }


def composite_score(df: pd.DataFrame, columns: list,
                    reverse_items: list = None,
                    scale_max: int = 5) -> pd.Series:
    """
    Sum/mean Likert items into a composite score.
    Reverse-coding requires EXPLICIT researcher confirmation before this is called.
    Formula: reversed_item = (scale_max + 1) - original_item
    """
    sub = df[columns].copy()
    if reverse_items:
        for col in reverse_items:
            if col in sub.columns:
                sub[col] = (scale_max + 1) - sub[col]
    return sub.mean(axis=1)


# ══════════════════════════════════════════════════════════════════════════════
# ASSUMPTION CHECKS  (run BEFORE primary tests — spec requirement)
# ══════════════════════════════════════════════════════════════════════════════

def check_normality(series: pd.Series, label: str = "") -> dict:
    """
    Shapiro-Wilk (n ≤ 50) or Kolmogorov-Smirnov (n > 50).
    Status icons: ✓ Satisfied  ⚠ Potential issue  ✕ Violated
    """
    clean = series.dropna()
    n = len(clean)

    if n < 3:
        return {
            "column": label, "test": "N/A", "n": n,
            "status": "unknown", "icon": "⚠",
            "label": "⚠ Too few observations (n < 3)",
        }

    if n <= 50:
        stat, p = shapiro(clean)
        test_name = "Shapiro-Wilk"
    else:
        stat, p = kstest(clean, "norm", args=(float(clean.mean()), float(clean.std())))
        test_name = "Kolmogorov-Smirnov"

    satisfied = p > 0.05
    return {
        "column": label,
        "test": test_name,
        "statistic": round(float(stat), 4),
        "p_value": round(float(p), 4),
        "n": n,
        "status": "satisfied" if satisfied else "violated",
        "icon": "✓" if satisfied else "✕",
        "label": "✓ Normal distribution" if satisfied else "✕ Non-normal distribution",
        "recommendation": (
            None if satisfied
            else "Consider a non-parametric equivalent "
                 "(e.g. Mann-Whitney U instead of independent t-test)."
        ),
        "ai_suggestion_available": not satisfied,
    }


def check_homogeneity(*groups, labels=None) -> dict:
    """Levene's test for equality of variances. Run BEFORE group comparisons."""
    valid = [g for g in groups if len(g) >= 2]
    if len(valid) < 2:
        return {
            "test": "Levene's", "status": "unknown",
            "label": "⚠ Insufficient data", "icon": "⚠",
        }

    stat, p = levene(*valid)
    satisfied = p > 0.05
    return {
        "test": "Levene's",
        "statistic": round(float(stat), 4),
        "p_value": round(float(p), 4),
        "status": "satisfied" if satisfied else "potential_issue",
        "icon": "✓" if satisfied else "⚠",
        "label": (
            "✓ Equal variances"
            if satisfied else
            "⚠ Unequal variances — consider Welch's t-test"
        ),
    }


def check_collinearity(df: pd.DataFrame, predictors: list) -> dict:
    """Variance Inflation Factor (VIF). Run BEFORE regression."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    sub = df[predictors].dropna()
    X = sub.values
    vif_data = {}
    for i, col in enumerate(predictors):
        try:
            vif = variance_inflation_factor(X, i)
            if vif < 5:
                status, icon = "✓ OK", "✓"
            elif vif < 10:
                status, icon = "⚠ Moderate multicollinearity", "⚠"
            else:
                status, icon = "✕ High multicollinearity", "✕"
            vif_data[col] = {"vif": round(float(vif), 3), "status": status, "icon": icon}
        except Exception:
            vif_data[col] = {"vif": None, "status": "Could not compute", "icon": "⚠"}
    return {"test": "VIF (Variance Inflation Factor)", "predictors": vif_data}


def run_all_assumptions(df: pd.DataFrame, columns: list,
                        test_type: str = "comparison") -> dict:
    """
    Run all relevant assumption checks before a primary test.
    Returns structured report: ✓ Satisfied / ⚠ Potential issue / ✕ Violated
    """
    result = {"checks": [], "all_satisfied": True}

    for col in columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            norm = check_normality(df[col], label=col)
            result["checks"].append({"type": "normality", **norm})
            if norm["status"] == "violated":
                result["all_satisfied"] = False

    if test_type == "comparison" and len(columns) >= 2:
        groups = [
            df[c].dropna().values
            for c in columns
            if pd.api.types.is_numeric_dtype(df[c])
        ]
        if len(groups) >= 2:
            hom = check_homogeneity(*groups)
            result["checks"].append({"type": "homogeneity", **hom})
            if hom["status"] == "potential_issue":
                result["all_satisfied"] = False

    if test_type == "regression" and len(columns) >= 2:
        vif = check_collinearity(df, columns)
        result["checks"].append({"type": "collinearity", **vif})

    return result


# ══════════════════════════════════════════════════════════════════════════════
# T-TESTS
# ══════════════════════════════════════════════════════════════════════════════

def independent_ttest(group1: pd.Series, group2: pd.Series,
                      group1_label: str = "Group 1",
                      group2_label: str = "Group 2",
                      alpha: float = 0.05, tails: int = 2,
                      equal_var: bool = True) -> dict:
    g1, g2 = group1.dropna().values, group2.dropna().values
    t_stat, p_two = stats.ttest_ind(g1, g2, equal_var=equal_var)
    p = p_two if tails == 2 else p_two / 2
    n1, n2 = len(g1), len(g2)
    df_val = n1 + n2 - 2

    pooled_sd = np.sqrt(
        ((n1 - 1) * np.var(g1, ddof=1) + (n2 - 1) * np.var(g2, ddof=1)) / df_val
    ) if df_val > 0 else 1
    cohens_d = (np.mean(g1) - np.mean(g2)) / pooled_sd if pooled_sd != 0 else 0

    diff = float(np.mean(g1) - np.mean(g2))
    se_diff = float(np.sqrt(np.var(g1, ddof=1) / n1 + np.var(g2, ddof=1) / n2))
    t_crit = float(stats.t.ppf(1 - 0.025, df_val))
    ci = [round(diff - t_crit * se_diff, 4), round(diff + t_crit * se_diff, 4)]

    reject = bool(p < alpha)
    apa = f"t({df_val}) = {round(t_stat, 2)}, p {_fmt_p(p)}, d = {round(cohens_d, 2)}"

    return {
        "test": "Independent-samples t-test",
        "variant": "Welch" if not equal_var else "Student",
        "group1": {"label": group1_label, "n": n1,
                   "mean": round(float(np.mean(g1)), 4),
                   "sd": round(float(np.std(g1, ddof=1)), 4)},
        "group2": {"label": group2_label, "n": n2,
                   "mean": round(float(np.mean(g2)), 4),
                   "sd": round(float(np.std(g2, ddof=1)), 4)},
        "t_statistic": round(float(t_stat), 4),
        "df": int(df_val),
        "p_value": round(float(p), 4),
        "cohens_d": round(float(cohens_d), 4),
        "effect_size_label": _cohens_d_label(abs(cohens_d)),
        "ci_95_difference": ci,
        "alpha": alpha,
        "tails": tails,
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": apa,
        "plain_language": _plain_ttest(group1_label, group2_label, g1, g2, reject, apa),
    }


def paired_ttest(pre: pd.Series, post: pd.Series,
                 alpha: float = 0.05, tails: int = 2,
                 pre_label: str = "Pre-test",
                 post_label: str = "Post-test") -> dict:
    pre_v, post_v = pre.dropna().values, post.dropna().values
    min_n = min(len(pre_v), len(post_v))
    pre_v, post_v = pre_v[:min_n], post_v[:min_n]

    t_stat, p_two = stats.ttest_rel(pre_v, post_v)
    p = p_two if tails == 2 else p_two / 2
    df_val = min_n - 1
    diff = post_v - pre_v
    cohens_d = (
        float(np.mean(diff) / np.std(diff, ddof=1))
        if np.std(diff, ddof=1) != 0 else 0
    )

    reject = bool(p < alpha)
    apa = f"t({df_val}) = {round(t_stat, 2)}, p {_fmt_p(p)}, d = {round(cohens_d, 2)}"

    return {
        "test": "Paired-samples t-test",
        "pre_label": pre_label, "post_label": post_label,
        "n_pairs": min_n,
        "mean_pre": round(float(np.mean(pre_v)), 4),
        "mean_post": round(float(np.mean(post_v)), 4),
        "mean_gain": round(float(np.mean(diff)), 4),
        "sd_gain": round(float(np.std(diff, ddof=1)), 4),
        "t_statistic": round(float(t_stat), 4),
        "df": df_val,
        "p_value": round(float(p), 4),
        "cohens_d": round(float(cohens_d), 4),
        "effect_size_label": _cohens_d_label(abs(cohens_d)),
        "alpha": alpha,
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": apa,
    }


# ══════════════════════════════════════════════════════════════════════════════
# NON-PARAMETRIC
# ══════════════════════════════════════════════════════════════════════════════

def mann_whitney(g1: pd.Series, g2: pd.Series,
                 g1_label: str = "Group 1", g2_label: str = "Group 2",
                 alpha: float = 0.05) -> dict:
    g1c, g2c = g1.dropna().values, g2.dropna().values
    stat, p = mannwhitneyu(g1c, g2c, alternative="two-sided")
    r = 1 - (2 * stat) / (len(g1c) * len(g2c))
    reject = bool(p < alpha)
    return {
        "test": "Mann-Whitney U",
        "group1": {"label": g1_label, "n": len(g1c),
                   "median": round(float(np.median(g1c)), 4)},
        "group2": {"label": g2_label, "n": len(g2c),
                   "median": round(float(np.median(g2c)), 4)},
        "U_statistic": round(float(stat), 4),
        "p_value": round(float(p), 4),
        "rank_biserial_r": round(float(r), 4),
        "effect_size_label": _r_label(abs(r)),
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": f"U = {round(stat, 2)}, p {_fmt_p(p)}, r = {round(r, 2)}",
    }


def wilcoxon_signed_rank(pre: pd.Series, post: pd.Series,
                          alpha: float = 0.05) -> dict:
    pairs = pd.concat([pre, post], axis=1).dropna()
    x, y = pairs.iloc[:, 0].values, pairs.iloc[:, 1].values
    stat, p = wilcoxon(x, y)
    n = len(x)
    r = 1 - (2 * stat) / (n * (n + 1))
    reject = bool(p < alpha)
    return {
        "test": "Wilcoxon Signed-Rank",
        "n_pairs": n,
        "W_statistic": round(float(stat), 4),
        "p_value": round(float(p), 4),
        "rank_biserial_r": round(float(r), 4),
        "effect_size_label": _r_label(abs(r)),
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": f"W = {round(stat, 2)}, p {_fmt_p(p)}, r = {round(r, 2)}",
    }


def kruskal_wallis(groups: list, labels: list = None,
                    alpha: float = 0.05) -> dict:
    clean = [g.dropna().values for g in groups]
    stat, p = kruskal(*clean)
    reject = bool(p < alpha)
    labels = labels or [f"Group {i+1}" for i in range(len(groups))]
    return {
        "test": "Kruskal-Wallis H",
        "n_groups": len(groups),
        "groups": [
            {"label": l, "n": len(g), "median": round(float(np.median(g)), 4)}
            for l, g in zip(labels, clean)
        ],
        "H_statistic": round(float(stat), 4),
        "df": len(groups) - 1,
        "p_value": round(float(p), 4),
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": f"H({len(groups)-1}) = {round(stat, 2)}, p {_fmt_p(p)}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# ONE-WAY ANOVA + ANCOVA
# ══════════════════════════════════════════════════════════════════════════════

def one_way_anova(groups: list, labels: list = None,
                   alpha: float = 0.05) -> dict:
    clean = [g.dropna().values for g in groups]
    f_stat, p = f_oneway(*clean)
    k, N = len(clean), sum(len(g) for g in clean)
    df_between, df_within = k - 1, N - k

    grand_mean = np.mean(np.concatenate(clean))
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in clean)
    ss_total   = sum(np.sum((g - grand_mean) ** 2) for g in clean)
    eta_sq = ss_between / ss_total if ss_total != 0 else 0

    reject = bool(p < alpha)
    labels = labels or [f"Group {i+1}" for i in range(k)]
    return {
        "test": "One-Way ANOVA",
        "n_groups": k, "N": N,
        "groups": [
            {"label": l, "n": len(g),
             "mean": round(float(np.mean(g)), 4),
             "sd": round(float(np.std(g, ddof=1)), 4)}
            for l, g in zip(labels, clean)
        ],
        "F_statistic": round(float(f_stat), 4),
        "df_between": df_between,
        "df_within": df_within,
        "p_value": round(float(p), 4),
        "eta_squared": round(float(eta_sq), 4),
        "effect_size_label": _eta_label(eta_sq),
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": (
            f"F({df_between}, {df_within}) = {round(f_stat, 2)}, "
            f"p {_fmt_p(p)}, η² = {round(eta_sq, 3)}"
        ),
    }


def ancova(df: pd.DataFrame, dependent: str, group_col: str,
           covariates: list, alpha: float = 0.05) -> dict:
    """
    Analysis of Covariance (ANCOVA).
    Controls for covariate(s) before testing group differences.
    Spec: included as part of 'Experimental & Group Comparisons' module.
    """
    data = df[[dependent, group_col] + covariates].dropna()
    dummies = pd.get_dummies(data[group_col], drop_first=True, dtype=float)
    X = pd.concat([dummies, data[covariates]], axis=1)
    X = sm.add_constant(X)
    y = data[dependent]
    model = sm.OLS(y, X).fit()

    group_preds = [c for c in model.params.index if c in dummies.columns]
    group_p_vals = [model.pvalues[g] for g in group_preds]
    reject = bool(all(p < alpha for p in group_p_vals)) if group_p_vals else False

    coef_table = {}
    for var in model.params.index:
        coef_table[str(var)] = {
            "coefficient": round(float(model.params[var]), 4),
            "se": round(float(model.bse[var]), 4),
            "t": round(float(model.tvalues[var]), 4),
            "p_value": round(float(model.pvalues[var]), 4),
            "significant": bool(model.pvalues[var] < alpha),
        }

    return {
        "test": "ANCOVA",
        "dependent": dependent,
        "group_variable": group_col,
        "covariates": covariates,
        "n": int(model.nobs),
        "r_squared": round(float(model.rsquared), 4),
        "adj_r_squared": round(float(model.rsquared_adj), 4),
        "f_statistic": round(float(model.fvalue), 4),
        "f_p_value": round(float(model.f_pvalue), 4),
        "coefficients": coef_table,
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": (
            f"F({int(model.df_model)}, {int(model.df_resid)}) = "
            f"{round(model.fvalue, 2)}, p {_fmt_p(model.f_pvalue)}, "
            f"R² = {round(model.rsquared, 3)}"
        ),
        "note": "ANCOVA controls for covariate(s) before assessing group differences.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# CORRELATION
# ══════════════════════════════════════════════════════════════════════════════

def correlation(x: pd.Series, y: pd.Series,
                method: str = "pearson", alpha: float = 0.05) -> dict:
    pairs = pd.concat([x, y], axis=1).dropna()
    xv, yv = pairs.iloc[:, 0].values, pairs.iloc[:, 1].values
    n = len(xv)

    if method == "pearson":
        r, p = stats.pearsonr(xv, yv)
        r_sq = r ** 2
        apa = f"r({n-2}) = {round(r, 2)}, p {_fmt_p(p)}"
    elif method == "spearman":
        r, p = stats.spearmanr(xv, yv)
        r_sq = r ** 2
        apa = f"rs({n-2}) = {round(r, 2)}, p {_fmt_p(p)}"
    else:  # kendall
        r, p = stats.kendalltau(xv, yv)
        r_sq = None
        apa = f"τ = {round(r, 2)}, p {_fmt_p(p)}"

    reject = bool(p < alpha)
    return {
        "test": f"{method.capitalize()} correlation",
        "x_label": x.name or "X", "y_label": y.name or "Y",
        "n": n,
        "r": round(float(r), 4),
        "r_squared": round(float(r_sq), 4) if r_sq is not None else None,
        "p_value": round(float(p), 4),
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": apa,
        # Spec requirement: always append causation caution
        "caution": (
            "Correlation describes a statistical association only — "
            "it does not imply or establish causation."
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# RELIABILITY — Cronbach's Alpha + McDonald's Omega
# ══════════════════════════════════════════════════════════════════════════════

def cronbach_alpha(df: pd.DataFrame, columns: list) -> dict:
    sub = df[columns].dropna()
    k = len(columns)
    if k < 2:
        return {"test": "Cronbach's Alpha", "error": "Need at least 2 items."}

    item_vars = sub.var(axis=0, ddof=1).sum()
    total_var = sub.sum(axis=1).var(ddof=1)
    alpha_val = (k / (k - 1)) * (1 - item_vars / total_var) if total_var != 0 else None

    item_total = {}
    for col in columns:
        rest = sub.drop(columns=[col]).sum(axis=1)
        item_total[col] = round(float(sub[col].corr(rest)), 4)

    return {
        "test": "Cronbach's Alpha",
        "n_items": k,
        "n_respondents": len(sub),
        "alpha": round(float(alpha_val), 4) if alpha_val is not None else None,
        "interpretation": _alpha_label(alpha_val) if alpha_val else "Could not compute",
        "item_total_correlations": item_total,
        "apa_string": f"α = {round(alpha_val, 2)}" if alpha_val else "α = N/A",
    }


def mcdonald_omega(df: pd.DataFrame, columns: list) -> dict:
    """
    McDonald's omega (ω) — preferred when items are not tau-equivalent.
    Uses one-factor CFA loadings via FactorAnalysis approximation.
    """
    sub = df[columns].dropna()
    k = len(columns)
    if k < 3:
        return {"test": "McDonald's Omega", "error": "Need at least 3 items for omega."}

    try:
        from sklearn.decomposition import FactorAnalysis
        fa = FactorAnalysis(n_components=1, random_state=42)
        fa.fit(sub)
        loadings = fa.components_[0]
        uniquenesses = fa.noise_variance_

        sum_loadings = np.sum(loadings)
        sum_unique = np.sum(uniquenesses)
        omega = (sum_loadings ** 2) / ((sum_loadings ** 2) + sum_unique)

        return {
            "test": "McDonald's Omega",
            "n_items": k,
            "n_respondents": len(sub),
            "omega": round(float(omega), 4),
            "interpretation": _alpha_label(omega),
            "item_loadings": {col: round(float(l), 4) for col, l in zip(columns, loadings)},
            "apa_string": f"ω = {round(omega, 2)}",
            "note": "Omega is preferred when items have unequal factor loadings.",
        }
    except Exception as e:
        return {"test": "McDonald's Omega", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# REGRESSION
# ══════════════════════════════════════════════════════════════════════════════

def linear_regression(df: pd.DataFrame, dependent: str, predictors: list,
                       show_equation: bool = True) -> dict:
    data = df[[dependent] + predictors].dropna()
    y = data[dependent]
    X = sm.add_constant(data[predictors])
    model = sm.OLS(y, X).fit()

    coefs = {}
    for var in model.params.index:
        coefs[str(var)] = {
            "coefficient": round(float(model.params[var]), 4),
            "se": round(float(model.bse[var]), 4),
            "t": round(float(model.tvalues[var]), 4),
            "p_value": round(float(model.pvalues[var]), 4),
            "ci_95": [
                round(float(model.conf_int().loc[var, 0]), 4),
                round(float(model.conf_int().loc[var, 1]), 4),
            ],
            "significant": bool(model.pvalues[var] < 0.05),
        }

    pred_parts = " + ".join([f"β{i+1}·{p}" for i, p in enumerate(predictors)])
    equation = f"ŷ = β₀ + {pred_parts}" if show_equation else None

    return {
        "test": (
            "Multiple Linear Regression" if len(predictors) > 1
            else "Simple Linear Regression"
        ),
        "dependent": dependent,
        "predictors": predictors,
        "n": int(model.nobs),
        "r_squared": round(float(model.rsquared), 4),
        "adj_r_squared": round(float(model.rsquared_adj), 4),
        "f_statistic": round(float(model.fvalue), 4),
        "f_p_value": round(float(model.f_pvalue), 4),
        "coefficients": coefs,
        "equation_template": equation,
        "show_equation": show_equation,
        "apa_string": (
            f"R² = {round(model.rsquared, 3)}, "
            f"F({int(model.df_model)}, {int(model.df_resid)}) = "
            f"{round(model.fvalue, 2)}, p {_fmt_p(model.f_pvalue)}"
        ),
        "caution": (
            "Regression coefficients reflect statistical association — not causation."
        ),
    }


def logistic_regression(df: pd.DataFrame, dependent: str,
                         predictors: list) -> dict:
    data = df[[dependent] + predictors].dropna()
    y = data[dependent]
    X = sm.add_constant(data[predictors])
    model = sm.Logit(y, X).fit(disp=0)

    coefs = {}
    for var in model.params.index:
        coefs[str(var)] = {
            "coefficient": round(float(model.params[var]), 4),
            "odds_ratio": round(float(np.exp(model.params[var])), 4),
            "se": round(float(model.bse[var]), 4),
            "z": round(float(model.tvalues[var]), 4),
            "p_value": round(float(model.pvalues[var]), 4),
            "significant": bool(model.pvalues[var] < 0.05),
        }

    return {
        "test": "Logistic Regression",
        "dependent": dependent,
        "predictors": predictors,
        "n": int(model.nobs),
        "pseudo_r_squared": round(float(model.prsquared), 4),
        "log_likelihood": round(float(model.llf), 4),
        "AIC": round(float(model.aic), 4),
        "coefficients": coefs,
        "caution": "Odds ratios represent association strength — not causal effects.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# QUALITATIVE / TEXT  (AI-OFF deterministic mode)
# ══════════════════════════════════════════════════════════════════════════════

def word_frequency(responses: list, top_n: int = 20,
                   stopwords: set = None) -> dict:
    """Basic word frequency — fully deterministic, no AI required."""
    import re
    from collections import Counter

    default_stops = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "is", "was", "are", "were", "i", "we",
        "it", "this", "that", "my", "our", "their", "be", "have", "do",
        "not", "they", "he", "she", "you", "as", "from", "by", "about",
        "les", "des", "une", "est", "pas", "que", "qui", "dans", "sur",
    }
    stops = stopwords or default_stops
    all_words = []
    for r in responses:
        words = re.findall(r'\b[a-zA-Z\u0600-\u06FF]{3,}\b', str(r).lower())
        all_words.extend([w for w in words if w not in stops])

    freq = Counter(all_words)
    return {
        "total_responses": len(responses),
        "total_words": len(all_words),
        "unique_words": len(freq),
        "top_words": [
            {"word": w, "count": c,
             "pct": round(100 * c / max(len(all_words), 1), 1)}
            for w, c in freq.most_common(top_n)
        ],
    }


def ngram_frequency(responses: list, n: int = 2, top_k: int = 15) -> dict:
    """N-gram frequency analysis — deterministic."""
    import re
    from collections import Counter
    all_ngrams = []
    for r in responses:
        words = re.findall(r'\b[a-zA-Z\u0600-\u06FF]{3,}\b', str(r).lower())
        all_ngrams.extend(
            [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]
        )
    freq = Counter(all_ngrams)
    return {
        "n": n,
        "total_ngrams": len(all_ngrams),
        "top_ngrams": [
            {"ngram": ng, "count": c} for ng, c in freq.most_common(top_k)
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# MIXED-METHODS
# ══════════════════════════════════════════════════════════════════════════════

def mixed_methods_crosstab(df: pd.DataFrame,
                            group_col: str, theme_col: str) -> dict:
    """
    Cross-tabulate qualitative themes against quantitative groups.
    Spec: "Did the High-Motivation group mention different themes than the Low-Motivation group?"
    Returns counts and row-normalized percentages — no AI involved.
    """
    ct     = pd.crosstab(df[group_col], df[theme_col], margins=True)
    ct_pct = pd.crosstab(df[group_col], df[theme_col], normalize="index") * 100

    return {
        "group_column": group_col,
        "theme_column": theme_col,
        "crosstab_counts": ct.to_dict(),
        "crosstab_percentages": ct_pct.round(1).to_dict(),
        "note": "Percentages are row-normalized (within each group).",
    }


# ══════════════════════════════════════════════════════════════════════════════
# FORMATTING HELPERS  (all APA strings come from here — never from AI)
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_p(p: float) -> str:
    if p < 0.001:
        return "< .001"
    s = f"{p:.3f}"
    return f"= {s.lstrip('0') or '0'}"


def _conclusion(reject: bool) -> str:
    """Strict frequentist phrasing — spec requirement. Never 'proven' or 'confirmed'."""
    if reject:
        return "There is sufficient statistical evidence to reject the null hypothesis."
    return "There is insufficient evidence to reject the null hypothesis."


def _plain_ttest(l1, l2, g1, g2, reject, apa) -> str:
    direction = "higher" if np.mean(g1) > np.mean(g2) else "lower"
    if reject:
        return (
            f"{l1} (M = {round(float(np.mean(g1)), 2)}, "
            f"SD = {round(float(np.std(g1, ddof=1)), 2)}) scored significantly "
            f"{direction} than {l2} "
            f"(M = {round(float(np.mean(g2)), 2)}, "
            f"SD = {round(float(np.std(g2, ddof=1)), 2)}), {apa}."
        )
    return (
        f"No statistically significant difference was found between "
        f"{l1} and {l2}, {apa}."
    )


def _cohens_d_label(d: float) -> str:
    if d < 0.2: return "negligible"
    if d < 0.5: return "small"
    if d < 0.8: return "medium"
    return "large"


def _r_label(r: float) -> str:
    if r < 0.1: return "negligible"
    if r < 0.3: return "small"
    if r < 0.5: return "medium"
    return "large"


def _eta_label(eta: float) -> str:
    if eta < 0.01: return "negligible"
    if eta < 0.06: return "small"
    if eta < 0.14: return "medium"
    return "large"


def _alpha_label(a: float) -> str:
    if a >= 0.9: return "Excellent (≥ 0.90)"
    if a >= 0.8: return "Good (≥ 0.80)"
    if a >= 0.7: return "Acceptable (≥ 0.70)"
    if a >= 0.6: return "Questionable (≥ 0.60)"
    return "Poor (< 0.60)"
