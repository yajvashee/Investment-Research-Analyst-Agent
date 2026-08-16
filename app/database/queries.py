"""Reusable queries for historical company financials."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.database.models import HistoricalFinancial


def get_company_financials(ticker: str, session: Session | None = None) -> list[HistoricalFinancial]:
    """Return all available years for a ticker, or an empty list if it is unknown."""
    normalized_ticker = ticker.strip().upper()
    statement = (
        select(HistoricalFinancial)
        .where(HistoricalFinancial.ticker == normalized_ticker)
        .order_by(HistoricalFinancial.fiscal_year)
    )
    if session is not None:
        return list(session.scalars(statement))

    with get_session() as database_session:
        return list(database_session.scalars(statement))


def compare_company_financials(
    tickers: list[str], session: Session | None = None
) -> dict[str, list[HistoricalFinancial]]:
    """Return the available financial history for each requested ticker."""
    normalized_tickers = [ticker.strip().upper() for ticker in tickers]
    if session is not None:
        return {ticker: get_company_financials(ticker, session) for ticker in normalized_tickers}

    with get_session() as database_session:
        return {
            ticker: get_company_financials(ticker, database_session)
            for ticker in normalized_tickers
        }
