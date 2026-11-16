from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.config import settings


class RiskFinding(BaseModel):
    rule_id: str
    rule_name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    weight: int  # Risk points added (e.g. LOW: 5, MEDIUM: 15, HIGH: 25, CRITICAL: 40)
    affected_keys: list[str]
    reason: str
    metadata: dict[str, Any] = {}


def check_blocked_issues(
    issues: list[dict[str, Any]],
    now: datetime | None = None,
    threshold_days: int | None = None,
) -> list[RiskFinding]:
    """Flag issues that have remained in BLOCKED status beyond the threshold."""
    ref_time = now or datetime.now(timezone.utc).replace(tzinfo=None)
    threshold = (
        threshold_days
        if threshold_days is not None
        else settings.risk_blocked_days_threshold
    )
    findings = []

    for issue in issues:
        if issue.get("status") != "BLOCKED":
            continue

        # Calculate how long the issue has been blocked from history or updated_at
        blocked_since = None
        for h in issue.get("history", []):
            if h.get("field_name") == "status" and h.get("new_value") == "BLOCKED":
                blocked_since = datetime.fromisoformat(h["changed_at"])
                break

        if not blocked_since and issue.get("updated_at"):
            blocked_since = datetime.fromisoformat(issue["updated_at"])

        if not blocked_since:
            continue

        days_blocked = (ref_time - blocked_since).days
        if days_blocked >= threshold:
            points = issue.get("story_points", 0)
            is_critical = points >= 5 or issue.get("priority") in {"HIGH", "CRITICAL"}
            severity = "CRITICAL" if is_critical else "HIGH"
            weight = 35 if severity == "CRITICAL" else 25

            findings.append(
                RiskFinding(
                    rule_id="RULE_BLOCKED_ISSUE",
                    rule_name="Long-standing Blocked Issue",
                    severity=severity,
                    weight=weight,
                    affected_keys=[issue["key"]],
                    reason=(
                        f"Issue {issue['key']} has been blocked for {days_blocked} days "
                        f"(threshold: {threshold} days, {points} story points)."
                    ),
                    metadata={
                        "issue_key": issue["key"],
                        "days_blocked": days_blocked,
                        "threshold_days": threshold,
                        "story_points": points,
                        "blocked_by": issue.get("blocked_by", []),
                    },
                )
            )

    return findings


def check_overdue_issues(
    issues: list[dict[str, Any]],
    now: datetime | None = None,
    buffer_days: int | None = None,
) -> list[RiskFinding]:
    """Flag issues that are either overdue or due within buffer days and incomplete."""
    ref_time = now or datetime.now(timezone.utc).replace(tzinfo=None)
    buffer = (
        buffer_days if buffer_days is not None else settings.risk_overdue_buffer_days
    )
    findings = []

    for issue in issues:
        status = issue.get("status")
        if status in {"DONE", "COMPLETED"}:
            continue

        due_date_str = issue.get("due_date")
        if not due_date_str:
            continue

        due_date = datetime.fromisoformat(due_date_str)
        points = issue.get("story_points", 0)

        # Overdue
        if due_date < ref_time:
            days_overdue = (ref_time - due_date).days
            findings.append(
                RiskFinding(
                    rule_id="RULE_OVERDUE_ISSUE",
                    rule_name="Overdue Unfinished Issue",
                    severity="CRITICAL",
                    weight=40,
                    affected_keys=[issue["key"]],
                    reason=(
                        f"Issue {issue['key']} is overdue by {days_overdue} days "
                        f"with status {status} ({points} story points)."
                    ),
                    metadata={
                        "issue_key": issue["key"],
                        "days_overdue": days_overdue,
                        "status": status,
                        "story_points": points,
                    },
                )
            )
        # Due soon and not even in review
        elif (due_date - ref_time).days <= buffer and status not in {
            "IN_REVIEW",
            "DONE",
        }:
            days_until_due = (due_date - ref_time).days
            findings.append(
                RiskFinding(
                    rule_id="RULE_DUE_SOON_NOT_IN_REVIEW",
                    rule_name="Approaching Due Date Not In Review",
                    severity="HIGH",
                    weight=20,
                    affected_keys=[issue["key"]],
                    reason=(
                        f"Issue {issue['key']} is due in {days_until_due} days "
                        f"and is still {status} ({points} story points)."
                    ),
                    metadata={
                        "issue_key": issue["key"],
                        "days_until_due": days_until_due,
                        "status": status,
                        "story_points": points,
                    },
                )
            )

    return findings


