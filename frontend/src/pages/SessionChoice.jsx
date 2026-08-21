import axios from "axios";

const API = process.env.REACT_APP_API_URL || "";

export default function SessionChoice({ onChoice }) {
  const start = async (mode) => {
    const res = await axios.post(`${API}/api/sessions/start`, { mode, lab_id: "silab" });
    onChoice(mode, res.data.session_token);
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
    }}>
      <div style={{ maxWidth: 680, width: "100%", padding: "2rem" }}>
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📊</div>
          <h1 style={{ color: "white", fontSize: "1.75rem", fontWeight: 700, margin: 0 }}>
            ResearchStat Platform
          </h1>
          <p style={{ color: "#94a3b8", marginTop: "0.5rem" }}>
            Academic statistical analysis · HCI · Psychology · Education · Social Sciences
          </p>
        </div>

        <p style={{ color: "#cbd5e1", textAlign: "center", marginBottom: "1.5rem" }}>
          Choose how this session handles your research data before uploading anything.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          {/* Standard Mode */}
          <button onClick={() => start("standard")} style={{
            background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 16, padding: "1.75rem", textAlign: "left",
            cursor: "pointer", color: "white", transition: "all 0.2s"
          }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(99,102,241,0.2)"; e.currentTarget.style.borderColor = "#6366f1"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"; }}
          >
            <div style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>💾</div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: "0.5rem" }}>Standard Mode</div>
            <div style={{ color: "#94a3b8", fontSize: "0.875rem", lineHeight: 1.6, marginBottom: "1rem" }}>
              Session and audit trail saved securely. Resume later, export anytime.
            </div>
            <ul style={{ color: "#64748b", fontSize: "0.8rem", margin: 0, paddingLeft: "1.25rem", lineHeight: 2 }}>
              <li>Encrypted database storage</li>
              <li>Resume analysis across sessions</li>
              <li>Usage counted in lab statistics</li>
            </ul>
          </button>

          {/* No-Save Mode */}
          <button onClick={() => start("ephemeral")} style={{
            background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.3)",
            borderRadius: 16, padding: "1.75rem", textAlign: "left",
            cursor: "pointer", color: "white", transition: "all 0.2s"
          }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(16,185,129,0.15)"; e.currentTarget.style.borderColor = "#10b981"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "rgba(16,185,129,0.08)"; e.currentTarget.style.borderColor = "rgba(16,185,129,0.3)"; }}
          >
            <div style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>🔒</div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: "0.5rem" }}>
              No-Save Mode
              <span style={{ marginLeft: "0.5rem", background: "#059669", color: "white",
                fontSize: "0.65rem", padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>
                PRIVACY FIRST
              </span>
            </div>
            <div style={{ color: "#6ee7b7", fontSize: "0.875rem", lineHeight: 1.6, marginBottom: "1rem" }}>
              Nothing written to any database or disk. Exists in RAM only for this session.
            </div>
            <ul style={{ color: "#34d399", fontSize: "0.8rem", margin: 0, paddingLeft: "1.25rem", lineHeight: 2 }}>
              <li>Zero data persistence — guaranteed</li>
              <li>No login required</li>
              <li>Session cleared when tab closes</li>
              <li>Not counted in lab usage stats</li>
            </ul>
          </button>
        </div>

        <details style={{ marginTop: "1.5rem" }}>
          <summary style={{ color: "#94a3b8", cursor: "pointer", fontSize: "0.875rem" }}>
            What does "No-Save Mode" actually protect?
          </summary>
          <div style={{
            marginTop: "0.75rem", background: "rgba(255,255,255,0.05)",
            borderRadius: 8, padding: "1rem", color: "#94a3b8", fontSize: "0.8rem", lineHeight: 1.8
          }}>
            <b style={{ color: "white" }}>Never written anywhere:</b> your dataset, variable names,
            hypothesis text, test results, AI suggestions, audit decisions, and your identity.<br />
            <b style={{ color: "white" }}>In server RAM only (cleared on session end):</b> the active
            dataframe used for calculations — technically required to run statistics.<br />
            <b style={{ color: "white" }}>Exportable before you close:</b> all outputs, tables, and
            APA reports — download them before ending your session.
          </div>
        </details>
      </div>
    </div>
  );
}
