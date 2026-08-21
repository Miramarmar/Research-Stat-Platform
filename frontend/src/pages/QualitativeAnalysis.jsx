import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function QualitativeAnalysis({ apiHeaders, dataset, aiEnabled }) {
  const [col, setCol] = useState("");
  const [result, setResult] = useState(null);
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState("");

  const cols = dataset?.columns || [];

  const runDeterministic = async () => {
    setLoading(true);
    const res = await axios.post(`${API}/api/stats/text/deterministic`,
      { column: col, top_n: 20, ngram_n: 2 }, { headers: apiHeaders });
    setResult(res.data);
    setThemes([]);
    setLoading(false);
  };

  const runThematic = async () => {
    if (!aiEnabled) return alert("Enable AI Assistance to run thematic analysis.");
    setLoading(true);
    const res = await axios.post(`${API}/api/ai/thematic`,
      { column: col, context }, { headers: apiHeaders });
    setThemes(res.data.themes || []);
    setLoading(false);
  };

  const themeAction = async (action, indices, newName) => {
    await axios.post(`${API}/api/ai/thematic/action`,
      { action, theme_indices: indices, new_name: newName }, { headers: apiHeaders });
    if (action === "delete") setThemes(t => t.filter((_, i) => !indices.includes(i)));
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.25rem" }}>
        Qualitative & Text Analysis
      </h2>
      <p style={{ color: "#64748b", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        AI OFF: deterministic word frequency and n-grams. AI ON: thematic clustering
        with mandatory source quote evidence.
      </p>
      <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
        padding: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#374151",
            display: "block", marginBottom: 4 }}>Open-Ended Text Column</label>
          <select value={col} onChange={e => setCol(e.target.value)}
            style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
              border: "1px solid #e2e8f0", fontSize: "0.875rem" }}>
            <option value="">Select column</option>
            {cols.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        {aiEnabled && (
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#374151",
              display: "block", marginBottom: 4 }}>Research Context (helps AI)</label>
            <input value={context} onChange={e => setContext(e.target.value)}
              placeholder="e.g. Responses from Tunisian students about AI learning tools"
              style={{ width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
                border: "1px solid #e2e8f0", fontSize: "0.875rem", boxSizing: "border-box" }} />
          </div>
        )}
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button onClick={runDeterministic} disabled={!col || loading}
            style={{ background: "#6366f1", color: "white", border: "none", borderRadius: 8,
              padding: "0.5rem 1.25rem", cursor: "pointer", fontWeight: 600,
              opacity: col ? 1 : 0.5, fontSize: "0.875rem" }}>
            {loading ? "Analyzing..." : "🔢 Word Frequency"}
          </button>
          <button onClick={runThematic} disabled={!col || loading || !aiEnabled}
            title={!aiEnabled ? "Enable AI Assistance first" : ""}
            style={{ background: aiEnabled ? "rgba(124,58,237,0.1)" : "#f1f5f9",
              color: aiEnabled ? "#7c3aed" : "#94a3b8",
              border: `1px solid ${aiEnabled ? "#7c3aed" : "#e2e8f0"}`,
              borderRadius: 8, padding: "0.5rem 1.25rem", cursor: aiEnabled ? "pointer" : "not-allowed",
              fontWeight: 600, fontSize: "0.875rem" }}>
            🤖 AI Thematic Analysis
          </button>
        </div>
      </div>

      {/* Deterministic results */}
      {result && (
        <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
          padding: "1.25rem", marginBottom: "1rem" }}>
          <div style={{ fontWeight: 700, marginBottom: "0.75rem" }}>
            Word Frequency — {result.word_frequency?.total_responses} responses
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {result.word_frequency?.top_words?.map(({ word, count, pct }) => (
              <span key={word} style={{ background: "#f1f5f9", borderRadius: 6,
                padding: "3px 10px", fontSize: "0.8rem", color: "#374151" }}>
                {word} <strong>{count}</strong> ({pct}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI themes — purple border, AI badge on every card */}
      {themes.length > 0 && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
            <span style={{ background: "#7c3aed", color: "white", fontSize: "0.65rem",
              fontWeight: 700, padding: "2px 6px", borderRadius: 4 }}>AI GENERATED</span>
            <span style={{ fontSize: "0.75rem", color: "#6d28d9" }}>
              All themes must be verified against source quotes before reporting.
              Researcher controls: merge · rename · delete
            </span>
          </div>
          {themes.map((theme, idx) => (
            <div key={idx} style={{ background: "rgba(124,58,237,0.04)",
              border: "2px solid #7c3aed", borderRadius: 12,
              padding: "1.25rem", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontWeight: 700, color: "#4c1d95", marginBottom: 4 }}>
                    {theme.theme_name}
                  </div>
                  <div style={{ color: "#6d28d9", fontSize: "0.8rem" }}>{theme.description}</div>
                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                    <span style={{ background: "#ede9fe", color: "#5b21b6", padding: "2px 8px",
                      borderRadius: 4, fontSize: "0.75rem", fontWeight: 600 }}>
                      N = {theme.n} ({theme.pct}%)
                    </span>
                  </div>
                </div>
                <button onClick={() => themeAction("delete", [idx])}
                  style={{ background: "#fee2e2", color: "#991b1b", border: "none",
                    borderRadius: 6, padding: "3px 8px", cursor: "pointer", fontSize: "0.75rem" }}>
                  Delete
                </button>
              </div>
              {theme.representative_quotes?.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                  <div style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: 600,
                    textTransform: "uppercase", marginBottom: 4 }}>Source Quotes</div>
                  {theme.representative_quotes.map((q, qi) => (
                    <blockquote key={qi} style={{ margin: "0 0 0.4rem", paddingLeft: "0.75rem",
                      borderLeft: "3px solid #7c3aed", color: "#4c1d95",
                      fontSize: "0.85rem", fontStyle: "italic" }}>
                      "{q}"
                    </blockquote>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
