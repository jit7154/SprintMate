from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CiRunRead(BaseModel):
    id: int
    pr_id: int
    commit_hash: str
    status: str
    failed_step: str | None
    run_duration_seconds: int
    run_completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PullRequestRead(BaseModel):
    id: int
    pr_number: int
    repo: str
    title: str
    branch: str
    status: str
    review_status: str
    issue_key: str | None
    author_id: int
    author_name: str | None = None
    requested_reviewers: list[int]
    pr_created_at: datetime
    pr_updated_at: datetime
    age_days: int = 0
    is_stuck: bool = False
    latest_ci_status: str | None = None
    ci_runs: list[CiRunRead] = []

    model_config = ConfigDict(from_attributes=True)
