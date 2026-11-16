from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


def get_async_database_url(url: str) -> str:
    """Normalize database URL for async SQLAlchemy driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    get_async_database_url(settings.database_url),
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create all database tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mission: Mapped[str] = mapped_column(String(255), nullable=False)

    developers: Mapped[list["Developer"]] = relationship(
        "Developer", back_populates="team"
    )


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # manager, developer
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    weekly_capacity_points: Mapped[int] = mapped_column(Integer, default=8)

    team: Mapped[Team] = relationship("Team", back_populates="developers")
    issues: Mapped[list["Issue"]] = relationship("Issue", back_populates="assignee")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # COMPLETED, ACTIVE, UPCOMING
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sprint_goal: Mapped[str] = mapped_column(Text, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, default=10)
    days_elapsed: Mapped[int] = mapped_column(Integer, default=0)

    issues: Mapped[list["Issue"]] = relationship("Issue", back_populates="sprint")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # TO_DO, IN_PROGRESS, IN_REVIEW, DONE, BLOCKED
    story_points: Mapped[int] = mapped_column(Integer, default=3)
    priority: Mapped[str] = mapped_column(
        String(20), default="MEDIUM"
    )  # LOW, MEDIUM, HIGH, CRITICAL
    sprint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sprints.id"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("developers.id"), nullable=True
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sprint: Mapped[Sprint] = relationship("Sprint", back_populates="issues")
    assignee: Mapped[Developer | None] = relationship(
        "Developer", back_populates="issues"
    )
    history: Mapped[list["IssueHistory"]] = relationship(
        "IssueHistory", back_populates="issue"
    )


class IssueDependency(Base):
    __tablename__ = "issue_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blocker_issue_key: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    blocked_issue_key: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), default="blocks")


class IssueHistory(Base):
    __tablename__ = "issue_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("issues.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), default="System")
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    issue: Mapped[Issue] = relationship("Issue", back_populates="history")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pr_number: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    repo: Mapped[str] = mapped_column(String(100), default="DevCore/monorepo")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="OPEN"
    )  # OPEN, MERGED, CLOSED
    review_status: Mapped[str] = mapped_column(
        String(30), default="PENDING_REVIEW"
    )  # PENDING_REVIEW, APPROVED, CHANGES_REQUESTED
    issue_key: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("developers.id"), nullable=False
    )
    requested_reviewers: Mapped[list[int]] = mapped_column(JSON, default=list)
    pr_created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    pr_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ci_runs: Mapped[list["CiRun"]] = relationship(
        "CiRun", back_populates="pull_request"
    )


class CiRun(Base):
    __tablename__ = "ci_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pr_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pull_requests.id"), nullable=False
    )
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # SUCCESS, FAILURE, RUNNING
    failed_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    run_duration_seconds: Mapped[int] = mapped_column(Integer, default=120)
    run_completed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    pull_request: Mapped[PullRequest] = relationship(
        "PullRequest", back_populates="ci_runs"
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    issue_key: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    current_assignee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_assignee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("developers.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", index=True
    )  # PENDING, APPROVED, REJECTED, STALE, EXECUTED
    created_by: Mapped[str] = mapped_column(String(100), default="InvestigatorAgent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # proposal, issue
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # approve, reject, execute, create
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # manager, developer, system
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # SUCCESS, REJECTED, STALE_REJECTED
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    tools_called: Mapped[list[str]] = mapped_column(JSON, default=list)
    agent_path: Mapped[list[str]] = mapped_column(JSON, default=list)
    errors_and_retries: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
