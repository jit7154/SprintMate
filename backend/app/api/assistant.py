from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import run_investigation
from app.db import get_db
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.standup.builder import generate_standup_report

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query", response_model=AssistantQueryResponse)
async def query_assistant(
    request: AssistantQueryRequest,
    session: AsyncSession = Depends(get_db),
) -> AssistantQueryResponse:
    """Run multi-agent risk investigation via Supervisor and Investigator agents."""
    return await run_investigation(
        query=request.query,
        session=session,
        sprint_id=request.sprint_id,
    )


@router.post("/standup", response_model=dict[str, Any])
async def generate_standup(
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate daily standup report combining deterministic telemetry with an executive AI summary."""
    return await generate_standup_report(session)
