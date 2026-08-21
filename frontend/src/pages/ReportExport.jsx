import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function ReportExport({ apiHeaders, sessionMode }) {
  const [loading, setLoading] = useState(null);

  const download = async (format) => {
    setLoading(format);
    try {
      const res = await axios.post(`${API}/api/reports/generate`,
        { format, title: "Statistical Analysis Report", include_audit: true, include_hypotheses: true },
        { headers: apiHeaders, responseType: format === "json" ? "json" : "blob" }
      );
      if (format === "json") {
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url;
        a.download = "analysis_config.json"; a.click();
      } else {
        const mimes = { pdf: "application/pdf",
          docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          csv: "text/csv" };
        const url = URL.createObjectURL(new Blob([res.data], { type: mimes[format] }));
        const a = document.createElement("a"); a.href = url;
        a.download = `report.${format}`; a.click();
      }
    } catch (err) {
      alert("Export error: " + err.message);
    }
    setLoading(null);
  };

  const formats = [
    { id: "pdf", icon: "📄", label: "PDF Report", desc: "APA-formatted full report with all results, conclusions, and audit trail." },
    { id: "docx", icon: "📝", label: "Word Document", desc: "Editable .docx with hypothesis evaluations, APA strings, and plain-language summaries." },
    { id: "csv", icon: "📊", label: "Results CSV", desc: "Flat table of all tests run: test name, APA string, p-value, conclusion." },
    { id: "json", icon: "⚙️", label: "Reproducibility Config", desc: "Full analysis configuration snapshot. Re-import to reproduce this exact environment." },
  ];

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.25rem" }}>
        Export & Reports
      </h2>
      <p style={{ color: "#64748b", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        All reports are APA-formatted. Raw data is never included in any export.
      </p>

      {sessionMode === "ephemeral" && (
        <div style={{ background: "#fefce8", border: "1px solid #fde68a", borderRadius: 8,
          padding: "0.75rem 1rem", marginBottom: "1.5rem", color: "#854d0e", fontSize: "0.85rem" }}>
          ⚠️ <strong>No-Save Mode:</strong> Export your results before closing this tab.
          Once the session ends, all results are permanently cleared.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {formats.map(({ id, icon, label, desc }) => (
          <div key={id} style={{ background: "white", borderRadius: 12,
            border: "1px solid #e2e8f0", padding: "1.25rem",
            display: "flex", alignItems: "center", gap: "1.25rem" }}>
            <span style={{ fontSize: "2rem" }}>{icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: 2 }}>{label}</div>
              <div style={{ color: "#64748b", fontSize: "0.8rem" }}>{desc}</div>
            </div>
            <button onClick={() => download(id)} disabled={loading === id}
              style={{ background: "#6366f1", color: "white", border: "none",
                borderRadius: 8, padding: "0.5rem 1.25rem", cursor: "pointer",
                fontWeight: 600, fontSize: "0.85rem", flexShrink: 0,
                opacity: loading === id ? 0.6 : 1 }}>
              {loading === id ? "Generating..." : "Download"}
            </button>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "1.5rem", background: "#f8fafc", borderRadius: 10,
        padding: "1rem", border: "1px solid #e2e8f0" }}>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem", fontWeight: 700 }}>
          📋 Audit Trail
        </h3>
        <p style={{ color: "#64748b", fontSize: "0.8rem", margin: 0 }}>
          The audit trail records every action: dataset import, cleaning decisions,
          variable type overrides, tests run, AI suggestions accepted/rejected,
          and hypothesis evaluations. It is included in PDF and Word exports.
          Download the JSON config to reproduce the full analysis environment.
        </p>
      </div>
    </div>
  );
}
