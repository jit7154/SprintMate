import uuid
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import async_session_maker
from app.main import app
from app.services.observability.usage_logger import (
    get_usage_summary,
    log_agent_usage,
)
from app.services.standup.builder import build_standup_data

REF_DATE = datetime(2026, 11, 17, 0, 0, 0)


@pytest.mark.asyncio
async def test_usage_logging_and_summary():
    async with async_session_maker() as session:
        # Log 2 mock requests
        await log_agent_usage(
            session=session,
            request_id=f"test-req-{uuid.uuid4()}",
            query="Analyze sprint bottlenecks",
            latency_ms=1200.0,
            input_tokens=500,
            output_tokens=150,
            tools_called=["get_sprint", "search_issues"],
            agent_path=["supervisor", "investigator", "supervisor"],
        )

        await log_agent_usage(
            session=session,
            request_id=f"test-req-{uuid.uuid4()}",
            query="Check PR #211 build failure",
            latency_ms=800.0,
            input_tokens=400,
            output_tokens=100,
            tools_called=["get_pull_request", "get_ci_status"],
            agent_path=["supervisor", "investigator"],
        )

        summary = await get_usage_summary(session)
        assert summary["total_investigations"] >= 2
        assert summary["average_latency_ms"] > 0
        assert summary["total_input_tokens"] >= 900
        assert len(summary["records"]) >= 2


@pytest.mark.asyncio
async def test_deterministic_standup_data():
    async with async_session_maker() as session:
        standup = await build_standup_data(session, now=REF_DATE)

        assert standup["sprint_name"] == "Sprint 24"
        assert len(standup["completed"]) >= 1
        assert len(standup["in_progress"]) >= 1

        # Check seeded blockers
        blocker_keys = [b["key"] for b in standup["blockers"]]
        assert "PAY-142" in blocker_keys

        # Check delayed items
        delayed_keys = [d["key"] for d in standup["delayed"]]
        assert "PAY-139" in delayed_keys

        # Check pending PR reviews
        pending_pr_nums = [p["pr_number"] for p in standup["pending_reviews"]]
        assert 204 in pending_pr_nums

        # Check discussion points include overloaded developer
        assert any("David Kim" in pt for pt in standup["discussion_points"])


@pytest.mark.asyncio
async def test_usage_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/usage")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_investigations" in data
        assert "average_latency_ms" in data
        assert "records" in data
