from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ragsync import chat

app = FastAPI(title="rag-sync")

PAGE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>rag-sync</title>
  <style>
    body {
      font-family: system-ui, sans-serif;
      max-width: 720px;
      margin: 40px auto;
      padding: 0 16px;
    }
    input { width: 78%; padding: 8px; font-size: 16px; }
    button { padding: 8px 14px; font-size: 16px; }
    #out { margin-top: 24px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>rag-sync</h1>
  <form id="form">
    <input id="q" placeholder="Ask a question about your documents" required>
    <button type="submit">Ask</button>
  </form>
  <div id="out"></div>
  <h3>Sources</h3>
  <ul id="sources"></ul>
  <script>
    const form = document.getElementById("form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const out = document.getElementById("out");
      out.textContent = "Thinking...";
      const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: document.getElementById("q").value}),
      });
      if (!res.ok) {
        out.textContent = "Error " + res.status;
        return;
      }
      const data = await res.json();
      out.textContent = data.answer;
      const list = document.getElementById("sources");
      list.replaceChildren();
      for (const s of data.sources) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = s.url;
        a.textContent = s.title;
        a.target = "_blank";
        li.appendChild(a);
        list.appendChild(li);
      }
    });
  </script>
</body>
</html>
"""


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest) -> dict:
    return chat.answer(request.question)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE
