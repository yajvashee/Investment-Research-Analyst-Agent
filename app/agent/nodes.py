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
PORTFOLIO_UNIVERSE = ["MSFT", "AAPL", "KO", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD"]
RISK_GROUPS = {
    "lower": ["MSFT", "AAPL", "KO"],
    "balanced": ["GOOGL", "AMZN", "META"],
    "higher": ["NVDA", "TSLA", "AMD"],
}

def understand_request(state: InvestmentAgentState) -> dict:
    query = state["user_query"]; lower = query.lower()
    companies = sorted({ticker for name, ticker in COMPANIES.items() if name in lower} | {match.upper() for match in re.findall(r"\b(?:MSFT|AAPL|KO|GOOGL|AMZN|META|NVDA|TSLA|AMD)\b", query, re.I)})
    amount = re.search(r"[£$]\s*([\d,]+(?:\.\d+)?)", query)
    is_comparison = "compare" in lower or (len(companies) >= 2 and any(word in lower for word in ("invest", "better", "versus", "vs", " or ")))
    risk_screen_terms = ("avoid", "highest risk", "most risky", "riskiest", "most volatile", "greater caution")
    question_type = "risk_screen" if any(term in lower for term in risk_screen_terms) else "portfolio_strategy" if amount or "strategy" in lower or "allocate" in lower else "company_comparison" if is_comparison else "company_news" if any(word in lower for word in ("recent development", "recent news", "announced", "latest news")) else "company_risk" if "risk" in lower else "current_market_data" if any(word in lower for word in ("p/e", "valuation", "current price", "market cap")) else "historical_financials" if any(word in lower for word in ("revenue", "eps", "debt", "cash", "changed over time")) else "general_investment_research"
    risk = next((value for value in ("lower", "balanced", "higher") if value in lower), None)
    horizon = next((value for value in ("short", "medium", "long") if value in lower), None)
    return {"companies": companies, "investment_amount": float(amount.group(1).replace(",", "")) if amount else None, "risk_preference": risk, "time_horizon": horizon, "question_type": question_type}

def research_planner(state: InvestmentAgentState) -> dict:
    question_type = state["question_type"]
    tools = {"company_risk": ["rag"], "company_news": ["rag"], "risk_screen": ["historical", "rag"], "historical_financials": ["historical"], "current_market_data": ["market"], "company_comparison": ["historical", "market", "rag"], "portfolio_strategy": ["historical", "market", "rag"]}.get(question_type, ["historical", "rag"])
    return {"selected_tools": tools, "research_plan": f"Use {', '.join(tools)} data for {question_type.replace('_', ' ')}."}

def tool_execution(state: InvestmentAgentState) -> dict:
    # A general strategy question starts with all nine local financial records.
    # The smaller shortlist is selected in company_analysis before API/RAG calls.
    if state.get("companies"):
        companies = state["companies"]
    elif state.get("question_type") == "portfolio_strategy":
        companies = PORTFOLIO_UNIVERSE
    elif state.get("question_type") == "risk_screen":
        # These are project higher-volatility categories, not a claim that
        # any company must be avoided.
        companies = RISK_GROUPS["higher"]
    elif state.get("question_type") == "historical_financials":
        # Questions about the available company universe need the whole local
        # database, even when the user has not named a ticker.
        companies = PORTFOLIO_UNIVERSE
    else:
        companies = []
    results, sources = {}, []
    for tool in state["selected_tools"]:
        if state.get("question_type") == "portfolio_strategy" and tool != "historical":
            continue
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
    financials = state.get("tool_results", {}).get("historical", {}).get("financials", {})
    growth_by_ticker: dict[str, Decimal] = {}
    for ticker, records in financials.items():
        if len(records) >= 2:
            first, last = records[0], records[-1]
            if Decimal(first["revenue"]) != 0:
                growth = (Decimal(last["revenue"]) / Decimal(first["revenue"]) - 1) * 100
                growth_by_ticker[ticker] = growth
                observations.append(f"{ticker} revenue changed {growth:.1f}% from {first['fiscal_year']} to {last['fiscal_year']}.")
    if state.get("question_type") == "risk_screen" and growth_by_ticker:
        # Lower historical growth is used only to order the project's existing
        # higher-volatility category; it is not a prediction of share prices.
        caution_order = sorted(growth_by_ticker, key=growth_by_ticker.get)
        most_caution = caution_order[:2]
        risk_answer = (
            "Direct answer: based on the historical figures and reported risk disclosures available in this project, "
            f"{most_caution[0]} and {most_caution[1]} require the greatest caution within the higher-volatility group. "
            "This is not an instruction to avoid either company; it identifies where the available evidence shows more uncertainty."
        )
        observations.append(risk_answer)
        return {"analysis": observations, "risk_answer": risk_answer}
    if state.get("question_type") != "portfolio_strategy" or not growth_by_ticker:
        return {"analysis": observations or ["No numerical trend could be calculated from the available tool data."]}

    # This is a transparent, deliberately simple screen: revenue growth,
    # profitability, and cash relative to debt. It is not a price forecast.
    def score(ticker: str) -> Decimal:
        records = financials[ticker]
        latest = records[-1]
        growth_score = growth_by_ticker[ticker]
        profit_score = Decimal("100") if Decimal(latest["net_income"]) > 0 else Decimal("0")
        debt = Decimal(latest["total_debt"])
        cash = Decimal(latest["cash_and_equivalents"])
        balance_score = min((cash / debt) * Decimal("100"), Decimal("100")) if debt > 0 else Decimal("100")
        return growth_score + profit_score + balance_score

    ranked = sorted(growth_by_ticker, key=score, reverse=True)
    preference = state.get("risk_preference")
    if preference == "balanced":
        # A balanced illustrative shortlist has one financially stronger company
        # from each project risk category.
        shortlist = [max((ticker for ticker in group if ticker in growth_by_ticker), key=score) for group in RISK_GROUPS.values()]
    elif preference in {"lower", "higher"}:
        preferred = [ticker for ticker in RISK_GROUPS[preference] if ticker in growth_by_ticker]
        shortlist = sorted(preferred, key=score, reverse=True)[:3]
    else:
        shortlist = ranked[:3]

    observations.append(
        "Educational shortlist based on historical revenue growth, positive latest net income, and cash relative to debt: "
        + ", ".join(shortlist)
        + "."
    )
    return {"companies": shortlist, "analysis": observations}


def supplementary_research(state: InvestmentAgentState) -> dict:
    """Fetch slower/current evidence only for a portfolio shortlist."""
    if state.get("question_type") != "portfolio_strategy" or not state.get("companies"):
        return {}

    results = dict(state.get("tool_results", {}))
    sources = list(state.get("sources", []))
    companies = state["companies"]
    try:
        results["market"] = get_current_market_data(companies)
    except Exception as error:
        results["market"] = {"status": "error", "error": str(error)}
    try:
        rag = {ticker: search_financial_documents(ticker, state["user_query"], 3) for ticker in companies}
        results["rag"] = rag
        for value in rag.values():
            sources.extend(item["citation"] for item in value.get("results", []))
    except Exception as error:
        results["rag"] = {"status": "error", "error": str(error)}
    return {"tool_results": results, "sources": sources}

def comparison_or_strategy(state: InvestmentAgentState) -> dict:
    if state.get("question_type") == "risk_screen":
        return {"recommendation": "This is a risk-focused comparison, not a recommendation to avoid any company or an allocation instruction. The companies reviewed are in the project's higher-volatility category and should be assessed alongside the cited company-specific risks."}
    if not state.get("investment_amount"): return {"recommendation": "No allocation requested; compare the reported evidence and risks before making any decision."}
    companies = state.get("companies") or PORTFOLIO_UNIVERSE[:3]
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
    # Make the conclusion visible even if the LLM chooses a long explanatory format.
    if state.get("risk_answer"):
        response = f"{state['risk_answer']}\n\n{response}"
    return {"final_response": response}
