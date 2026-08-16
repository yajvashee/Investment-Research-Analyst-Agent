"""SQLAlchemy models for structured historical financial data."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class shared by all database models."""


class HistoricalFinancial(Base):
    """One company's reported financial figures for one fiscal year."""

    __tablename__ = "historical_financials"
    __table_args__ = (UniqueConstraint("ticker", "fiscal_year", name="uq_ticker_fiscal_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_debt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_and_equivalents: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    shareholders_equity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    eps: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def to_dict(self) -> dict[str, int | str | Decimal | datetime]:
        """Return a simple representation for later application layers."""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "revenue": self.revenue,
            "net_income": self.net_income,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_debt": self.total_debt,
            "cash_and_equivalents": self.cash_and_equivalents,
            "shareholders_equity": self.shareholders_equity,
            "eps": self.eps,
            "created_at": self.created_at,
        }
