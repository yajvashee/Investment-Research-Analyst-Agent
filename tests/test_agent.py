import ast
import app.agent.nodes as nodes
from app.agent.graph import investment_agent


def test_request_understanding_and_planning():
    understood = nodes.understand_request({"user_query": "Compare Microsoft and Apple with a balanced £1,000 strategy."})
    plan = nodes.research_planner({"question_type": understood["question_type"]})
    assert understood["companies"] == ["AAPL", "MSFT"]
    assert understood["investment_amount"] == 1000.0
    assert plan["selected_tools"] == ["historical", "market", "rag"]


def test_investment_question_with_two_companies_is_a_comparison():
    understood = nodes.understand_request({"user_query": "Should I invest in Apple or Microsoft?"})
    assert understood["question_type"] == "company_comparison"


def test_avoid_question_overrides_an_investment_amount_with_risk_screen():
    understood = nodes.understand_request({"user_query": "What companies should I avoid? Investment amount: £1000. Risk preference: higher."})
    plan = nodes.research_planner({"question_type": understood["question_type"]})
    assert understood["question_type"] == "risk_screen"
    assert plan["selected_tools"] == ["historical", "rag"]


def test_recent_development_question_uses_rag_only():
    understood = nodes.understand_request({"user_query": "What recent developments has NVIDIA announced?"})
    plan = nodes.research_planner({"question_type": understood["question_type"]})
    assert understood["question_type"] == "company_news"
    assert plan["selected_tools"] == ["rag"]


def test_broad_historical_question_uses_all_available_companies(monkeypatch):
    captured = []
    monkeypatch.setattr(nodes, "get_historical_financials", lambda tickers: captured.append(tickers) or {"status": "success", "financials": {}})
    nodes.tool_execution({"question_type": "historical_financials", "selected_tools": ["historical"], "user_query": "Which available companies have stronger revenue growth?"})
    assert captured == [nodes.PORTFOLIO_UNIVERSE]


def test_risk_screen_uses_project_higher_volatility_group_without_market_api(monkeypatch):
    requested = []
    monkeypatch.setattr(nodes, "get_historical_financials", lambda tickers: requested.append(("historical", tickers)) or {"status": "success", "financials": {}})
    monkeypatch.setattr(nodes, "search_financial_documents", lambda ticker, _query, _k: requested.append(("rag", ticker)) or {"status": "success", "results": []})
    result = nodes.tool_execution({"question_type": "risk_screen", "selected_tools": ["historical", "rag"], "user_query": "avoid"})
    assert requested == [("historical", ["NVDA", "TSLA", "AMD"]), ("rag", "NVDA"), ("rag", "TSLA"), ("rag", "AMD")]
    assert "market" not in result["tool_results"]


def test_risk_screen_adds_a_direct_cautious_answer():
    financials = {
        "NVDA": [{"fiscal_year": 2021, "revenue": "100"}, {"fiscal_year": 2024, "revenue": "400"}],
        "TSLA": [{"fiscal_year": 2021, "revenue": "100"}, {"fiscal_year": 2024, "revenue": "180"}],
        "AMD": [{"fiscal_year": 2021, "revenue": "100"}, {"fiscal_year": 2024, "revenue": "150"}],
    }
    result = nodes.company_analysis({"question_type": "risk_screen", "tool_results": {"historical": {"financials": financials}}})
    assert "AMD and TSLA require the greatest caution" in result["risk_answer"]


def test_tool_execution_reuses_wrappers_and_keeps_sources(monkeypatch):
    monkeypatch.setattr(nodes, "get_historical_financials", lambda _t: {"status": "success", "financials": {}})
    monkeypatch.setattr(nodes, "get_current_market_data", lambda _t: {"status": "success", "market_data": []})
    monkeypatch.setattr(nodes, "search_financial_documents", lambda ticker, _q, _k: {"status": "success", "results": [{"citation": {"ticker": ticker, "source": "test"}}]})
    result = nodes.tool_execution({"companies": ["MSFT"], "selected_tools": ["historical", "market", "rag"], "user_query": "test"})
    assert result["tool_results"]["historical"]["status"] == "success"
    assert result["sources"] == [{"ticker": "MSFT", "source": "test"}]


