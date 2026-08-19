"""Run a small, explainable evaluation of the investment research agent."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent.graph import run_investment_agent
from app.agent.nodes import research_planner, understand_request


QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "questions.json"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "results.json"


def _tool_errors(result: dict) -> list[str]:
    return [
        value.get("error", "Tool request failed.")
        for value in result.get("tool_results", {}).values()
        if value.get("status") == "error"
    ]


def evaluate(live: bool = False, limit: int | None = None) -> list[dict]:
    """Evaluate routing by default; use --live only when external quota is available."""
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    results = []
    for case in questions[:limit]:
        understood = understand_request({"user_query": case["question"]})
        plan = research_planner({"question_type": understood["question_type"]})
        actual_tools = plan["selected_tools"]
        item = {
            "id": case["id"],
            "question": case["question"],
            "expected_tools": case["expected_tools"],
            "actual_tools": actual_tools,
            "tool_selection_pass": actual_tools == case["expected_tools"],
            "companies_detected": understood["companies"],
            "mode": "live" if live else "routing_only",
            "warnings": [],
            "sources_returned": 0,
        }
        if live:
            agent_result = run_investment_agent(case["question"])
            item["warnings"] = _tool_errors(agent_result)
            item["sources_returned"] = len(agent_result.get("sources", []))
            item["tool_execution_pass"] = not item["warnings"]
            item["has_educational_disclaimer"] = "educational investment research" in agent_result.get("final_response", "").lower()
        results.append(item)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate agent routing, with optional live tool execution.")
    parser.add_argument("--live", action="store_true", help="Call Azure/Alpha Vantage services. This may consume quota or incur usage charges.")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N questions.")
    args = parser.parse_args()

    results = evaluate(live=args.live, limit=args.limit)
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    passed = sum(item["tool_selection_pass"] for item in results)
    print(f"Tool-selection evaluation: {passed}/{len(results)} passed. Results saved to {RESULTS_PATH.relative_to(PROJECT_ROOT)}")
    for item in results:
        print(f"[{ 'PASS' if item['tool_selection_pass'] else 'FAIL' }] {item['id']}: expected {item['expected_tools']}, actual {item['actual_tools']}")


if __name__ == "__main__":
    main()
