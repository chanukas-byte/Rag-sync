import os

from ragsync.chunking import chunk_text
from ragsync.embeddings import embed
from ragsync.sources.drive import fetch_document, list_documents
from ragsync.store import get_connection, upsert_chunks


def build_chunks(doc: dict, text: str) -> list[dict]:
    """Cut one document into chunks, embed them, and add the metadata."""
    pieces = chunk_text(text)
    vectors = embed(pieces)
    return [
        {
            "id": f"{doc['id']}:{i}",
            "doc_id": doc["id"],
            "chunk_index": i,
            "content": piece,
            "embedding": vector,
            "title": doc["title"],
            "source": "drive",
            "url": doc["url"],
        }
        for i, (piece, vector) in enumerate(zip(pieces, vectors, strict=True))
    ]


def ingest_all(folder_id: str) -> int:
    """Read every document in the Drive folder and store its chunks."""
    conn = get_connection()
    total = 0
    for doc in list_documents(folder_id):
        text = fetch_document(doc["id"])
        chunks = build_chunks(doc, text)
        upsert_chunks(conn, chunks)
        total += len(chunks)
        print(f"{doc['title']}: {len(chunks)} chunks")
    conn.close()
    return total


if __name__ == "__main__":
    count = ingest_all(os.environ["DRIVE_FOLDER_ID"])
    print(f"Done: {count} chunks stored")
