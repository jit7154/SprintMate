import pytest_asyncio

from app.db import engine


@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    """Ensure asyncpg engine connection pool is cleanly closed between test loops."""
    yield
    await engine.dispose()
