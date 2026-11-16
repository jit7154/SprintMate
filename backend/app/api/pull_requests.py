from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.adapters import get_vcs_adapter

router = APIRouter(prefix="/pull-requests", tags=["pull_requests"])


@router.get("", response_model=list[dict[str, Any]])
async def list_pull_requests(
    issue_key: str | None = Query(None, alias="issue_key"),
    status_filter: str | None = Query(None, alias="status"),
    stuck_only: bool = Query(False, alias="stuck_only"),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List pull requests with optional stuck flag, status, or issue key filter."""
    vcs = get_vcs_adapter(session)
    prs = await vcs.list_pull_requests(
        issue_key=issue_key,
        status=status_filter,
    )
    if stuck_only:
        prs = [pr for pr in prs if pr.get("is_stuck")]
    return prs


@router.get("/{pr_number}", response_model=dict[str, Any])
async def get_pull_request(
    pr_number: int,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get single pull request details with CI run history."""
    vcs = get_vcs_adapter(session)
    pr = await vcs.get_pull_request(pr_number)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pull request #{pr_number} not found.",
        )
    return pr
