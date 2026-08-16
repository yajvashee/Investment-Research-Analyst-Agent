"""Import selected annual historical financials from SimFin ZIP datasets."""

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import HistoricalFinancial


TARGET_COMPANIES = {
    "MSFT": "Microsoft",
    "AAPL": "Apple",
    "KO": "Coca-Cola",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "NVDA": "Nvidia",
    "TSLA": "Tesla",
    "AMD": "AMD",
}
TARGET_YEARS = {2021, 2022, 2023, 2024}
SIMFIN_TICKER_ALIASES = {"GOOG": "GOOGL"}
MILLION = Decimal("1000000")


@dataclass(frozen=True)
class ImportResult:
    """Counts returned after a SimFin import."""

    inserted: int
    updated: int
    skipped: int


def _read_dataset(zip_path: Path) -> dict[tuple[str, int], dict[str, str]]:
    """Read one semicolon-separated SimFin CSV from a ZIP archive."""
    with ZipFile(zip_path) as archive:
        csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
        with archive.open(csv_name) as file:
            rows = csv.DictReader((line.decode("utf-8") for line in file), delimiter=";")
            return {
                (SIMFIN_TICKER_ALIASES.get(row["Ticker"], row["Ticker"]), int(row["Fiscal Year"])): row
                for row in rows
                if SIMFIN_TICKER_ALIASES.get(row["Ticker"], row["Ticker"]) in TARGET_COMPANIES
                and int(row["Fiscal Year"]) in TARGET_YEARS
                # Income and cash-flow files use FY; balance sheets use the year-end Q4 snapshot.
                and row["Fiscal Period"] in {"FY", "Q4"}
            }


def _millions(value: str, default_zero: bool = False) -> Decimal:
    """Convert SimFin's full currency units into USD millions."""
    if default_zero and not value:
        return Decimal("0")
    return Decimal(value) / MILLION


def import_simfin_annual_data(data_directory: Path, session: Session) -> ImportResult:
    """Load the chosen nine companies and four annual periods into PostgreSQL."""
    income = _read_dataset(data_directory / "us-income-annual.zip")
    balance = _read_dataset(data_directory / "us-balance-annual.zip")
    cashflow = _read_dataset(data_directory / "us-cashflow-annual.zip")
    inserted = updated = skipped = 0

    for key in sorted(set(income) & set(balance) & set(cashflow)):
        income_row, balance_row, cashflow_row = income[key], balance[key], cashflow[key]
        ticker, fiscal_year = key
        try:
            net_income = _millions(income_row["Net Income"])
            diluted_shares = Decimal(income_row["Shares (Diluted)"])
            values = {
                "company_name": TARGET_COMPANIES[ticker],
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "revenue": _millions(income_row["Revenue"]),
                "net_income": net_income,
                "total_assets": _millions(balance_row["Total Assets"]),
                "total_liabilities": _millions(balance_row["Total Liabilities"]),
                "total_debt": _millions(balance_row["Short Term Debt"], default_zero=True)
                + _millions(balance_row["Long Term Debt"], default_zero=True),
                "cash_and_equivalents": _millions(balance_row["Cash, Cash Equivalents & Short Term Investments"]),
                "shareholders_equity": _millions(balance_row["Total Equity"]),
                "eps": net_income * MILLION / diluted_shares,
            }
        except (ArithmeticError, KeyError, ValueError):
            skipped += 1
            continue

        existing = session.scalar(
            select(HistoricalFinancial).where(
                HistoricalFinancial.ticker == ticker,
                HistoricalFinancial.fiscal_year == fiscal_year,
            )
        )
        if existing is None:
            session.add(HistoricalFinancial(**values))
            inserted += 1
        else:
            for field, value in values.items():
                setattr(existing, field, value)
            updated += 1

    session.commit()
    return ImportResult(inserted=inserted, updated=updated, skipped=skipped)
