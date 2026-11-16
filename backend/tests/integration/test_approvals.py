import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db import Issue, async_session_maker
from app.main import app
from app.services.approvals.proposals import create_proposal_entry


@pytest.fixture(autouse=True)
async def restore_seed_state():
    """Ensure modified issue assignees are restored after approval tests."""
    yield
    async with async_session_maker() as session:
        for k in ["PAY-141", "PAY-145", "PAY-148"]:
            stmt = select(Issue).where(Issue.key == k)
            res = await session.execute(stmt)
            issue = res.scalars().first()
            if issue:
                issue.assignee_id = 6
        await session.commit()


@pytest.mark.asyncio
async def test_approval_happy_path():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a proposal for PAY-141 (currently assigned to David Kim, id 6)
        async with async_session_maker() as session:
            proposal = await create_proposal_entry(
                session=session,
                issue_key="PAY-141",
                proposed_assignee_id=7,  # Rachel Green
                reason="Load balancing from David Kim to Rachel Green",
            )
            prop_id = proposal["id"]

        # Manager approves
        headers = {"X-User-Role": "manager", "X-User-Id": "manager-alex"}
        resp = await client.post(f"/api/proposals/{prop_id}/approve", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "EXECUTED"
        assert data["new_assignee_id"] == 7

        # Verify database issue state
        async with async_session_maker() as session:
            stmt = select(Issue).where(Issue.key == "PAY-141")
            res = await session.execute(stmt)
            issue = res.scalars().first()
            assert issue.assignee_id == 7

        # Verify audit log entry
        audit_resp = await client.get("/api/audit?entity_type=proposal")
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert any(
            entry["entity_id"] == str(prop_id) and entry["outcome"] == "SUCCESS"
            for entry in logs
        )


@pytest.mark.asyncio
async def test_wrong_role_forbidden():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Non-manager role (developer)
        dev_headers = {"X-User-Role": "developer", "X-User-Id": "dev-priya"}

        # Attempt approve -> 403 Forbidden
        approve_resp = await client.post(
            "/api/proposals/1/approve", headers=dev_headers
        )
        assert approve_resp.status_code == 403
        assert "requires 'manager' role" in approve_resp.json()["detail"].lower()

        # Attempt reject -> 403 Forbidden
        reject_resp = await client.post("/api/proposals/1/reject", headers=dev_headers)
        assert reject_resp.status_code == 403
        assert "requires 'manager' role" in reject_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stale_proposal_detection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create proposal for PAY-148 (currently assigned to David Kim, id 6)
        async with async_session_maker() as session:
            proposal = await create_proposal_entry(
                session=session,
                issue_key="PAY-148",
                proposed_assignee_id=7,
                reason="Reassign to Rachel Green",
            )
            prop_id = proposal["id"]

            # Simulate concurrent change: another engineer changes PAY-148 assignee to Tom Bradley (id 8)
            stmt = select(Issue).where(Issue.key == "PAY-148")
            res = await session.execute(stmt)
            issue = res.scalars().first()
            issue.assignee_id = 8
            await session.commit()

        # Manager now attempts to approve the stale proposal
        headers = {"X-User-Role": "manager", "X-User-Id": "manager-alex"}
        resp = await client.post(f"/api/proposals/{prop_id}/approve", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        # Proposal must be marked STALE
        assert data["status"] == "STALE"
        assert "stale" in data["message"].lower()

        # Verify database issue was NOT mutated to 7 (remains 8)
        async with async_session_maker() as session:
            stmt = select(Issue).where(Issue.key == "PAY-148")
            res = await session.execute(stmt)
            issue = res.scalars().first()
            assert issue.assignee_id == 8

        # Verify audit log records STALE_REJECTED
        audit_resp = await client.get("/api/audit?outcome=STALE_REJECTED")
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert any(entry["entity_id"] == str(prop_id) for entry in logs)


@pytest.mark.asyncio
async def test_double_approval_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create proposal for PAY-145 (currently assigned to id 6)
        async with async_session_maker() as session:
            proposal = await create_proposal_entry(
                session=session,
                issue_key="PAY-145",
                proposed_assignee_id=5,  # Elena
                reason="Elena is familiar with report parsers",
            )
            prop_id = proposal["id"]

        headers = {"X-User-Role": "manager", "X-User-Id": "manager-alex"}

        # First approval -> 200 OK
        resp1 = await client.post(f"/api/proposals/{prop_id}/approve", headers=headers)
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "EXECUTED"

        # Second approval on already executed proposal -> 400 Bad Request
        resp2 = await client.post(f"/api/proposals/{prop_id}/approve", headers=headers)
        assert resp2.status_code == 400
        assert "already 'EXECUTED'" in resp2.json()["detail"]
