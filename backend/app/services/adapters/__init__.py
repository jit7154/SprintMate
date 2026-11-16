from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.adapters.demo_tracker import DemoTrackerAdapter
from app.services.adapters.github_demo import GithubDemoAdapter
from app.services.adapters.github_live import GithubLiveAdapter
from app.services.adapters.tracker_base import BaseTrackerAdapter, BaseVcsAdapter


def get_tracker_adapter(session: AsyncSession) -> BaseTrackerAdapter:
    """Return configured issue tracker adapter."""
    return DemoTrackerAdapter(session)


def get_vcs_adapter(session: AsyncSession) -> BaseVcsAdapter:
    """Return configured VCS adapter based on DATA_MODE."""
    if settings.data_mode == "live" and settings.github_repo:
        return GithubLiveAdapter()
    return GithubDemoAdapter(session)
