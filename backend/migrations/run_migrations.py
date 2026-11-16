#!/usr/bin/env python3
"""Execute SQL migration scripts against the configured PostgreSQL database."""

import asyncio
import sys
from pathlib import Path

# Ensure backend directory is in python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import engine  # noqa: E402


async def run_migrations() -> None:
    migrations_dir = Path(__file__).resolve().parent
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("No migration files found.")
        return

    # Use raw asyncpg connection to support multi-command DDL scripts via simple query protocol
    raw_conn = await engine.raw_connection()
    try:
        asyncpg_conn = raw_conn.driver_connection
        for sql_file in sql_files:
            print(f"Applying migration: {sql_file.name}")
            content = sql_file.read_text(encoding="utf-8")
            await asyncpg_conn.execute(content)
    finally:
        raw_conn.close()
        await engine.dispose()

    print("All migrations applied successfully.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
