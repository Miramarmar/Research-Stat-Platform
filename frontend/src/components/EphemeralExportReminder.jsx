import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

export default function EphemeralExportReminder({ apiHeaders }) {
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(null);

  if (dismissed) return null;

  const download = async (format) => {
    setLoading(format);
    try {
      const res = await axios.post(`${API}/api/reports/generate`,
        { format, title: "Statistical Analysis Report" },
        { headers: apiHeaders, responseType: format === "json" ? "json" : "blob" }
      );
      const mimes = { pdf: "application/pdf",
        docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" };
      const url = URL.createObjectURL(new Blob([res.data], { type: mimes[format] }));
      const a = document.createElement("a"); a.href = url;
      a.download = `report.${format}`; a.click();
    } catch (err) { alert("Export error: " + err.message); }
    setLoading(null);
  };

  return (
    <div style={{
      position: "fixed", bottom: "1.5rem", right: "1.5rem",
      background: "#0f172a", color: "white", borderRadius: 14,
      padding: "1rem 1.25rem", maxWidth: 300,
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      border: "1px solid rgba(255,255,255,0.1)", zIndex: 1000
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontWeight: 700 }}>
          <span>🔒</span><span>No-Save Mode</span>
        </div>
        <button onClick={() => setDismissed(true)} style={{ background: "none", border: "none",
          color: "#64748b", cursor: "pointer", fontSize: "1rem", padding: 0 }}>✕</button>
      </div>
      <p style={{ margin: "0.5rem 0 0.75rem", fontSize: "0.8rem", color: "#94a3b8", lineHeight: 1.5 }}>
        You have results. Export now — they will be gone when you close this tab.
      </p>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button onClick={() => download("pdf")} disabled={!!loading}
          style={{ flex: 1, background: "#6366f1", color: "white", border: "none",
            borderRadius: 8, padding: "0.45rem", cursor: "pointer",
            fontSize: "0.75rem", fontWeight: 600, opacity: loading ? 0.6 : 1 }}>
          {loading === "pdf" ? "..." : "📄 PDF"}
        </button>
        <button onClick={() => download("docx")} disabled={!!loading}
          style={{ flex: 1, background: "#374151", color: "white", border: "none",
            borderRadius: 8, padding: "0.45rem", cursor: "pointer",
            fontSize: "0.75rem", fontWeight: 600, opacity: loading ? 0.6 : 1 }}>
          {loading === "docx" ? "..." : "📝 Word"}
        </button>
      </div>
    </div>
  );
}
