from datetime import datetime, timezone
from typing import Any

from google import genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.adapters import get_tracker_adapter, get_vcs_adapter
from app.services.risk.rules import (
    check_blocked_issues,
    check_developer_overload,
    check_overdue_issues,
    check_pr_failing_ci,
    check_pr_no_review,
)
from app.services.risk.workload import calculate_developer_workloads


async def build_standup_data(
    session: AsyncSession,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Deterministically compile standup sections from database telemetry."""
    ref_time = now or datetime.now(timezone.utc).replace(tzinfo=None)
    tracker = get_tracker_adapter(session)
    vcs = get_vcs_adapter(session)

    sprint = await tracker.get_sprint()
    if not sprint:
        return {"error": "No active sprint found for standup report."}

    issues = await tracker.list_issues(sprint_id=sprint["id"])
    prs = await vcs.list_pull_requests()
    devs = await tracker.list_developers()

    # Hydrate issues with dependencies
    detailed_issues = []
    for issue in issues:
        det = await tracker.get_issue(issue["key"])
        detailed_issues.append(det or issue)

    completed = [
        {
            "key": i["key"],
            "title": i["title"],
            "assignee": i.get("assignee_name"),
            "points": i.get("story_points"),
        }
        for i in detailed_issues
        if i.get("status") in {"DONE", "COMPLETED"}
    ]

    in_progress = [
        {
            "key": i["key"],
            "title": i["title"],
            "assignee": i.get("assignee_name"),
            "points": i.get("story_points"),
        }
        for i in detailed_issues
        if i.get("status") == "IN_PROGRESS"
    ]

    blockers = [
        {
            "key": i["key"],
            "title": i["title"],
            "assignee": i.get("assignee_name"),
            "blocked_by": i.get("blocked_by", []),
        }
        for i in detailed_issues
        if i.get("status") == "BLOCKED"
    ]

    # Delayed (overdue)
    delayed_findings = check_overdue_issues(detailed_issues, now=ref_time)
    delayed = [
        {
            "key": f.metadata["issue_key"],
            "reason": f.reason,
            "days_overdue": f.metadata.get("days_overdue", 0),
        }
        for f in delayed_findings
    ]

    # Pending reviews
    pending_reviews = [
        {
            "pr_number": pr["pr_number"],
            "title": pr["title"],
            "author": pr.get("author_name"),
            "age_days": pr.get("age_days", 0),
            "issue_key": pr.get("issue_key"),
        }
        for pr in prs
        if pr.get("status") == "OPEN" and pr.get("review_status") == "PENDING_REVIEW"
    ]

    # Discussion points from risk rules
    discussion_points = []
    workloads = calculate_developer_workloads(devs, detailed_issues)
    for over in check_developer_overload(workloads):
        discussion_points.append(over.reason)
    for ci_fail in check_pr_failing_ci(prs):
        discussion_points.append(ci_fail.reason)
    for stale_pr in check_pr_no_review(prs):
        discussion_points.append(stale_pr.reason)
    for blk in check_blocked_issues(detailed_issues, now=ref_time):
        discussion_points.append(blk.reason)

    return {
        "sprint_name": sprint["name"],
        "sprint_goal": sprint["sprint_goal"],
        "days_elapsed": sprint["days_elapsed"],
        "total_days": sprint["total_days"],
        "completed": completed,
        "in_progress": in_progress,
        "blockers": blockers,
        "delayed": delayed,
        "pending_reviews": pending_reviews,
        "discussion_points": discussion_points[:6],
    }


async def generate_standup_report(
    session: AsyncSession,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Generate engineering manager daily standup report combining deterministic data with LLM summary."""
    data = await build_standup_data(session, now=now)
    if "error" in data:
        return data

    prompt = f"""
You are the DevCore standup summarizer. Below is the ground-truth engineering telemetry for today's standup:

Sprint: {data["sprint_name"]} (Day {data["days_elapsed"]} of {data["total_days"]})
Sprint Goal: {data["sprint_goal"]}
Completed Work ({len(data["completed"])} items): {", ".join(i["key"] for i in data["completed"][:5])}
Active In Progress ({len(data["in_progress"])} items): {", ".join(i["key"] for i in data["in_progress"][:5])}
Blockers: {data["blockers"]}
Delayed/Overdue: {data["delayed"]}
Pending PR Reviews: {data["pending_reviews"][:4]}
Key Discussion Points: {data["discussion_points"][:4]}

Write a concise, professional 2-paragraph morning standup executive briefing for the Engineering Manager.
Include specific issue keys (e.g. PAY-142, PAY-139), PR numbers (e.g. PR #204), and action items.
Do not hallucinate any issues or facts not listed above.
"""

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        summary = resp.text.strip()
    except Exception:
        summary = (
            f"Daily Standup Briefing: {data['sprint_name']} is at day {data['days_elapsed']}/{data['total_days']}. "
            f"There are {len(data['blockers'])} blockers and {len(data['delayed'])} delayed issues requiring team discussion."
        )

    data["summary"] = summary
    return data
