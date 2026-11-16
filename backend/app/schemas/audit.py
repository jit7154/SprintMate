from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_role: str
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    outcome: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
