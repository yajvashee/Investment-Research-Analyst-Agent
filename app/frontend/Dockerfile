FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY app ./app

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app/frontend/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
