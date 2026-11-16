# Postmortem: INC-2024-04 Database Connection Pool Exhaustion in Worker Tier

**Date:** 2024-09-22  
**Service:** core-platform / worker-tier  
**Severity:** SEV-2  

## Summary
Background batch workers consumed all 100 available PostgreSQL connection slots, starving the public API servers.

## Root Cause
When an async worker encountered an unhandled network error, the context manager failed to close 
the SQLAlchemy session, leaving connections in `IDLE in transaction` state indefinitely.

## Remediation & Learnings
1. Enforced `pool_pre_ping=True` and `pool_recycle=1800` in SQLAlchemy engine configuration.
2. Added `idle_in_transaction_session_timeout = 30000` to PostgreSQL server settings.
3. Installed PgBouncer in transaction pooling mode.
