"""Small, idempotent sample dataset for Phase 2 database checks."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import create_database_tables, get_session
from app.database.models import HistoricalFinancial


SAMPLE_FINANCIALS = (
    {"company_name": "Microsoft", "ticker": "MSFT", "fiscal_year": 2023, "revenue": "211915", "net_income": "72361", "total_assets": "411976", "total_liabilities": "205753", "total_debt": "47805", "cash_and_equivalents": "111256", "shareholders_equity": "206223", "eps": "9.68"},
    {"company_name": "Microsoft", "ticker": "MSFT", "fiscal_year": 2024, "revenue": "245122", "net_income": "88308", "total_assets": "512163", "total_liabilities": "243686", "total_debt": "45390", "cash_and_equivalents": "75531", "shareholders_equity": "268477", "eps": "11.80"},
    {"company_name": "Apple", "ticker": "AAPL", "fiscal_year": 2023, "revenue": "383285", "net_income": "96995", "total_assets": "352583", "total_liabilities": "290437", "total_debt": "111088", "cash_and_equivalents": "61555", "shareholders_equity": "62146", "eps": "6.16"},
    {"company_name": "Apple", "ticker": "AAPL", "fiscal_year": 2024, "revenue": "391035", "net_income": "93736", "total_assets": "364980", "total_liabilities": "308030", "total_debt": "119058", "cash_and_equivalents": "29943", "shareholders_equity": "56950", "eps": "6.08"},
)


def seed_sample_data(session: Session | None = None) -> int:
    """Insert sample records once and return the number added."""
    create_database_tables()
    if session is None:
        with get_session() as database_session:
            return seed_sample_data(database_session)

    inserted_count = 0
    for record in SAMPLE_FINANCIALS:
        exists = session.scalar(
            select(HistoricalFinancial.id).where(
                HistoricalFinancial.ticker == record["ticker"],
                HistoricalFinancial.fiscal_year == record["fiscal_year"],
            )
        )
        if exists is None:
            financials = {key: Decimal(value) if key not in {"company_name", "ticker", "fiscal_year"} else value for key, value in record.items()}
            session.add(HistoricalFinancial(**financials))
            inserted_count += 1
    session.commit()
    return inserted_count
