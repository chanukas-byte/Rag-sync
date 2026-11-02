import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")


def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a vector using a local Ollama server."""
    if not texts:
        return []
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": MODEL_NAME, "input": texts},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
