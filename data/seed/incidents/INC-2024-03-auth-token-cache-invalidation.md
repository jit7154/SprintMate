# Postmortem: INC-2024-03 Auth Token Cache Invalidation Cascading Failure

**Date:** 2024-08-04  
**Service:** auth-service  
**Severity:** SEV-2  

## Summary
A brief network partition caused Redis node eviction. All subsequent API gateway calls experienced cache misses, 
causing a thundering herd on the Postgres auth database that increased p99 latency from 4ms to 1200ms.

## Remediation & Learnings
1. Implemented probabilistic early expiration (XFetch algorithm) on JWT verification cache.
2. Added in-memory singleflight mutex in FastAPI middleware to deduplicate database verification requests.
