from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Developer, Issue, Proposal
from app.services.approvals.audit_log import record_audit_entry


async def list_proposals(
    session: AsyncSession,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List proposals enriched with issue details and assignee skill/workload comparisons."""
    stmt = select(Proposal).order_by(Proposal.created_at.desc())
    if status:
        stmt = stmt.where(Proposal.status == status.upper())

    result = await session.execute(stmt)
    proposals = result.scalars().all()

    enriched = []
    for prop in proposals:
        # Fetch issue details
        issue_stmt = select(Issue).where(Issue.key == prop.issue_key)
        issue_res = await session.execute(issue_stmt)
        issue = issue_res.scalars().first()

        # Fetch current and proposed developers
        cur_dev = None
        if prop.current_assignee_id:
            c_stmt = select(Developer).where(Developer.id == prop.current_assignee_id)
            c_res = await session.execute(c_stmt)
            cur_dev = c_res.scalars().first()

        p_stmt = select(Developer).where(Developer.id == prop.proposed_assignee_id)
        p_res = await session.execute(p_stmt)
        prop_dev = p_res.scalars().first()

        skills_comp = {
            "current_assignee_skills": cur_dev.skills if cur_dev else [],
            "proposed_assignee_skills": prop_dev.skills if prop_dev else [],
            "required_labels": issue.labels if issue else [],
        }

        workload_comp = {
            "current_assignee_capacity": cur_dev.weekly_capacity_points
            if cur_dev
            else 0,
            "proposed_assignee_capacity": prop_dev.weekly_capacity_points
            if prop_dev
            else 0,
        }

        enriched.append(
            {
                "id": prop.id,
                "issue_key": prop.issue_key,
                "issue_title": issue.title if issue else "Unknown Issue",
                "current_assignee_id": prop.current_assignee_id,
                "current_assignee_name": cur_dev.name if cur_dev else "Unassigned",
                "proposed_assignee_id": prop.proposed_assignee_id,
                "proposed_assignee_name": prop_dev.name
                if prop_dev
                else "Unknown Developer",
                "reason": prop.reason,
                "status": prop.status,
                "created_by": prop.created_by,
                "created_at": prop.created_at.isoformat(),
                "updated_at": prop.updated_at.isoformat(),
                "skills_comparison": skills_comp,
                "workload_comparison": workload_comp,
            }
        )

    return enriched


async def create_proposal_entry(
    session: AsyncSession,
    issue_key: str,
    proposed_assignee_id: int,
    reason: str,
    created_by: str = "InvestigatorAgent",
    actor_id: str = "system",
    actor_role: str = "system",
) -> dict[str, Any]:
    """Store a new proposal row in PENDING status."""
    key = issue_key.strip().upper()
    issue_stmt = select(Issue).where(Issue.key == key)
    res = await session.execute(issue_stmt)
    issue = res.scalars().first()
    if not issue:
        raise ValueError(f"Issue '{key}' not found.")

    proposal = Proposal(
        issue_key=key,
        current_assignee_id=issue.assignee_id,
        proposed_assignee_id=proposed_assignee_id,
        reason=reason,
        status="PENDING",
        created_by=created_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)

    # Audit log creation
    await record_audit_entry(
        session=session,
        entity_type="proposal",
        entity_id=str(proposal.id),
        action="create_proposal",
        actor_id=actor_id,
        actor_role=actor_role,
        before_state=None,
        after_state={
            "issue_key": key,
            "current_assignee_id": issue.assignee_id,
            "proposed_assignee_id": proposed_assignee_id,
            "status": "PENDING",
        },
        outcome="SUCCESS",
    )

    return {
        "id": proposal.id,
        "issue_key": proposal.issue_key,
        "current_assignee_id": proposal.current_assignee_id,
        "proposed_assignee_id": proposal.proposed_assignee_id,
        "reason": proposal.reason,
        "status": proposal.status,
        "created_by": proposal.created_by,
        "created_at": proposal.created_at.isoformat(),
        "updated_at": proposal.updated_at.isoformat(),
    }
