.PHONY: help install run run-prod test test-unit test-integration reset-db clean db-up db-down migrate makemigrations

VENV_BIN         := .venv/bin
PYTHON           := $(VENV_BIN)/python
PYTEST           := $(VENV_BIN)/pytest
UVICORN          := $(VENV_BIN)/uvicorn
ALEMBIC          := $(VENV_BIN)/alembic
PORT             ?= 8010
CHROMA_PERSIST_DIR ?= ./storage/chroma

help:
	@echo "Targets:"
	@echo "  install          Install dependencies into .venv"
	@echo "  run              Run the API with auto-reload (dev). Override port: make run PORT=8020"
	@echo "  run-prod         Run the API as in the Dockerfile (no reload)"
	@echo "  test             Run the full test suite"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  reset-db         Wipe ChromaDB storage (deletes all ingested documents)"
	@echo "  clean            Remove caches (__pycache__, .pytest_cache)"
	@echo "  db-up            Start the local Postgres container (docker compose)"
	@echo "  db-down          Stop the local Postgres container"
	@echo "  migrate          Apply Alembic migrations (alembic upgrade head)"
	@echo "  makemigrations   Autogenerate a new Alembic revision: make makemigrations msg=\"...\""

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT) --reload

run-prod:
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT)

test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit

test-integration:
	$(PYTEST) tests/integration

reset-db:
	@echo "This will permanently delete all ingested documents in $(CHROMA_PERSIST_DIR)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Aborted."; exit 1)
	rm -rf $(CHROMA_PERSIST_DIR)
	mkdir -p $(CHROMA_PERSIST_DIR)
	@echo "ChromaDB storage reset."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	$(ALEMBIC) upgrade head

makemigrations:
	$(ALEMBIC) revision --autogenerate -m "$(msg)"
