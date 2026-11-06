def start_run(conn, trigger: str) -> int:
    with conn.transaction():
        row = conn.execute(
            "INSERT INTO sync_runs (trigger) VALUES (%s) RETURNING id", (trigger,)
        ).fetchone()
    conn.commit()
    return row[0]


def finish_run(conn, run_id: int, counts: dict | None, status: str, error: str | None = None):
    counts = counts or {}
    with conn.transaction():
        conn.execute(
            """
            UPDATE sync_runs
            SET finished_at = now(), status = %s,
                added = %s, updated = %s, unchanged = %s, deleted = %s, error = %s
            WHERE id = %s
            """,
            (
                status,
                counts.get("added", 0),
                counts.get("updated", 0),
                counts.get("unchanged", 0),
                counts.get("deleted", 0),
                error,
                run_id,
            ),
        )
    conn.commit()


def record_failed_event(conn, event: str, doc_id: str, error: str) -> None:
    with conn.transaction():
        conn.execute(
            "INSERT INTO failed_events (event, doc_id, error) VALUES (%s, %s, %s)",
            (event, doc_id, error),
        )
    conn.commit()
