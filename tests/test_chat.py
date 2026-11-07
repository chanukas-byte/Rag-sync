from ragsync import chat


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": "3 retries"}}


def test_build_prompt_contains_context_and_question():
    chunks = [{"title": "Doc A", "url": "u", "content": "Retries are 3."}]
    prompt = chat.build_prompt("How many retries?", chunks)
    assert "Retries are 3." in prompt
    assert "How many retries?" in prompt
    assert "Doc A" in prompt


def test_answer_returns_text_and_unique_sources(monkeypatch):
    chunks = [
        {"title": "Doc A", "url": "u1", "content": "x"},
        {"title": "Doc A", "url": "u1", "content": "y"},
    ]
    monkeypatch.setattr(chat, "search", lambda question, k=5: chunks)
    monkeypatch.setattr(chat.httpx, "post", lambda *args, **kwargs: FakeResponse())

    result = chat.answer("How many retries?")

    assert result["answer"] == "3 retries"
    assert result["sources"] == [{"title": "Doc A", "url": "u1"}]
