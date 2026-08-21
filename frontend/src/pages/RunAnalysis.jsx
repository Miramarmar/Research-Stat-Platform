import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

const TESTS = [
  { id: "ttest_ind", label: "Independent t-test", category: "Group Comparison" },
  { id: "ttest_paired", label: "Paired t-test", category: "Group Comparison" },
  { id: "mann_whitney", label: "Mann-Whitney U", category: "Non-Parametric" },
  { id: "wilcoxon", label: "Wilcoxon Signed-Rank", category: "Non-Parametric" },
  { id: "kruskal", label: "Kruskal-Wallis H", category: "Non-Parametric" },
  { id: "anova", label: "One-Way ANOVA", category: "Group Comparison" },
  { id: "pearson", label: "Pearson Correlation", category: "Correlation" },
  { id: "spearman", label: "Spearman Correlation", category: "Correlation" },
  { id: "kendall", label: "Kendall's Tau", category: "Correlation" },
  { id: "linear", label: "Linear Regression", category: "Regression" },
  { id: "logistic", label: "Logistic Regression", category: "Regression" },
  { id: "cronbach", label: "Cronbach's Alpha + Omega", category: "Reliability" },
  { id: "learning_gain", label: "Learning Gain (Pre/Post)", category: "Experimental" },
];

