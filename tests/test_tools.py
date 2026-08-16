from datetime import datetime
from decimal import Decimal

from langchain_core.documents import Document

import app.agent.tools as tools
from app.market_data.service import MarketData


class FakeFinancialRecord:
    def to_dict(self):
        return {"ticker": "MSFT", "fiscal_year": 2024, "revenue": Decimal("100.50"), "created_at": datetime(2024, 1, 1)}


def test_historical_financials_tool_wraps_existing_query(monkeypatch):
    monkeypatch.setattr(tools, "compare_company_financials", lambda tickers: {ticker: [FakeFinancialRecord()] for ticker in tickers})
    result = tools.get_historical_financials("msft")
    assert result["status"] == "success" and result["financials"]["MSFT"][0]["revenue"] == "100.50"


def test_market_data_tool_wraps_existing_service(monkeypatch):
    market_data = MarketData("MSFT", Decimal("100"), None, None, None, None, None, None, 10)
    monkeypatch.setattr(tools, "get_market_data_for_companies", lambda _tickers: [market_data])
    result = tools.get_current_market_data(["msft"])
    assert result == {"status": "success", "market_data": [{"ticker": "MSFT", "current_price": "100", "market_cap": None, "pe_ratio": None, "week_52_high": None, "week_52_low": None, "price_change": None, "price_change_percent": None, "volume": 10}]}


def test_document_search_tool_keeps_source_metadata(monkeypatch):
    document = Document(page_content="Risk text", metadata={"ticker": "MSFT", "company_name": "Microsoft", "document_name": "Report", "document_type": "annual_report", "fiscal_year": 2024, "page_number": 2, "section": "Risk Factors", "source": "https://example.com"})
    monkeypatch.setattr(tools, "search_company_documents", lambda *_args: [document])
    result = tools.search_financial_documents("msft", "main risks")
    assert result["status"] == "success" and result["results"][0]["citation"]["source"] == "https://example.com"


def test_invalid_tool_inputs_have_predictable_errors():
    assert tools.get_historical_financials("BAD!")["status"] == "error"
    assert tools.get_current_market_data([])["status"] == "error"
    assert tools.search_financial_documents("MSFT", "", 5)["status"] == "error"
