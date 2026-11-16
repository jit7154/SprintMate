import math
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import UsageRecord


def estimate_gemini_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for Gemini 3.5 Flash Lite in USD ($0.075/1M input, $0.30/1M output)."""
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    return round(input_cost + output_cost, 6)


async def log_agent_usage(
    session: AsyncSession,
    request_id: str,
    query: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    tools_called: list[str],
    agent_path: list[str],
    errors_and_retries: list[str] | None = None,
) -> UsageRecord:
    """Persist request execution metrics and cost to the usage_records table."""
    cost = estimate_gemini_cost(input_tokens, output_tokens)
    record = UsageRecord(
        request_id=request_id,
        query=query,
        latency_ms=round(latency_ms, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=cost,
        tools_called=tools_called,
        agent_path=agent_path,
        errors_and_retries=errors_and_retries or [],
        created_at=datetime.utcnow(),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_usage_summary(session: AsyncSession) -> dict[str, Any]:
    """Calculate aggregated telemetry metrics (p50/p95 latency, average cost, totals)."""
    stmt = select(UsageRecord).order_by(UsageRecord.created_at.desc())
    res = await session.execute(stmt)
    records = res.scalars().all()

    total_count = len(records)
    if total_count == 0:
        return {
            "total_investigations": 0,
            "average_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "average_cost_usd": 0.0,
            "total_cost_usd": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "records": [],
        }

    latencies = sorted(r.latency_ms for r in records)
    p95_idx = max(0, math.ceil(len(latencies) * 0.95) - 1)
    p95_latency = latencies[p95_idx]

    avg_latency = sum(latencies) / total_count
    total_cost = sum(r.estimated_cost_usd for r in records)
    avg_cost = total_cost / total_count
    total_input = sum(r.input_tokens for r in records)
    total_output = sum(r.output_tokens for r in records)

    return {
        "total_investigations": total_count,
        "average_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "average_cost_usd": round(avg_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "records": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "query": r.query,
                "latency_ms": r.latency_ms,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "estimated_cost_usd": r.estimated_cost_usd,
                "tools_called": r.tools_called,
                "agent_path": r.agent_path,
                "errors_and_retries": r.errors_and_retries,
                "created_at": r.created_at.isoformat(),
            }
            for r in records[:50]
        ],
    }
