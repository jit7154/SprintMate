from typing import Any

from app.db import async_session_maker
from app.services.adapters.github_demo import GithubDemoAdapter


async def search_pull_requests(
    issue_key: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Search pull requests with optional issue key link or status filter."""
    async with async_session_maker() as session:
        vcs = GithubDemoAdapter(session)
        return await vcs.list_pull_requests(
            issue_key=issue_key.strip().upper() if issue_key else None,
            status=status.strip().upper() if status else None,
        )


async def get_pull_request(pr_number: int) -> dict[str, Any]:
    """Retrieve full pull request details including branch, review state, age, and CI runs."""
    async with async_session_maker() as session:
        vcs = GithubDemoAdapter(session)
        pr = await vcs.get_pull_request(pr_number)
        if not pr:
            return {"error": f"Pull request #{pr_number} not found."}
        return pr


async def get_ci_status(pr_number: int) -> dict[str, Any]:
    """Retrieve the latest continuous integration run result and failed steps for a pull request."""
    async with async_session_maker() as session:
        vcs = GithubDemoAdapter(session)
        ci = await vcs.get_ci_status(pr_number)
        if not ci:
            return {"error": f"No CI runs recorded for pull request #{pr_number}."}
        return ci
