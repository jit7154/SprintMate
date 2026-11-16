#!/usr/bin/env python3
"""Deterministic seed data generator for DevCore synthetic workspace."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

# Base reference timestamp: 2026-11-17T00:00:00
BASE_DATE = datetime(2026, 11, 17, 0, 0, 0)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SEED_DIR = ROOT_DIR / "data" / "seed"
INCIDENTS_DIR = SEED_DIR / "incidents"


def generate_data():
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. TEAMS (3 teams)
    teams = [
        {
            "id": 1,
            "name": "Core Platform",
            "mission": "Scalable cloud infrastructure, authentication, database reliability, and developer tooling.",
        },
        {
            "id": 2,
            "name": "Payments & Billing",
            "mission": "Secure payment processing, recurring subscriptions, invoice reconciliation, and fraud prevention.",
        },
        {
            "id": 3,
            "name": "Customer Experience",
            "mission": "Frontend dashboards, real-time analytics, user onboarding, and notification delivery.",
        },
    ]

    # 2. DEVELOPERS (12 developers across 3 teams)
    developers = [
        # Core Platform
        {
            "id": 1,
            "name": "Alex Rivera",
            "email": "alex.rivera@devcore.internal",
            "role": "manager",
            "team_id": 1,
            "skills": ["python", "devops", "postgres", "fastapi", "architecture"],
            "weekly_capacity_points": 10,
        },
        {
            "id": 2,
            "name": "Sarah Chen",
            "email": "sarah.chen@devcore.internal",
            "role": "developer",
            "team_id": 1,
            "skills": ["devops", "kubernetes", "terraform", "aws", "docker"],
            "weekly_capacity_points": 8,
        },
        {
            "id": 3,
            "name": "Marcus Johnson",
            "email": "marcus.johnson@devcore.internal",
            "role": "developer",
            "team_id": 1,
            "skills": ["python", "redis", "docker", "fastapi"],
            "weekly_capacity_points": 8,
        },
        {
            "id": 4,
            "name": "Priya Sharma",
            "email": "priya.sharma@devcore.internal",
            "role": "developer",
            "team_id": 1,
            "skills": ["python", "fastapi", "testing", "postgres"],
            "weekly_capacity_points": 6,
        },
        # Payments & Billing
        {
            "id": 5,
            "name": "Elena Rostova",
            "email": "elena.rostova@devcore.internal",
            "role": "developer",
            "team_id": 2,
            "skills": ["payments", "python", "postgres", "stripe", "webhooks"],
            "weekly_capacity_points": 8,
        },
        {
            "id": 6,
            "name": "David Kim",
            "email": "david.kim@devcore.internal",
            "role": "developer",
            "team_id": 2,
            "skills": ["payments", "security", "go", "python", "idempotency"],
            "weekly_capacity_points": 8,  # OVERLOADED TARGET (assigned 16 pts)
        },
        {
            "id": 7,
            "name": "Rachel Green",
            "email": "rachel.green@devcore.internal",
            "role": "developer",
            "team_id": 2,
            "skills": ["payments", "webhooks", "python", "fastapi", "stripe"],
            "weekly_capacity_points": 7,  # Available capacity (underutilized)
        },
        {
            "id": 8,
            "name": "Tom Bradley",
            "email": "tom.bradley@devcore.internal",
            "role": "developer",
            "team_id": 2,
            "skills": ["python", "testing", "fastapi", "sql"],
            "weekly_capacity_points": 5,
        },
        # Customer Experience
        {
            "id": 9,
            "name": "Maya Lin",
            "email": "maya.lin@devcore.internal",
            "role": "developer",
            "team_id": 3,
            "skills": ["react", "typescript", "tailwind", "ui/ux", "frontend"],
            "weekly_capacity_points": 10,
        },
        {
            "id": 10,
            "name": "Leo Martinez",
            "email": "leo.martinez@devcore.internal",
            "role": "developer",
            "team_id": 3,
            "skills": ["react", "typescript", "recharts", "dashboard"],
            "weekly_capacity_points": 8,
        },
        {
            "id": 11,
            "name": "Chloe Dupont",
            "email": "chloe.dupont@devcore.internal",
            "role": "developer",
            "team_id": 3,
            "skills": ["react", "python", "fastapi", "fullstack"],
            "weekly_capacity_points": 8,
        },
        {
            "id": 12,
            "name": "Samira Khan",
            "email": "samira.khan@devcore.internal",
            "role": "developer",
            "team_id": 3,
            "skills": ["react", "css", "html", "javascript"],
            "weekly_capacity_points": 5,
        },
    ]

    # 3. SPRINTS (3 sprints: Completed 23, Active 24, Upcoming 25)
    # Sprint 24: Day 8 of 10. Start = BASE_DATE - 8 days, End = BASE_DATE + 2 days
    sprint_23_start = BASE_DATE - timedelta(days=22)
    sprint_23_end = BASE_DATE - timedelta(days=9)
    sprint_24_start = BASE_DATE - timedelta(days=8)
    sprint_24_end = BASE_DATE + timedelta(days=2)
    sprint_25_start = BASE_DATE + timedelta(days=3)
    sprint_25_end = BASE_DATE + timedelta(days=17)

    sprints = [
        {
            "id": 1,
            "name": "Sprint 23",
            "status": "COMPLETED",
            "start_date": sprint_23_start.isoformat(),
            "end_date": sprint_23_end.isoformat(),
            "sprint_goal": "Upgrade database clusters and establish core metrics instrumentation.",
            "total_days": 10,
            "days_elapsed": 10,
        },
        {
            "id": 2,
            "name": "Sprint 24",
            "status": "ACTIVE",
            "start_date": sprint_24_start.isoformat(),
            "end_date": sprint_24_end.isoformat(),
            "sprint_goal": "Launch automated payment retry engine and unified merchant webhook reconciliation.",
            "total_days": 10,
            "days_elapsed": 8,
        },
        {
            "id": 3,
            "name": "Sprint 25",
            "status": "UPCOMING",
            "start_date": sprint_25_start.isoformat(),
            "end_date": sprint_25_end.isoformat(),
            "sprint_goal": "Deliver customer-facing billing analytics portal and self-serve webhooks.",
            "total_days": 10,
            "days_elapsed": 0,
        },
    ]

    # 4. ISSUES (60 issues across 3 sprints)
    issues = []
    dependencies = []
    issue_history = []
    issue_id_counter = 1
    hist_id_counter = 1

    # Sprint 23 Issues (Completed, ~15 issues)
    for i in range(1, 16):
        key = f"CORE-{90 + i}" if i <= 5 else (f"PAY-{120 + i}" if i <= 10 else f"CX-{180 + i}")
        dev_id = ((i - 1) % 12) + 1
        issues.append(
            {
                "id": issue_id_counter,
                "key": key,
                "title": f"Sprint 23 Baseline Work Item {i}",
                "description": f"Completed deliverable for Sprint 23 milestone {i}.",
                "status": "DONE",
                "story_points": 3,
                "priority": "MEDIUM",
                "sprint_id": 1,
                "assignee_id": dev_id,
                "due_date": (sprint_23_end - timedelta(days=1)).isoformat(),
                "labels": ["baseline", "sprint-23"],
                "created_at": (sprint_23_start).isoformat(),
                "updated_at": (sprint_23_end).isoformat(),
            }
        )
        issue_id_counter += 1

    # Sprint 24 Issues (ACTIVE, 30 issues with deliberate anomalies)
    # David Kim (dev id 6, capacity 8): assigned PAY-139 (5), PAY-141 (5), PAY-145 (3), PAY-148 (3) = 16 points (OVERLOADED)
    # PAY-139: OVERDUE (due 2 days ago, status IN_PROGRESS)
    # PAY-142: BLOCKED for 4 days by PAY-139
    # PAY-150: Sprint Goal deliverable, blocked by PAY-142
    # PAY-145: Linked PR 204 has been waiting for review for 4 days
    # CORE-108: Linked PR 211 has failing CI

    s24_specs = [
        # Key anomalies
        (
            "PAY-139",
            "Stripe idempotency key race condition in webhook worker",
            "IN_PROGRESS",
            5,
            "CRITICAL",
            6,  # David Kim
            BASE_DATE - timedelta(days=2),  # OVERDUE by 2 days
            ["payments", "stripe", "incident-followup"],
            BASE_DATE - timedelta(days=8),
        ),
        (
            "PAY-142",
            "Retry failed recurring payments engine",
            "BLOCKED",
            5,
            "HIGH",
            5,  # Elena
            BASE_DATE + timedelta(days=1),
            ["payments", "retry", "core-engine"],
            BASE_DATE - timedelta(days=7),
        ),
        (
            "PAY-150",
            "Unified merchant webhook reconciliation - Sprint Goal deliverable",
            "TO_DO",
            8,
            "CRITICAL",
            7,  # Rachel Green
            BASE_DATE + timedelta(days=2),
            ["payments", "sprint-goal", "reconciliation"],
            BASE_DATE - timedelta(days=8),
        ),
        (
            "PAY-141",
            "Implement SEPA direct debit retry backoff",
            "IN_PROGRESS",
            5,
            "HIGH",
            6,  # David Kim
            BASE_DATE + timedelta(days=2),
            ["payments", "sepa"],
            BASE_DATE - timedelta(days=6),
        ),
        (
            "PAY-145",
            "Reconciliation report CSV parser and aggregator",
            "IN_REVIEW",
            3,
            "MEDIUM",
            6,  # David Kim
            BASE_DATE + timedelta(days=1),
            ["payments", "reports"],
            BASE_DATE - timedelta(days=5),
        ),
        (
            "PAY-148",
            "Webhook signature verification cache layer",
            "TO_DO",
            3,
            "MEDIUM",
            6,  # David Kim
            BASE_DATE + timedelta(days=2),
            ["payments", "security"],
            BASE_DATE - timedelta(days=4),
        ),
        (
            "CORE-108",
            "Database connection pool sizing for worker tier",
            "IN_REVIEW",
            5,
            "HIGH",
            2,  # Sarah Chen
            BASE_DATE + timedelta(days=1),
            ["infra", "postgres", "pool"],
            BASE_DATE - timedelta(days=6),
        ),
        (
            "CORE-105",
            "Async Redis client migration for token caching",
            "DONE",
            3,
            "MEDIUM",
            3,  # Marcus
            BASE_DATE - timedelta(days=2),
            ["infra", "redis"],
            BASE_DATE - timedelta(days=7),
        ),
        (
            "CORE-106",
            "Kubernetes HPA scaling triggers on webhook queue depth",
            "IN_PROGRESS",
            5,
            "HIGH",
            2,  # Sarah Chen
            BASE_DATE + timedelta(days=1),
            ["infra", "k8s"],
            BASE_DATE - timedelta(days=6),
        ),
        (
            "CORE-107",
            "OpenTelemetry distributed tracing for payment ingress",
            "DONE",
            5,
            "MEDIUM",
            1,  # Alex
            BASE_DATE - timedelta(days=1),
            ["observability", "otel"],
            BASE_DATE - timedelta(days=8),
        ),
        (
            "CX-201",
            "Merchant payment retry history drawer in dashboard",
            "DONE",
            5,
            "MEDIUM",
            9,  # Maya Lin
            BASE_DATE - timedelta(days=1),
            ["frontend", "react"],
            BASE_DATE - timedelta(days=8),
        ),
        (
            "CX-202",
            "Reconciliation discrepancies alert banner component",
            "IN_PROGRESS",
            3,
            "MEDIUM",
            10,  # Leo
            BASE_DATE + timedelta(days=2),
            ["frontend", "react"],
            BASE_DATE - timedelta(days=5),
        ),
        (
            "CX-203",
            "Export failed payments audit trail to CSV",
            "DONE",
            5,
            "LOW",
            11,  # Chloe
            BASE_DATE - timedelta(days=2),
            ["fullstack", "csv"],
            BASE_DATE - timedelta(days=7),
        ),
        (
            "CX-204",
            "Filter webhooks by processing latency and HTTP status",
            "IN_PROGRESS",
            3,
            "LOW",
            12,  # Samira
            BASE_DATE + timedelta(days=1),
            ["frontend", "filters"],
            BASE_DATE - timedelta(days=4),
        ),
    ]

    # Additional standard issues for Sprint 24 to reach ~30 issues
    for idx in range(15, 31):
        team_pfx = "CORE" if idx <= 20 else ("PAY" if idx <= 25 else "CX")
        k = f"{team_pfx}-{100 + idx}"
        d_id = ((idx - 1) % 12) + 1
        # Avoid assigning to David Kim (6) to keep his points exact at 16
        if d_id == 6:
            d_id = 7
        st = "DONE" if idx % 4 == 0 else ("IN_PROGRESS" if idx % 2 == 0 else "TO_DO")
        pts = 2 if idx % 3 == 0 else 3
        s24_specs.append(
            (
                k,
                f"Sprint 24 refinement task: {team_pfx} module enhancement {idx}",
                st,
                pts,
                "MEDIUM",
                d_id,
                BASE_DATE + timedelta(days=2),
                [team_pfx.lower(), "enhancement"],
                BASE_DATE - timedelta(days=6),
            )
        )

    for spec in s24_specs:
        key, title, status, points, priority, assignee, due_date, labels, created_at = spec
        issue_obj = {
            "id": issue_id_counter,
            "key": key,
            "title": title,
            "description": f"Specification for {key}: {title}.",
            "status": status,
            "story_points": points,
            "priority": priority,
            "sprint_id": 2,
            "assignee_id": assignee,
            "due_date": due_date.isoformat() if due_date else None,
            "labels": labels,
            "created_at": created_at.isoformat(),
            "updated_at": (BASE_DATE - timedelta(hours=4)).isoformat(),
        }
        issues.append(issue_obj)

        # Seed realistic history
        issue_history.append(
            {
                "id": hist_id_counter,
                "issue_id": issue_id_counter,
                "field_name": "status",
                "old_value": "TO_DO",
                "new_value": status,
                "changed_by": "Alex Rivera",
                "changed_at": (created_at + timedelta(days=1)).isoformat(),
            }
        )
        hist_id_counter += 1

        if key == "PAY-142":
            # Seed history showing it was marked BLOCKED 4 days ago
            issue_history.append(
                {
                    "id": hist_id_counter,
                    "issue_id": issue_id_counter,
                    "field_name": "status",
                    "old_value": "IN_PROGRESS",
                    "new_value": "BLOCKED",
                    "changed_by": "Elena Rostova",
                    "changed_at": (BASE_DATE - timedelta(days=4)).isoformat(),
                }
            )
            hist_id_counter += 1

        issue_id_counter += 1

    # Sprint 25 Issues (Upcoming, 15 issues)
    for i in range(1, 16):
        team_pfx = "CORE" if i <= 5 else ("PAY" if i <= 10 else "CX")
        key = f"{team_pfx}-{210 + i}"
        dev_id = ((i - 1) % 12) + 1
        issues.append(
            {
                "id": issue_id_counter,
                "key": key,
                "title": f"Sprint 25 Planned Roadmap: {team_pfx} Feature {i}",
                "description": "Planned deliverable for Sprint 25.",
                "status": "TO_DO",
                "story_points": 3,
                "priority": "MEDIUM",
                "sprint_id": 3,
                "assignee_id": dev_id,
                "due_date": (sprint_25_end - timedelta(days=2)).isoformat(),
                "labels": ["planned", "sprint-25"],
                "created_at": BASE_DATE.isoformat(),
                "updated_at": BASE_DATE.isoformat(),
            }
        )
        issue_id_counter += 1

    # 5. DEPENDENCIES
    # PAY-150 (Goal) blocked by PAY-142
    # PAY-142 blocked by PAY-139 (overdue, assigned to overloaded David Kim)
    dependencies.append(
        {
            "id": 1,
            "blocker_issue_key": "PAY-139",
            "blocked_issue_key": "PAY-142",
            "relationship_type": "blocks",
        }
    )
    dependencies.append(
        {
            "id": 2,
            "blocker_issue_key": "PAY-142",
            "blocked_issue_key": "PAY-150",
            "relationship_type": "blocks",
        }
    )

    # 6. PULL REQUESTS & CI RUNS (~30 pull requests)
    pull_requests = []
    ci_runs = []
    pr_id_counter = 1
    ci_id_counter = 1

    # PR 204: PAY-145 - WAITING FOR REVIEW FOR 4 DAYS (STUCK)
    pr_204_created = BASE_DATE - timedelta(days=4)
    pull_requests.append(
        {
            "id": pr_id_counter,
            "pr_number": 204,
            "repo": "DevCore/monorepo",
            "title": "PAY-145: Reconciliation report CSV parser and aggregator",
            "branch": "feature/PAY-145-reconciliation-parser",
            "status": "OPEN",
            "review_status": "PENDING_REVIEW",
            "issue_key": "PAY-145",
            "author_id": 6,  # David Kim
            "requested_reviewers": [5, 7],  # Elena, Rachel
            "pr_created_at": pr_204_created.isoformat(),
            "pr_updated_at": pr_204_created.isoformat(),
        }
    )
    ci_runs.append(
        {
            "id": ci_id_counter,
            "pr_id": pr_id_counter,
            "commit_hash": "a8f9c1e023456789012345678901234567890123",
            "status": "SUCCESS",
            "failed_step": None,
            "run_duration_seconds": 115,
            "run_completed_at": (pr_204_created + timedelta(minutes=15)).isoformat(),
        }
    )
    pr_id_counter += 1
    ci_id_counter += 1

    # PR 211: CORE-108 - FAILING CI (STUCK)
    pr_211_created = BASE_DATE - timedelta(days=2)
    pull_requests.append(
        {
            "id": pr_id_counter,
            "pr_number": 211,
            "repo": "DevCore/monorepo",
            "title": "CORE-108: Database connection pool sizing for worker tier",
            "branch": "fix/CORE-108-pool-saturation",
            "status": "OPEN",
            "review_status": "PENDING_REVIEW",
            "issue_key": "CORE-108",
            "author_id": 2,  # Sarah Chen
            "requested_reviewers": [1, 3],  # Alex, Marcus
            "pr_created_at": pr_211_created.isoformat(),
            "pr_updated_at": (BASE_DATE - timedelta(hours=6)).isoformat(),
        }
    )
    ci_runs.append(
        {
            "id": ci_id_counter,
            "pr_id": pr_id_counter,
            "commit_hash": "d4e5f6a7b8c90123456789012345678901234567",
            "status": "FAILURE",
            "failed_step": "test_pool_saturation",
            "run_duration_seconds": 182,
            "run_completed_at": (pr_211_created + timedelta(minutes=12)).isoformat(),
        }
    )
    pr_id_counter += 1
    ci_id_counter += 1

    # Additional pull requests across historical and current sprint issues
    additional_pr_specs = [
        ("CORE-105", 200, "CORE-105: Async Redis client migration", 3, "MERGED", "APPROVED", "SUCCESS", None, 7),
        ("CORE-107", 201, "CORE-107: OpenTelemetry distributed tracing", 1, "MERGED", "APPROVED", "SUCCESS", None, 6),
        ("CX-201", 202, "CX-201: Payment retry history drawer", 9, "MERGED", "APPROVED", "SUCCESS", None, 5),
        ("CX-203", 203, "CX-203: Export audit trail to CSV", 11, "MERGED", "APPROVED", "SUCCESS", None, 4),
        ("CORE-106", 205, "CORE-106: K8s HPA scaling triggers on webhook queue", 2, "OPEN", "APPROVED", "SUCCESS", None, 1),
        ("CX-202", 206, "CX-202: Reconciliation alert banner", 10, "OPEN", "PENDING_REVIEW", "SUCCESS", None, 1),
        ("CX-204", 207, "CX-204: Filter webhooks by processing latency", 12, "OPEN", "PENDING_REVIEW", "SUCCESS", None, 1),
        ("PAY-141", 208, "PAY-141: SEPA direct debit retry backoff", 6, "OPEN", "PENDING_REVIEW", "SUCCESS", None, 1),
    ]

    for spec in additional_pr_specs:
        ik, num, title, author, st, r_st, ci_st, fail_step, days_ago = spec
        created_dt = BASE_DATE - timedelta(days=days_ago)
        pull_requests.append(
            {
                "id": pr_id_counter,
                "pr_number": num,
                "repo": "DevCore/monorepo",
                "title": title,
                "branch": f"feature/{ik.lower()}",
                "status": st,
                "review_status": r_st,
                "issue_key": ik,
                "author_id": author,
                "requested_reviewers": [1 if author != 1 else 2],
                "pr_created_at": created_dt.isoformat(),
                "pr_updated_at": (created_dt + timedelta(hours=8)).isoformat(),
            }
        )
        ci_runs.append(
            {
                "id": ci_id_counter,
                "pr_id": pr_id_counter,
                "commit_hash": hashlib.sha1(f"pr-{num}".encode()).hexdigest(),
                "status": ci_st,
                "failed_step": fail_step,
                "run_duration_seconds": 105,
                "run_completed_at": (created_dt + timedelta(minutes=20)).isoformat(),
            }
        )
        pr_id_counter += 1
        ci_id_counter += 1

    # Fill up to 30 PRs with completed sprint 23 pull requests (numbers 151-170)
    for i in range(1, 21):
        num = 150 + i
        ik = f"CORE-{90 + (i % 5 + 1)}" if i <= 10 else f"PAY-{120 + (i % 5 + 1)}"
        auth_id = (i % 12) + 1
        created_dt = sprint_23_start + timedelta(days=i % 8)
        pull_requests.append(
            {
                "id": pr_id_counter,
                "pr_number": num,
                "repo": "DevCore/monorepo",
                "title": f"{ik}: Historical sprint PR {num}",
                "branch": f"feature/{ik.lower()}-hist-{num}",
                "status": "MERGED",
                "review_status": "APPROVED",
                "issue_key": ik,
                "author_id": auth_id,
                "requested_reviewers": [1],
                "pr_created_at": created_dt.isoformat(),
                "pr_updated_at": (created_dt + timedelta(days=1)).isoformat(),
            }
        )
        ci_runs.append(
            {
                "id": ci_id_counter,
                "pr_id": pr_id_counter,
                "commit_hash": hashlib.sha1(f"hist-{num}".encode()).hexdigest(),
                "status": "SUCCESS",
                "failed_step": None,
                "run_duration_seconds": 90,
                "run_completed_at": (created_dt + timedelta(minutes=25)).isoformat(),
            }
        )
        pr_id_counter += 1
        ci_id_counter += 1

    # 7. INCIDENT REPORTS (5 markdown files)
    incidents_meta = [
        {
            "id": 1,
            "incident_number": "INC-2024-01",
            "title": "Stripe Webhook Delivery Timeout under High Load",
            "service": "payment-service",
            "date": "2024-03-12",
            "filename": "INC-2024-01-stripe-webhook-timeout.md",
            "summary": "Stripe webhook worker exhausted thread pool due to unindexed merchant lookup query.",
            "content": """# Postmortem: INC-2024-01 Stripe Webhook Delivery Timeout

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
""",
        },
        {
            "id": 2,
            "incident_number": "INC-2024-02",
            "title": "Idempotency Key Race Condition in Payment Retry Engine",
            "service": "payment-service",
            "date": "2024-06-18",
            "filename": "INC-2024-02-idempotency-key-race.md",
            "summary": "Concurrent automated retry worker instances processed duplicate transactions due to non-atomic lock acquisition.",
            "content": """# Postmortem: INC-2024-02 Idempotency Key Race Condition

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
""",
        },
        {
            "id": 3,
            "incident_number": "INC-2024-03",
            "title": "Auth Token Cache Invalidation Cascading Failure",
            "service": "auth-service",
            "date": "2024-08-04",
            "filename": "INC-2024-03-auth-token-cache-invalidation.md",
            "summary": "Redis cluster node failover triggered thundering herd on primary auth database.",
            "content": """# Postmortem: INC-2024-03 Auth Token Cache Invalidation Cascading Failure

