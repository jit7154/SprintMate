from typing import Any

from sqlalchemy import select

from app.db import Issue, Proposal, async_session_maker
from app.services.adapters.demo_tracker import DemoTrackerAdapter


async def search_issues(
    query: str | None = None,
    status: str | None = None,
    sprint_id: int | None = None,
    assignee_id: int | None = None,
) -> list[dict[str, Any]]:
    """Search tracked issues with optional query string, status, sprint, or assignee filter."""
    async with async_session_maker() as session:
        tracker = DemoTrackerAdapter(session)
        issues = await tracker.list_issues(
            sprint_id=sprint_id,
            status=status,
            assignee_id=assignee_id,
        )
        if query:
            q = query.lower()
            issues = [
                i
                for i in issues
                if q in i["key"].lower()
                or q in i["title"].lower()
                or q in i.get("description", "").lower()
            ]
        return issues


async def get_issue(issue_key: str) -> dict[str, Any]:
    """Retrieve full details of an issue by key, including dependencies, status, points, and history."""
    async with async_session_maker() as session:
        tracker = DemoTrackerAdapter(session)
        issue = await tracker.get_issue(issue_key.strip().upper())
        if not issue:
            return {"error": f"Issue '{issue_key}' not found."}
        return issue


async def get_sprint(sprint_id: int | None = None) -> dict[str, Any]:
    """Get active sprint or sprint by ID, including total days, elapsed days, and sprint goal."""
    async with async_session_maker() as session:
        tracker = DemoTrackerAdapter(session)
        sprint = await tracker.get_sprint(sprint_id)
        if not sprint:
            return {"error": "Sprint not found."}
        return sprint


async def get_issue_history(issue_key: str) -> list[dict[str, Any]]:
    """Get chronological status and field changes for an issue."""
    async with async_session_maker() as session:
        tracker = DemoTrackerAdapter(session)
        return await tracker.get_issue_history(issue_key.strip().upper())


async def propose_reassignment(
    issue_key: str,
    proposed_assignee_id: int,
    reason: str,
    created_by: str = "InvestigatorAgent",
) -> dict[str, Any]:
    """Propose reassigning an issue to another developer.

    This creates a PENDING proposal requiring human manager approval.
    It does NOT execute or modify the issue directly.
    """
    key = issue_key.strip().upper()
    async with async_session_maker() as session:
        # Verify issue exists
        stmt = select(Issue).where(Issue.key == key)
        res = await session.execute(stmt)
        issue = res.scalars().first()
        if not issue:
            return {
                "error": f"Cannot propose reassignment: issue '{key}' does not exist."
            }

        proposal = Proposal(
            issue_key=key,
            current_assignee_id=issue.assignee_id,
            proposed_assignee_id=proposed_assignee_id,
            reason=reason,
            status="PENDING",
            created_by=created_by,
        )
        session.add(proposal)
        await session.commit()
        await session.refresh(proposal)

        return {
            "proposal_id": proposal.id,
            "issue_key": proposal.issue_key,
            "current_assignee_id": proposal.current_assignee_id,
            "proposed_assignee_id": proposal.proposed_assignee_id,
            "reason": proposal.reason,
            "status": proposal.status,
            "created_by": proposal.created_by,
            "created_at": proposal.created_at.isoformat(),
            "message": "Reassignment proposal created in PENDING status. Awaiting manager approval.",
        }
