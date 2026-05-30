-- Run this once against the shared platform database.
-- This adds the MCP-specific tables to the existing ai-platform-api database.

CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id            BIGSERIAL PRIMARY KEY,
    request_id    TEXT        NOT NULL,
    session_id    TEXT,
    user_id       TEXT,
    brand_id      TEXT,
    workspace_id  TEXT,
    tool_name     TEXT        NOT NULL,
    tool_version  TEXT        NOT NULL,
    input_args_json  JSONB    NOT NULL,
    output_summary   TEXT     NOT NULL,
    output_size_bytes INTEGER NOT NULL,
    latency_ms    INTEGER     NOT NULL,
    status        TEXT        NOT NULL,
    error_code    TEXT,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_brand_ts
    ON mcp_audit_log (brand_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_user_ts
    ON mcp_audit_log (user_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_tool_ts
    ON mcp_audit_log (tool_name, timestamp);

-- Brand tenancy tables (used by brand-server auth)

CREATE TABLE IF NOT EXISTS brands (
    id         TEXT        PRIMARY KEY,
    name       TEXT        NOT NULL,
    status     TEXT        NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brand_api_keys (
    id                   BIGSERIAL   PRIMARY KEY,
    brand_id             TEXT        NOT NULL REFERENCES brands(id),
    key_prefix           TEXT        NOT NULL,
    key_hash             TEXT        NOT NULL,
    environment          TEXT        NOT NULL,
    scopes               JSONB       NOT NULL DEFAULT '[]',
    rate_limit_per_minute INTEGER    NOT NULL DEFAULT 100,
    status               TEXT        NOT NULL DEFAULT 'active',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rotated_at           TIMESTAMPTZ,
    last_used_at         TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_brand_api_keys_prefix
    ON brand_api_keys (key_prefix);

-- Seed PROLOOK as a brand tenant (dogfood)
INSERT INTO brands (id, name) VALUES ('prolook', 'PROLOOK')
ON CONFLICT (id) DO NOTHING;
