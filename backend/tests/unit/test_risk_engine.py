from datetime import datetime

from app.services.risk.rules import (
    check_blocked_issues,
    check_completion_lag,
    check_dependency_chains,
    check_developer_overload,
    check_overdue_issues,
    check_pr_failing_ci,
    check_pr_no_review,
)
from app.services.risk.scoring import evaluate_sprint_risk
from app.services.risk.workload import calculate_developer_workloads

REF_DATE = datetime(2026, 11, 17, 0, 0, 0)


def test_rule_blocked_issues_pure_unit():
    issues = [
        {
            "key": "DEV-101",
            "title": "Payment gateway timeout",
            "status": "BLOCKED",
            "story_points": 5,
            "priority": "HIGH",
            "updated_at": "2026-11-13T00:00:00",
            "history": [
                {
                    "field_name": "status",
                    "new_value": "BLOCKED",
                    "changed_at": "2026-11-13T00:00:00",
                }
            ],
        },
        {
            "key": "DEV-102",
            "title": "Update README",
            "status": "BLOCKED",
            "story_points": 1,
            "priority": "LOW",
            "updated_at": "2026-11-16T12:00:00",  # Blocked only 0.5 days
            "history": [],
        },
    ]

    findings = check_blocked_issues(issues, now=REF_DATE, threshold_days=3)
    assert len(findings) == 1
    assert findings[0].affected_keys == ["DEV-101"]
    assert findings[0].severity == "CRITICAL"
    assert findings[0].metadata["days_blocked"] == 4


def test_rule_overdue_issues_pure_unit():
    issues = [
        {
            "key": "DEV-103",
            "title": "Fix memory leak",
            "status": "IN_PROGRESS",
            "story_points": 8,
            "due_date": "2026-11-15T00:00:00",
        },
        {
            "key": "DEV-104",
            "title": "Refactor styles",
            "status": "DONE",
            "story_points": 2,
            "due_date": "2026-11-10T00:00:00",
        },
    ]

    findings = check_overdue_issues(issues, now=REF_DATE)
    assert len(findings) == 1
    assert findings[0].affected_keys == ["DEV-103"]
    assert findings[0].severity == "CRITICAL"
    assert findings[0].metadata["days_overdue"] == 2


def test_rule_pr_no_review_pure_unit():
    prs = [
        {
            "pr_number": 301,
            "title": "Add caching layer",
            "status": "OPEN",
            "review_status": "PENDING_REVIEW",
            "age_days": 3,
            "author_name": "Alice",
            "issue_key": "DEV-105",
        },
        {
            "pr_number": 302,
            "title": "Fix typo",
            "status": "OPEN",
            "review_status": "APPROVED",
            "age_days": 1,
            "author_name": "Bob",
            "issue_key": "DEV-106",
        },
    ]

    findings = check_pr_no_review(prs)
    assert len(findings) == 1
    assert "PR #301" in findings[0].affected_keys
    assert findings[0].metadata["age_days"] == 3


def test_rule_pr_failing_ci_pure_unit():
    prs = [
        {
            "pr_number": 303,
            "title": "Implement rate limiting",
            "status": "OPEN",
            "latest_ci_status": "FAILURE",
            "ci_runs": [
                {
                    "status": "FAILURE",
                    "failed_step": "test_integration",
                }
            ],
            "author_name": "Charlie",
            "issue_key": "DEV-107",
        },
        {
            "pr_number": 304,
            "title": "Add health endpoint",
            "status": "OPEN",
            "latest_ci_status": "SUCCESS",
            "ci_runs": [
                {
                    "status": "SUCCESS",
                    "failed_step": None,
                }
            ],
            "author_name": "Dana",
            "issue_key": "DEV-108",
        },
    ]

    findings = check_pr_failing_ci(prs)
    assert len(findings) == 1
    assert "PR #303" in findings[0].affected_keys
    assert findings[0].metadata["failed_step"] == "test_integration"


