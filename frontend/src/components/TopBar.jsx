import { useState } from "react";
import axios from "axios";
const API = process.env.REACT_APP_API_URL || "";

const AI_DISCLAIMER = `By enabling AI Assistance, you acknowledge that your statistical results (not raw data) will be transmitted to a third-party AI API for plain-language interpretation and thematic analysis suggestions.\n\nThe platform assumes zero responsibility for any data privacy implications arising from use of the AI layer.\n\nYou may disable AI at any time. Raw dataset content is never sent to the AI.`;

export default function TopBar({ dataset, sessionMode, aiEnabled, setAiEnabled,
  aiDisclaimerAccepted, setAiDisclaimerAccepted, alpha, setAlpha, apiHeaders }) {

  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const handleAiToggle = async () => {
    if (aiEnabled) {
      setAiEnabled(false);
      await axios.patch(`${API}/api/sessions/settings`,
        { ai_enabled: false }, { headers: apiHeaders });
    } else if (!aiDisclaimerAccepted) {
      setShowDisclaimer(true);
    } else {
      setAiEnabled(true);
    }
  };

  const acceptDisclaimer = async () => {
    await axios.post(`${API}/api/ai/disclaimer/accept`,
      { accepted: true }, { headers: apiHeaders });
    setAiDisclaimerAccepted(true);
    setAiEnabled(true);
    setShowDisclaimer(false);
  };

  return (
    <>
      <header style={{
        background: "#0f172a", borderBottom: "1px solid #1e293b",
        padding: "0 1.5rem", height: 52, display: "flex",
        alignItems: "center", gap: "1.5rem", flexShrink: 0
      }}>
        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
          Dataset: <strong style={{ color: "white" }}>{dataset?.filename ?? "—"}</strong>
        </span>
        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
          N = <strong style={{ color: "white" }}>{dataset?.n ?? "—"}</strong>
        </span>
        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
          α = <strong style={{ color: "white" }}>{alpha}</strong>
        </span>

        {/* Session mode badge */}
        <div style={{
          padding: "3px 10px", borderRadius: 999, fontSize: "0.75rem", fontWeight: 600,
          background: sessionMode === "ephemeral" ? "rgba(16,185,129,0.15)" : "rgba(99,102,241,0.15)",
          color: sessionMode === "ephemeral" ? "#34d399" : "#a5b4fc",
          border: `1px solid ${sessionMode === "ephemeral" ? "rgba(16,185,129,0.3)" : "rgba(99,102,241,0.3)"}`,
        }}>
          {sessionMode === "ephemeral" ? "🔒 No-Save Mode" : "💾 Standard Mode"}
        </div>

        {/* AI Toggle */}
        <button onClick={handleAiToggle} style={{
          marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.4rem",
          background: aiEnabled ? "rgba(124,58,237,0.2)" : "rgba(55,65,81,0.5)",
          border: `1px solid ${aiEnabled ? "#7c3aed" : "#374151"}`,
          borderRadius: 999, padding: "4px 14px", color: aiEnabled ? "#c4b5fd" : "#6b7280",
          cursor: "pointer", fontSize: "0.8rem", fontWeight: 600, transition: "all 0.2s"
        }}>
          <span>{aiEnabled ? "🤖" : "🔒"}</span>
          <span>AI Assistance: {aiEnabled ? "ON" : "OFF"}</span>
        </button>
      </header>

      {/* AI Disclaimer Modal */}
      {showDisclaimer && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999
        }}>
          <div style={{
            background: "#1e293b", borderRadius: 16, padding: "2rem",
            maxWidth: 480, width: "90%", border: "1px solid #7c3aed"
          }}>
            <h3 style={{ color: "white", margin: "0 0 1rem" }}>⚠️ AI Privacy Disclaimer</h3>
            <p style={{ color: "#94a3b8", fontSize: "0.875rem", lineHeight: 1.7, whiteSpace: "pre-line" }}>
              {AI_DISCLAIMER}
            </p>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button onClick={acceptDisclaimer} style={{
                flex: 1, background: "#7c3aed", color: "white", border: "none",
                borderRadius: 8, padding: "0.6rem", cursor: "pointer", fontWeight: 600
              }}>
                I Understand — Enable AI
              </button>
              <button onClick={() => setShowDisclaimer(false)} style={{
                flex: 1, background: "#374151", color: "#94a3b8", border: "none",
                borderRadius: 8, padding: "0.6rem", cursor: "pointer"
              }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
