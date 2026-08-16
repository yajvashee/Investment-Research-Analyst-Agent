"""Demonstrate the three Phase 5 tools independently, without an agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.tools import (  # noqa: E402
    get_current_market_data,
    get_historical_financials,
    search_financial_documents,
)


def show(title: str, result: dict) -> None:
    print(f"\n{title}\n{'-' * len(title)}")
    print(json.dumps(result, indent=2))


show("Historical Financials Tool", get_historical_financials("MSFT"))
show("Market Data Tool", get_current_market_data("MSFT"))
show("Company Document Search Tool", search_financial_documents("NVDA", "What recent developments has NVIDIA announced?", k=3))
