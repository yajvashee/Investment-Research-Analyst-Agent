from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.agent.graph import run_investment_agent
query = " ".join(sys.argv[1:]) or "How has Microsoft's revenue changed over time?"
result = run_investment_agent(query)
print(result["final_response"])
