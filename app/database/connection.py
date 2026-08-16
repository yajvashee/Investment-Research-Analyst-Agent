"""SQLAlchemy connection helpers for the local PostgreSQL database."""

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


load_dotenv()


def get_database_url() -> str:
    """Build the PostgreSQL URL from environment variables."""
    if database_url := os.getenv("DATABASE_URL"):
        return database_url

    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD is required. Copy .env.example to .env first.")

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "investment_agent")
    user = os.getenv("POSTGRES_USER", "postgres")
    return f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"


@lru_cache
def get_engine() -> Engine:
    """Return one reusable SQLAlchemy engine for the application process."""
    return create_engine(get_database_url(), pool_pre_ping=True)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a database session and always close it afterwards."""
    session_factory = sessionmaker(bind=get_engine())
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def create_database_tables() -> None:
    """Create the Phase 2 tables if they do not already exist."""
    from app.database.models import Base

    Base.metadata.create_all(bind=get_engine())
