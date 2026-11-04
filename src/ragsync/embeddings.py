import os

import httpx
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")


@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a vector using a local Ollama server."""
    if not texts:
        return []
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": MODEL_NAME, "input": texts},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
