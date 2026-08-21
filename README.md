# ResearchStat Platform

**Academic Statistical Analysis · HCI · Psychology · Education · Social Sciences**

> "A deterministic statistical engine where the researcher has absolute control,
> augmented by an explainable, strictly separated AI assistant."

Built for SILAB — Institut Supérieur de Documentation, University of Manouba

---

## What This Does

A full-stack research analysis platform that:
- Runs **all statistics deterministically** (SciPy/StatsModels — the AI never touches math)
- Provides an **optional, toggleable AI layer** for plain-language interpretation and thematic analysis only
- Offers **No-Save Mode** (zero data persistence — everything in RAM, cleared on close)
- Includes a **Lab Admin Dashboard** (usage analytics only — research data never visible)
- Generates **APA-formatted reports** (PDF, Word, CSV)
- Supports Arabic, French, and English text analysis

---

## Quick Start (Local Development)

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your keys
uvicorn main:app --reload
# → API running at http://localhost:8000
# → Docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm start
# → App running at http://localhost:3000
```

---

## Session Modes

| | Standard Mode | No-Save Mode |
|---|---|---|
| Dataset stored | DB metadata | RAM only |
| Results stored | Database | RAM only |
| Audit trail | Database | RAM (exportable) |
| Login required | Yes | No |
| Resume later | ✓ | ✗ |
| Counted in admin stats | ✓ | ✗ |
| Tab close = data loss | No | Yes (warned) |

---

## Statistical Modules

- Descriptive statistics (N, Mean, Median, SD, Variance, Skewness, Kurtosis, IQR, CI)
- Assumption checks (Shapiro-Wilk/KS normality, Levene's homogeneity, VIF collinearity)
- t-tests (independent, paired) — Welch and Student variants
- ANOVA (one-way) + ANCOVA (with covariate control)
- Non-parametric (Mann-Whitney U, Wilcoxon Signed-Rank, Kruskal-Wallis)
- Correlations (Pearson, Spearman, Kendall's tau)
- Regression (simple linear, multiple linear, logistic)
- Reliability (Cronbach's α, McDonald's ω)
- Learning gain (pre-test / post-test auto-calculation)
- Qualitative text (word frequency, n-grams — AI OFF)
- Thematic analysis (AI ON — with researcher control)
- Mixed-methods cross-tabulation (themes × groups)

---

## Architecture

```
frontend/          React 18 — dashboard, charts, report UI
backend/
  main.py          FastAPI entry point + cleanup thread
  stats/engine.py  ALL math — SciPy, StatsModels, Pandas
  ai/assistant.py  AI layer — interpretation + thematic only
  session/         Ephemeral store (RAM-only No-Save Mode)
  analytics/       Usage telemetry (admin dashboard only)
  api/             REST endpoints (sessions, data, stats, reports, admin)
```

---

## Deployment

See `MINISTRY_MIGRATION.md` for the complete ministry hosting guide.
See `SUPABASE_SETUP.sql` to create the analytics tables and functions.

---

## Philosophy

1. **Deterministic engine is the source of truth.** Python calculates. React displays.
2. **AI text is always visually distinct.** Purple border + "AI" badge — never confused with statistics.
3. **Nothing deleted silently.** Every cleaning decision is logged before execution.
4. **Frequentist phrasing is hardcoded.** "Reject H₀" / "Fail to Reject H₀" — never "proven."
5. **No-Save Mode is genuinely stateless.** The server is a calculator, not a recorder.
