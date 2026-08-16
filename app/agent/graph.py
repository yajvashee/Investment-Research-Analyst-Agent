"""Public LangGraph entry point for the single investment research agent."""
from langgraph.graph import END, START, StateGraph
from app.agent.nodes import comparison_or_strategy, company_analysis, final_response, research_planner, tool_execution, understand_request
from app.agent.state import InvestmentAgentState

def build_investment_agent():
    graph = StateGraph(InvestmentAgentState)
    graph.add_node("understand_request", understand_request); graph.add_node("research_planner", research_planner)
    graph.add_node("tool_execution", tool_execution); graph.add_node("company_analysis", company_analysis)
    graph.add_node("comparison_or_strategy", comparison_or_strategy); graph.add_node("final_response", final_response)
    graph.add_edge(START, "understand_request"); graph.add_edge("understand_request", "research_planner")
    graph.add_edge("research_planner", "tool_execution"); graph.add_edge("tool_execution", "company_analysis")
    graph.add_edge("company_analysis", "comparison_or_strategy"); graph.add_edge("comparison_or_strategy", "final_response"); graph.add_edge("final_response", END)
    return graph.compile()

investment_agent = build_investment_agent()

def run_investment_agent(query: str) -> dict:
    """Run one research query through the complete single-agent graph."""
    return investment_agent.invoke({"user_query": query})
