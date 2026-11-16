from datetime import datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (
    Developer,
    Incident,
    Issue,
    IssueDependency,
    IssueHistory,
    Sprint,
    Team,
)
from app.services.adapters.tracker_base import BaseTrackerAdapter


class DemoTrackerAdapter(BaseTrackerAdapter):
    """PostgreSQL-backed Jira-style issue tracker adapter for DevCore."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_sprint(self, sprint_id: int | None = None) -> dict[str, Any] | None:
        if sprint_id is not None:
            stmt = select(Sprint).where(Sprint.id == sprint_id)
        else:
            stmt = select(Sprint).where(Sprint.status == "ACTIVE")
        result = await self.session.execute(stmt)
        sprint = result.scalars().first()
        if not sprint:
            return None
        return {
            "id": sprint.id,
            "name": sprint.name,
            "status": sprint.status,
            "start_date": sprint.start_date.isoformat(),
            "end_date": sprint.end_date.isoformat(),
            "sprint_goal": sprint.sprint_goal,
            "total_days": sprint.total_days,
            "days_elapsed": sprint.days_elapsed,
        }

    async def list_sprints(self) -> list[dict[str, Any]]:
        stmt = select(Sprint).order_by(Sprint.id.asc())
        result = await self.session.execute(stmt)
        sprints = result.scalars().all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "sprint_goal": s.sprint_goal,
                "total_days": s.total_days,
                "days_elapsed": s.days_elapsed,
            }
            for s in sprints
        ]

    async def list_issues(
        self,
        sprint_id: int | None = None,
        status: str | None = None,
        assignee_id: int | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(Issue, Developer.name).outerjoin(
            Developer, Issue.assignee_id == Developer.id
        )
        if sprint_id is not None:
            stmt = stmt.where(Issue.sprint_id == sprint_id)
        if status is not None:
            stmt = stmt.where(Issue.status == status)
        if assignee_id is not None:
            stmt = stmt.where(Issue.assignee_id == assignee_id)
        stmt = stmt.order_by(Issue.id.asc())

        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "id": issue.id,
                "key": issue.key,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status,
                "story_points": issue.story_points,
                "priority": issue.priority,
                "sprint_id": issue.sprint_id,
                "assignee_id": issue.assignee_id,
                "assignee_name": dev_name or "Unassigned",
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "labels": issue.labels or [],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
            }
            for issue, dev_name in rows
        ]

    async def get_issue(self, issue_key: str) -> dict[str, Any] | None:
        stmt = (
            select(Issue, Developer.name)
            .outerjoin(Developer, Issue.assignee_id == Developer.id)
            .where(Issue.key == issue_key)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None
        issue, dev_name = row

        # Fetch history
        hist_stmt = (
            select(IssueHistory)
            .where(IssueHistory.issue_id == issue.id)
            .order_by(IssueHistory.changed_at.desc())
        )
        hist_res = await self.session.execute(hist_stmt)
        history = [
            {
                "id": h.id,
                "field_name": h.field_name,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at.isoformat(),
            }
            for h in hist_res.scalars().all()
        ]

        # Fetch dependencies
        blocked_by_stmt = select(IssueDependency.blocker_issue_key).where(
            IssueDependency.blocked_issue_key == issue_key
        )
        blocked_by_res = await self.session.execute(blocked_by_stmt)
        blocked_by = [r for r in blocked_by_res.scalars().all()]

        blocks_stmt = select(IssueDependency.blocked_issue_key).where(
            IssueDependency.blocker_issue_key == issue_key
        )
        blocks_res = await self.session.execute(blocks_stmt)
        blocks = [r for r in blocks_res.scalars().all()]

        return {
            "id": issue.id,
            "key": issue.key,
            "title": issue.title,
            "description": issue.description,
            "status": issue.status,
            "story_points": issue.story_points,
            "priority": issue.priority,
            "sprint_id": issue.sprint_id,
            "assignee_id": issue.assignee_id,
            "assignee_name": dev_name or "Unassigned",
            "due_date": issue.due_date.isoformat() if issue.due_date else None,
            "labels": issue.labels or [],
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "history": history,
            "blocked_by": blocked_by,
            "blocks": blocks,
        }

    async def get_issue_history(self, issue_key: str) -> list[dict[str, Any]]:
        stmt = (
            select(IssueHistory)
            .join(Issue, IssueHistory.issue_id == Issue.id)
            .where(Issue.key == issue_key)
            .order_by(IssueHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return [
            {
                "id": h.id,
                "field_name": h.field_name,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at.isoformat(),
            }
            for h in result.scalars().all()
        ]

    async def list_developers(self, team_id: int | None = None) -> list[dict[str, Any]]:
        stmt = select(Developer, Team.name).join(Team, Developer.team_id == Team.id)
        if team_id is not None:
            stmt = stmt.where(Developer.team_id == team_id)
        stmt = stmt.order_by(Developer.id.asc())

        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "id": dev.id,
                "name": dev.name,
                "email": dev.email,
                "role": dev.role,
                "team_id": dev.team_id,
                "team_name": team_name,
                "skills": dev.skills or [],
                "weekly_capacity_points": dev.weekly_capacity_points,
            }
            for dev, team_name in rows
        ]

    async def get_developer(self, developer_id: int) -> dict[str, Any] | None:
        stmt = (
            select(Developer, Team.name)
            .join(Team, Developer.team_id == Team.id)
            .where(Developer.id == developer_id)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None
        dev, team_name = row
        return {
            "id": dev.id,
            "name": dev.name,
            "email": dev.email,
            "role": dev.role,
            "team_id": dev.team_id,
            "team_name": team_name,
            "skills": dev.skills or [],
            "weekly_capacity_points": dev.weekly_capacity_points,
        }

    async def update_issue_assignee(self, issue_key: str, new_assignee_id: int) -> bool:
        stmt = select(Issue).where(Issue.key == issue_key)
        res = await self.session.execute(stmt)
        issue = res.scalars().first()
        if not issue:
            return False

        old_assignee_id = issue.assignee_id
        issue.assignee_id = new_assignee_id
        issue.updated_at = datetime.utcnow()

        # Log history
        history_entry = IssueHistory(
            issue_id=issue.id,
            field_name="assignee_id",
            old_value=str(old_assignee_id) if old_assignee_id else None,
            new_value=str(new_assignee_id),
            changed_by="SprintMate Reassignment Executor",
            changed_at=datetime.utcnow(),
        )
        self.session.add(history_entry)
        await self.session.commit()
        return True

    async def search_incidents(self, query: str) -> list[dict[str, Any]]:
        """Plain keyword search across past incident reports."""
        tokens = query.lower().split()
        conditions = []
        for token in tokens:
            if len(token) > 2:
                like_pattern = f"%{token}%"
                conditions.append(
                    or_(
                        Incident.title.ilike(like_pattern),
                        Incident.content.ilike(like_pattern),
                        Incident.service.ilike(like_pattern),
                    )
                )

        if conditions:
            stmt = select(Incident).where(or_(*conditions)).order_by(Incident.id.desc())
        else:
            stmt = select(Incident).order_by(Incident.id.desc())

        result = await self.session.execute(stmt)
        incidents = result.scalars().all()
        return [
            {
                "id": inc.id,
                "incident_number": inc.incident_number,
                "title": inc.title,
                "service": inc.service,
                "date": inc.date,
                "content": inc.content,
            }
            for inc in incidents
        ]
