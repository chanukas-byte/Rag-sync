from ragsync import evaluate


def test_first_rank_finds_position():
    chunks = [{"title": "x.txt"}, {"title": "02-etl-vs-elt.txt"}]
    assert evaluate.first_rank(chunks, "02-etl-vs-elt") == 2


def test_first_rank_miss():
    assert evaluate.first_rank([{"title": "a.txt"}], "b") is None


def test_score_hit_rate_and_mrr():
    result = evaluate.score([1, 2, None, 4])
    assert result["questions"] == 4
    assert result["hit_rate"] == 0.75
    assert result["mrr"] == (1 + 0.5 + 0.25) / 4


def test_evaluate_uses_retrieve(monkeypatch, tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question": "q1", "expected_doc": "doc-a"}\n{"question": "q2", "expected_doc": "doc-b"}\n'
    )
    monkeypatch.setattr(evaluate, "retrieve", lambda question, k: [{"title": "doc-a.txt"}])

    result = evaluate.evaluate(path)

    assert result["hit_rate"] == 0.5
    assert result["mrr"] == 0.5
