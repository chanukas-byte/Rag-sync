# Rag-sync

[![CI](https://github.com/chanukas-byte/Rag-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/chanukas-byte/Rag-sync/actions)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**A RAG knowledge base that stays in sync with Google Drive: edits and deletions reach the vector database in about a minute.**

Most RAG demos embed a folder once and go stale. `Rag-sync` is the data pipeline that keeps an AI assistant's knowledge current. When a document is created, edited or deleted, a Make automation triggers a Python service that hashes the content, re-chunks and re-embeds only what changed, and updates Postgres with pgvector in a single transaction, so stale chunks never linger.

> **Demo:** _add a GIF or Loom link here (edit a doc, watch the chat answer change)._

---

## Features

- **Change detection** via Make (new, edited, deleted files) plus a nightly reconciliation job as a safety net
- **Incremental loads**: content hashing skips unchanged documents, so no wasted embedding calls
- **Idempotent upserts**: deterministic chunk IDs (`doc_id:chunk_index`); replaying an event gives the same result
- **Stale chunk cleanup**: delete-then-insert in one transaction, so a shorter edited document leaves no old chunks
- **Delete handling**: removed documents lose all their vectors
- **Reliability**: retries with backoff, dead-letter table (`failed_events`), sync run history, `/health` endpoint
- **Evaluation**: retrieval metrics (hit rate@5, MRR) on a question set, with chunking experiments
- **Chat assistant** that answers only from retrieved context and cites sources

## Architecture

```
Google Drive
    │  new / edited / deleted
    ▼
Make scenario ──► POST /webhook/doc-event
                        │
                        ▼
                 FastAPI sync service
          fetch → hash → chunk → embed → upsert
                        │
                        ▼
             Postgres + pgvector
        (chunks, documents, failed_events, sync_runs)
                        ▲
                        │ top-k similarity search
                 Chat API (/chat)
```

_Replace this with a diagram image in `docs/architecture.png` (Excalidraw or Mermaid)._

## Tech stack

| Layer | Tool |
| --- | --- |
| Triggers | Make |
| API / pipeline | Python 3.12, FastAPI |
| Vector store + state | Postgres 16 + pgvector |
| Embeddings | OpenAI text-embedding-3-small (or bge/e5) |
| Retries | tenacity |
| Tests | pytest, GitHub Actions |
| Packaging | Docker Compose |

## Quick start

```bash
git clone https://github.com/chanukas-byte/Rag-sync.git
cd Rag-sync
cp .env.example .env        # add your API keys and Drive folder ID
make up                     # start Postgres + pgvector
make seed                   # ingest the sample folder
make run                    # start the API on http://localhost:8000
```

Ask a question:

```bash
curl -X POST localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund window?"}'
```

### Environment variables

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Postgres connection string |
| `EMBEDDING_API_KEY` | Key for the embedding provider |
| `LLM_API_KEY` | Key for the answering model |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to service account credentials |
| `DRIVE_FOLDER_ID` | Folder to watch |
| `WEBHOOK_SECRET` | Shared secret checked on webhook calls |

## How syncing works

1. Make detects a change and calls `POST /webhook/doc-event` with `{event, doc_id, source}`.
2. The service fetches the document and computes a SHA-256 hash of the normalized text.
3. If the hash matches the stored one, the event is skipped.
4. Otherwise the text is chunked (~500 tokens, 50 overlap) and embedded.
5. In one transaction: old chunks for the document are deleted, new chunks inserted, and the `documents` state row updated.
6. Deleted events remove the chunks and mark the document as deleted.
7. A nightly `sync_all()` compares the source with the state table to catch anything missed.

## Design decisions

- **Make is trigger-only.** All logic lives in versioned, tested code; Make only detects and forwards events.
- **Delete-then-insert in a transaction** instead of upsert alone, because an edited document can produce fewer chunks and upserts would leave stale tails.
- **Hash-based skipping** keeps embedding cost proportional to what changed, not to corpus size.
- **pgvector** keeps vectors and state in one database, which makes atomic updates simple. Qdrant would be the next step for larger scale or heavier filtering.

## Evaluation

Run `make eval` to score retrieval on `eval/questions.jsonl`.

| Config | Hit rate@5 | MRR |
| --- | --- | --- |
| 300 tokens, 0 overlap | _tbd_ | _tbd_ |
| 500 tokens, 50 overlap | _tbd_ | _tbd_ |
| 800 tokens, 50 overlap | _tbd_ | _tbd_ |
| 500 tokens + hybrid search | _tbd_ | _tbd_ |

## Project structure

```
Rag-sync/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
├── make/              # exported Make scenario blueprints (secrets removed)
├── docs/              # architecture diagram, ADRs
├── sql/               # schema and migrations
├── src/ragsync/
│   ├── api.py
│   ├── sources/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── store.py
│   ├── sync.py
│   └── chat.py
├── tests/
└── eval/
```

## Testing

```bash
make test     # unit + integration tests
make lint     # ruff
make eval     # retrieval evaluation
```

Key tests: unchanged documents are skipped, edited documents replace their chunks, shorter documents leave no stale chunks, deleted documents are fully removed, and replaying the same event three times changes nothing.

## Limitations and next steps

- Single source (Google Drive); Notion and Confluence connectors are planned.
- Background tasks run in-process; a real queue (Redis/RQ) would be the next upgrade.
- No per-user access control yet; chunk metadata is designed to support it.
- At larger scale: batch embedding, a managed vector database, and observability dashboards.

## License

MIT. See [LICENSE](LICENSE).
