import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid } from "recharts";
const API = process.env.REACT_APP_API_URL || "";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/api/admin/dashboard`, { headers: { "session-token": "x", "mode": "standard", "role": "admin" } })
      .then(r => { setData(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ padding: "2rem", color: "#64748b" }}>Loading usage data...</p>;

  const kpis = data ? [
    { label: "Total Researchers", value: data.total_users ?? 0, icon: "👥" },
    { label: "Sessions (30d)", value: data.sessions_last_30d ?? 0, icon: "📊" },
    { label: "Avg. Session", value: `${data.avg_session_minutes ?? 0} min`, icon: "⏱️" },
    { label: "AI Adoption", value: `${data.ai_adoption_rate ?? 0}%`, icon: "🤖" },
  ] : [];

  return (
    <div style={{ maxWidth: 960 }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: "0 0 0.5rem" }}>
        🏛️ Lab Administration Dashboard
      </h2>

      {/* Privacy notice — always visible */}
      <div style={{ background: "#f0fdf4", border: "1px solid #86efac", borderRadius: 8,
        padding: "0.75rem 1rem", marginBottom: "1rem", color: "#166534", fontSize: "0.8rem",
        display: "flex", gap: "0.5rem" }}>
        <span>🔒</span>
        <span>
          This dashboard shows <strong>usage patterns only</strong>. No research data,
          dataset contents, variable names, or individual results are accessible here.
          Researcher privacy is fully preserved.
        </span>
      </div>

      {/* No-save mode note */}
      <div style={{ background: "#fefce8", border: "1px solid #fde68a", borderRadius: 8,
        padding: "0.6rem 1rem", marginBottom: "1.5rem", color: "#854d0e", fontSize: "0.75rem" }}>
        ℹ️ Researchers who used <strong>No-Save Mode</strong> are not counted here by design —
        their sessions leave no trace anywhere in the system.
      </div>

      {/* KPI cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
        {kpis.map(({ label, value, icon }) => (
          <div key={label} style={{ background: "white", border: "1px solid #e2e8f0",
            borderRadius: 12, padding: "1.25rem", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: 4 }}>{icon}</div>
            <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a" }}>{value}</div>
            <div style={{ color: "#64748b", fontSize: "0.8rem" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Daily active users chart */}
      {data?.daily_active_users?.length > 0 && (
        <div style={{ background: "white", borderRadius: 12, padding: "1.5rem",
          marginBottom: "1.25rem", border: "1px solid #e2e8f0" }}>
          <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700, color: "#0f172a" }}>
            Daily Active Researchers (Last 30 Days)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.daily_active_users}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="users" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Feature usage chart */}
      {data?.most_used_features?.length > 0 && (
        <div style={{ background: "white", borderRadius: 12, padding: "1.5rem",
          border: "1px solid #e2e8f0" }}>
          <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700, color: "#0f172a" }}>
            Most-Used Analysis Features
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.most_used_features} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis dataKey="feature_name" type="category" width={150} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="uses" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {data?.note && (
        <p style={{ color: "#94a3b8", fontSize: "0.8rem", marginTop: "1rem" }}>{data.note}</p>
      )}
    </div>
  );
}
