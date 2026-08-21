import { useState, useEffect } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function DescriptiveStats({ apiHeaders, dataset }) {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!dataset) return;
    setLoading(true);
    const res = await axios.get(`${API}/api/stats/descriptive`, { headers: apiHeaders });
    setStats(res.data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [dataset]);

  const NUM_FIELDS = [["n","N"],["missing","Missing"],["mean","Mean"],["median","Median"],
    ["sd","SD"],["variance","Variance"],["min","Min"],["max","Max"],
    ["skewness","Skewness"],["kurtosis","Kurtosis"]];

  return (
    <div style={{ maxWidth: 1000 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 1rem" }}>
        Descriptive Statistics
      </h2>
      {loading && <p style={{ color: "#64748b" }}>Computing...</p>}
      {!dataset && <p style={{ color: "#94a3b8" }}>Import a dataset first.</p>}
      {Object.entries(stats).map(([col, s]) => (
        <div key={col} style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0",
          marginBottom: "1rem", overflow: "hidden" }}>
          <div style={{ padding: "0.75rem 1.25rem", background: "#f8fafc",
            borderBottom: "1px solid #e2e8f0", fontWeight: 700, color: "#0f172a",
            display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <span>{col}</span>
            <span style={{ background: "#dbeafe", color: "#1e40af", fontSize: "0.7rem",
              fontWeight: 600, padding: "1px 6px", borderRadius: 4 }}>{s.type}</span>
          </div>
          <div style={{ padding: "1rem 1.25rem" }}>
            {s.type === "numerical" ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                {NUM_FIELDS.map(([key, label]) => s[key] !== undefined && s[key] !== null && (
                  <div key={key} style={{ background: "#f8fafc", borderRadius: 6,
                    padding: "0.4rem 0.75rem", border: "1px solid #e2e8f0", minWidth: 80 }}>
                    <div style={{ fontSize: "0.65rem", color: "#94a3b8", fontWeight: 600 }}>{label}</div>
                    <div style={{ fontWeight: 700, color: "#0f172a" }}>{s[key]}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: "0.5rem", fontSize: "0.8rem", color: "#64748b" }}>
                  N = {s.n} | Unique values: {s.unique_values}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {Object.entries(s.frequencies || {}).slice(0, 10).map(([val, count]) => (
                    <span key={val} style={{ background: "#f1f5f9", borderRadius: 6,
                      padding: "2px 8px", fontSize: "0.75rem", color: "#374151" }}>
                      {val}: {count} ({s.valid_percentages?.[val]}%)
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
