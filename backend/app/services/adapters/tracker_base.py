from abc import ABC, abstractmethod
from typing import Any


class BaseTrackerAdapter(ABC):
    """Abstract interface for issue tracking systems (Jira / Demo Tracker)."""

    @abstractmethod
    async def get_sprint(self, sprint_id: int | None = None) -> dict[str, Any] | None:
        """Get active sprint or sprint by id."""

    @abstractmethod
    async def list_sprints(self) -> list[dict[str, Any]]:
        """List all sprints in chronological order."""

    @abstractmethod
    async def list_issues(
        self,
        sprint_id: int | None = None,
        status: str | None = None,
        assignee_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """List issues matching filters."""

    @abstractmethod
    async def get_issue(self, issue_key: str) -> dict[str, Any] | None:
        """Get full issue details by key."""

    @abstractmethod
    async def get_issue_history(self, issue_key: str) -> list[dict[str, Any]]:
        """Get status and field history for an issue."""

    @abstractmethod
    async def list_developers(self, team_id: int | None = None) -> list[dict[str, Any]]:
        """List developers with their teams, skills, and capacities."""

    @abstractmethod
    async def get_developer(self, developer_id: int) -> dict[str, Any] | None:
        """Get single developer details."""

    @abstractmethod
    async def update_issue_assignee(self, issue_key: str, new_assignee_id: int) -> bool:
        """Update issue assignee."""

    @abstractmethod
    async def search_incidents(self, query: str) -> list[dict[str, Any]]:
        """Search past incident reports by keyword."""


class BaseVcsAdapter(ABC):
    """Abstract interface for version control systems (GitHub Demo / GitHub Live)."""

    @abstractmethod
    async def list_pull_requests(
        self,
        issue_key: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List pull requests with optional issue key or status filter."""

    @abstractmethod
    async def get_pull_request(self, pr_number: int) -> dict[str, Any] | None:
        """Get pull request details by PR number."""

    @abstractmethod
    async def get_ci_status(self, pr_number: int) -> dict[str, Any] | None:
        """Get latest CI run result for a pull request."""
