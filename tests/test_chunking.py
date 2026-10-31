import pytest

from ragsync.chunking import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_one_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_long_text_is_split_with_overlap():
    text = " ".join(f"w{i}" for i in range(200))
    chunks = chunk_text(text, max_words=50, overlap=10)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 60 for c in chunks)
    assert chunks[0].split()[-10:] == chunks[1].split()[:10]


def test_no_words_are_lost():
    text = " ".join(f"w{i}" for i in range(200))
    chunks = chunk_text(text, max_words=50, overlap=10)
    assert set(" ".join(chunks).split()) == set(text.split())


def test_overlap_must_be_smaller_than_max():
    with pytest.raises(ValueError):
        chunk_text("a b c", max_words=5, overlap=5)
