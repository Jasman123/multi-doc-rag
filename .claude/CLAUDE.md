# multi-doc-rag

Multi-document RAG API: FastAPI backend (ports & adapters architecture), ChromaDB vector store
with hybrid (vector + BM25) retrieval, JWT auth backed by Postgres, and a plain HTML/JS frontend.

This project was originally developed inside a larger personal monorepo of independent
FastAPI/AI-agent projects; this repo is a history-preserving export of just this project
(via `git subtree split`), which is why some early commit subjects reference the parent repo's
naming (e.g. `project-3`) before it settled on `multi-doc-rag`.

## Working in this repo

- Backend has its own venv/deps — use `backend/venv/bin/python` (or recreate from
  `backend/requirements.txt`), not a global interpreter.
- `backend/.env` (see `backend/.env.example` for required keys: `OPENAI_API_KEY`,
  `DATABASE_URL`, `SECRET_KEY`, ...) holds live secrets — never commit it, never print its
  contents in full.
- Migrations are managed with Alembic (`backend/alembic/`); use the `Makefile` targets for
  run/test/reset-db where available.
- `docs/testing/PT_Maju_Bersama_Company_Profile.pdf` is a synthetic/fictitious company profile
  used only as an ingestion test fixture — it is not real client data.

## Commit convention

Conventional Commits: `type(scope): short description` (e.g. `feat(multi-doc-rag): ...`,
`fix(multi-doc-rag): ...`). Imperative mood, no trailing period.
