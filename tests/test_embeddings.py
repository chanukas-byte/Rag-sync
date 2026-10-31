from ragsync import embeddings


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"embeddings": [[1.0, 2.0], [3.0, 4.0]]}


def test_embed_calls_ollama(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(embeddings.httpx, "post", fake_post)

    result = embeddings.embed(["a", "b"])

    assert result == [[1.0, 2.0], [3.0, 4.0]]
    assert captured["url"].endswith("/api/embed")
    assert captured["json"]["input"] == ["a", "b"]


def test_embed_empty_input():
    assert embeddings.embed([]) == []
