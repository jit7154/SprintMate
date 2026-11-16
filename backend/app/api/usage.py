from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.observability.usage_logger import get_usage_summary

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=dict[str, Any])
async def get_usage_metrics(
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve system-wide agent usage metrics, latencies, tokens, costs, and historical query logs."""
    return await get_usage_summary(session)