function ResultCard({ result }) {
  if (!result) return null;
  const reject = result.reject_h0;
  return (
    <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
      <div style={{
        padding: "0.75rem 1.25rem",
        background: reject === true ? "#f0fdf4" : reject === false ? "#fff1f2" : "#f8fafc",
        borderBottom: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center"
      }}>
        <span style={{ fontWeight: 700, color: "#0f172a" }}>{result.test}</span>
        {reject !== undefined && (
          <span style={{
            padding: "3px 10px", borderRadius: 999, fontSize: "0.75rem", fontWeight: 700,
            background: reject ? "#dcfce7" : "#fee2e2",
            color: reject ? "#166534" : "#991b1b"
          }}>
            {reject ? "Reject H₀" : "Fail to Reject H₀"}
          </span>
        )}
      </div>
      <div style={{ padding: "1.25rem" }}>
        {result.apa_string && (
          <div style={{ marginBottom: "0.75rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: 600, textTransform: "uppercase", marginBottom: 2 }}>APA Result</div>
            <code style={{ background: "#f8fafc", padding: "6px 10px", borderRadius: 6,
              display: "block", fontSize: "0.875rem", color: "#1e293b", border: "1px solid #e2e8f0" }}>
              {result.apa_string}
            </code>
          </div>
        )}
        {result.frequentist_conclusion && (
          <div style={{ marginBottom: "0.75rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: 600, textTransform: "uppercase", marginBottom: 2 }}>Formal Conclusion</div>
            <p style={{ color: "#374151", fontSize: "0.875rem", margin: 0, fontStyle: "italic" }}>
              {result.frequentist_conclusion}
            </p>
          </div>
        )}
        {result.plain_language && (
          <div style={{ marginBottom: "0.75rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: 600, textTransform: "uppercase", marginBottom: 2 }}>Plain Language</div>
            <p style={{ color: "#374151", fontSize: "0.875rem", margin: 0 }}>{result.plain_language}</p>
          </div>
        )}
        {result.caution && (
          <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6,
            padding: "0.5rem 0.75rem", fontSize: "0.8rem", color: "#92400e" }}>
            ⚠ {result.caution}
          </div>
        )}
        {/* Key metrics grid */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "1rem" }}>
          {[
            ["p-value", result.p_value],
            ["Effect Size", result.cohens_d ?? result.eta_squared ?? result.rank_biserial_r ?? result.r],
            ["Effect Label", result.effect_size_label],
            ["df", result.df],
            ["N", result.n || (result.group1?.n !== undefined ? `${result.group1.n} / ${result.group2?.n}` : null)],
          ].filter(([, v]) => v !== null && v !== undefined).map(([label, val]) => (
            <div key={label} style={{ background: "#f8fafc", borderRadius: 6, padding: "0.4rem 0.75rem",
              border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.65rem", color: "#94a3b8", fontWeight: 600 }}>{label}</div>
              <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.9rem" }}>{String(val)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function RunAnalysis({ apiHeaders, dataset, alpha, aiEnabled, onResult }) {
  const [test, setTest] = useState("ttest_ind");
  const [col1, setCol1] = useState("");
  const [col2, setCol2] = useState("");
  const [groupCol, setGroupCol] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);

  const cols = dataset?.columns || [];
  const categories = [...new Set(TESTS.map(t => t.category))];

  const run = async () => {
    setLoading(true);
    setResult(null);
    try {
      let res;
      if (["pearson", "spearman", "kendall"].includes(test)) {
        res = await axios.post(`${API}/api/stats/correlation`,
          { x_column: col1, y_column: col2, method: test, alpha }, { headers: apiHeaders });
      } else if (["linear", "logistic"].includes(test)) {
        res = await axios.post(`${API}/api/stats/regression`,
          { type: test, dependent: col1, predictors: col2.split(",").map(s => s.trim()).filter(Boolean), alpha }, { headers: apiHeaders });
      } else if (test === "cronbach") {
        res = await axios.post(`${API}/api/stats/reliability`,
          { columns: col2.split(",").map(s => s.trim()).filter(Boolean) }, { headers: apiHeaders });
      } else if (test === "learning_gain") {
        res = await axios.post(`${API}/api/stats/learning-gain`,
          { pre_column: col1, post_column: col2 }, { headers: apiHeaders });
      } else if (test === "anova") {
        res = await axios.post(`${API}/api/stats/anova`,
          { group_column: groupCol, value_column: col1, alpha }, { headers: apiHeaders });
      } else if (["mann_whitney", "wilcoxon", "kruskal"].includes(test)) {
        res = await axios.post(`${API}/api/stats/nonparametric`,
          { test, column1: col1, column2: col2 || null, group_col: groupCol || null, alpha }, { headers: apiHeaders });
      } else {
        const type = test === "ttest_ind" ? "independent" : "paired";
        res = await axios.post(`${API}/api/stats/ttest`,
          { type, column1: col1, column2: col2, group_col: groupCol || null, alpha }, { headers: apiHeaders });
      }
      setResult(res.data);
      onResult && onResult(res.data);
    } catch (err) {
      alert("Analysis error: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  const getAiSuggestion = async () => {
    if (!aiEnabled) return alert("Enable AI Assistance in the top bar first.");
    try {
      const assumptionRes = await axios.post(`${API}/api/stats/assumptions`,
        { columns: [col1, col2].filter(Boolean), test_type: "comparison" }, { headers: apiHeaders });
      const sugRes = await axios.post(`${API}/api/ai/suggest-test`, {
        normality_results: assumptionRes.data.checks.filter(c => c.type === "normality"),
        n: dataset?.n || 0, n_groups: 2, design: "between-subjects"
      }, { headers: apiHeaders });
      setAiSuggestion(sugRes.data);
    } catch (err) {
      alert("AI suggestion error: " + err.message);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 1.5rem" }}>
        Run Statistical Analysis
      </h2>

      <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
        padding: "1.5rem", marginBottom: "1.5rem" }}>

        {/* Test selector */}
        <div style={{ marginBottom: "1.25rem" }}>
          <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600,
            color: "#374151", marginBottom: "0.4rem" }}>Statistical Test</label>
          <select value={test} onChange={e => setTest(e.target.value)}
            style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
              border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}>
            {categories.map(cat => (
              <optgroup key={cat} label={cat}>
                {TESTS.filter(t => t.category === cat).map(t => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.25rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600,
              color: "#374151", marginBottom: "0.4rem" }}>
              {["linear", "logistic"].includes(test) ? "Dependent Variable" : "Column 1 / Pre-Test"}
            </label>
            <select value={col1} onChange={e => setCol1(e.target.value)}
              style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
                border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}>
              <option value="">Select column</option>
              {cols.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600,
              color: "#374151", marginBottom: "0.4rem" }}>
              {["linear", "logistic"].includes(test) ? "Predictors (comma-separated)" :
               test === "cronbach" ? "Items (comma-separated)" : "Column 2 / Post-Test"}
            </label>
            {["linear", "logistic", "cronbach"].includes(test) ? (
              <input value={col2} onChange={e => setCol2(e.target.value)} placeholder="col1, col2, col3"
                style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
                  border: "1px solid #e2e8f0", fontSize: "0.875rem", boxSizing: "border-box" }} />
            ) : (
              <select value={col2} onChange={e => setCol2(e.target.value)}
                style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
                  border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}>
                <option value="">Select column</option>
                {cols.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            )}
          </div>
        </div>

        {["ttest_ind", "anova", "mann_whitney", "kruskal"].includes(test) && (
          <div style={{ marginBottom: "1.25rem" }}>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600,
              color: "#374151", marginBottom: "0.4rem" }}>Group Column (optional)</label>
            <select value={groupCol} onChange={e => setGroupCol(e.target.value)}
              style={{ width: "50%", padding: "0.5rem 0.75rem", borderRadius: 8,
                border: "1px solid #e2e8f0", fontSize: "0.875rem", background: "white" }}>
              <option value="">None</option>
              {cols.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button onClick={run} disabled={loading || !col1}
            style={{ background: "#6366f1", color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.5rem", cursor: col1 ? "pointer" : "not-allowed",
              fontWeight: 600, fontSize: "0.875rem", opacity: col1 ? 1 : 0.5 }}>
            {loading ? "Running..." : "▶ Run Analysis"}
          </button>
          {aiEnabled && (
            <button onClick={getAiSuggestion}
              style={{ background: "rgba(124,58,237,0.1)", color: "#7c3aed",
                border: "1px solid #7c3aed", borderRadius: 8, padding: "0.6rem 1rem",
                cursor: "pointer", fontWeight: 600, fontSize: "0.875rem" }}>
              🤖 Ask AI to Suggest Test
            </button>
          )}
        </div>
      </div>

      {/* AI suggestion — visually distinct with purple border */}
      {aiSuggestion && (
        <div style={{ background: "rgba(124,58,237,0.05)", border: "2px solid #7c3aed",
          borderRadius: 12, padding: "1.25rem", marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
            <span style={{ background: "#7c3aed", color: "white", fontSize: "0.65rem",
              fontWeight: 700, padding: "2px 6px", borderRadius: 4 }}>AI SUGGESTION</span>
            <span style={{ color: "#6d28d9", fontSize: "0.75rem" }}>
              {aiSuggestion.disclaimer}
            </span>
          </div>
          <pre style={{ color: "#4c1d95", fontSize: "0.875rem", margin: 0, whiteSpace: "pre-wrap",
            fontFamily: "inherit" }}>{aiSuggestion.suggestion}</pre>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            {aiSuggestion.actions?.map(a => (
              <button key={a} style={{
                background: a === "Accept" ? "#7c3aed" : "#e5e7eb",
                color: a === "Accept" ? "white" : "#374151",
                border: "none", borderRadius: 6, padding: "4px 12px",
                cursor: "pointer", fontSize: "0.8rem", fontWeight: 600
              }} onClick={() => setAiSuggestion(null)}>
                {a}
              </button>
            ))}
          </div>
        </div>
      )}

      {result && <ResultCard result={result} />}
    </div>
  );
}
