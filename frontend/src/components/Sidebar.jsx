const nav = [
  { id: "import",      icon: "📂", label: "Import & Clean" },
  { id: "descriptive", icon: "📊", label: "Descriptive Stats" },
  { id: "assumptions", icon: "✅", label: "Assumption Checks" },
  { id: "analysis",    icon: "🧪", label: "Run Analysis" },
  { id: "hypotheses",  icon: "🎯", label: "Hypotheses" },
  { id: "qualitative", icon: "💬", label: "Qualitative / Text" },
  { id: "reports",     icon: "📄", label: "Export & Reports" },
];

export default function Sidebar({ page, setPage, sessionMode }) {
  return (
    <aside style={{
      width: 220, background: "#0f172a", display: "flex",
      flexDirection: "column", borderRight: "1px solid #1e293b", flexShrink: 0
    }}>
      <div style={{ padding: "1.25rem 1rem", borderBottom: "1px solid #1e293b" }}>
        <div style={{ color: "white", fontWeight: 700, fontSize: "0.95rem" }}>📊 ResearchStat</div>
        <div style={{ color: "#475569", fontSize: "0.7rem", marginTop: 2 }}>
          Research Analysis Platform
        </div>
      </div>

      <nav style={{ flex: 1, padding: "0.5rem 0" }}>
        {nav.map(({ id, icon, label }) => (
          <button key={id} onClick={() => setPage(id)} style={{
            width: "100%", display: "flex", alignItems: "center",
            gap: "0.6rem", padding: "0.6rem 1rem",
            background: page === id ? "rgba(99,102,241,0.15)" : "transparent",
            borderLeft: page === id ? "3px solid #6366f1" : "3px solid transparent",
            border: "none", color: page === id ? "#a5b4fc" : "#64748b",
            cursor: "pointer", textAlign: "left", fontSize: "0.85rem",
            transition: "all 0.15s"
          }}>
            <span>{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div style={{ padding: "0.75rem 1rem", borderTop: "1px solid #1e293b" }}>
        <button onClick={() => setPage("admin")} style={{
          width: "100%", display: "flex", alignItems: "center", gap: "0.6rem",
          padding: "0.6rem 1rem", background: "transparent", border: "none",
          color: "#475569", cursor: "pointer", fontSize: "0.8rem"
        }}>
          <span>🏛️</span><span>Lab Admin</span>
        </button>
        <div style={{
          marginTop: "0.5rem", padding: "0.5rem 0.75rem", borderRadius: 6,
          background: sessionMode === "ephemeral" ? "rgba(16,185,129,0.1)" : "rgba(99,102,241,0.1)",
          fontSize: "0.7rem",
          color: sessionMode === "ephemeral" ? "#34d399" : "#818cf8"
        }}>
          {sessionMode === "ephemeral" ? "🔒 No-Save Mode" : "💾 Standard Mode"}
        </div>
      </div>
    </aside>
  );
}
