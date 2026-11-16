from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import UserContext, get_current_user, require_role
from app.db import get_db
from app.schemas.proposal import ProposalAction, ProposalCreate, ProposalRead
from app.services.approvals.executor import approve_proposal, reject_proposal
from app.services.approvals.proposals import create_proposal_entry, list_proposals

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("", response_model=list[ProposalRead])
async def get_all_proposals(
    status_filter: str | None = Query(None, alias="status"),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List reassignment proposals with issue context, skill matches, and workload deltas."""
    return await list_proposals(session, status=status_filter)


@router.post("", response_model=dict[str, Any])
async def create_new_proposal(
    payload: ProposalCreate,
    current_user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new reassignment proposal in PENDING status."""
    return await create_proposal_entry(
        session=session,
        issue_key=payload.issue_key,
        proposed_assignee_id=payload.proposed_assignee_id,
        reason=payload.reason,
        created_by=payload.created_by,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
    )


@router.post("/{proposal_id}/approve", response_model=dict[str, Any])
async def approve_reassignment(
    proposal_id: int,
    current_user: UserContext = Depends(require_role("manager")),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Approve a proposal. Requires manager role, verifies state, and updates the issue."""
    return await approve_proposal(
        session=session,
        proposal_id=proposal_id,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
    )


@router.post("/{proposal_id}/reject", response_model=dict[str, Any])
async def reject_reassignment(
    proposal_id: int,
    action: ProposalAction | None = None,
    current_user: UserContext = Depends(require_role("manager")),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reject a proposal. Requires manager role and writes an audit log."""
    comment = action.comment if action else None
    return await reject_proposal(
        session=session,
        proposal_id=proposal_id,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        comment=comment,
    )
