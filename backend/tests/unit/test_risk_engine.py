from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import async_session_maker
from app.main import app
from app.services.adapters import get_tracker_adapter, get_vcs_adapter
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


@pytest.mark.asyncio
async def test_deterministic_rules_on_seeded_data():
    async with async_session_maker() as session:
        tracker = get_tracker_adapter(session)
        vcs = get_vcs_adapter(session)

        sprint = await tracker.get_sprint()
        assert sprint is not None

        issues = await tracker.list_issues(sprint_id=sprint["id"])
        prs = await vcs.list_pull_requests()
        devs = await tracker.list_developers()

        detailed_issues = []
        for issue in issues:
            det = await tracker.get_issue(issue["key"])
            detailed_issues.append(det or issue)

        # 1. Blocked Issues Rule
        blocked_findings = check_blocked_issues(detailed_issues, now=REF_DATE)
        assert len(blocked_findings) >= 1
        blocked_keys = [f.affected_keys[0] for f in blocked_findings]
        assert "PAY-142" in blocked_keys
        pay_142_finding = next(
            f for f in blocked_findings if "PAY-142" in f.affected_keys
        )
        assert pay_142_finding.metadata["days_blocked"] == 4
        assert pay_142_finding.metadata["threshold_days"] == 3

        # 2. Overdue Issues Rule
        overdue_findings = check_overdue_issues(detailed_issues, now=REF_DATE)
        assert len(overdue_findings) >= 1
        overdue_keys = [f.affected_keys[0] for f in overdue_findings]
        assert "PAY-139" in overdue_keys
        pay_139_finding = next(
            f for f in overdue_findings if "PAY-139" in f.affected_keys
        )
        assert pay_139_finding.severity == "CRITICAL"
        assert pay_139_finding.metadata["days_overdue"] == 2

        # 3. PR No Review Rule
        pr_review_findings = check_pr_no_review(prs)
        assert any("PR #204" in f.affected_keys for f in pr_review_findings)
        pr_204_finding = next(
            f for f in pr_review_findings if "PR #204" in f.affected_keys
        )
        assert pr_204_finding.metadata["age_days"] >= 3

        # 4. PR Failing CI Rule
        pr_ci_findings = check_pr_failing_ci(prs)
        assert any("PR #211" in f.affected_keys for f in pr_ci_findings)
        pr_211_finding = next(f for f in pr_ci_findings if "PR #211" in f.affected_keys)
        assert pr_211_finding.metadata["failed_step"] == "test_pool_saturation"

        # 5. Developer Overload Rule
        workloads = calculate_developer_workloads(devs, detailed_issues)
        overload_findings = check_developer_overload(workloads)
        assert len(overload_findings) >= 1
        assert any("David Kim" in f.affected_keys for f in overload_findings)
        dk_finding = next(
            f for f in overload_findings if "David Kim" in f.affected_keys
        )
        assert dk_finding.metadata["assigned_points"] == 16
        assert dk_finding.metadata["capacity_points"] == 8
        assert dk_finding.metadata["utilization_ratio"] == 2.0

        # 6. Dependency Chain Threat Rule
        dep_findings = check_dependency_chains(detailed_issues)
        assert len(dep_findings) >= 1
        goal_threat = next(f for f in dep_findings if "PAY-150" in f.affected_keys)
        assert "PAY-142" in goal_threat.affected_keys
        assert goal_threat.severity == "CRITICAL"

        # 7. Velocity Completion Lag Rule
        lag_findings = check_completion_lag(sprint, detailed_issues)
        assert len(lag_findings) >= 1
        lag_finding = lag_findings[0]
        assert lag_finding.metadata["days_elapsed"] == 8
        assert lag_finding.metadata["total_days"] == 10
        assert lag_finding.metadata["lag_ratio"] > 0.40

        # Full Scoring
        evaluation = evaluate_sprint_risk(
            sprint, detailed_issues, prs, devs, now=REF_DATE
        )
        assert evaluation.overall_score >= 80
        assert evaluation.risk_level == "CRITICAL"
        assert evaluation.blocked_issues_count >= 1
        assert evaluation.overdue_issues_count >= 1
        assert evaluation.stuck_prs_count >= 2
        assert evaluation.overloaded_devs_count >= 1
        assert len(evaluation.breakdown) == 6
        assert len(evaluation.top_risks) >= 3
        assert (
            "PAY-142" in evaluation.explanation or "PAY-139" in evaluation.explanation
        )


@pytest.mark.asyncio
async def test_sprint_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sprints list
        resp = await client.get("/api/sprints")
        assert resp.status_code == 200
        sprints = resp.json()
        assert len(sprints) == 3

        # Active sprint summary & risk
        resp = await client.get("/api/sprints/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sprint"]["name"] == "Sprint 24"
        assert data["risk_evaluation"]["risk_level"] in {"HIGH", "CRITICAL"}
        assert data["risk_evaluation"]["overall_score"] > 50

        # Burndown
        resp = await client.get("/api/sprints/2/burndown")
        assert resp.status_code == 200
        burndown = resp.json()
        assert len(burndown) == 11
        assert burndown[0]["day"] == "Day 0"
        assert burndown[0]["actual"] is not None

        # Stuck pull requests
        resp = await client.get("/api/pull-requests?stuck_only=true")
        assert resp.status_code == 200
        stuck_prs = resp.json()
        assert len(stuck_prs) == 2
        stuck_numbers = [p["pr_number"] for p in stuck_prs]
        assert 204 in stuck_numbers
        assert 211 in stuck_numbers

        # Single pull request
        resp = await client.get("/api/pull-requests/211")
        assert resp.status_code == 200
        pr_211 = resp.json()
        assert pr_211["latest_ci_status"] == "FAILURE"
        assert len(pr_211["ci_runs"]) >= 1

        # Team developers workload
        resp = await client.get("/api/team/developers")
        assert resp.status_code == 200
        devs = resp.json()
        assert len(devs) == 12
        dk = next(d for d in devs if d["name"] == "David Kim")
        assert dk["assigned_points"] == 16
        assert dk["is_overloaded"] is True
