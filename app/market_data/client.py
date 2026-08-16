"""Small Alpha Vantage HTTP client; provider JSON stays inside this module."""

import os
from typing import Any

from dotenv import load_dotenv
import httpx


class MarketDataError(Exception):
    """Base error for market-data requests."""


class InvalidTickerError(MarketDataError):
    """Raised when the provider does not recognise a ticker."""


class RateLimitError(MarketDataError):
    """Raised when the provider reports an API quota limit."""


class AlphaVantageClient:
    """Request the two Alpha Vantage endpoints needed in Phase 3."""

    base_url = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("FINANCE_API_KEY")
        if not self.api_key:
            raise MarketDataError("Set ALPHA_VANTAGE_API_KEY in .env before requesting market data.")
        self.timeout_seconds = timeout_seconds

    def _request(self, function: str, ticker: str) -> dict[str, Any]:
        try:
            response = httpx.get(
                self.base_url,
                params={"function": function, "symbol": ticker, "apikey": self.api_key},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise MarketDataError("The market-data request timed out.") from error
        except httpx.RequestError as error:
            raise MarketDataError("Unable to reach the market-data provider.") from error
        except httpx.HTTPStatusError as error:
            raise MarketDataError(f"Market-data provider returned HTTP {error.response.status_code}.") from error

        data = response.json()
        if "Note" in data:
            raise RateLimitError("Alpha Vantage rate limit reached. Please wait and try again.")
        if "Information" in data:
            raise MarketDataError(f"Alpha Vantage response: {data['Information']}")
        if "Error Message" in data:
            raise InvalidTickerError(f"Unknown ticker: {ticker.upper()}")
        return data

    def get_quote(self, ticker: str) -> dict[str, Any]:
        """Return the provider's quote payload for one ticker."""
        return self._request("GLOBAL_QUOTE", ticker)

    def get_overview(self, ticker: str) -> dict[str, Any]:
        """Return the provider's company-overview payload for one ticker."""
        return self._request("OVERVIEW", ticker)