**Date:** 2024-08-04  
**Service:** auth-service  
**Severity:** SEV-2  

## Summary
A brief network partition caused Redis node eviction. All subsequent API gateway calls experienced cache misses, 
causing a thundering herd on the Postgres auth database that increased p99 latency from 4ms to 1200ms.

## Remediation & Learnings
1. Implemented probabilistic early expiration (XFetch algorithm) on JWT verification cache.
2. Added in-memory singleflight mutex in FastAPI middleware to deduplicate database verification requests.
""",
        },
        {
            "id": 4,
            "incident_number": "INC-2024-04",
            "title": "Database Connection Pool Exhaustion in Worker Tier",
            "service": "core-platform",
            "date": "2024-09-22",
            "filename": "INC-2024-04-database-connection-pool-exhaustion.md",
            "summary": "Celery background workers did not release SQLAlchemy sessions on unhandled task exceptions.",
            "content": """# Postmortem: INC-2024-04 Database Connection Pool Exhaustion in Worker Tier

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
""",
        },
        {
            "id": 5,
            "incident_number": "INC-2024-05",
            "title": "Payment Service Circuit Breaker Flapping",
            "service": "payment-service",
            "date": "2024-11-02",
            "filename": "INC-2024-05-payment-service-circuit-breaker.md",
            "summary": "Aggressive circuit breaker error threshold caused transient webhook rejections during brief merchant spikes.",
            "content": """# Postmortem: INC-2024-05 Payment Service Circuit Breaker Flapping

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
""",
        },
    ]

    for inc in incidents_meta:
        file_path = INCIDENTS_DIR / inc["filename"]
        file_path.write_text(inc["content"], encoding="utf-8")

    # 8. GROUND TRUTH FOR EVALS (deliberately seeded anomalies)
    ground_truth = {
        "sprint_id": 2,
        "sprint_name": "Sprint 24",
        "reference_date": BASE_DATE.isoformat(),
        "sprint_status": {
            "total_days": 10,
            "days_elapsed": 8,
            "days_remaining": 2,
            "total_points": 52,
            "completed_points": 18,
            "expected_completion_ratio": 0.80,
            "actual_completion_ratio": 0.346,
            "is_behind_schedule": True,
        },
        "anomalies": {
            "blocked_issues": [
                {
                    "key": "PAY-142",
                    "title": "Retry failed recurring payments engine",
                    "blocked_by": "PAY-139",
                    "days_blocked": 4,
                    "threshold_days": 3,
                    "severity": "HIGH",
                    "reason": "Issue PAY-142 has been blocked for 4 days (exceeds 3 day threshold).",
                }
            ],
            "overdue_issues": [
                {
                    "key": "PAY-139",
                    "title": "Stripe idempotency key race condition in webhook worker",
                    "due_date": (BASE_DATE - timedelta(days=2)).isoformat(),
                    "days_overdue": 2,
                    "status": "IN_PROGRESS",
                    "severity": "CRITICAL",
                    "reason": "Issue PAY-139 is overdue by 2 days and still IN_PROGRESS.",
                }
            ],
            "overloaded_developers": [
                {
                    "developer_id": 6,
                    "developer_name": "David Kim",
                    "capacity_points": 8,
                    "assigned_points": 16,
                    "overload_ratio": 2.0,
                    "severity": "HIGH",
                    "assigned_issues": ["PAY-139", "PAY-141", "PAY-145", "PAY-148"],
                    "reason": "Developer David Kim assigned 16 story points exceeding capacity of 8 points (200% load).",
                }
            ],
            "stuck_pull_requests": [
                {
                    "pr_number": 204,
                    "issue_key": "PAY-145",
                    "title": "PAY-145: Reconciliation report CSV parser and aggregator",
                    "age_days": 4,
                    "review_status": "PENDING_REVIEW",
                    "severity": "MEDIUM",
                    "reason": "PR #204 has been waiting for review for 4 days without activity.",
                },
                {
                    "pr_number": 211,
                    "issue_key": "CORE-108",
                    "title": "CORE-108: Database connection pool sizing for worker tier",
                    "age_days": 2,
                    "ci_status": "FAILURE",
                    "failed_step": "test_pool_saturation",
                    "severity": "HIGH",
                    "reason": "PR #211 has failing CI run in step 'test_pool_saturation'.",
                },
            ],
            "dependency_chain_threats": [
                {
                    "sprint_goal_issue": "PAY-150",
                    "dependency_chain": ["PAY-150", "PAY-142", "PAY-139"],
                    "root_blocker": "PAY-139",
                    "severity": "CRITICAL",
                    "reason": "Sprint Goal issue PAY-150 is blocked by PAY-142, which is blocked by overdue issue PAY-139.",
                }
            ],
        },
        "reassignment_ground_truth": {
            "source_issue": "PAY-139",
            "overloaded_developer": "David Kim",
            "recommended_candidates": [
                {
                    "developer_id": 7,
                    "developer_name": "Rachel Green",
                    "matching_skills": ["payments", "webhooks", "python", "stripe"],
                    "capacity_points": 7,
                    "assigned_points": 0,
                    "reason": "Rachel Green possesses direct payments and stripe skills with 7 points of free capacity.",
                }
            ],
        },
    }

    # Combined devcore JSON
    devcore_data = {
        "teams": teams,
        "developers": developers,
        "sprints": sprints,
        "issues": issues,
        "dependencies": dependencies,
        "issue_history": issue_history,
        "pull_requests": pull_requests,
        "ci_runs": ci_runs,
        "incidents": [
            {
                "id": inc["id"],
                "incident_number": inc["incident_number"],
                "title": inc["title"],
                "service": inc["service"],
                "date": inc["date"],
                "content": inc["content"],
            }
            for inc in incidents_meta
        ],
    }

    devcore_file = SEED_DIR / "devcore.json"
    devcore_file.write_text(json.dumps(devcore_data, indent=2), encoding="utf-8")

    gt_file = SEED_DIR / "ground_truth.json"
    gt_file.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")

    print("Generated seed data:")
    print(f"  Teams: {len(teams)}")
    print(f"  Developers: {len(developers)}")
    print(f"  Sprints: {len(sprints)}")
    print(f"  Issues: {len(issues)}")
    print(f"  Dependencies: {len(dependencies)}")
    print(f"  Pull Requests: {len(pull_requests)}")
    print(f"  CI Runs: {len(ci_runs)}")
    print(f"  Incidents: {len(incidents_meta)}")
    print(f"  Output: {devcore_file}")
    print(f"  Ground Truth: {gt_file}")


if __name__ == "__main__":
    generate_data()
