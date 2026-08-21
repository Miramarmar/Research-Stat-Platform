import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

const TYPE_COLORS = {
  numerical: { bg: "#dcfce7", color: "#166534", label: "Numerical" },
  categorical: { bg: "#dbeafe", color: "#1e40af", label: "Categorical" },
  likert: { bg: "#fef9c3", color: "#854d0e", label: "Likert" },
  open_ended: { bg: "#fce7f3", color: "#9d174d", label: "Open-Ended" },
  pretest: { bg: "#ede9fe", color: "#5b21b6", label: "Pre-Test" },
  posttest: { bg: "#ffedd5", color: "#9a3412", label: "Post-Test" },
};

const ACTION_COLORS = { Keep: "#6366f1", Exclude: "#ef4444", "Impute (Mean)": "#f59e0b",
  "Impute (Median)": "#f59e0b", "Impute (Mode)": "#f59e0b", Modify: "#8b5cf6" };

export default function DataImport({ apiHeaders, setDataset }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [colTypes, setColTypes] = useState({});
  const [decisions, setDecisions] = useState({});
  const [applyingIssue, setApplyingIssue] = useState(null);

  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await axios.post(`${API}/api/data/import`, form, { headers: apiHeaders });
      setResult(res.data);
      setColTypes(res.data.column_types);
      setDataset(res.data);
      setDecisions({});
    } catch (err) {
      alert("Import failed: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  const overrideType = async (col, newType) => {
    const updated = { ...colTypes, [col]: newType };
    setColTypes(updated);
    await axios.post(`${API}/api/data/types/override`,
      { column: col, new_type: newType }, { headers: apiHeaders });
  };

  const applyDecision = async (issue, action) => {
    setApplyingIssue(issue.type + (issue.column || ""));
    try {
      const res = await axios.post(`${API}/api/data/clean`, {
        issue_type: issue.type,
        column: issue.column || null,
        rows: issue.rows || null,
        action,
      }, { headers: apiHeaders });
      setDecisions(d => ({ ...d, [issue.type + (issue.column || "")]: { action, result: res.data } }));
    } catch (err) {
      alert("Error applying decision: " + err.message);
    }
    setApplyingIssue(null);
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.25rem" }}>
        Import Dataset
      </h2>
      <p style={{ color: "#64748b", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        Accepts .csv, .xlsx, and Google Forms exports. Variable types auto-detected.
      </p>

      <label style={{
        display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem",
        border: "2px dashed #cbd5e1", borderRadius: 12, padding: "2.5rem",
        cursor: "pointer", background: "white", transition: "border-color 0.2s",
        marginBottom: "1.5rem"
      }}>
        <span style={{ fontSize: "2rem" }}>📂</span>
        <span style={{ fontWeight: 600, color: "#374151" }}>
          {loading ? "Importing..." : "Click to upload or drag & drop"}
        </span>
        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>.csv · .xlsx · Google Forms export</span>
        <input type="file" accept=".csv,.xlsx" onChange={upload} style={{ display: "none" }} />
      </label>

      {result && (
        <>
          {/* Dataset summary */}
          <div style={{
            background: "white", borderRadius: 12, padding: "1.25rem",
            border: "1px solid #e2e8f0", marginBottom: "1.5rem",
            display: "flex", gap: "2rem", flexWrap: "wrap"
          }}>
            {[
              ["📋 File", result.filename],
              ["👥 Participants", `N = ${result.n}`],
              ["📐 Variables", result.n_cols],
              ["⚠️ Issues Found", result.n_issues],
            ].map(([label, val]) => (
              <div key={label}>
                <div style={{ color: "#64748b", fontSize: "0.75rem" }}>{label}</div>
                <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#0f172a" }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Data issues — researcher must decide for each */}
          {result.data_issues?.length > 0 && (
            <div style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#b45309", margin: "0 0 0.75rem" }}>
                ⚠️ Data Quality Issues — Researcher Decision Required
              </h3>
              <p style={{ color: "#78716c", fontSize: "0.8rem", marginBottom: "1rem" }}>
                The platform never auto-deletes data. Every decision is logged in the audit trail.
              </p>
              {result.data_issues.map((issue) => {
                const key = issue.type + (issue.column || "");
                const decided = decisions[key];
                return (
                  <div key={key} style={{
                    background: decided ? "#f0fdf4" : "#fffbeb",
                    border: `1px solid ${decided ? "#86efac" : "#fde68a"}`,
                    borderRadius: 10, padding: "1rem", marginBottom: "0.75rem"
                  }}>
                    <div style={{ fontWeight: 600, marginBottom: "0.5rem", color: "#1c1917" }}>
                      {issue.description}
                    </div>
                    {decided ? (
                      <div style={{ color: "#166534", fontSize: "0.8rem", fontWeight: 600 }}>
                        ✓ Decision logged: <strong>{decided.action}</strong>
                        {decided.result?.rows_affected > 0 && ` — ${decided.result.rows_affected} row(s) affected`}
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                        {issue.options.map(opt => (
                          <button key={opt}
                            onClick={() => applyDecision(issue, opt)}
                            disabled={applyingIssue === key}
                            style={{
                              background: ACTION_COLORS[opt] || "#6366f1", color: "white",
                              border: "none", borderRadius: 6, padding: "4px 12px",
                              cursor: "pointer", fontSize: "0.8rem", fontWeight: 600,
                              opacity: applyingIssue === key ? 0.6 : 1
                            }}>
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Variable type table */}
          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
            <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid #e2e8f0", fontWeight: 700, color: "#0f172a" }}>
              Variable Types — Review & Override
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  {["Variable", "Detected Type", "Override", "Preview Values"].map(h => (
                    <th key={h} style={{ padding: "0.6rem 1rem", textAlign: "left",
                      fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.columns.map((col, i) => {
                  const type = colTypes[col] || "numerical";
                  const tc = TYPE_COLORS[type] || TYPE_COLORS.numerical;
                  const preview = result.preview?.slice(0, 3).map(r => r[col]).filter(v => v !== "").join(", ");
                  return (
                    <tr key={col} style={{ borderTop: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "0.6rem 1rem", fontWeight: 600, color: "#1e293b", fontSize: "0.85rem" }}>
                        {col}
                      </td>
                      <td style={{ padding: "0.6rem 1rem" }}>
                        <span style={{ background: tc.bg, color: tc.color,
                          padding: "2px 8px", borderRadius: 4, fontSize: "0.75rem", fontWeight: 600 }}>
                          {tc.label}
                        </span>
                      </td>
                      <td style={{ padding: "0.6rem 1rem" }}>
                        <select value={type} onChange={e => overrideType(col, e.target.value)}
                          style={{ fontSize: "0.8rem", padding: "3px 6px", borderRadius: 4,
                            border: "1px solid #e2e8f0", background: "white" }}>
                          {Object.keys(TYPE_COLORS).map(t => (
                            <option key={t} value={t}>{TYPE_COLORS[t].label}</option>
                          ))}
                        </select>
                      </td>
                      <td style={{ padding: "0.6rem 1rem", color: "#94a3b8", fontSize: "0.75rem" }}>
                        {preview || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
