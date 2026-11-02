CREATE TABLE IF NOT EXISTS documents (
  doc_id         TEXT PRIMARY KEY,
  source         TEXT NOT NULL,
  title          TEXT,
  content_hash   TEXT NOT NULL,
  chunk_count    INT  NOT NULL,
  last_synced_at TIMESTAMPTZ DEFAULT now(),
  status         TEXT NOT NULL DEFAULT 'active'
);