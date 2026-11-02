from ragsync import sync

DOC = {"id": "d1", "title": "T", "url": "u"}


def test_hash_ignores_trailing_spaces_and_line_endings():
    assert sync.content_hash("a  \r\nb\n") == sync.content_hash("a\nb")


def test_hash_changes_when_text_changes():
    assert sync.content_hash("a") != sync.content_hash("b")


def test_unchanged_document_is_skipped(monkeypatch):
    stored = {"content_hash": sync.content_hash("hello"), "status": "active"}
    monkeypatch.setattr(sync, "get_document", lambda conn, doc_id: stored)
    called = []
    monkeypatch.setattr(sync, "build_chunks", lambda doc, text: called.append(1) or [])

    assert sync.sync_document(None, DOC, "hello") == "unchanged"
    assert called == []


def test_new_document_is_added(monkeypatch):
    monkeypatch.setattr(sync, "get_document", lambda conn, doc_id: None)
    monkeypatch.setattr(sync, "build_chunks", lambda doc, text: ["chunk"])
    saved = []
    monkeypatch.setattr(
        sync, "replace_document", lambda conn, doc, h, chunks: saved.append((doc["id"], h, chunks))
    )

    assert sync.sync_document(None, DOC, "hello") == "added"
    assert saved == [("d1", sync.content_hash("hello"), ["chunk"])]


def test_changed_document_is_updated(monkeypatch):
    stored = {"content_hash": "old-hash", "status": "active"}
    monkeypatch.setattr(sync, "get_document", lambda conn, doc_id: stored)
    monkeypatch.setattr(sync, "build_chunks", lambda doc, text: ["chunk"])
    monkeypatch.setattr(sync, "replace_document", lambda conn, doc, h, chunks: None)

    assert sync.sync_document(None, DOC, "new text") == "updated"
