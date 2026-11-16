#!/usr/bin/env python3
"""Evaluates end-to-end agent investigation answers, evidence grounding, and telemetry."""

import asyncio
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.config import settings

if settings.gemini_api_key and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

from app.agents.supervisor import extract_evidence, run_investigation
from app.db import async_session_maker


async def run_agent_evaluation():
    scenarios_path = ROOT_DIR / "evals" / "scenarios" / "scenarios.jsonl"
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = [json.loads(line) for line in f if line.strip()]

    agent_scenarios = [s for s in scenarios if s.get("category") == "risk_identification"]

    total = len(agent_scenarios)
    evidence_hits = 0
    latencies = []
    total_tokens = 0

    print("=" * 70)
    print("SPRINTMATE AGENT GROUNDING & INVESTIGATION EVALUATION")
    print("=" * 70)
    print(f"{'Scenario ID':<12} | {'Expected Keys':<22} | {'Cited Keys':<22} | Latency")
    print("-" * 70)

    async with async_session_maker() as session:
        for i, sc in enumerate(agent_scenarios):
            if i > 0:
                # Add delay to stay well within free tier 15 RPM quota
                await asyncio.sleep(4.0)

            try:
                result = await run_investigation(
                    query=sc["query"],
                    sprint_id=2,
                    session=session,
                )

                expected = set(sc.get("expected_keys", []))
                detected_evidence = {e.key for e in result.evidence}

                overlap = expected.intersection(detected_evidence)
                is_hit = len(overlap) > 0 or any(k in result.answer for k in expected)
                if is_hit:
                    evidence_hits += 1

                latencies.append(result.latency_ms)
                total_tokens += (result.input_tokens + result.output_tokens)

                exp_str = ", ".join(list(expected)[:2])
                det_str = ", ".join(list(detected_evidence)[:2]) if detected_evidence else "In text"
                print(f"{sc['id']:<12} | {exp_str:<22} | {det_str:<22} | {result.latency_ms:.0f}ms")
            except Exception as e:
                print(f"{sc['id']:<12} | Error: {str(e)[:45]}")

    grounding_recall = (evidence_hits / total) * 100 if total > 0 else 100.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("-" * 70)
    print(f"Total Scenarios: {total} | Grounding Recall: {grounding_recall:.1f}% | Avg Latency: {avg_latency:.1f}ms")
    print(f"Total Tokens Consumed: {total_tokens}")
    print("=" * 70)

    return {
        "grounding_recall": grounding_recall,
        "avg_latency_ms": avg_latency,
        "total_tokens": total_tokens,
    }


if __name__ == "__main__":
    asyncio.run(run_agent_evaluation())
