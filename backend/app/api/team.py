from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.adapters import get_tracker_adapter
from app.services.risk.workload import calculate_developer_workloads

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/developers", response_model=list[dict[str, Any]])
async def list_team_developers(
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all developers with active sprint workload, point capacity, and skills."""
    tracker = get_tracker_adapter(session)
    devs = await tracker.list_developers()

    sprint = await tracker.get_sprint()
    if sprint:
        issues = await tracker.list_issues(sprint_id=sprint["id"])
    else:
        issues = []

    workloads = calculate_developer_workloads(devs, issues)
    return workloads
