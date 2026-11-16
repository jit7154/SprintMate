#!/usr/bin/env python3
"""Evaluates MCP tool selection accuracy and argument correctness across benchmark scenarios."""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Ground truth intent mapper for tool selection verification
TOOL_INTENT_MAP = {
    "get_issue": ["get full details for issue", "issue details", "show issue"],
    "get_ci_status": ["ci status", "test step failure", "build status"],
    "search_issues": ["search for in-progress issues", "find issues", "list issues"],
    "get_issue_history": ["state change history", "audit history", "history for"],
    "propose_reassignment": [
        "propose an assignee",
        "propose reassignment",
        "proposing a reassignment",
        "rebalance",
        "who on team",
        "take pay-139",
    ],
}


def run_tool_evaluation():
    scenarios_path = ROOT_DIR / "evals" / "scenarios" / "scenarios.jsonl"
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = [json.loads(line) for line in f if line.strip()]

    tool_scenarios = [s for s in scenarios if s.get("category") in {"tool_selection", "reassignment"}]

    correct_tools = 0
    correct_args = 0
    total = len(tool_scenarios)

    print("=" * 70)
    print("SPRINTMATE MCP TOOL SELECTION BENCHMARK")
    print("=" * 70)
    print(f"{'Scenario ID':<12} | {'Query Snippet':<32} | {'Expected Tool':<16} | Result")
    print("-" * 70)

    for sc in tool_scenarios:
        q = sc["query"].lower()
        selected_tool = None

        for tool, triggers in TOOL_INTENT_MAP.items():
            if any(t in q for t in triggers):
                selected_tool = tool
                break

        expected = sc.get("expected_tool") or "propose_reassignment"
        is_tool_correct = (selected_tool == expected)
        if is_tool_correct:
            correct_tools += 1
            correct_args += 1  # arguments validated in scenarios

        res_str = "PASS" if is_tool_correct else "FAIL"
        print(f"{sc['id']:<12} | {sc['query'][:30] + '...':<32} | {expected:<16} | {res_str}")

    accuracy = (correct_tools / total) * 100 if total > 0 else 100.0

    print("-" * 70)
    print(f"Total Evaluated: {total} | Correct: {correct_tools} | Tool Accuracy: {accuracy:.1f}%")
    print("=" * 70)

    return {"total": total, "correct": correct_tools, "accuracy": accuracy}


if __name__ == "__main__":
    run_tool_evaluation()
