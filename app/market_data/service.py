"""Provider-independent market-data service functions."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import time

from app.market_data.client import AlphaVantageClient, InvalidTickerError


@dataclass(frozen=True)
class MarketData:
    """The stable market-data shape used by the rest of this project."""

    ticker: str
    current_price: Decimal | None
    market_cap: Decimal | None
    pe_ratio: Decimal | None
    week_52_high: Decimal | None
    week_52_low: Decimal | None
    price_change: Decimal | None
    price_change_percent: Decimal | None
    volume: int | None


def _decimal(value: str | None) -> Decimal | None:
    if not value or value in {"None", "-"}:
        return None
    try:
        return Decimal(value.replace("%", ""))
    except (AttributeError, InvalidOperation):
        return None


def get_market_data(ticker: str, client: AlphaVantageClient | None = None) -> MarketData:
    """Fetch and normalize current/recent market information for one ticker."""
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise InvalidTickerError("Ticker cannot be empty.")

    provider = client or AlphaVantageClient()
    quote = provider.get_quote(normalized_ticker).get("Global Quote", {})
    if not quote.get("01. symbol"):
        raise InvalidTickerError(f"Unknown ticker: {normalized_ticker}")
    # Alpha Vantage's free tier permits only one request per second.
    time.sleep(1.1)
    overview = provider.get_overview(normalized_ticker)
    return MarketData(
        ticker=quote["01. symbol"].upper(),
        current_price=_decimal(quote.get("05. price")),
        market_cap=_decimal(overview.get("MarketCapitalization")),
        pe_ratio=_decimal(overview.get("PERatio")),
        week_52_high=_decimal(overview.get("52WeekHigh")),
        week_52_low=_decimal(overview.get("52WeekLow")),
        price_change=_decimal(quote.get("09. change")),
        price_change_percent=_decimal(quote.get("10. change percent")),
        volume=int(quote["06. volume"]) if quote.get("06. volume") else None,
    )


def get_market_data_for_companies(tickers: list[str]) -> list[MarketData]:
    """Fetch normalized market data for each ticker in order."""
    client = AlphaVantageClient()
    return [get_market_data(ticker, client) for ticker in tickers]
