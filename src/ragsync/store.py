import os

import psycopg
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector

load_dotenv()

UPSERT_SQL = """
INSERT INTO chunks
    (id, doc_id, chunk_index, content, embedding, title, source, url)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding,
    title = EXCLUDED.title,
    source = EXCLUDED.source,
    url = EXCLUDED.url,
    updated_at = now()
"""

DOCUMENT_SQL = """
INSERT INTO documents
    (doc_id, source, title, content_hash, chunk_count, last_synced_at, status)
VALUES
    (%s, %s, %s, %s, %s, now(), 'active')
ON CONFLICT (doc_id) DO UPDATE SET
    source = EXCLUDED.source,
    title = EXCLUDED.title,
    content_hash = EXCLUDED.content_hash,
    chunk_count = EXCLUDED.chunk_count,
    last_synced_at = now(),
    status = 'active'
"""

MARK_DELETED_SQL = """
UPDATE documents
SET status = 'deleted', chunk_count = 0, last_synced_at = now()
WHERE doc_id = %s
"""


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    register_vector(conn)
    return conn


def _chunk_params(c: dict) -> tuple:
    return (
        c["id"],
        c["doc_id"],
        c["chunk_index"],
        c["content"],
        Vector(c["embedding"]),
        c.get("title"),
        c.get("source"),
        c.get("url"),
    )


def upsert_chunks(conn: psycopg.Connection, chunks: list[dict]) -> None:
    """Insert chunks, or update them if the same id already exists."""
    with conn.cursor() as cur:
        for c in chunks:
            cur.execute(UPSERT_SQL, _chunk_params(c))
    conn.commit()


def get_document(conn: psycopg.Connection, doc_id: str) -> dict | None:
    row = conn.execute(
        "SELECT content_hash, status FROM documents WHERE doc_id = %s", (doc_id,)
    ).fetchone()
    return {"content_hash": row[0], "status": row[1]} if row else None


def list_active_doc_ids(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute("SELECT doc_id FROM documents WHERE status = 'active'").fetchall()
    return {r[0] for r in rows}


def replace_document(
    conn: psycopg.Connection, doc: dict, content_hash: str, chunks: list[dict]
) -> None:
    """Swap a document's chunks for new ones in ONE transaction."""
    with conn.transaction():
        conn.execute("DELETE FROM chunks WHERE doc_id = %s", (doc["id"],))
        for c in chunks:
            conn.execute(UPSERT_SQL, _chunk_params(c))
        conn.execute(
            DOCUMENT_SQL,
            (doc["id"], "drive", doc.get("title"), content_hash, len(chunks)),
        )
    conn.commit()


def mark_deleted(conn: psycopg.Connection, doc_id: str) -> None:
    """Remove all chunks of a document and mark it deleted."""
    with conn.transaction():
        conn.execute("DELETE FROM chunks WHERE doc_id = %s", (doc_id,))
        conn.execute(MARK_DELETED_SQL, (doc_id,))
    conn.commit()