def test_analysis_strategy_and_safe_final_fallback(monkeypatch):
    analysis = nodes.company_analysis({"tool_results": {"historical": {"financials": {"MSFT": [{"fiscal_year": 2021, "revenue": "100"}, {"fiscal_year": 2024, "revenue": "150"}]}}}})
    strategy = nodes.comparison_or_strategy({"investment_amount": 1000.0, "companies": ["MSFT", "AAPL"]})
    monkeypatch.setattr(nodes, "_chat_model", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    final = nodes.final_response({"research_plan": "plan", "analysis": analysis["analysis"], "recommendation": strategy["recommendation"]})
    assert "50.0%" in analysis["analysis"][0] and "'MSFT': 500.0" in strategy["recommendation"]
    assert "educational investment research" in final["final_response"]


def test_portfolio_strategy_creates_a_three_company_shortlist():
    def records(final_revenue: str, cash: str = "100", debt: str = "20"):
        return [
            {"fiscal_year": 2021, "revenue": "100", "net_income": "10", "cash_and_equivalents": cash, "total_debt": debt},
            {"fiscal_year": 2024, "revenue": final_revenue, "net_income": "10", "cash_and_equivalents": cash, "total_debt": debt},
        ]

    financials = {
        "MSFT": records("150"), "AAPL": records("120"), "KO": records("110"),
        "GOOGL": records("140"), "AMZN": records("130"), "META": records("120"),
        "NVDA": records("200"), "TSLA": records("150"), "AMD": records("160"),
    }
    result = nodes.company_analysis({"question_type": "portfolio_strategy", "risk_preference": "balanced", "tool_results": {"historical": {"financials": financials}}})
    assert result["companies"] == ["MSFT", "GOOGL", "NVDA"]


def test_supplementary_research_only_uses_the_shortlist(monkeypatch):
    requested = []
    monkeypatch.setattr(nodes, "get_current_market_data", lambda tickers: {"status": "success", "tickers": tickers})
    monkeypatch.setattr(nodes, "search_financial_documents", lambda ticker, _query, _k: requested.append(ticker) or {"status": "success", "results": []})
    result = nodes.supplementary_research({"question_type": "portfolio_strategy", "companies": ["MSFT", "GOOGL", "NVDA"], "tool_results": {"historical": {}}, "sources": [], "user_query": "strategy"})
    assert result["tool_results"]["market"]["tickers"] == ["MSFT", "GOOGL", "NVDA"]
    assert requested == ["MSFT", "GOOGL", "NVDA"]


def test_strategy_allocation_adds_exactly_to_requested_amount():
    strategy = nodes.comparison_or_strategy({"investment_amount": 1000.0, "companies": ["MSFT", "AAPL", "KO"]})
    allocation_text = strategy["recommendation"].split("Illustrative equal-weight allocation: ", 1)[1].split(". This", 1)[0]
    allocation = ast.literal_eval(allocation_text)
    assert sum(allocation.values()) == 1000.0


def test_rag_failure_is_returned_as_a_safe_tool_error(monkeypatch):
    monkeypatch.setattr(nodes, "search_financial_documents", lambda *_args: (_ for _ in ()).throw(RuntimeError("RAG unavailable")))
    result = nodes.tool_execution({"question_type": "company_risk", "companies": ["MSFT"], "selected_tools": ["rag"], "user_query": "risks"})
    assert result["tool_results"]["rag"]["status"] == "error"
    assert "RAG unavailable" in result["tool_results"]["rag"]["error"]


def test_graph_has_single_linear_entrypoint():
    assert investment_agent is not None
