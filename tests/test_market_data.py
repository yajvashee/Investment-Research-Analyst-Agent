"""Mocked tests for market-data normalization."""

from decimal import Decimal

import pytest

from app.market_data.client import InvalidTickerError
from app.market_data.service import get_market_data


class FakeClient:
    def get_quote(self, ticker: str) -> dict:
        return {"Global Quote": {"01. symbol": ticker, "05. price": "100.50", "06. volume": "12345", "09. change": "1.25", "10. change percent": "1.26%"}}

    def get_overview(self, ticker: str) -> dict:
        return {"MarketCapitalization": "1000000000", "PERatio": "20.1", "52WeekHigh": "120", "52WeekLow": "80"}


def test_market_data_is_normalized() -> None:
    data = get_market_data("msft", FakeClient())

    assert data.ticker == "MSFT"
    assert data.current_price == Decimal("100.50")
    assert data.price_change_percent == Decimal("1.26")
    assert data.volume == 12345


def test_empty_ticker_fails_safely() -> None:
    with pytest.raises(InvalidTickerError):
        get_market_data(" ", FakeClient())
