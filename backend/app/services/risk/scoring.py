from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.services.risk.rules import (
    RiskFinding,
    check_blocked_issues,
    check_completion_lag,
    check_dependency_chains,
    check_developer_overload,
    check_overdue_issues,
    check_pr_failing_ci,
    check_pr_no_review,
)
from app.services.risk.workload import calculate_developer_workloads


class RiskCategoryBreakdown(BaseModel):
    category_id: str
    category_name: str
    score_contribution: int
    findings_count: int
    findings: list[RiskFinding]


class SprintRiskEvaluation(BaseModel):
    sprint_id: int
    sprint_name: str
    overall_score: int  # 0 to 100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    days_elapsed: int
    total_days: int
    days_remaining: int
    total_story_points: int
    completed_story_points: int
    completion_percentage: float
    expected_completion_percentage: float
    blocked_issues_count: int
    overdue_issues_count: int
    stuck_prs_count: int
    overloaded_devs_count: int
    breakdown: list[RiskCategoryBreakdown]
    top_risks: list[RiskFinding]
    explanation: str


def evaluate_sprint_risk(
    sprint: dict[str, Any],
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    developers: list[dict[str, Any]],
    now: datetime | None = None,
) -> SprintRiskEvaluation:
    """Evaluate sprint risk across all deterministic rules and combine into an explainable score."""
    ref_time = now or datetime.now(timezone.utc).replace(tzinfo=None)

    # 1. Workload calculation
    workload_summary = calculate_developer_workloads(developers, issues)

    # 2. Execute deterministic rules
    blocked_findings = check_blocked_issues(issues, now=ref_time)
    overdue_findings = check_overdue_issues(issues, now=ref_time)
    pr_review_findings = check_pr_no_review(pull_requests)
    pr_ci_findings = check_pr_failing_ci(pull_requests)
    stuck_pr_findings = pr_review_findings + pr_ci_findings
    overload_findings = check_developer_overload(workload_summary)
    dependency_findings = check_dependency_chains(issues)
    lag_findings = check_completion_lag(sprint, issues)

    # 3. Categorized breakdown
    categories = [
        RiskCategoryBreakdown(
            category_id="blocked_issues",
            category_name="Blocked Issues",
            score_contribution=sum(f.weight for f in blocked_findings),
            findings_count=len(blocked_findings),
            findings=blocked_findings,
        ),
        RiskCategoryBreakdown(
            category_id="overdue_issues",
            category_name="Overdue & Imminent Deadlines",
            score_contribution=sum(f.weight for f in overdue_findings),
            findings_count=len(overdue_findings),
            findings=overdue_findings,
        ),
        RiskCategoryBreakdown(
            category_id="stuck_prs",
            category_name="Stuck Pull Requests & Failing CI",
            score_contribution=sum(f.weight for f in stuck_pr_findings),
            findings_count=len(stuck_pr_findings),
            findings=stuck_pr_findings,
        ),
        RiskCategoryBreakdown(
            category_id="developer_overload",
            category_name="Developer Capacity Overload",
            score_contribution=sum(f.weight for f in overload_findings),
            findings_count=len(overload_findings),
            findings=overload_findings,
        ),
        RiskCategoryBreakdown(
            category_id="dependency_chains",
            category_name="Unresolved Dependency Chains",
            score_contribution=sum(f.weight for f in dependency_findings),
            findings_count=len(dependency_findings),
            findings=dependency_findings,
        ),
        RiskCategoryBreakdown(
            category_id="schedule_lag",
            category_name="Sprint Velocity & Schedule Lag",
            score_contribution=sum(f.weight for f in lag_findings),
            findings_count=len(lag_findings),
            findings=lag_findings,
        ),
    ]

    all_findings = (
        blocked_findings
        + overdue_findings
        + stuck_pr_findings
        + overload_findings
        + dependency_findings
        + lag_findings
    )

    # Sort top risks by severity and weight
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_findings.sort(key=lambda f: (severity_order.get(f.severity, 4), -f.weight))

    raw_score = sum(c.score_contribution for c in categories)
    overall_score = min(100, raw_score)

    if overall_score >= 80:
        risk_level = "CRITICAL"
    elif overall_score >= 60:
        risk_level = "HIGH"
    elif overall_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Progress stats
    total_days = sprint.get("total_days", 10)
    days_elapsed = sprint.get("days_elapsed", 0)
    days_remaining = max(0, total_days - days_elapsed)
    total_points = sum(i.get("story_points", 0) for i in issues)
    completed_points = sum(
        i.get("story_points", 0)
        for i in issues
        if i.get("status") in {"DONE", "COMPLETED"}
    )
    completion_percentage = (
        round((completed_points / total_points) * 100, 1) if total_points > 0 else 0.0
    )
    expected_completion = (
        round((days_elapsed / total_days) * 100, 1) if total_days > 0 else 0.0
    )

    # Human-readable deterministic explanation
    top_issues_cited = [
        key
        for f in all_findings[:3]
        for key in f.affected_keys
        if "-" in key or "PR #" in key
    ]
    explanation_parts = [
        f"Sprint risk is rated {risk_level} ({overall_score}/100) based on deterministic rule evaluation."
    ]
    if len(all_findings) > 0:
        explanation_parts.append(f"The primary driver is {all_findings[0].reason}")
    if top_issues_cited:
        explanation_parts.append(
            f"Key items requiring immediate attention: {', '.join(top_issues_cited[:4])}."
        )

    explanation = " ".join(explanation_parts)

    return SprintRiskEvaluation(
        sprint_id=sprint.get("id", 0),
        sprint_name=sprint.get("name", "Active Sprint"),
        overall_score=overall_score,
        risk_level=risk_level,
        days_elapsed=days_elapsed,
        total_days=total_days,
        days_remaining=days_remaining,
        total_story_points=total_points,
        completed_story_points=completed_points,
        completion_percentage=completion_percentage,
        expected_completion_percentage=expected_completion,
        blocked_issues_count=len(blocked_findings),
        overdue_issues_count=len(overdue_findings),
        stuck_prs_count=len(stuck_pr_findings),
        overloaded_devs_count=len(overload_findings),
        breakdown=categories,
        top_risks=all_findings[:5],
        explanation=explanation,
    )
