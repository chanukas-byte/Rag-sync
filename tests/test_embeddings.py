import numpy as np

from ragsync import embeddings


class FakeModel:
    def embed(self, texts):
        return (np.ones(3) for _ in texts)


def test_embed_returns_plain_lists(monkeypatch):
    monkeypatch.setattr(embeddings, "_model", lambda: FakeModel())
    assert embeddings.embed(["a", "b"]) == [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]


def test_embed_empty_input():
    assert embeddings.embed([]) == []
