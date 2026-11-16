from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProposalCreate(BaseModel):
    issue_key: str
    proposed_assignee_id: int
    reason: str
    created_by: str = "InvestigatorAgent"


class ProposalRead(BaseModel):
    id: int
    issue_key: str
    issue_title: str | None = None
    current_assignee_id: int | None
    current_assignee_name: str | None = None
    proposed_assignee_id: int
    proposed_assignee_name: str | None = None
    reason: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    skills_comparison: dict | None = None
    workload_comparison: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class ProposalAction(BaseModel):
    comment: str | None = None
