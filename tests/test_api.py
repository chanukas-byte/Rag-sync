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


def test_webhook_rejects_wrong_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    response = client.post(
        "/webhook/doc-event",
        json={"event": "updated", "doc_id": "d1"},
        headers={"X-Webhook-Secret": "wrong"},
    )
    assert response.status_code == 401


def test_webhook_rejects_missing_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    response = client.post("/webhook/doc-event", json={"event": "updated", "doc_id": "d1"})
    assert response.status_code == 401


def test_webhook_accepts_and_runs_handler(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    calls = []
    monkeypatch.setattr(
        api.sync, "handle_event", lambda event, doc_id: calls.append((event, doc_id))
    )

    response = client.post(
        "/webhook/doc-event",
        json={"event": "updated", "doc_id": "d1"},
        headers={"X-Webhook-Secret": "s3cret"},
    )

    assert response.status_code == 202
    assert calls == [("updated", "d1")]


def test_webhook_rejects_unknown_event(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    response = client.post(
        "/webhook/doc-event",
        json={"event": "exploded", "doc_id": "d1"},
        headers={"X-Webhook-Secret": "s3cret"},
    )
    assert response.status_code == 422
