from fastapi.testclient import TestClient

from ragsync import api


class FakeConn:
    def execute(self, sql, *args):
        class Result:
            def fetchone(self):
                return ("success",)

        return Result()

    def close(self):
        pass


class OkResponse:
    def raise_for_status(self):
        pass


def test_ready_ok(monkeypatch):
    monkeypatch.setattr(api, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(api.httpx, "get", lambda *a, **k: OkResponse())

    response = TestClient(api.app).get("/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"
    assert response.json()["last_sync"] == "success"


def test_ready_degraded_when_database_down(monkeypatch):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(api, "get_connection", boom)
    monkeypatch.setattr(api.httpx, "get", lambda *a, **k: OkResponse())

    response = TestClient(api.app).get("/ready")

    assert response.status_code == 503
    assert response.json()["database"].startswith("error")
