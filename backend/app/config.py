from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration loaded from environment variables."""

    # Server settings
    port: int = 8001
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"

    # Database settings (default connects to local docker-compose postgres on 5433)
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/sprintmate"
    )

    # LLM and Agent settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    data_mode: str = "demo"  # "demo" or "live"
    github_repo: str = ""
    github_token: str = ""

    # Deterministic risk engine thresholds
    risk_blocked_days_threshold: int = 3
    risk_overdue_buffer_days: int = 2
    risk_pr_stale_days_threshold: int = 2
    risk_completion_lag_threshold: float = 0.20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
