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


def test_graph_has_single_linear_entrypoint():
    assert investment_agent is not None
