"""The six small nodes for the single investment-research agent."""
from __future__ import annotations
import json, os, re
from decimal import Decimal
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from app.agent.prompts import FINAL_RESPONSE_PROMPT
from app.agent.tools import get_current_market_data, get_historical_financials, search_financial_documents
from app.agent.state import InvestmentAgentState

COMPANIES = {"microsoft":"MSFT", "apple":"AAPL", "coca-cola":"KO", "coca cola":"KO", "alphabet":"GOOGL", "google":"GOOGL", "amazon":"AMZN", "meta":"META", "nvidia":"NVDA", "tesla":"TSLA", "amd":"AMD"}

def understand_request(state: InvestmentAgentState) -> dict:
    query = state["user_query"]; lower = query.lower()
    companies = sorted({ticker for name, ticker in COMPANIES.items() if name in lower} | {match.upper() for match in re.findall(r"\b(?:MSFT|AAPL|KO|GOOGL|AMZN|META|NVDA|TSLA|AMD)\b", query, re.I)})
    amount = re.search(r"[£$]\s*([\d,]+(?:\.\d+)?)", query)
    is_comparison = "compare" in lower or (len(companies) >= 2 and any(word in lower for word in ("invest", "better", "versus", "vs", " or ")))
    question_type = "portfolio_strategy" if amount or "strategy" in lower or "allocate" in lower else "company_comparison" if is_comparison else "company_risk" if "risk" in lower else "current_market_data" if any(word in lower for word in ("p/e", "valuation", "current price", "market cap")) else "historical_financials" if any(word in lower for word in ("revenue", "eps", "debt", "cash", "changed over time")) else "general_investment_research"
    risk = next((value for value in ("lower", "balanced", "higher") if value in lower), None)
    horizon = next((value for value in ("short", "medium", "long") if value in lower), None)
    return {"companies": companies, "investment_amount": float(amount.group(1).replace(",", "")) if amount else None, "risk_preference": risk, "time_horizon": horizon, "question_type": question_type}

def research_planner(state: InvestmentAgentState) -> dict:
    question_type = state["question_type"]
    tools = {"company_risk": ["rag"], "historical_financials": ["historical"], "current_market_data": ["market"], "company_comparison": ["historical", "market", "rag"], "portfolio_strategy": ["historical", "market", "rag"]}.get(question_type, ["historical", "rag"])
    return {"selected_tools": tools, "research_plan": f"Use {', '.join(tools)} data for {question_type.replace('_', ' ')}."}

def tool_execution(state: InvestmentAgentState) -> dict:
    companies = state.get("companies") or (["MSFT", "AAPL", "GOOGL", "NVDA", "KO"] if state["question_type"] == "portfolio_strategy" else [])
    results, sources = {}, []
    for tool in state["selected_tools"]:
        try:
            if tool == "historical": results[tool] = get_historical_financials(companies)
            elif tool == "market": results[tool] = get_current_market_data(companies)
            else:
                rag = {ticker: search_financial_documents(ticker, state["user_query"], 3) for ticker in companies}
                results[tool] = rag
                for value in rag.values():
                    sources.extend(item["citation"] for item in value.get("results", []))
        except Exception as error:
            results[tool] = {"status": "error", "error": str(error)}
    return {"tool_results": results, "sources": sources}

def company_analysis(state: InvestmentAgentState) -> dict:
    observations = []
    for ticker, records in state.get("tool_results", {}).get("historical", {}).get("financials", {}).items():
        if len(records) >= 2:
            first, last = records[0], records[-1]
            if Decimal(first["revenue"]) != 0:
                growth = (Decimal(last["revenue"]) / Decimal(first["revenue"]) - 1) * 100
                observations.append(f"{ticker} revenue changed {growth:.1f}% from {first['fiscal_year']} to {last['fiscal_year']}.")
    return {"analysis": observations or ["No numerical trend could be calculated from the available tool data."]}

def comparison_or_strategy(state: InvestmentAgentState) -> dict:
    if not state.get("investment_amount"): return {"recommendation": "No allocation requested; compare the reported evidence and risks before making any decision."}
    companies = state.get("companies") or ["MSFT", "AAPL", "GOOGL", "NVDA", "KO"]
    amount = state["investment_amount"]; share = round(amount / len(companies), 2)
    allocation = {ticker: share for ticker in companies}; allocation[companies[-1]] = round(amount - share * (len(companies)-1), 2)
    return {"recommendation": f"Illustrative equal-weight allocation: {allocation}. This is a neutral example, not a prediction or recommendation."}

def _chat_model() -> AzureChatOpenAI:
    load_dotenv()
    return AzureChatOpenAI(azure_endpoint=os.environ["AZURE_ENDPOINT"], api_key=os.environ["AZURE_API_KEY"], api_version=os.environ["CHAT_API_VERSION"], azure_deployment=os.environ["CHAT_DEPLOYMENT"], temperature=0)

def final_response(state: InvestmentAgentState) -> dict:
    try:
        response = _chat_model().invoke(FINAL_RESPONSE_PROMPT.format(state=json.dumps(state, default=str))).content
    except Exception:
        response = "\n".join([state.get("research_plan", ""), *state.get("analysis", []), state.get("recommendation", ""), "This is educational investment research, not personalised financial advice."])
    return {"final_response": response}
