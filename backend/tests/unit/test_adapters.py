import pytest

from app.db import async_session_maker
from app.services.adapters.demo_tracker import DemoTrackerAdapter
from app.services.adapters.github_demo import GithubDemoAdapter


@pytest.mark.asyncio
async def test_demo_tracker_sprint_and_issues():
    async with async_session_maker() as session:
        adapter = DemoTrackerAdapter(session)

        # Active sprint
        sprint = await adapter.get_sprint()
        assert sprint is not None
        assert sprint["name"] == "Sprint 24"
        assert sprint["status"] == "ACTIVE"

        # List sprints
        sprints = await adapter.list_sprints()
        assert len(sprints) == 3

        # List issues for active sprint
        issues = await adapter.list_issues(sprint_id=sprint["id"])
        assert len(issues) == 30

        # Verify key seeded issues
        issue_139 = await adapter.get_issue("PAY-139")
        assert issue_139 is not None
        assert issue_139["assignee_name"] == "David Kim"
        assert issue_139["status"] == "IN_PROGRESS"
        assert "PAY-142" in issue_139["blocks"]

        issue_142 = await adapter.get_issue("PAY-142")
        assert issue_142 is not None
        assert issue_142["status"] == "BLOCKED"
        assert "PAY-139" in issue_142["blocked_by"]

        # Developers
        devs = await adapter.list_developers()
        assert len(devs) == 12

        # Search incidents
        incidents = await adapter.search_incidents("idempotency")
        assert len(incidents) >= 1
        assert "INC-2024-02" in [inc["incident_number"] for inc in incidents]


@pytest.mark.asyncio
async def test_github_demo_adapter():
    async with async_session_maker() as session:
        vcs = GithubDemoAdapter(session)

        # All PRs
        prs = await vcs.list_pull_requests()
        assert len(prs) == 30

        # PR 204 (stuck, waiting for review)
        pr_204 = await vcs.get_pull_request(204)
        assert pr_204 is not None
        assert pr_204["issue_key"] == "PAY-145"
        assert pr_204["is_stuck"] is True
        assert pr_204["age_days"] >= 2

        # PR 211 (stuck, failing CI)
        pr_211 = await vcs.get_pull_request(211)
        assert pr_211 is not None
        assert pr_211["issue_key"] == "CORE-108"
        assert pr_211["is_stuck"] is True
        assert pr_211["latest_ci_status"] == "FAILURE"

        ci_status = await vcs.get_ci_status(211)
        assert ci_status is not None
        assert ci_status["status"] == "FAILURE"
        assert ci_status["failed_step"] == "test_pool_saturation"
