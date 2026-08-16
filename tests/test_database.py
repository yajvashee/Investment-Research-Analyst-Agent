"""Integration tests for the PostgreSQL historical-financials layer."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database.connection import create_database_tables, get_engine, get_session
from app.database.queries import get_company_financials
from app.database.seed import seed_sample_data


@pytest.fixture(scope="module")
def database_is_ready() -> None:
    """Prepare the Docker PostgreSQL database, or skip if it is not running."""
    try:
        create_database_tables()
        seed_sample_data()
    except (OperationalError, RuntimeError) as error:
        pytest.skip(f"PostgreSQL is not available: {error}")


def test_database_connection(database_is_ready: None) -> None:
    with get_engine().connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1


def test_get_company_financials_for_valid_ticker(database_is_ready: None) -> None:
    with get_session() as session:
        financials = get_company_financials("msft", session)

    assert len(financials) >= 2
    assert financials[0].ticker == "MSFT"


def test_get_company_financials_for_invalid_ticker(database_is_ready: None) -> None:
    with get_session() as session:
        financials = get_company_financials("NOT_A_TICKER", session)

    assert financials == []
