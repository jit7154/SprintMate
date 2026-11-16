from pydantic import BaseModel, ConfigDict


class DeveloperRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    team_id: int
    team_name: str | None = None
    skills: list[str]
    weekly_capacity_points: int
    assigned_points: int = 0
    assigned_issues_count: int = 0
    is_overloaded: bool = False

    model_config = ConfigDict(from_attributes=True)


class TeamRead(BaseModel):
    id: int
    name: str
    mission: str
    developers: list[DeveloperRead] = []

    model_config = ConfigDict(from_attributes=True)
