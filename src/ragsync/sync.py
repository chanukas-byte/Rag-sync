import hashlib
import os

from ragsync.ingest import build_chunks
from ragsync.sources.drive import fetch_document, get_document_info, list_documents
from ragsync.store import (
    get_connection,
    get_document,
    list_active_doc_ids,
    mark_deleted,
    replace_document,
)


def normalize(text: str) -> str:
    """Ignore trailing spaces and line-ending differences."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def sync_document(conn, doc: dict, text: str) -> str:
    """Sync one document. Returns 'added', 'updated' or 'unchanged'."""
    new_hash = content_hash(text)
    existing = get_document(conn, doc["id"])
    if existing and existing["status"] == "active" and existing["content_hash"] == new_hash:
        return "unchanged"

    chunks = build_chunks(doc, text)
    replace_document(conn, doc, new_hash, chunks)
    is_new = existing is None or existing["status"] == "deleted"
    return "added" if is_new else "updated"


def sync_all(folder_id: str) -> dict:
    """Sync every document in the folder and remove the ones that disappeared."""
    conn = get_connection()
    counts = {"added": 0, "updated": 0, "unchanged": 0, "deleted": 0}
    seen = set()

    for doc in list_documents(folder_id):
        seen.add(doc["id"])
        result = sync_document(conn, doc, fetch_document(doc["id"]))
        counts[result] += 1
        print(f"{result:>9}  {doc['title']}")

    missing = list_active_doc_ids(conn) - seen
    if missing and not seen:
        conn.close()
        raise RuntimeError("Drive returned no documents; refusing to delete everything.")
    for doc_id in missing:
        mark_deleted(conn, doc_id)
        counts["deleted"] += 1
        print(f"  deleted  {doc_id}")

    conn.close()
    return counts


def handle_event(event: str, doc_id: str) -> None:
    conn = get_connection()
    try:
        if event == "deleted":
            mark_deleted(conn, doc_id)
            result = "deleted"
        else:
            doc = get_document_info(doc_id)
            result = sync_document(conn, doc, fetch_document(doc_id))
    finally:
        conn.close()
    print(f"webhook {event} {doc_id}: {result}")


if __name__ == "__main__":
    print(sync_all(os.environ["DRIVE_FOLDER_ID"]))