def check_pr_no_review(
    pull_requests: list[dict[str, Any]],
    threshold_days: int | None = None,
) -> list[RiskFinding]:
    """Flag open pull requests awaiting review for longer than threshold days."""
    threshold = (
        threshold_days
        if threshold_days is not None
        else settings.risk_pr_stale_days_threshold
    )
    findings = []

    for pr in pull_requests:
        if pr.get("status") != "OPEN":
            continue

        if pr.get("review_status") == "PENDING_REVIEW":
            age_days = pr.get("age_days", 0)
            if age_days >= threshold:
                severity = "HIGH" if age_days >= 4 else "MEDIUM"
                weight = 25 if severity == "HIGH" else 15
                affected = [f"PR #{pr['pr_number']}"]
                if pr.get("issue_key"):
                    affected.append(pr["issue_key"])

                findings.append(
                    RiskFinding(
                        rule_id="RULE_PR_NO_REVIEW",
                        rule_name="Pull Request Awaiting Review Stagnant",
                        severity=severity,
                        weight=weight,
                        affected_keys=affected,
                        reason=(
                            f"PR #{pr['pr_number']} ({pr.get('title', '')}) has been waiting "
                            f"for review for {age_days} days (threshold: {threshold} days)."
                        ),
                        metadata={
                            "pr_number": pr["pr_number"],
                            "age_days": age_days,
                            "issue_key": pr.get("issue_key"),
                            "author_name": pr.get("author_name"),
                        },
                    )
                )

    return findings


def check_pr_failing_ci(
    pull_requests: list[dict[str, Any]],
) -> list[RiskFinding]:
    """Flag open pull requests blocked by failing CI builds."""
    findings = []

    for pr in pull_requests:
        if pr.get("status") != "OPEN":
            continue

        if pr.get("latest_ci_status") == "FAILURE":
            # Identify failed step
            failed_step = "unknown"
            for ci in pr.get("ci_runs", []):
                if ci.get("status") == "FAILURE":
                    failed_step = ci.get("failed_step", "unknown")
                    break

            affected = [f"PR #{pr['pr_number']}"]
            if pr.get("issue_key"):
                affected.append(pr["issue_key"])

            findings.append(
                RiskFinding(
                    rule_id="RULE_PR_FAILING_CI",
                    rule_name="Pull Request CI Build Failure",
                    severity="HIGH",
                    weight=30,
                    affected_keys=affected,
                    reason=(
                        f"PR #{pr['pr_number']} ({pr.get('title', '')}) has failing CI "
                        f"tests in step '{failed_step}'."
                    ),
                    metadata={
                        "pr_number": pr["pr_number"],
                        "failed_step": failed_step,
                        "issue_key": pr.get("issue_key"),
                        "author_name": pr.get("author_name"),
                    },
                )
            )

    return findings


def check_developer_overload(
    workload_summary: list[dict[str, Any]],
) -> list[RiskFinding]:
    """Flag developers whose assigned story points exceed their weekly capacity."""
    findings = []

    for dev in workload_summary:
        if dev.get("is_overloaded"):
            assigned = dev.get("assigned_points", 0)
            capacity = dev.get("weekly_capacity_points", 1)
            ratio = assigned / max(capacity, 1)
            severity = "CRITICAL" if ratio >= 1.5 else "HIGH"
            weight = 35 if severity == "CRITICAL" else 20
            keys = dev.get("assigned_issue_keys", [])

            findings.append(
                RiskFinding(
                    rule_id="RULE_DEVELOPER_OVERLOAD",
                    rule_name="Developer Capacity Overloaded",
                    severity=severity,
                    weight=weight,
                    affected_keys=[dev["name"], *keys],
                    reason=(
                        f"Developer {dev['name']} is assigned {assigned} story points "
                        f"exceeding capacity of {capacity} points ({ratio:.0%} load, {len(keys)} issues: {', '.join(keys)})."
                    ),
                    metadata={
                        "developer_id": dev["id"],
                        "developer_name": dev["name"],
                        "assigned_points": assigned,
                        "capacity_points": capacity,
                        "utilization_ratio": ratio,
                        "assigned_issue_keys": keys,
                    },
                )
            )

    return findings


