import hashlib
import os
from pathlib import Path

import psycopg
import pytest

from ragsync import chat, embeddings, store, sync
from ragsync.sources import hybrid

TEST_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="TEST_DATABASE_URL not set")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def fake_vector(text, dim=768):
    digest = hashlib.sha256(text.encode()).digest()
    return [digest[i % len(digest)] / 255 + 0.01 for i in range(dim)]


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def make_fake_post(dim=768):
    def fake_post(url, **kwargs):
        texts = kwargs["json"]["input"]
        return FakeResponse({"embeddings": [fake_vector(t, dim) for t in texts]})

    return fake_post


@pytest.fixture(scope="module")
def schema():
    assert "test" in TEST_URL.rsplit("/", 1)[-1], "refusing to run on a non-test database"
    with psycopg.connect(TEST_URL, autocommit=True) as admin:
        admin.execute("DROP SCHEMA public CASCADE")
        admin.execute("CREATE SCHEMA public")
        for path in sorted(SQL_DIR.glob("*.sql")):
            admin.execute(path.read_text())


@pytest.fixture
def conn(schema, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    monkeypatch.setattr(embeddings.httpx, "post", make_fake_post())
    with psycopg.connect(TEST_URL, autocommit=True) as admin:
        admin.execute("TRUNCATE chunks, documents, sync_runs, failed_events")
    connection = store.get_connection()
    assert "test" in connection.info.dbname, "get_connection() is not using the test database"
    yield connection
    connection.close()


def doc(doc_id="doc-1", title="Doc One.txt"):
    return {
        "id": doc_id,
        "title": title,
        "url": "http://example.com/doc-1",
        "modified_time": "2026-01-01T00:00:00Z",
    }


def chunk_count(conn, doc_id="doc-1"):
    return conn.execute("SELECT count(*) FROM chunks WHERE doc_id = %s", (doc_id,)).fetchone()[0]


def count_containing(conn, word):
    return conn.execute(
        "SELECT count(*) FROM chunks WHERE content LIKE %s", (f"%{word}%",)
    ).fetchone()[0]


def doc_status(conn, doc_id="doc-1"):
    return conn.execute("SELECT status FROM documents WHERE doc_id = %s", (doc_id,)).fetchone()[0]


def long_text(word, paragraphs=8):
    return "\n\n".join(f"Paragraph {i} " + f"{word} " * 60 for i in range(paragraphs))


def test_first_sync_adds_document(conn):
    assert sync.sync_document(conn, doc(), long_text("alpha")) == "added"
    assert chunk_count(conn) > 1
    assert doc_status(conn) == "active"


def test_second_sync_is_unchanged(conn):
    sync.sync_document(conn, doc(), long_text("alpha"))
    before = chunk_count(conn)

    assert sync.sync_document(conn, doc(), long_text("alpha")) == "unchanged"
    assert chunk_count(conn) == before


def test_changed_text_leaves_no_stale_chunks(conn):
    sync.sync_document(conn, doc(), long_text("alpha"))
    assert chunk_count(conn) > 1

    result = sync.sync_document(conn, doc(), "A short replacement note about beta.")

    assert result == "updated"
    assert chunk_count(conn) == 1
    assert count_containing(conn, "alpha") == 0


def test_mark_deleted_removes_chunks(conn):
    sync.sync_document(conn, doc(), long_text("alpha"))

    store.mark_deleted(conn, "doc-1")

    assert chunk_count(conn) == 0
    assert doc_status(conn) == "deleted"


def test_failed_update_rolls_back(conn, monkeypatch):
    sync.sync_document(conn, doc(), long_text("alpha"))
    before = chunk_count(conn)

    monkeypatch.setattr(embeddings.httpx, "post", make_fake_post(dim=3))
    with pytest.raises(psycopg.Error):
        sync.sync_document(conn, doc(), long_text("beta"))

    assert chunk_count(conn) == before
    assert count_containing(conn, "alpha") == before


def test_vector_and_keyword_search_run_on_real_sql(conn):
    sync.sync_document(conn, doc(), "The on-call rota changes over on Monday at 09:00.")
    conn.commit()

    vector_hits = chat.retrieve("who is on call?", 5)
    keyword_hits = hybrid.keyword_search("When does the rota change over?")

    assert [c["title"] for c in vector_hits] == ["Doc One.txt"]
    assert [c["title"] for c in keyword_hits] == ["Doc One.txt"]
