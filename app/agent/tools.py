"""Thin, agent-compatible wrappers around the completed data-source services."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from langchain_core.documents import Document
from langchain_core.tools import StructuredTool

from app.database.queries import compare_company_financials
from app.market_data.client import MarketDataError
from app.market_data.service import get_market_data_for_companies
from app.rag.retriever import search_company_documents


def _normalise_tickers(tickers: str | list[str]) -> list[str]:
    values = [tickers] if isinstance(tickers, str) else tickers
    if not values or not all(isinstance(ticker, str) and ticker.strip().isalpha() for ticker in values):
        raise ValueError("Provide one or more alphabetic ticker symbols, for example MSFT.")
    return [ticker.strip().upper() for ticker in values]


def _json_value(value: Any) -> Any:
    if isinstance(value, (Decimal, datetime, date)):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


def get_historical_financials(tickers: str | list[str]) -> dict[str, Any]:
    """Get all available historical financial records for one or more tickers."""
    try:
        normalised = _normalise_tickers(tickers)
    except ValueError as error:
        return {"status": "error", "financials": {}, "error": str(error)}

    results = compare_company_financials(normalised)
    financials = {
        ticker: [_json_value(record.to_dict()) for record in records]
        for ticker, records in results.items()
    }
    missing = [ticker for ticker, records in financials.items() if not records]
    return {"status": "success", "financials": financials, "missing_tickers": missing}


def get_current_market_data(tickers: str | list[str]) -> dict[str, Any]:
    """Get normalized current or recent market data for one or more tickers."""
    try:
        normalised = _normalise_tickers(tickers)
        records = get_market_data_for_companies(normalised)
    except (ValueError, MarketDataError) as error:
        return {"status": "error", "market_data": [], "error": str(error)}
    return {
        "status": "success",
        "market_data": [_json_value(asdict(record) if is_dataclass(record) else record) for record in records],
    }


def _citation(document: Document) -> dict[str, Any]:
    fields = ("company_name", "ticker", "document_name", "document_type", "fiscal_year", "page_number", "section", "source")
    return {field: document.metadata.get(field) for field in fields}


def search_financial_documents(ticker: str, query: str, k: int = 5) -> dict[str, Any]:
    """Search a company's indexed reports and official news, returning text and citations."""
    if not isinstance(ticker, str) or not ticker.strip().isalpha():
        return {"status": "error", "results": [], "error": "Provide an alphabetic ticker symbol, for example MSFT."}
    if not isinstance(query, str) or not query.strip():
        return {"status": "error", "results": [], "error": "Query cannot be empty."}
    if not isinstance(k, int) or not 1 <= k <= 10:
        return {"status": "error", "results": [], "error": "k must be an integer from 1 to 10."}
    try:
        documents = search_company_documents(ticker.strip().upper(), query.strip(), k)
    except RuntimeError as error:
        return {"status": "error", "results": [], "error": str(error)}
    return {
        "status": "success",
        "ticker": ticker.strip().upper(),
        "query": query.strip(),
        "results": [{"text": document.page_content, "citation": _citation(document)} for document in documents],
    }


historical_financials_tool = StructuredTool.from_function(
    func=get_historical_financials,
    name="get_historical_financials",
    description="Use for historical, structured company financials such as revenue, EPS, debt, cash, and annual trends.",
)
current_market_data_tool = StructuredTool.from_function(
    func=get_current_market_data,
    name="get_current_market_data",
    description="Use for current or recent market figures such as price, valuation, 52-week range, and volume.",
)
financial_document_search_tool = StructuredTool.from_function(
    func=search_financial_documents,
    name="search_financial_documents",
    description="Use for company-reported risks, business strategy, annual-report evidence, and indexed official news. Always provide a ticker and a focused question.",
)

AGENT_TOOLS = [historical_financials_tool, current_market_data_tool, financial_document_search_tool]
