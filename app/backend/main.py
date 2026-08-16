"""Thin HTTP interface for the existing LangGraph investment agent."""
from fastapi import FastAPI, HTTPException
from app.agent.graph import run_investment_agent
from app.backend.schemas import ResearchRequest, ResearchResponse

app = FastAPI(title="Investment Research Analyst API", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}

def _question_with_context(request: ResearchRequest) -> str:
    context = []
    if request.investment_amount is not None: context.append(f"Investment amount: £{request.investment_amount}.")
    if request.risk_preference: context.append(f"Risk preference: {request.risk_preference}.")
    if request.time_horizon: context.append(f"Time horizon: {request.time_horizon}.")
    return " ".join([request.question, *context])

@app.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest) -> ResearchResponse:
    try:
        result = run_investment_agent(_question_with_context(request))
    except Exception as error:
        raise HTTPException(status_code=503, detail="Research service is temporarily unavailable.") from error
    tool_results = result.get("tool_results", {})
    warnings = [value.get("error", "Tool request failed.") for value in tool_results.values() if value.get("status") == "error"]
    return ResearchResponse(status="success", answer=result.get("final_response", "No response generated."), companies_analyzed=result.get("companies", []), sources=result.get("sources", []), tools_used=result.get("selected_tools", []), warnings=warnings)
