from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import CiRun, Developer, PullRequest
from app.services.adapters.tracker_base import BaseVcsAdapter


class GithubDemoAdapter(BaseVcsAdapter):
    """PostgreSQL-backed GitHub demo adapter for DevCore."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_pull_requests(
        self,
        issue_key: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(PullRequest, Developer.name)
            .join(Developer, PullRequest.author_id == Developer.id)
            .order_by(PullRequest.pr_created_at.desc())
        )
        if issue_key:
            stmt = stmt.where(PullRequest.issue_key == issue_key)
        if status:
            stmt = stmt.where(PullRequest.status == status)

        result = await self.session.execute(stmt)
        rows = result.all()

        now = datetime.utcnow()
        prs_output = []

        for pr, author_name in rows:
            # Fetch latest CI run
            ci_stmt = (
                select(CiRun)
                .where(CiRun.pr_id == pr.id)
                .order_by(CiRun.run_completed_at.desc())
            )
            ci_res = await self.session.execute(ci_stmt)
            ci_runs = ci_res.scalars().all()
            latest_ci = ci_runs[0].status if ci_runs else None

            age_days = (now - pr.pr_created_at).days
            is_stuck = pr.status == "OPEN" and (
                (pr.review_status == "PENDING_REVIEW" and age_days >= 2)
                or (latest_ci == "FAILURE")
            )

            prs_output.append(
                {
                    "id": pr.id,
                    "pr_number": pr.pr_number,
                    "repo": pr.repo,
                    "title": pr.title,
                    "branch": pr.branch,
                    "status": pr.status,
                    "review_status": pr.review_status,
                    "issue_key": pr.issue_key,
                    "author_id": pr.author_id,
                    "author_name": author_name,
                    "requested_reviewers": pr.requested_reviewers or [],
                    "pr_created_at": pr.pr_created_at.isoformat(),
                    "pr_updated_at": pr.pr_updated_at.isoformat(),
                    "age_days": age_days,
                    "is_stuck": is_stuck,
                    "latest_ci_status": latest_ci,
                    "ci_runs": [
                        {
                            "id": c.id,
                            "pr_id": c.pr_id,
                            "commit_hash": c.commit_hash,
                            "status": c.status,
                            "failed_step": c.failed_step,
                            "run_duration_seconds": c.run_duration_seconds,
                            "run_completed_at": c.run_completed_at.isoformat(),
                        }
                        for c in ci_runs
                    ],
                }
            )

        return prs_output

    async def get_pull_request(self, pr_number: int) -> dict[str, Any] | None:
        stmt = (
            select(PullRequest, Developer.name)
            .join(Developer, PullRequest.author_id == Developer.id)
            .where(PullRequest.pr_number == pr_number)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None
        pr, author_name = row

        ci_stmt = (
            select(CiRun)
            .where(CiRun.pr_id == pr.id)
            .order_by(CiRun.run_completed_at.desc())
        )
        ci_res = await self.session.execute(ci_stmt)
        ci_runs = ci_res.scalars().all()
        latest_ci = ci_runs[0].status if ci_runs else None

        age_days = (datetime.utcnow() - pr.pr_created_at).days
        is_stuck = pr.status == "OPEN" and (
            (pr.review_status == "PENDING_REVIEW" and age_days >= 2)
            or (latest_ci == "FAILURE")
        )

        return {
            "id": pr.id,
            "pr_number": pr.pr_number,
            "repo": pr.repo,
            "title": pr.title,
            "branch": pr.branch,
            "status": pr.status,
            "review_status": pr.review_status,
            "issue_key": pr.issue_key,
            "author_id": pr.author_id,
            "author_name": author_name,
            "requested_reviewers": pr.requested_reviewers or [],
            "pr_created_at": pr.pr_created_at.isoformat(),
            "pr_updated_at": pr.pr_updated_at.isoformat(),
            "age_days": age_days,
            "is_stuck": is_stuck,
            "latest_ci_status": latest_ci,
            "ci_runs": [
                {
                    "id": c.id,
                    "pr_id": c.pr_id,
                    "commit_hash": c.commit_hash,
                    "status": c.status,
                    "failed_step": c.failed_step,
                    "run_duration_seconds": c.run_duration_seconds,
                    "run_completed_at": c.run_completed_at.isoformat(),
                }
                for c in ci_runs
            ],
        }

    async def get_ci_status(self, pr_number: int) -> dict[str, Any] | None:
        stmt = (
            select(CiRun)
            .join(PullRequest, CiRun.pr_id == PullRequest.id)
            .where(PullRequest.pr_number == pr_number)
            .order_by(CiRun.run_completed_at.desc())
        )
        result = await self.session.execute(stmt)
        latest_run = result.scalars().first()
        if not latest_run:
            return None

        return {
            "pr_number": pr_number,
            "commit_hash": latest_run.commit_hash,
            "status": latest_run.status,
            "failed_step": latest_run.failed_step,
            "run_duration_seconds": latest_run.run_duration_seconds,
            "run_completed_at": latest_run.run_completed_at.isoformat(),
        }
