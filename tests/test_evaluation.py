from scripts.evaluate_agent import evaluate


def test_routing_evaluation_passes_all_representative_cases():
    results = evaluate()
    assert len(results) >= 10
    assert all(result["tool_selection_pass"] for result in results)
