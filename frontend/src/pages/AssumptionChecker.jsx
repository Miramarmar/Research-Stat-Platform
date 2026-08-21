import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function AssumptionChecker({ apiHeaders, dataset, aiEnabled }) {
  const [selected, setSelected] = useState([]);
  const [testType, setTestType] = useState("comparison");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const cols = dataset?.columns || [];

  const run = async () => {
    setLoading(true);
    const res = await axios.post(`${API}/api/stats/assumptions`,
      { columns: selected, test_type: testType }, { headers: apiHeaders });
    setResult(res.data);
    setLoading(false);
  };

  const STATUS_ICON = { satisfied: "✓", potential_issue: "⚠", violated: "✕", unknown: "⚠" };
  const STATUS_COLOR = { satisfied: "#166534", potential_issue: "#854d0e", violated: "#991b1b", unknown: "#64748b" };
  const STATUS_BG = { satisfied: "#dcfce7", potential_issue: "#fef9c3", violated: "#fee2e2", unknown: "#f1f5f9" };

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.25rem" }}>
        Assumption Checks
      </h2>
      <p style={{ color: "#64748b", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Run before primary tests. Results display ✓ Satisfied · ⚠ Potential issue · ✕ Violated.
      </p>
      <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
        padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#374151",
            display: "block", marginBottom: 6 }}>Select Variables to Check</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {cols.map(c => (
              <button key={c} onClick={() => setSelected(s => s.includes(c) ? s.filter(x => x !== c) : [...s, c])}
                style={{ padding: "4px 10px", borderRadius: 6, fontSize: "0.8rem", cursor: "pointer",
                  background: selected.includes(c) ? "#6366f1" : "#f1f5f9",
                  color: selected.includes(c) ? "white" : "#374151",
                  border: "none", fontWeight: selected.includes(c) ? 600 : 400 }}>
                {c}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <select value={testType} onChange={e => setTestType(e.target.value)}
            style={{ padding: "0.4rem 0.75rem", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: "0.85rem" }}>
            <option value="comparison">Group comparison</option>
            <option value="regression">Regression</option>
          </select>
          <button onClick={run} disabled={loading || selected.length === 0}
            style={{ background: "#6366f1", color: "white", border: "none", borderRadius: 8,
              padding: "0.5rem 1.25rem", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem",
              opacity: selected.length ? 1 : 0.5 }}>
            {loading ? "Checking..." : "Run Checks"}
          </button>
        </div>
      </div>
      {result && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
            <span style={{ fontWeight: 700, color: "#0f172a" }}>Results</span>
            <span style={{ fontSize: "0.75rem", padding: "2px 8px", borderRadius: 999, fontWeight: 600,
              background: result.all_satisfied ? "#dcfce7" : "#fee2e2",
              color: result.all_satisfied ? "#166534" : "#991b1b" }}>
              {result.all_satisfied ? "All assumptions satisfied" : "Issues detected — review before proceeding"}
            </span>
          </div>
          {result.checks.map((c, i) => (
            <div key={i} style={{ background: STATUS_BG[c.status] || "#f8fafc",
              border: `1px solid ${STATUS_COLOR[c.status] || "#e2e8f0"}40`,
              borderRadius: 10, padding: "1rem", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <span style={{ fontWeight: 700, color: STATUS_COLOR[c.status] || "#374151", marginRight: "0.5rem" }}>
                    {STATUS_ICON[c.status] || "⚠"}
                  </span>
                  <span style={{ fontWeight: 600 }}>{c.column || "All groups"} — {c.test}</span>
                </div>
                <span style={{ fontSize: "0.75rem", color: STATUS_COLOR[c.status] || "#64748b", fontWeight: 600 }}>
                  {c.label}
                </span>
              </div>
              {c.p_value !== undefined && (
                <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: 4 }}>
                  Statistic = {c.statistic}, p = {c.p_value}, n = {c.n}
                </div>
              )}
              {c.recommendation && (
                <div style={{ marginTop: 6, fontSize: "0.8rem", color: "#92400e",
                  background: "#fffbeb", padding: "4px 8px", borderRadius: 6 }}>
                  💡 {c.recommendation}
                  {aiEnabled && c.ai_suggestion_available && (
                    <span style={{ marginLeft: "0.5rem", background: "#7c3aed", color: "white",
                      fontSize: "0.65rem", padding: "1px 5px", borderRadius: 3 }}>AI suggestion available</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
