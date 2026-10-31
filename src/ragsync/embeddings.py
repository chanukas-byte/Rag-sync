from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a vector (a list of 384 numbers)."""
    if not texts:
        return []
    return [vector.tolist() for vector in _model().embed(texts)]
