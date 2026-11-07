import httpx
from pgvector import Vector

from ragsync.embeddings import OLLAMA_URL, embed
from ragsync.store import get_connection

CHAT_MODEL = "qwen2.5:0.5b"
TOP_K = 5

SEARCH_SQL = """
SELECT title, url, content
FROM chunks
ORDER BY embedding <=> %s
LIMIT %s
"""


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    """Find the k chunks whose meaning is closest to the question."""
    vector = embed([question])[0]
    with get_connection() as conn:
        rows = conn.execute(SEARCH_SQL, (Vector(vector), k)).fetchall()
    return [{"title": t, "url": u, "content": c} for t, u, c in rows]


def search(question: str, k: int = TOP_K) -> list[dict]:
    """Hybrid search: vector + keyword, merged."""
    from ragsync.sources.hybrid import hybrid_retrieve

    return hybrid_retrieve(question, k)


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{c['title']}]\n{c['content']}" for c in chunks)
    return (
        "Answer the question using ONLY the context below. "
        "If the answer is not in the context, say you do not know. "
        "Mention the document title you used.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\nAnswer:"
    )


def answer(question: str) -> dict:
    """Return the model's answer and the documents it was based on."""
    chunks = search(question)
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": [{"role": "user", "content": build_prompt(question, chunks)}],
            "stream": False,
        },
        timeout=300,
    )
    response.raise_for_status()
    unique = {}
    for c in chunks:
        unique.setdefault(c["url"], c["title"])
    return {
        "answer": response.json()["message"]["content"],
        "sources": [{"title": t, "url": u} for u, t in unique.items()],
    }


if __name__ == "__main__":
    import sys

    result = answer(" ".join(sys.argv[1:]))
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"- {s['title']}: {s['url']}")
