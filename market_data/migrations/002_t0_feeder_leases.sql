CREATE TABLE IF NOT EXISTS market_data.feeder_leases (
    lease_name TEXT PRIMARY KEY CHECK (length(btrim(lease_name)) > 0),
    owner_id TEXT NULL,
    generation BIGINT NOT NULL CHECK (generation >= 0),
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK (
        (owner_id IS NULL AND expires_at = '-infinity'::timestamptz)
        OR
        (owner_id IS NOT NULL AND expires_at > '-infinity'::timestamptz)
    )
);

CREATE INDEX IF NOT EXISTS feeder_leases_expiry_idx
    ON market_data.feeder_leases (expires_at);
