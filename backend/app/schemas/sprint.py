from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SprintBase(BaseModel):
    name: str
    status: str
    start_date: datetime
    end_date: datetime
    sprint_goal: str
    total_days: int
    days_elapsed: int


class SprintRead(SprintBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
