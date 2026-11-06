from ragsync.chat import retrieve
from ragsync.store import get_connection

CANDIDATES = 20
RRF_K = 60

KEYWORD_SQL = """
WITH q AS (
    SELECT replace(plainto_tsquery('english', %s)::text, '&', '|')::tsquery AS query
)
SELECT c.title, c.url, c.content
FROM chunks c, q
WHERE c.content_tsv @@ q.query
ORDER BY ts_rank_cd(c.content_tsv, q.query) DESC
LIMIT %s
"""


def keyword_search(question: str, k: int = CANDIDATES) -> list[dict]:
    """Find chunks that contain any of the important words in the question."""
    with get_connection() as conn:
        rows = conn.execute(KEYWORD_SQL, (question, k)).fetchall()
    return [{"title": t, "url": u, "content": c} for t, u, c in rows]


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 5) -> list[dict]:
    """Merge ranked lists. A chunk ranked well in several lists rises to the top."""
    scores: dict[tuple, float] = {}
    items: dict[tuple, dict] = {}
    for results in result_lists:
        for rank, chunk in enumerate(results, start=1):
            key = (chunk["title"], chunk["content"])
            scores[key] = scores.get(key, 0.0) + 1 / (RRF_K + rank)
            items[key] = chunk
    ordered = sorted(scores, key=scores.get, reverse=True)
    return [items[key] for key in ordered[:k]]


def hybrid_retrieve(question: str, k: int = 5) -> list[dict]:
    vector_hits = retrieve(question, CANDIDATES)
    keyword_hits = keyword_search(question, CANDIDATES)
    return reciprocal_rank_fusion([vector_hits, keyword_hits], k)