def test_workload_and_overload_pure_unit():
    devs = [
        {
            "id": 1,
            "name": "Alex Smith",
            "role": "Senior Engineer",
            "weekly_capacity_points": 8,
            "skills": ["Python", "FastAPI"],
        },
        {
            "id": 2,
            "name": "Beth Jones",
            "role": "Mid Engineer",
            "weekly_capacity_points": 8,
            "skills": ["React"],
        },
    ]
    issues = [
        {"key": "DEV-1", "assignee_id": 1, "story_points": 5, "status": "IN_PROGRESS"},
        {"key": "DEV-2", "assignee_id": 1, "story_points": 8, "status": "IN_PROGRESS"},  # Total = 13
        {"key": "DEV-3", "assignee_id": 2, "story_points": 3, "status": "IN_PROGRESS"},  # Total = 3
    ]

    workloads = calculate_developer_workloads(devs, issues)
    alex_workload = next(w for w in workloads if w["id"] == 1)
    assert alex_workload["assigned_points"] == 13
    assert alex_workload["weekly_capacity_points"] == 8
    assert alex_workload["utilization_ratio"] > 1.5
    assert alex_workload["is_overloaded"] is True

    findings = check_developer_overload(workloads)
    assert len(findings) == 1
    assert "Alex Smith" in findings[0].affected_keys


def test_dependency_chain_and_lag_pure_unit():
    issues = [
        {
            "key": "DEV-110",
            "title": "Auth token refresh",
            "status": "BLOCKED",
            "labels": ["sprint-goal"],
            "story_points": 5,
            "blocked_by": ["DEV-109"],
            "blocks": ["DEV-111"],
        },
        {
            "key": "DEV-111",
            "title": "OAuth provider integration",
            "status": "IN_PROGRESS",
            "labels": ["sprint-goal"],
            "story_points": 8,
            "blocked_by": ["DEV-110"],
            "blocks": [],
        },
    ]

    dep_findings = check_dependency_chains(issues)
    assert len(dep_findings) >= 1
    assert any("DEV-110" in f.affected_keys for f in dep_findings)

    sprint = {
        "id": 1,
        "name": "Sprint 1",
        "total_days": 10,
        "days_elapsed": 8,
        "sprint_goal": "OAuth Launch",
    }
    lag_findings = check_completion_lag(sprint, issues)
    assert len(lag_findings) >= 1
    assert lag_findings[0].metadata["days_elapsed"] == 8


def test_evaluate_sprint_risk_pure_unit():
    sprint = {
        "id": 1,
        "name": "Sprint 1",
        "total_days": 10,
        "days_elapsed": 8,
        "sprint_goal": "Core stability",
    }
    issues = [
        {
            "key": "DEV-201",
            "title": "Blocked auth bug",
            "status": "BLOCKED",
            "story_points": 8,
            "priority": "HIGH",
            "updated_at": "2026-11-10T00:00:00",
            "history": [],
            "blocked_by": [],
            "blocks": [],
            "labels": ["sprint-goal"],
            "assignee_id": 1,
            "assignee_name": "Dev One",
        }
    ]
    prs = [
        {
            "pr_number": 501,
            "title": "Fix auth",
            "status": "OPEN",
            "review_status": "PENDING_REVIEW",
            "age_days": 4,
            "latest_ci_status": "FAILURE",
            "latest_ci_step": "test_auth",
            "author_name": "Dev One",
            "issue_key": "DEV-201",
        }
    ]
    devs = [
        {
            "id": 1,
            "name": "Dev One",
            "role": "Engineer",
            "weekly_capacity_points": 5,
            "skills": ["Python"],
        }
    ]

    evaluation = evaluate_sprint_risk(sprint, issues, prs, devs, now=REF_DATE)
    assert evaluation.overall_score >= 50
    assert evaluation.risk_level in {"HIGH", "CRITICAL"}
    assert len(evaluation.breakdown) == 6
    assert len(evaluation.top_risks) >= 1
