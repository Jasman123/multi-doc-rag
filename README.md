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
SDK. Concrete implementations live in `app/adapters`: a single
`OpenAICompatibleLLMAdapter` and `OpenAICompatibleEmbedderAdapter`, each built
on `openai.AsyncOpenAI(api_key, base_url)`. Because OpenAI, Google Gemini (via
its OpenAI-compatibility endpoint), and most local runtimes (Ollama, vLLM,
LM Studio, ...) all speak the same wire protocol, one adapter per port covers
all of them — swapping providers is a config change (base URL, key, model),
not a new adapter class.

Provider configuration (label, base URL, model, API key) is stored in
Postgres, one active row per role (`llm` / `embedder`), and is managed at
runtime by an admin through `/admin.html` rather than via `.env` — see
"Getting started" below. The stored API key is encrypted at rest
(`app/core/crypto.py`, Fernet) using a root key (`ENCRYPTION_KEY`) that *does*
still come from `.env` — that's the one secret that has to, since it's what
protects the ones stored in the database.

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
    adapters/       concrete EmbedderPort / LLMPort implementations (OpenAI-compatible, any provider)
    api/routes/      auth, ingest, query, admin (provider config) endpoints
    core/            settings, DB session, ChromaDB client, security, logging, crypto (Fernet)
    db/              user + provider_config repositories (Postgres/SQLAlchemy)
    models/          ORM models (User, ProviderConfig)
    ports/           abstract interfaces the core depends on
    retriever/       hybrid vector + BM25 retrieval, RRF fusion
    schemas/         Pydantic request/response models
    services/        ingestion, auth, admin (provider config), and the RAG LangGraph pipeline
    utils/           PDF parsing, chunking
  alembic/           DB migrations
  tests/             unit + integration tests (pytest)
  Dockerfile, docker-compose.yml, Makefile
frontend/
  index.html         document upload + chat UI
  login.html          login/register UI
  admin.html         admin-only LLM/embedder provider configuration
railway.toml          Railway deploy config
```

## Getting started

Prerequisites: Python 3.11, Docker (for local Postgres).

```bash
cd backend
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env   # then fill in SECRET_KEY and ENCRYPTION_KEY
                        # (generate ENCRYPTION_KEY with:
                        #  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

make db-up             # starts local Postgres via docker compose
make migrate           # alembic upgrade head
make run               # uvicorn with --reload on :8010
```

The frontend is served by the backend itself (mounted as static files), so
once the server is running, open `http://localhost:8010/` for the upload/chat
UI and `http://localhost:8010/login.html` to register/log in. API docs are at
`/docs`.

**No provider API keys go in `.env`.** After registering the first user,
promote it to `admin` directly in Postgres (`UPDATE users SET role = 'admin'
WHERE email = '...'`), log back in, and open `http://localhost:8010/admin.html`
to configure the LLM and embedder providers — see "Configuring providers"
below for exactly what to put in each field.

See `backend/.env.example` for all remaining configuration options (chunking,
top-k retrieval sizes, retry/grading thresholds, JWT settings, etc.).

### Configuring providers (admin)

`/admin.html` has two independent cards — **LLM Provider** (chat/completion)
and **Embedder Provider** (used at both ingest and query time) — each backed
by its own row in Postgres. `/api/v1/query` and `/api/v1/ingest` return `503`
until both cards have been saved at least once.

**Important**: the two cards don't share a key. If you point a card's Base
URL at a real endpoint (OpenAI, Gemini) but leave its API key unset, that
card's requests use a placeholder key and the provider rejects them with a
`401`. Setting a key on the LLM card does not carry over to the Embedder
card, and vice versa — set both if both point at a real (non-local) endpoint.

| Field | OpenAI | Gemini (OpenAI-compat) | Local (Ollama, vLLM, LM Studio, ...) |
|---|---|---|---|
| Provider label | `openai` | `gemini` | `ollama` |
| Base URL | *(leave empty — defaults to OpenAI)* | `https://generativelanguage.googleapis.com/v1beta/openai/` | `http://localhost:11434/v1` |
| Model name (LLM card) | `gpt-4o-mini` | `gemini-2.5-flash` | e.g. `llama3.1` |
| Model name (Embedder card) | `text-embedding-3-small` | `gemini-embedding-001` | e.g. `nomic-embed-text` |
| API key | your real OpenAI key | your real Gemini key | leave unset — most local runtimes ignore it |

To switch providers later, just edit the fields on either card and save —
no redeploy, no `.env` change, no new adapter code. This is the core point of
the unified `OpenAICompatibleLLMAdapter`/`OpenAICompatibleEmbedderAdapter`:
every provider above is served by the exact same adapter class, only the
config differs.

The **API key** control has three states, not two:
- Leave the field collapsed → key is left untouched on save.
- Click **"Set / replace key"**, type a new value → replaces the stored key.
- Click **"Set / replace key"**, check **"Clear stored key"**, leave the field
  blank → removes the stored key (use this when switching a card to a
  keyless local runtime).

The key status shown (**"Key configured"** / **"No key set"**) only ever
reflects *whether* a key is stored — the UI never displays or re-fetches the
key itself, since it's encrypted at rest and the backend has no endpoint that
returns it in plaintext.

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
