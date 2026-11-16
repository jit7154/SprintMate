import pytest

from mcp_server.tools_github import (
    get_ci_status,
    get_pull_request,
    search_pull_requests,
)
from mcp_server.tools_jira import (
    get_issue,
    get_issue_history,
    get_sprint,
    propose_reassignment,
    search_issues,
)


@pytest.mark.asyncio
async def test_mcp_jira_search_and_get():
    # 1. search_issues
    issues = await search_issues(status="IN_PROGRESS", sprint_id=2)
    assert len(issues) >= 1
    assert any(i["key"] == "PAY-139" for i in issues)

    # 2. get_issue
    issue_139 = await get_issue("PAY-139")
    assert issue_139["key"] == "PAY-139"
    assert issue_139["status"] == "IN_PROGRESS"
    assert issue_139["assignee_name"] == "David Kim"

    issue_142 = await get_issue("PAY-142")
    assert issue_142["key"] == "PAY-142"
    assert issue_142["status"] == "BLOCKED"
    assert "PAY-139" in issue_142["blocked_by"]

    # 3. get_sprint
    sprint = await get_sprint()
    assert sprint["name"] == "Sprint 24"
    assert sprint["status"] == "ACTIVE"

    # 4. get_issue_history
    history = await get_issue_history("PAY-142")
    assert len(history) >= 1
    assert any(h["new_value"] == "BLOCKED" for h in history)


@pytest.mark.asyncio
async def test_mcp_github_tools():
    # 5. search_pull_requests
    prs = await search_pull_requests(issue_key="PAY-145")
    assert len(prs) == 1
    assert prs[0]["pr_number"] == 204

    # 6. get_pull_request
    pr_204 = await get_pull_request(204)
    assert pr_204["pr_number"] == 204
    assert pr_204["review_status"] == "PENDING_REVIEW"
    assert pr_204["is_stuck"] is True

    # 7. get_ci_status
    ci_211 = await get_ci_status(211)
    assert ci_211["status"] == "FAILURE"
    assert ci_211["failed_step"] == "test_pool_saturation"


@pytest.mark.asyncio
async def test_mcp_propose_reassignment_creates_pending_only():
    # 8. propose_reassignment
    # Propose reassigning PAY-139 from David Kim (id 6) to Rachel Green (id 7)
    proposal = await propose_reassignment(
        issue_key="PAY-139",
        proposed_assignee_id=7,
        reason="David Kim is at 200% capacity; Rachel Green has payment skills and 7 available points.",
        created_by="InvestigatorAgent",
    )
    assert proposal["status"] == "PENDING"
    assert proposal["issue_key"] == "PAY-139"
    assert proposal["proposed_assignee_id"] == 7
    assert proposal["current_assignee_id"] == 6

    # Verify that PAY-139 was NOT modified directly by the MCP tool!
    issue_after = await get_issue("PAY-139")
    assert issue_after["assignee_id"] == 6
    assert issue_after["assignee_name"] == "David Kim"
