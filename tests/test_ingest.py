from ragsync import ingest


def test_build_chunks_makes_ids_and_metadata(monkeypatch):
    monkeypatch.setattr(ingest, "embed", lambda texts: [[0.0] * 3 for _ in texts])
    doc = {"id": "d1", "title": "Doc", "url": "http://x"}
    text = " ".join(f"w{i}" for i in range(200))

    chunks = ingest.build_chunks(doc, text)

    assert len(chunks) > 1
    assert chunks[0]["id"] == "d1:0"
    assert chunks[1]["chunk_index"] == 1
    assert chunks[0]["title"] == "Doc"
    assert chunks[0]["source"] == "drive"


def test_build_chunks_empty_text_gives_nothing(monkeypatch):
    monkeypatch.setattr(ingest, "embed", lambda texts: [[0.0] * 3 for _ in texts])
    doc = {"id": "d1", "title": "Doc", "url": "http://x"}
    assert ingest.build_chunks(doc, "") == []
