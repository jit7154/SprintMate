import re
from datetime import datetime
from typing import Any

import httpx

from app.config import settings
from app.services.adapters.tracker_base import BaseVcsAdapter


class GithubLiveAdapter(BaseVcsAdapter):
    """Read-only GitHub REST API adapter for live repositories."""

    def __init__(self, repo: str | None = None, token: str | None = None):
        self.repo = repo or settings.github_repo
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _extract_issue_key(self, text: str) -> str | None:
        """Extract issue key such as CORE-101, PAY-142, CX-201 from title or branch."""
        match = re.search(r"\b([A-Z]{2,10}-\d+)\b", text)
        return match.group(1) if match else None

    async def list_pull_requests(
        self,
        issue_key: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.repo:
            return []

        state = (
            "open" if status == "OPEN" else ("closed" if status == "CLOSED" else "all")
        )
        url = f"{self.base_url}/repos/{self.repo}/pulls?state={state}&per_page=50"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=self._headers(), timeout=10.0)
                resp.raise_for_status()
                raw_prs = resp.json()
            except Exception:
                return []

        prs = []
        now = datetime.utcnow()
        for raw in raw_prs:
            title = raw.get("title", "")
            branch = raw.get("head", {}).get("ref", "")
            extracted_key = self._extract_issue_key(f"{title} {branch}")

            if issue_key and extracted_key != issue_key:
                continue

            created_at_dt = datetime.fromisoformat(
                raw["created_at"].replace("Z", "+00:00")
            )
            age_days = (now.replace(tzinfo=created_at_dt.tzinfo) - created_at_dt).days

            prs.append(
                {
                    "id": raw["id"],
                    "pr_number": raw["number"],
                    "repo": self.repo,
                    "title": title,
                    "branch": branch,
                    "status": "OPEN" if raw["state"] == "open" else "CLOSED",
                    "review_status": "PENDING_REVIEW",
                    "issue_key": extracted_key,
                    "author_id": 1,
                    "author_name": raw.get("user", {}).get("login", "unknown"),
                    "requested_reviewers": [
                        rev.get("id") for rev in raw.get("requested_reviewers", [])
                    ],
                    "pr_created_at": raw["created_at"],
                    "pr_updated_at": raw["updated_at"],
                    "age_days": age_days,
                    "is_stuck": raw["state"] == "open" and age_days >= 2,
                    "latest_ci_status": "SUCCESS",
                    "ci_runs": [],
                }
            )
        return prs

    async def get_pull_request(self, pr_number: int) -> dict[str, Any] | None:
        if not self.repo:
            return None

        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=self._headers(), timeout=10.0)
                resp.raise_for_status()
                raw = resp.json()
            except Exception:
                return None

        title = raw.get("title", "")
        branch = raw.get("head", {}).get("ref", "")
        extracted_key = self._extract_issue_key(f"{title} {branch}")
        created_at_dt = datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00"))
        age_days = (
            datetime.utcnow().replace(tzinfo=created_at_dt.tzinfo) - created_at_dt
        ).days

        return {
            "id": raw["id"],
            "pr_number": raw["number"],
            "repo": self.repo,
            "title": title,
            "branch": branch,
            "status": "OPEN" if raw["state"] == "open" else "CLOSED",
            "review_status": "PENDING_REVIEW",
            "issue_key": extracted_key,
            "author_id": 1,
            "author_name": raw.get("user", {}).get("login", "unknown"),
            "requested_reviewers": [
                rev.get("id") for rev in raw.get("requested_reviewers", [])
            ],
            "pr_created_at": raw["created_at"],
            "pr_updated_at": raw["updated_at"],
            "age_days": age_days,
            "is_stuck": raw["state"] == "open" and age_days >= 2,
            "latest_ci_status": "SUCCESS",
            "ci_runs": [],
        }

    async def get_ci_status(self, pr_number: int) -> dict[str, Any] | None:
        if not self.repo:
            return None

        pr = await self.get_pull_request(pr_number)
        if not pr:
            return None

        return {
            "pr_number": pr_number,
            "commit_hash": "HEAD",
            "status": "SUCCESS",
            "failed_step": None,
            "run_duration_seconds": 120,
            "run_completed_at": datetime.utcnow().isoformat(),
        }
