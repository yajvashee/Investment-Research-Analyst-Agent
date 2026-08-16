"""Pydantic request and response shapes for the FastAPI backend."""
from typing import Any
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    investment_amount: float | None = Field(default=None, gt=0)
    risk_preference: str | None = None
    time_horizon: str | None = None

class ResearchResponse(BaseModel):
    status: str
    answer: str
    companies_analyzed: list[str] = []
    sources: list[dict[str, Any]] = []
    tools_used: list[str] = []
    warnings: list[str] = []
