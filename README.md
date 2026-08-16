# Investment Research Analyst Agent

This project will become a single-agent tool for investment research. It is being built one phase at a time so that each layer can be understood and tested independently.

## Current status

The Python project foundation is ready. Phase 2 adds PostgreSQL historical financials: PostgreSQL runs in Docker while the Python application still runs locally on Windows. It does not yet contain RAG, a finance API, an agent, backend, or frontend functionality.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup and checks

```powershell
uv sync
uv run python scripts/health_check.py
uv run pytest
```

## PostgreSQL for Phase 2

Copy `.env.example` to `.env`, then choose a strong `POSTGRES_PASSWORD`.

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
uv run python scripts/initialize_database.py
uv run pytest
```

Stop PostgreSQL without deleting its data:

```powershell
docker compose down
```

Copy `.env.example` to `.env` when a later phase needs credentials. Keep real secrets only in `.env`.
