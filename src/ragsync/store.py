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


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    register_vector(conn)
    return conn


def upsert_chunks(conn: psycopg.Connection, chunks: list[dict]) -> None:
    """Insert chunks, or update them if the same id already exists."""
    with conn.cursor() as cur:
        for c in chunks:
            cur.execute(
                UPSERT_SQL,
                (
                    c["id"],
                    c["doc_id"],
                    c["chunk_index"],
                    c["content"],
                    Vector(c["embedding"]),
                    c.get("title"),
                    c.get("source"),
                    c.get("url"),
                ),
            )
    conn.commit()
