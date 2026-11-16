# Postmortem: INC-2024-01 Stripe Webhook Delivery Timeout

**Date:** 2024-03-12  
**Service:** payment-service / webhook-worker  
**Severity:** SEV-2  

## Summary
At 14:22 UTC, incoming Stripe payment intent webhooks began experiencing HTTP 504 timeouts. 
Over a 45-minute window, approximately 3,200 webhooks failed delivery and queued for retry.

## Root Cause
The `WebhookEventConsumer` executed synchronous database lookups on `merchants.external_stripe_account_id` 
without a composite database index. Under concurrent load of 400 req/sec, worker threads exhausted 
the database connection pool.

## Remediation & Learnings
1. Added missing composite index `idx_merchants_stripe_acct` on PostgreSQL.
2. Migrated webhook payload ingestion to asynchronous Redis pub/sub buffer.
3. Enforced strict 2.0-second timeout on all synchronous webhook validation handlers.
