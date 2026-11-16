#!/usr/bin/env python3
"""Loads DevCore seed data into PostgreSQL via SQLAlchemy async session."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db import (
    AuditLog,
    Base,
    CiRun,
    Developer,
    Incident,
    Issue,
    IssueDependency,
    IssueHistory,
    Proposal,
    PullRequest,
    Sprint,
    Team,
    UsageRecord,
    async_session_maker,
    engine,
)


def parse_dt(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str)


def load_json_file(seed_file: Path) -> dict:
    if not seed_file.exists():
        print(f"Error: {seed_file} not found. Run generate_seed.py first.")
        sys.exit(1)
    with open(seed_file, "r", encoding="utf-8") as f:
        return json.load(f)


async def load_seed_data(data: dict):
    print("Creating tables if not exists...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Populating database...")
    async with async_session_maker() as session:
        # Clear existing data in reverse dependency order
        for model in [
            UsageRecord,
            AuditLog,
            Proposal,
            CiRun,
            PullRequest,
            IssueHistory,
            IssueDependency,
            Issue,
            Sprint,
            Developer,
            Team,
            Incident,
        ]:
            await session.execute(model.__table__.delete())
        await session.commit()

        # 1. Teams
        for t in data["teams"]:
            session.add(Team(id=t["id"], name=t["name"], mission=t["mission"]))
        await session.flush()

        # 2. Developers
        for d in data["developers"]:
            session.add(
                Developer(
                    id=d["id"],
                    name=d["name"],
                    email=d["email"],
                    role=d["role"],
                    team_id=d["team_id"],
                    skills=d["skills"],
                    weekly_capacity_points=d["weekly_capacity_points"],
                )
            )
        await session.flush()

        # 3. Sprints
        for s in data["sprints"]:
            session.add(
                Sprint(
                    id=s["id"],
                    name=s["name"],
                    status=s["status"],
                    start_date=parse_dt(s["start_date"]),
                    end_date=parse_dt(s["end_date"]),
                    sprint_goal=s["sprint_goal"],
                    total_days=s["total_days"],
                    days_elapsed=s["days_elapsed"],
                )
            )
        await session.flush()

        # 4. Issues
        for i in data["issues"]:
            session.add(
                Issue(
                    id=i["id"],
                    key=i["key"],
                    title=i["title"],
                    description=i["description"],
                    status=i["status"],
                    story_points=i["story_points"],
                    priority=i["priority"],
                    sprint_id=i["sprint_id"],
                    assignee_id=i["assignee_id"],
                    due_date=parse_dt(i["due_date"]),
                    labels=i["labels"],
                    created_at=parse_dt(i["created_at"]),
                    updated_at=parse_dt(i["updated_at"]),
                )
            )
        await session.flush()

        # 5. Dependencies
        for dep in data["dependencies"]:
            session.add(
                IssueDependency(
                    id=dep["id"],
                    blocker_issue_key=dep["blocker_issue_key"],
                    blocked_issue_key=dep["blocked_issue_key"],
                    relationship_type=dep["relationship_type"],
                )
            )
        await session.flush()

        # 6. Issue History
        for h in data["issue_history"]:
            session.add(
                IssueHistory(
                    id=h["id"],
                    issue_id=h["issue_id"],
                    field_name=h["field_name"],
                    old_value=h["old_value"],
                    new_value=h["new_value"],
                    changed_by=h["changed_by"],
                    changed_at=parse_dt(h["changed_at"]),
                )
            )
        await session.flush()

        # 7. Pull Requests
        for pr in data["pull_requests"]:
            session.add(
                PullRequest(
                    id=pr["id"],
                    pr_number=pr["pr_number"],
                    repo=pr["repo"],
                    title=pr["title"],
                    branch=pr["branch"],
                    status=pr["status"],
                    review_status=pr["review_status"],
                    issue_key=pr["issue_key"],
                    author_id=pr["author_id"],
                    requested_reviewers=pr["requested_reviewers"],
                    pr_created_at=parse_dt(pr["pr_created_at"]),
                    pr_updated_at=parse_dt(pr["pr_updated_at"]),
                )
            )
        await session.flush()

        # 8. CI Runs
        for ci in data["ci_runs"]:
            session.add(
                CiRun(
                    id=ci["id"],
                    pr_id=ci["pr_id"],
                    commit_hash=ci["commit_hash"],
                    status=ci["status"],
                    failed_step=ci["failed_step"],
                    run_duration_seconds=ci["run_duration_seconds"],
                    run_completed_at=parse_dt(ci["run_completed_at"]),
                )
            )
        await session.flush()

        # 9. Incidents
        for inc in data["incidents"]:
            session.add(
                Incident(
                    id=inc["id"],
                    incident_number=inc["incident_number"],
                    title=inc["title"],
                    service=inc["service"],
                    date=inc["date"],
                    content=inc["content"],
                )
            )

        await session.commit()

    print("Seed data successfully loaded into PostgreSQL.")


if __name__ == "__main__":
    seed_path = ROOT_DIR / "data" / "seed" / "devcore.json"
    data = load_json_file(seed_path)
    asyncio.run(load_seed_data(data))
