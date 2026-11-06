CREATE TABLE IF NOT EXISTS sync_runs (
    id BIGSERIAL PRIMARY KEY,
    trigger TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    added INT NOT NULL DEFAULT 0,
    updated INT NOT NULL DEFAULT 0,
    unchanged INT NOT NULL DEFAULT 0,
    deleted INT NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS failed_events (
    id BIGSERIAL PRIMARY KEY,
    event TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    error TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);