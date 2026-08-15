# Investment Research Analyst Agent

This project will become a single-agent tool for investment research. It is being built one phase at a time so that each layer can be understood and tested independently.

## Phase 1 status

The Python project foundation is ready. It includes importable placeholder packages, logging, a health check, and a test. It does not yet contain a database, RAG pipeline, finance API, agent, backend, or frontend functionality.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup and checks

```powershell
uv sync
uv run python scripts/health_check.py
uv run pytest
```

Copy `.env.example` to `.env` when a later phase needs credentials. Keep real secrets only in `.env`.
