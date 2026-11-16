from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.adapters import get_tracker_adapter, get_vcs_adapter
from app.services.risk.scoring import SprintRiskEvaluation, evaluate_sprint_risk

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.get("", response_model=list[dict[str, Any]])
async def list_sprints(
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all sprints in chronological order."""
    tracker = get_tracker_adapter(session)
    return await tracker.list_sprints()


@router.get("/active", response_model=dict[str, Any])
async def get_active_sprint(
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get active sprint summary and real-time deterministic risk evaluation."""
    tracker = get_tracker_adapter(session)
    vcs = get_vcs_adapter(session)

    sprint = await tracker.get_sprint()
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active sprint found.",
        )

    issues = await tracker.list_issues(sprint_id=sprint["id"])
    prs = await vcs.list_pull_requests()
    devs = await tracker.list_developers()

    # Hydrate each issue with full details (dependencies & history) for accurate risk checking
    detailed_issues = []
    for issue in issues:
        det = await tracker.get_issue(issue["key"])
        detailed_issues.append(det or issue)

    risk_eval = evaluate_sprint_risk(sprint, detailed_issues, prs, devs)

    return {
        "sprint": sprint,
        "risk_evaluation": risk_eval.model_dump(),
    }


@router.get("/{sprint_id}", response_model=dict[str, Any])
async def get_sprint_by_id(
    sprint_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get single sprint by id."""
    tracker = get_tracker_adapter(session)
    sprint = await tracker.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found.",
        )
    return sprint


@router.get("/{sprint_id}/issues", response_model=list[dict[str, Any]])
async def get_sprint_issues(
    sprint_id: int,
    status_filter: str | None = Query(None, alias="status"),
    assignee_id: int | None = Query(None, alias="assignee_id"),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List issues belonging to a sprint with optional status or assignee filter."""
    tracker = get_tracker_adapter(session)
    return await tracker.list_issues(
        sprint_id=sprint_id,
        status=status_filter,
        assignee_id=assignee_id,
    )


@router.get("/{sprint_id}/risk", response_model=SprintRiskEvaluation)
async def get_sprint_risk(
    sprint_id: int,
    session: AsyncSession = Depends(get_db),
) -> SprintRiskEvaluation:
    """Compute and return deterministic risk evaluation for a sprint."""
    tracker = get_tracker_adapter(session)
    vcs = get_vcs_adapter(session)

    sprint = await tracker.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found.",
        )

    issues = await tracker.list_issues(sprint_id=sprint_id)
    prs = await vcs.list_pull_requests()
    devs = await tracker.list_developers()

    detailed_issues = []
    for issue in issues:
        det = await tracker.get_issue(issue["key"])
        detailed_issues.append(det or issue)

    return evaluate_sprint_risk(sprint, detailed_issues, prs, devs)


@router.get("/{sprint_id}/burndown", response_model=list[dict[str, Any]])
async def get_sprint_burndown(
    sprint_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Generate daily ideal vs actual burndown series for Recharts."""
    tracker = get_tracker_adapter(session)
    sprint = await tracker.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found.",
        )

    issues = await tracker.list_issues(sprint_id=sprint_id)
    total_points = sum(i.get("story_points", 0) for i in issues)
    completed_points = sum(
        i.get("story_points", 0)
        for i in issues
        if i.get("status") in {"DONE", "COMPLETED"}
    )
    total_days = sprint.get("total_days", 10)
    days_elapsed = sprint.get("days_elapsed", 0)

    # Burndown curve calculation
    burndown = []
    ideal_step = total_points / max(total_days, 1)

    # Seed realistic daily burndown progression
    for day in range(total_days + 1):
        ideal_remaining = max(0, round(total_points - (day * ideal_step), 1))
        actual_remaining = None

        if day <= days_elapsed:
            # Simulate historical day-by-day burn down to current completed points
            if day == 0:
                actual_remaining = total_points
            elif day == days_elapsed:
                actual_remaining = total_points - completed_points
            else:
                progress_fraction = (day / days_elapsed) ** 1.3
                burned = int(completed_points * progress_fraction)
                actual_remaining = total_points - burned

        burndown.append(
            {
                "day": f"Day {day}",
                "day_number": day,
                "ideal": ideal_remaining,
                "actual": actual_remaining,
            }
        )

    return burndown
