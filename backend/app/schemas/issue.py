from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IssueHistoryRead(BaseModel):
    id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_by: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueDependencyRead(BaseModel):
    blocker_issue_key: str
    blocked_issue_key: str
    relationship_type: str = "blocks"

    model_config = ConfigDict(from_attributes=True)


class IssueBase(BaseModel):
    key: str
    title: str
    description: str
    status: str
    story_points: int
    priority: str
    sprint_id: int
    assignee_id: int | None
    due_date: datetime | None
    labels: list[str]


class IssueRead(IssueBase):
    id: int
    created_at: datetime
    updated_at: datetime
    assignee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class IssueDetail(IssueRead):
    history: list[IssueHistoryRead] = []
    blocked_by: list[str] = []
    blocks: list[str] = []
    linked_prs: list[dict] = []
