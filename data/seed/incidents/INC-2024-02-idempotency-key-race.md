# Postmortem: INC-2024-02 Idempotency Key Race Condition

**Date:** 2024-06-18  
**Service:** payment-service / retry-worker  
**Severity:** SEV-1  

## Summary
Double billing occurred on 14 customer accounts during an automated retry spike following an upstream payment gateway blip.

## Root Cause
The retry engine checked payment state (`SELECT status FROM payments WHERE idempotency_key = ?`) 
before inserting a transaction record, creating a Time-of-Check to Time-of-Use (TOCTOU) race condition. 
Two worker containers picked up the same failed charge simultaneously before either wrote the lock record.

## Remediation & Learnings
1. Migrated idempotency validation to atomic PostgreSQL advisory locks (`pg_try_advisory_xact_lock`).
2. Implemented mandatory distributed Redis lock with a 30-second TTL before executing any charge API call.
3. Added automated reconciliation cron that flags duplicate Stripe transaction IDs.
