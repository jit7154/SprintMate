from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.audit import AuditLogRead
from app.services.approvals.audit_log import list_audit_entries

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
async def get_audit_trail(
    entity_type: str | None = Query(None, alias="entity_type"),
    outcome: str | None = Query(None, alias="outcome"),
    limit: int = Query(100, alias="limit"),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve immutable audit log records with before/after state snapshots."""
    return await list_audit_entries(
        session=session,
        entity_type=entity_type,
        outcome=outcome,
        limit=limit,
    )
