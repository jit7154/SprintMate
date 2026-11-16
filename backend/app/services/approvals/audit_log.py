from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AuditLog


async def record_audit_entry(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: str,
    actor_role: str,
    before_state: dict[str, Any] | None,
    after_state: dict[str, Any] | None,
    outcome: str,
) -> AuditLog:
    """Write an append-only audit log row for compliance and tracking."""
    log_entry = AuditLog(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        before_state=before_state,
        after_state=after_state,
        outcome=outcome,
        timestamp=datetime.utcnow(),
    )
    session.add(log_entry)
    await session.commit()
    await session.refresh(log_entry)
    return log_entry


async def list_audit_entries(
    session: AsyncSession,
    entity_type: str | None = None,
    outcome: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List recent audit log rows in reverse chronological order."""
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if outcome:
        stmt = stmt.where(AuditLog.outcome == outcome)

    result = await session.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": entry.id,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "action": entry.action,
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "before_state": entry.before_state,
            "after_state": entry.after_state,
            "outcome": entry.outcome,
            "timestamp": entry.timestamp.isoformat(),
        }
        for entry in logs
    ]