def check_dependency_chains(
    issues: list[dict[str, Any]],
) -> list[RiskFinding]:
    """Detect unfinished dependency chains threatening critical sprint deliverables."""
    findings = []
    issues_by_key = {issue["key"]: issue for issue in issues}

    for issue in issues:
        blocked_by = issue.get("blocked_by", [])
        if not blocked_by:
            continue

        for blocker_key in blocked_by:
            blocker = issues_by_key.get(blocker_key)
            if not blocker:
                continue

            blocker_status = blocker.get("status")
            if blocker_status not in {"DONE", "COMPLETED"}:
                # Check if this blocker is itself blocked (chain of depth >= 2)
                second_order_blockers = blocker.get("blocked_by", [])
                chain = [issue["key"], blocker_key]
                if second_order_blockers:
                    chain.extend(second_order_blockers)

                is_sprint_goal = (
                    "sprint-goal" in issue.get("labels", [])
                    or "Sprint Goal" in issue.get("title", "")
                    or issue.get("priority") == "CRITICAL"
                )
                severity = "CRITICAL" if is_sprint_goal else "HIGH"
                weight = 40 if severity == "CRITICAL" else 20

                findings.append(
                    RiskFinding(
                        rule_id="RULE_DEPENDENCY_CHAIN",
                        rule_name="Unresolved Dependency Threatening Sprint Deliverable",
                        severity=severity,
                        weight=weight,
                        affected_keys=chain,
                        reason=(
                            f"Unresolved dependency chain threatens {issue['key']} ({issue.get('title', '')}): "
                            f"blocked by {blocker_key} ({blocker_status})"
                            + (
                                f", which is further blocked by {', '.join(second_order_blockers)}"
                                if second_order_blockers
                                else ""
                            )
                            + "."
                        ),
                        metadata={
                            "target_issue": issue["key"],
                            "chain": chain,
                            "is_sprint_goal": is_sprint_goal,
                            "root_blocker": chain[-1],
                        },
                    )
                )

    return findings


def check_completion_lag(
    sprint: dict[str, Any],
    issues: list[dict[str, Any]],
    threshold_lag: float | None = None,
) -> list[RiskFinding]:
    """Compare completed points percentage against sprint time elapsed percentage."""
    findings = []
    total_days = sprint.get("total_days", 10)
    days_elapsed = sprint.get("days_elapsed", 0)
    if total_days <= 0 or days_elapsed <= 0:
        return findings

    time_ratio = min(days_elapsed / total_days, 1.0)
    threshold = (
        threshold_lag
        if threshold_lag is not None
        else settings.risk_completion_lag_threshold
    )

    total_points = sum(i.get("story_points", 0) for i in issues)
    if total_points == 0:
        return findings

    completed_points = sum(
        i.get("story_points", 0)
        for i in issues
        if i.get("status") in {"DONE", "COMPLETED"}
    )
    work_ratio = completed_points / total_points

    lag = time_ratio - work_ratio
    if lag > threshold:
        severity = "HIGH" if lag > 0.35 else "MEDIUM"
        weight = 30 if severity == "HIGH" else 15

        findings.append(
            RiskFinding(
                rule_id="RULE_COMPLETION_LAG",
                rule_name="Sprint Velocity Schedule Lag",
                severity=severity,
                weight=weight,
                affected_keys=[sprint.get("name", "Active Sprint")],
                reason=(
                    f"Sprint completion lagging: {work_ratio:.1%} completed ({completed_points}/{total_points} pts) "
                    f"vs {time_ratio:.1%} sprint elapsed ({days_elapsed}/{total_days} days), lagging by {lag:.1%}."
                ),
                metadata={
                    "total_points": total_points,
                    "completed_points": completed_points,
                    "days_elapsed": days_elapsed,
                    "total_days": total_days,
                    "work_completion_ratio": work_ratio,
                    "time_elapsed_ratio": time_ratio,
                    "lag_ratio": lag,
                },
            )
        )

    return findings
