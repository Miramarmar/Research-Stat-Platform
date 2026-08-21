-- ResearchStat Platform — Supabase / PostgreSQL Setup
-- Run this in your Supabase SQL Editor (or psql for ministry hosting)

-- ═══════════════════════════════════════════════════════
-- USAGE ANALYTICS TABLES (admin dashboard only)
-- Research data NEVER goes in these tables
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS usage_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_id      TEXT NOT NULL DEFAULT 'external',
    device_type TEXT DEFAULT 'desktop',
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    duration_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS usage_feature_events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id   UUID REFERENCES usage_sessions(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    ai_enabled   BOOLEAN DEFAULT FALSE,
    occurred_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- ROW-LEVEL SECURITY — researchers can never see analytics
-- ═══════════════════════════════════════════════════════

ALTER TABLE usage_sessions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_feature_events ENABLE ROW LEVEL SECURITY;

-- Only service role (backend) can read/write analytics
CREATE POLICY "backend_only_sessions"
    ON usage_sessions FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "backend_only_events"
    ON usage_feature_events FOR ALL
    USING (auth.role() = 'service_role');

-- ═══════════════════════════════════════════════════════
-- DASHBOARD SUMMARY FUNCTION (admin read-only)
-- ═══════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_dashboard_summary()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN json_build_object(
        'total_users',          (SELECT COUNT(DISTINCT lab_id) FROM usage_sessions),
        'sessions_last_30d',    (
            SELECT COUNT(*) FROM usage_sessions
            WHERE started_at > NOW() - INTERVAL '30 days'
        ),
        'avg_session_minutes',  (
            SELECT ROUND(AVG(duration_seconds) / 60.0, 1)
            FROM usage_sessions
            WHERE duration_seconds IS NOT NULL
        ),
        'ai_adoption_rate',     (
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (WHERE ai_enabled = TRUE) /
                NULLIF(COUNT(*), 0), 1
            )
            FROM usage_feature_events
        ),
        'most_used_features',   (
            SELECT json_agg(row_to_json(t))
            FROM (
                SELECT feature_name, COUNT(*) AS uses
                FROM usage_feature_events
                GROUP BY feature_name
                ORDER BY uses DESC
                LIMIT 6
            ) t
        ),
        'daily_active_users',   (
            SELECT json_agg(row_to_json(t))
            FROM (
                SELECT DATE(started_at) AS day, COUNT(*) AS sessions
                FROM usage_sessions
                WHERE started_at > NOW() - INTERVAL '30 days'
                GROUP BY day
                ORDER BY day
            ) t
        )
    );
END;
$$;
