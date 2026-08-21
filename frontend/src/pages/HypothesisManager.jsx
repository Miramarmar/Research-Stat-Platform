import { useState, useEffect } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function HypothesisManager({ apiHeaders, dataset, alpha }) {
  const [hypotheses, setHypotheses] = useState([]);
  const [form, setForm] = useState({ h1: "", h0: "", variable_iv: "", variable_dv: "",
    expected_direction: "any", test_type: "ttest" });
  const [adding, setAdding] = useState(false);

  const cols = dataset?.columns || [];

  const load = async () => {
    const res = await axios.get(`${API}/api/hypotheses/`, { headers: apiHeaders });
    setHypotheses(res.data.hypotheses);
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    setAdding(true);
    await axios.post(`${API}/api/hypotheses/`, form, { headers: apiHeaders });
    setForm({ h1: "", h0: "", variable_iv: "", variable_dv: "", expected_direction: "any", test_type: "ttest" });
    await load();
    setAdding(false);
  };

  const STATUS_STYLE = {
    pending: { bg: "#f1f5f9", color: "#64748b", label: "Pending evaluation" },
    reject_h0: { bg: "#dcfce7", color: "#166534", label: "Reject H₀" },
    fail_to_reject: { bg: "#fee2e2", color: "#991b1b", label: "Fail to Reject H₀" },
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.25rem" }}>
        Hypothesis Manager
      </h2>
      <p style={{ color: "#64748b", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Define H₁ and H₀, map them to variables, then link completed analyses to evaluate.
        Results use strict frequentist language — never "proven" or "confirmed".
      </p>

      {/* Add hypothesis form */}
      <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
        padding: "1.5rem", marginBottom: "1.5rem" }}>
        <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700 }}>Add Hypothesis</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div>
            <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151", display: "block", marginBottom: 4 }}>
              H₁ — Alternative Hypothesis
            </label>
            <textarea value={form.h1} onChange={e => setForm(f => ({ ...f, h1: e.target.value }))}
              placeholder="e.g. There is a significant difference in learning outcomes between the experimental and control groups."
              style={{ width: "100%", height: 60, padding: "0.5rem", borderRadius: 8,
                border: "1px solid #e2e8f0", fontSize: "0.875rem", resize: "vertical", boxSizing: "border-box" }} />
          </div>
          <div>
            <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151", display: "block", marginBottom: 4 }}>
              H₀ — Null Hypothesis
            </label>
            <textarea value={form.h0} onChange={e => setForm(f => ({ ...f, h0: e.target.value }))}
              placeholder="e.g. There is no significant difference in learning outcomes between the experimental and control groups."
              style={{ width: "100%", height: 60, padding: "0.5rem", borderRadius: 8,
                border: "1px solid #e2e8f0", fontSize: "0.875rem", resize: "vertical", boxSizing: "border-box" }} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.75rem" }}>
            {[
              { key: "variable_iv", label: "IV (Independent)" },
              { key: "variable_dv", label: "DV (Dependent)" },
            ].map(({ key, label }) => (
              <div key={key}>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151",
                  display: "block", marginBottom: 4 }}>{label}</label>
                <select value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  style={{ width: "100%", padding: "0.4rem", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: "0.8rem" }}>
                  <option value="">—</option>
                  {cols.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            ))}
            <div>
              <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151",
                display: "block", marginBottom: 4 }}>Expected Direction</label>
              <select value={form.expected_direction}
                onChange={e => setForm(f => ({ ...f, expected_direction: e.target.value }))}
                style={{ width: "100%", padding: "0.4rem", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: "0.8rem" }}>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="any">Any</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "#374151",
                display: "block", marginBottom: 4 }}>Planned Test</label>
              <select value={form.test_type}
                onChange={e => setForm(f => ({ ...f, test_type: e.target.value }))}
                style={{ width: "100%", padding: "0.4rem", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: "0.8rem" }}>
                {["ttest", "anova", "correlation", "regression", "nonparametric"].map(t =>
                  <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <button onClick={add} disabled={adding || !form.h1 || !form.h0}
            style={{ background: "#6366f1", color: "white", border: "none", borderRadius: 8,
              padding: "0.6rem 1.25rem", cursor: "pointer", fontWeight: 600,
              fontSize: "0.875rem", alignSelf: "flex-start",
              opacity: form.h1 && form.h0 ? 1 : 0.5 }}>
            {adding ? "Adding..." : "+ Add Hypothesis"}
          </button>
        </div>
      </div>

      {/* Hypothesis list */}
      {hypotheses.map((h) => {
        const st = STATUS_STYLE[h.status] || STATUS_STYLE.pending;
        return (
          <div key={h.id} style={{ background: "white", borderRadius: 12,
            border: "1px solid #e2e8f0", marginBottom: "1rem", overflow: "hidden" }}>
            <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid #f1f5f9",
              display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: "#0f172a", marginBottom: 4 }}>
                  H₁: {h.h1}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.85rem" }}>H₀: {h.h0}</div>
              </div>
              <span style={{ background: st.bg, color: st.color, padding: "3px 10px",
                borderRadius: 999, fontSize: "0.75rem", fontWeight: 700, flexShrink: 0, marginLeft: "1rem" }}>
                {st.label}
              </span>
            </div>
            {h.apa_string && (
              <div style={{ padding: "0.75rem 1.25rem", background: "#f8fafc" }}>
                <code style={{ fontSize: "0.8rem", color: "#374151" }}>{h.apa_string}</code>
                {h.formal_conclusion && (
                  <p style={{ margin: "0.4rem 0 0", fontSize: "0.8rem", fontStyle: "italic",
                    color: h.status === "reject_h0" ? "#166534" : "#991b1b" }}>
                    {h.formal_conclusion}
                  </p>
                )}
              </div>
            )}
            <div style={{ padding: "0.5rem 1.25rem", display: "flex", gap: "1rem",
              fontSize: "0.75rem", color: "#94a3b8" }}>
              {h.variable_iv && <span>IV: {h.variable_iv}</span>}
              {h.variable_dv && <span>DV: {h.variable_dv}</span>}
              {h.expected_direction && <span>Direction: {h.expected_direction}</span>}
            </div>
          </div>
        );
      })}
      {hypotheses.length === 0 && (
        <p style={{ color: "#94a3b8", fontSize: "0.875rem", textAlign: "center", padding: "2rem" }}>
          No hypotheses defined yet. Add your first H₁/H₀ above.
        </p>
      )}
    </div>
  );
}
