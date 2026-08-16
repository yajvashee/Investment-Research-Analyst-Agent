from fastapi.testclient import TestClient
import app.backend.main as backend

client = TestClient(backend.app)

def test_health():
    assert client.get("/health").json() == {"status": "healthy"}

def test_research_response_preserves_sources(monkeypatch):
    monkeypatch.setattr(backend, "run_investment_agent", lambda _q: {"final_response": "Grounded answer", "companies": ["MSFT"], "sources": [{"source": "https://example.com", "ticker": "MSFT"}], "selected_tools": ["historical", "rag"], "tool_results": {}})
    response = client.post("/research", json={"question": "What are Microsoft's risks?"})
    assert response.status_code == 200
    assert response.json()["sources"][0]["source"] == "https://example.com"

def test_empty_question_is_rejected():
    assert client.post("/research", json={"question": ""}).status_code == 422

def test_agent_failure_is_safe(monkeypatch):
    monkeypatch.setattr(backend, "run_investment_agent", lambda _q: (_ for _ in ()).throw(RuntimeError("secret traceback")))
    response = client.post("/research", json={"question": "Compare MSFT and AAPL"})
    assert response.status_code == 503 and response.json()["detail"] == "Research service is temporarily unavailable."
