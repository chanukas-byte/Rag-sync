from ragsync.sources import hybrid


def chunk(name):
    return {"title": name, "url": "", "content": name}


def test_rrf_prefers_chunks_found_by_both_lists():
    a, b, c = chunk("a"), chunk("b"), chunk("c")

    fused = hybrid.reciprocal_rank_fusion([[a, b], [c, b]], k=3)

    assert fused[0] == b


def test_rrf_limits_results_to_k():
    items = [chunk(str(i)) for i in range(10)]

    assert len(hybrid.reciprocal_rank_fusion([items], k=5)) == 5


def test_hybrid_retrieve_combines_both_searches(monkeypatch):
    monkeypatch.setattr(hybrid, "retrieve", lambda question, k: [chunk("v1"), chunk("v2")])
    monkeypatch.setattr(hybrid, "keyword_search", lambda question, k: [chunk("k1"), chunk("v2")])

    titles = [c["title"] for c in hybrid.hybrid_retrieve("question", 3)]

    assert titles[0] == "v2"
    assert set(titles) == {"v1", "v2", "k1"}
