"""State passed through the single LangGraph investment-research workflow."""
from __future__ import annotations
from typing import Any, TypedDict

class InvestmentAgentState(TypedDict, total=False):
    user_query: str
    investment_amount: float | None
    risk_preference: str | None
    time_horizon: str | None
    companies: list[str]
    question_type: str
    research_plan: str
    selected_tools: list[str]
    tool_results: dict[str, Any]
    analysis: list[str]
    risk_answer: str
    recommendation: str
    sources: list[dict[str, Any]]
    final_response: str
