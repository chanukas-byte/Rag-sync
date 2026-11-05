from ragsync import sync


class FakeConn:
    def rollback(self):
        pass

    def close(self):
        pass


def test_handle_event_records_failure(monkeypatch):
    recorded = []

    def boom(doc_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(sync, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(sync, "get_document_info", boom)
    monkeypatch.setattr(
        sync,
        "record_failed_event",
        lambda conn, event, doc_id, error: recorded.append((event, doc_id, error)),
    )

    sync.handle_event("updated", "abc")

    assert recorded[0][0] == "updated"
    assert recorded[0][1] == "abc"
    assert "boom" in recorded[0][2]


def test_run_sync_records_success(monkeypatch):
    calls = []
    monkeypatch.setattr(sync, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(sync, "start_run", lambda conn, trigger: 7)
    monkeypatch.setattr(sync, "sync_all", lambda folder_id: {"added": 1})
    monkeypatch.setattr(
        sync,
        "finish_run",
        lambda conn, run_id, counts, status, error=None: calls.append((run_id, status)),
    )

    assert sync.run_sync("folder", "nightly") == {"added": 1}
    assert calls == [(7, "success")]


def test_run_sync_records_failure(monkeypatch):
    calls = []

    def fail(folder_id):
        raise RuntimeError("drive down")

    monkeypatch.setattr(sync, "get_connection", lambda: FakeConn())
    monkeypatch.setattr(sync, "start_run", lambda conn, trigger: 8)
    monkeypatch.setattr(sync, "sync_all", fail)
    monkeypatch.setattr(
        sync,
        "finish_run",
        lambda conn, run_id, counts, status, error=None: calls.append((run_id, status)),
    )

    try:
        sync.run_sync("folder")
    except RuntimeError:
        pass

    assert calls == [(8, "failed")]
