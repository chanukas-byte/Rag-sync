from fastapi.testclient import TestClient

from ragsync import api

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_returns_answer(monkeypatch):
    monkeypatch.setattr(api.chat, "answer", lambda q: {"answer": "hi", "sources": []})
    response = client.post("/chat", json={"question": "hello?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "hi", "sources": []}


def test_chat_rejects_empty_question():
    assert client.post("/chat", json={"question": ""}).status_code == 422


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "rag-sync" in response.text
