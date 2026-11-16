from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Issue, IssueHistory, Proposal
from app.services.approvals.audit_log import record_audit_entry


async def approve_proposal(
    session: AsyncSession,
    proposal_id: int,
    actor_id: str,
    actor_role: str,
) -> dict[str, Any]:
    """Execute proposal approval with strict role verification and state re-check."""
    # 1. Role verification: only managers may approve proposals
    if actor_role.lower() != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only managers can approve proposals. Current role is '{actor_role}'.",
        )

    # 2. Fetch proposal
    prop_stmt = select(Proposal).where(Proposal.id == proposal_id)
    prop_res = await session.execute(prop_stmt)
    proposal = prop_res.scalars().first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found.",
        )

    if proposal.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve proposal: current status is already '{proposal.status}'.",
        )

    # 3. State re-check against current database state
    issue_stmt = select(Issue).where(Issue.key == proposal.issue_key)
    issue_res = await session.execute(issue_stmt)
    issue = issue_res.scalars().first()

    if not issue:
        proposal.status = "STALE"
        proposal.updated_at = datetime.utcnow()
        await record_audit_entry(
            session=session,
            entity_type="proposal",
            entity_id=str(proposal.id),
            action="approve",
            actor_id=actor_id,
            actor_role=actor_role,
            before_state={"status": "PENDING"},
            after_state={"status": "STALE", "reason": "Issue deleted or missing"},
            outcome="STALE_REJECTED",
        )
        await session.commit()
        return {
            "proposal_id": proposal.id,
            "status": "STALE",
            "message": "Proposal marked STALE: target issue no longer exists.",
        }

    # Verify issue current assignee still matches proposal's recorded current_assignee_id
    if issue.assignee_id != proposal.current_assignee_id:
        # State mismatch detected! Mark stale and do not mutate issue
        proposal.status = "STALE"
        proposal.updated_at = datetime.utcnow()

        await record_audit_entry(
            session=session,
            entity_type="proposal",
            entity_id=str(proposal.id),
            action="approve",
            actor_id=actor_id,
            actor_role=actor_role,
            before_state={
                "status": "PENDING",
                "expected_assignee_id": proposal.current_assignee_id,
            },
            after_state={
                "status": "STALE",
                "actual_assignee_id": issue.assignee_id,
                "reason": "Assignee changed concurrently",
            },
            outcome="STALE_REJECTED",
        )
        await session.commit()
        return {
            "proposal_id": proposal.id,
            "status": "STALE",
            "message": (
                f"Proposal marked STALE: issue {issue.key} assignee changed from "
                f"{proposal.current_assignee_id} to {issue.assignee_id} since proposal creation."
            ),
        }

    # 4. State checks passed: update issue assignee and mark proposal EXECUTED
    old_assignee_id = issue.assignee_id
    issue.assignee_id = proposal.proposed_assignee_id
    issue.updated_at = datetime.utcnow()

    # Record issue audit history
    history = IssueHistory(
        issue_id=issue.id,
        field_name="assignee_id",
        old_value=str(old_assignee_id) if old_assignee_id else None,
        new_value=str(proposal.proposed_assignee_id),
        changed_by=f"Approved by {actor_id}",
        changed_at=datetime.utcnow(),
    )
    session.add(history)

    # Update proposal state
    proposal.status = "EXECUTED"
    proposal.updated_at = datetime.utcnow()

    # Append-only audit log row
    await record_audit_entry(
        session=session,
        entity_type="proposal",
        entity_id=str(proposal.id),
        action="approve",
        actor_id=actor_id,
        actor_role=actor_role,
        before_state={
            "status": "PENDING",
            "issue_key": issue.key,
            "assignee_id": old_assignee_id,
        },
        after_state={
            "status": "EXECUTED",
            "issue_key": issue.key,
            "assignee_id": proposal.proposed_assignee_id,
        },
        outcome="SUCCESS",
    )

    await session.commit()

    return {
        "proposal_id": proposal.id,
        "issue_key": issue.key,
        "new_assignee_id": issue.assignee_id,
        "status": "EXECUTED",
        "message": f"Proposal approved and issue {issue.key} reassigned successfully.",
    }


async def reject_proposal(
    session: AsyncSession,
    proposal_id: int,
    actor_id: str,
    actor_role: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Reject a pending reassignment proposal with role verification and audit log."""
    # 1. Role verification: only managers may reject proposals
    if actor_role.lower() != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only managers can reject proposals. Current role is '{actor_role}'.",
        )

    # 2. Fetch proposal
    prop_stmt = select(Proposal).where(Proposal.id == proposal_id)
    prop_res = await session.execute(prop_stmt)
    proposal = prop_res.scalars().first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found.",
        )

    if proposal.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject proposal: status is already '{proposal.status}'.",
        )

    # 3. Mark rejected
    proposal.status = "REJECTED"
    proposal.updated_at = datetime.utcnow()

    await record_audit_entry(
        session=session,
        entity_type="proposal",
        entity_id=str(proposal.id),
        action="reject",
        actor_id=actor_id,
        actor_role=actor_role,
        before_state={"status": "PENDING"},
        after_state={"status": "REJECTED", "comment": comment},
        outcome="REJECTED",
    )

    await session.commit()

    return {
        "proposal_id": proposal.id,
        "status": "REJECTED",
        "message": "Proposal rejected by manager.",
    }
