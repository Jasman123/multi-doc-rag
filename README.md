# multi-doc-rag

A multi-document RAG (Retrieval-Augmented Generation) API. Upload PDFs, ask
questions across them, and get answers grounded in cited source chunks.

- **Backend**: FastAPI, built with a ports & adapters (hexagonal) architecture
- **Retrieval**: ChromaDB (vector) + BM25 (keyword) hybrid search, fused with
  reciprocal rank fusion, orchestrated as a corrective RAG pipeline in LangGraph
- **Auth**: JWT (access + refresh tokens), user store in Postgres
- **Frontend**: plain HTML/JS (no build step)

## Architecture

The backend core (`app/services`, `app/retriever`) depends only on the
abstract ports in `app/ports` (`EmbedderPort`, `LLMPort`), not on any concrete
SDK. Concrete implementations live in `app/adapters` (currently OpenAI for
both embeddings and chat) and are wired up via FastAPI dependencies in
`app/api/dependencies.py`. Swapping providers means writing a new adapter,
not touching the core logic.

Retrieval is a small [LangGraph](https://github.com/langchain-ai/langgraph)
state machine (`app/services/rag_graph/`) rather than a single linear
pipeline:

```
precheck -> analyze_query -> retrieve -> grade_documents -> generate
                                 ^              |
                                 +-- rewrite_query (if graded "insufficient")
```

It fetches candidates via hybrid vector+BM25 search, grades whether they
sufficiently answer the question, and rewrites the query and retries
(bounded by `RAG_MAX_RETRIES`) before falling back to a "no results" response
or generating a cited answer.

## Repo layout

```
backend/
  app/
    adapters/       concrete EmbedderPort / LLMPort implementations (OpenAI)
    api/routes/      auth, ingest, query endpoints
    core/            settings, DB session, ChromaDB client, security, logging
    db/              user repository (Postgres/SQLAlchemy)
    models/          ORM models
    ports/           abstract interfaces the core depends on
    retriever/       hybrid vector + BM25 retrieval, RRF fusion
    schemas/         Pydantic request/response models
    services/        ingestion, auth, and the RAG LangGraph pipeline
    utils/           PDF parsing, chunking
  alembic/           DB migrations
  tests/             unit + integration tests (pytest)
  Dockerfile, docker-compose.yml, Makefile
frontend/
  index.html         document upload + chat UI
  login.html          login/register UI
railway.toml          Railway deploy config
```

## Getting started

Prerequisites: Python 3.11, Docker (for local Postgres).

```bash
cd backend
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env   # then fill in OPENAI_API_KEY and SECRET_KEY

make db-up             # starts local Postgres via docker compose
make migrate           # alembic upgrade head
make run               # uvicorn with --reload on :8010
```

The frontend is served by the backend itself (mounted as static files), so
once the server is running, open `http://localhost:8010/` for the upload/chat
UI and `http://localhost:8010/login.html` to register/log in. API docs are at
`/docs`.

See `backend/.env.example` for all configuration options (chunking, top-k
retrieval sizes, retry/grading thresholds, JWT settings, etc.).

## Testing

```bash
cd backend
make test              # full suite
make test-unit         # unit tests only
make test-integration  # integration tests only
```

## Deployment

`railway.toml` + `backend/Dockerfile` deploy the app to Railway: migrations
run once per deploy via `preDeployCommand`, then the container starts
`uvicorn` directly. The Dockerfile build context is the repo root so both
`backend/` and `frontend/` are available to `COPY`.

## Notes

- This repo was split out of a larger personal monorepo of independent
  FastAPI/AI-agent projects via `git subtree split`, which is why some early
  commit subjects reference the parent repo's naming (e.g. `project-3`)
  before it settled on `multi-doc-rag`.
- `docs/testing/PT_Maju_Bersama_Company_Profile.pdf` (gitignored) is a
  synthetic/fictitious company profile used only as an ingestion test
  fixture — not real client data.
