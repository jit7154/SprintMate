# Postmortem: INC-2024-05 Payment Service Circuit Breaker Flapping

**Date:** 2024-11-02  
**Service:** payment-service  
**Severity:** SEV-3  

## Summary
Payment gateway circuit breaker tripped 14 times in 3 hours despite 98.5% upstream availability.

## Root Cause
Circuit breaker error rate threshold was configured to 5% with a 10-request sliding window. 
A burst of 2 malformed requests from a single client caused the entire gateway to reject healthy payments.

## Remediation & Learnings
1. Increased minimum evaluation volume from 10 requests to 100 requests.
2. Separated client error 4xx from upstream 5xx in circuit breaker trip calculation.
