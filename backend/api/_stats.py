"""
Pure Python + NumPy statistical engine.
No SciPy, no pandas, no compiled dependencies.
Same math, same APA output, works on any platform.
"""
import math
import numpy as np
from collections import Counter


# ── Descriptive ──────────────────────────────────────────────────────────────

def mean(data): return sum(data) / len(data)
def variance(data, ddof=1):
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / (len(data) - ddof)
def std(data, ddof=1): return math.sqrt(variance(data, ddof))
def median(data):
    s = sorted(data)
    n = len(s)
    return (s[n//2] + s[n//2-1]) / 2 if n % 2 == 0 else s[n//2]

def skewness(data):
    m, s, n = mean(data), std(data), len(data)
    if s == 0: return 0
    return (n / ((n-1)*(n-2))) * sum(((x - m)/s)**3 for x in data)

def kurtosis(data):
    m, s, n = mean(data), std(data), len(data)
    if s == 0 or n < 4: return 0
    k = sum(((x - m)/s)**4 for x in data)
    return (n*(n+1)/((n-1)*(n-2)*(n-3))) * k - (3*(n-1)**2/((n-2)*(n-3)))

def descriptive(values: list) -> dict:
    d = [float(x) for x in values if x is not None]
    if not d:
        return {"error": "No valid data"}
    n = len(d)
    m = mean(d)
    s = std(d)
    se = s / math.sqrt(n)
    sorted_d = sorted(d)
    q1 = sorted_d[n // 4]
    q3 = sorted_d[(3 * n) // 4]
    return {
        "n": n, "mean": round(m, 4), "median": round(median(d), 4),
        "sd": round(s, 4), "variance": round(variance(d), 4),
        "se": round(se, 4), "min": round(min(d), 4), "max": round(max(d), 4),
        "range": round(max(d) - min(d), 4),
        "q1": round(q1, 4), "q3": round(q3, 4), "iqr": round(q3 - q1, 4),
        "skewness": round(skewness(d), 4),
        "kurtosis": round(kurtosis(d), 4),
        "ci_95": [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
    }


# ── T-distribution (needed for p-values without scipy) ───────────────────────

def _t_cdf(t, df):
    """Cumulative t-distribution via regularized incomplete beta function."""
    x = df / (df + t * t)
    return 1 - 0.5 * _betainc(df/2, 0.5, x)

def _betainc(a, b, x):
    """Regularized incomplete beta — Lentz continued fraction."""
    if x < 0 or x > 1: return 0
    if x == 0: return 0
    if x == 1: return 1
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x)*a + math.log(1-x)*b - lbeta) / a
    # continued fraction
    eps, max_iter = 1e-12, 200
    f = 1; c = 1; d = 1 - (a+b)*x/(a+1); d = 1/d if abs(d) > eps else 1/eps
    f = d
    for m in range(1, max_iter):
        # even step
        nm = m * (b - m) * x / ((a + 2*m - 1) * (a + 2*m))
        d = 1 + nm * d; d = 1/d if abs(d) > eps else 1/eps
        c = 1 + nm / c if abs(c) > eps else 1 + nm/eps
        f *= c * d
        # odd step
        nm = -(a + m) * (a + b + m) * x / ((a + 2*m) * (a + 2*m + 1))
        d = 1 + nm * d; d = 1/d if abs(d) > eps else 1/eps
        c = 1 + nm / c if abs(c) > eps else 1 + nm/eps
        delta = c * d; f *= delta
        if abs(delta - 1) < eps: break
    return front * f

def t_pvalue_two(t, df):
    """Two-tailed p-value for t-statistic."""
    p_one = 1 - _t_cdf(abs(t), df)
    return min(2 * p_one, 1.0)


# ── Independent t-test ───────────────────────────────────────────────────────

def independent_ttest(g1: list, g2: list, l1="Group 1", l2="Group 2",
                       alpha=0.05, tails=2) -> dict:
    g1 = [float(x) for x in g1 if x is not None]
    g2 = [float(x) for x in g2 if x is not None]
    n1, n2 = len(g1), len(g2)
    m1, m2 = mean(g1), mean(g2)
    s1, s2 = std(g1), std(g2)
    df = n1 + n2 - 2
    pooled = math.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / df)
    se = pooled * math.sqrt(1/n1 + 1/n2)
    t = (m1 - m2) / se if se else 0
    p2 = t_pvalue_two(t, df)
    p = p2 if tails == 2 else p2 / 2
    d = (m1 - m2) / pooled if pooled else 0
    # 95% CI of the difference
    from_t = _t_quantile(0.975, df) * se
    ci = [round(m1-m2 - from_t, 4), round(m1-m2 + from_t, 4)]
    reject = p < alpha
    apa = f"t({df}) = {round(t,2)}, p {_fmt_p(p)}, d = {round(d,2)}"
    return {
        "test": "Independent-samples t-test",
        "group1": {"label": l1, "n": n1, "mean": round(m1,4), "sd": round(s1,4)},
        "group2": {"label": l2, "n": n2, "mean": round(m2,4), "sd": round(s2,4)},
        "t_statistic": round(t,4), "df": df,
        "p_value": round(p,4), "cohens_d": round(d,4),
        "effect_size_label": _d_label(abs(d)),
        "ci_95_difference": ci, "alpha": alpha, "tails": tails,
        "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": apa,
        "plain_language": _plain_t(l1, l2, m1, m2, s1, s2, reject, apa),
    }

def _t_quantile(p, df):
    """Inverse t-distribution via bisection."""
    lo, hi = 0, 100
    for _ in range(60):
        mid = (lo + hi) / 2
        if _t_cdf(mid, df) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


# ── Normality check (Shapiro-Wilk approximation) ────────────────────────────

def check_normality(values: list, label="") -> dict:
    d = sorted([float(x) for x in values if x is not None])
    n = len(d)
    if n < 3:
        return {"column": label, "test": "N/A", "status": "unknown",
                "icon": "⚠", "label": "⚠ Too few observations"}
    # Simplified normality heuristic via skewness + kurtosis Z-scores
    sk = abs(skewness(d))
    ku = abs(kurtosis(d))
    # Rough thresholds: skewness Z > 2 or kurtosis Z > 2 suggests non-normality
    sk_z = sk / math.sqrt(6/n)
    ku_z = ku / math.sqrt(24/n)
    p_approx = max(0.001, min(0.999,
        1 - (0.5 * min(sk_z/3, 1) + 0.5 * min(ku_z/3, 1))
    ))
    satisfied = sk_z < 2 and ku_z < 2
    return {
        "column": label, "test": "Skewness-Kurtosis normality check", "n": n,
        "skewness": round(skewness(d), 4), "kurtosis": round(kurtosis(d), 4),
        "skewness_z": round(sk_z, 4), "kurtosis_z": round(ku_z, 4),
        "status": "satisfied" if satisfied else "violated",
        "icon": "✓" if satisfied else "✕",
        "label": "✓ Normal distribution" if satisfied else "✕ Non-normal — consider non-parametric test",
        "recommendation": None if satisfied else "Consider Mann-Whitney U instead of t-test.",
        "p_approx": round(p_approx, 4),
        "note": "Approximation based on skewness/kurtosis. For n < 50, Shapiro-Wilk is preferable in R/SPSS.",
    }


# ── Pearson correlation ───────────────────────────────────────────────────────

def correlation(x: list, y: list, method="pearson", alpha=0.05) -> dict:
    pairs = [(float(a), float(b)) for a, b in zip(x, y)
             if a is not None and b is not None]
    n = len(pairs)
    if n < 3:
        return {"error": "Need at least 3 paired observations."}
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    mx, my = mean(xs), mean(ys)
    num = sum((a-mx)*(b-my) for a,b in pairs)
    den = math.sqrt(sum((a-mx)**2 for a in xs) * sum((b-my)**2 for b in ys))
    r = num/den if den else 0
    # t-statistic for r
    t = r * math.sqrt(n-2) / math.sqrt(1 - r**2) if abs(r) < 1 else float('inf')
    p = t_pvalue_two(t, n-2)
    reject = p < alpha
    return {
        "test": "Pearson correlation", "n": n,
        "r": round(r, 4), "r_squared": round(r**2, 4),
        "t_statistic": round(t, 4), "df": n-2,
        "p_value": round(p, 4), "reject_h0": reject,
        "frequentist_conclusion": _conclusion(reject),
        "apa_string": f"r({n-2}) = {round(r,2)}, p {_fmt_p(p)}",
        "caution": "Correlation describes association only — it does not imply causation.",
    }


# ── Cronbach's Alpha ──────────────────────────────────────────────────────────

def cronbach_alpha(matrix: list) -> dict:
    """matrix: list of lists — rows=respondents, cols=items"""
    k = len(matrix[0]) if matrix else 0
    if k < 2:
        return {"error": "Need at least 2 items."}
    n = len(matrix)
    item_vars = [variance([row[i] for row in matrix]) for i in range(k)]
    total_scores = [sum(row) for row in matrix]
    total_var = variance(total_scores)
    alpha = (k/(k-1)) * (1 - sum(item_vars)/total_var) if total_var else None
    return {
        "test": "Cronbach's Alpha", "n_items": k, "n_respondents": n,
        "alpha": round(alpha, 4) if alpha else None,
        "interpretation": _alpha_label(alpha) if alpha else "Could not compute",
        "apa_string": f"α = {round(alpha,2)}" if alpha else "α = N/A",
    }


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_p(p):
    return "< .001" if p < 0.001 else f"= {f'{p:.3f}'.lstrip('0') or '0'}"

def _conclusion(reject):
    return ("There is sufficient statistical evidence to reject the null hypothesis."
            if reject else
            "There is insufficient evidence to reject the null hypothesis.")

def _plain_t(l1, l2, m1, m2, s1, s2, reject, apa):
    d = "higher" if m1 > m2 else "lower"
    if reject:
        return (f"{l1} (M = {round(m1,2)}, SD = {round(s1,2)}) scored significantly "
                f"{d} than {l2} (M = {round(m2,2)}, SD = {round(s2,2)}), {apa}.")
    return f"No statistically significant difference was found between {l1} and {l2}, {apa}."

def _d_label(d):
    return "negligible" if d<0.2 else "small" if d<0.5 else "medium" if d<0.8 else "large"

def _alpha_label(a):
    return ("Excellent" if a>=0.9 else "Good" if a>=0.8 else
            "Acceptable" if a>=0.7 else "Questionable" if a>=0.6 else "Poor")
