import hmac
import os
from typing import Literal

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from ragsync import chat, sync
from ragsync.embeddings import OLLAMA_URL
from ragsync.store import get_connection

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


@app.get("/ready")
def ready():
    checks = {}
    last_sync = "never"
    try:
        conn = get_connection()
        try:
            conn.execute("SELECT 1")
            row = conn.execute("SELECT status FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                last_sync = row[0]
        finally:
            conn.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
    try:
        httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3).raise_for_status()
        checks["ollama"] = "ok"
    except Exception as exc:
        checks["ollama"] = f"error: {type(exc).__name__}"
    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "degraded", **checks, "last_sync": last_sync},
    )


@app.post("/chat")
def chat_endpoint(request: ChatRequest) -> dict:
    return chat.answer(request.question)


class DocEvent(BaseModel):
    event: Literal["created", "updated", "deleted"]
    doc_id: str = Field(min_length=1)


@app.post("/webhook/doc-event", status_code=202)
def doc_event(
    event: DocEvent,
    background: BackgroundTasks,
    x_webhook_secret: str | None = Header(default=None),
) -> dict:
    expected = os.environ.get("WEBHOOK_SECRET", "")
    if not expected or not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, expected):
        raise HTTPException(status_code=401, detail="invalid secret")
    background.add_task(sync.handle_event, event.event, event.doc_id)
    return {"status": "accepted"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE
