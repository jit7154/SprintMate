#!/usr/bin/env python3
"""Evaluates deterministic risk engine precision, recall, and F1 score against ground truth."""

import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys

# Ensure backend directory is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db import async_session_maker
from app.services.adapters.demo_tracker import DemoTrackerAdapter
from app.services.adapters.github_demo import GithubDemoAdapter
from app.services.risk.scoring import evaluate_sprint_risk

REF_DATE = datetime(2026, 11, 17, 0, 0, 0)


async def run_risk_evaluation():
    ground_truth_path = ROOT_DIR / "data" / "seed" / "ground_truth.json"
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    expected_anomalies = ground_truth["anomalies"]
    expected_blocked = {item["key"] for item in expected_anomalies["blocked_issues"]}
    expected_overdue = {item["key"] for item in expected_anomalies["overdue_issues"]}
    expected_overloaded = {item["developer_name"] for item in expected_anomalies["overloaded_developers"]}
    expected_stuck_prs = {f"PR #{item['pr_number']}" for item in expected_anomalies["stuck_pull_requests"]}

    async with async_session_maker() as session:
        tracker = DemoTrackerAdapter(session)
        vcs = GithubDemoAdapter(session)

        sprint = await tracker.get_sprint()
        issues = await tracker.list_issues(sprint_id=sprint["id"])
        prs = await vcs.list_pull_requests()
        devs = await tracker.list_developers()

        detailed_issues = []
        for i in issues:
            det = await tracker.get_issue(i["key"])
            detailed_issues.append(det or i)

        evaluation = evaluate_sprint_risk(sprint, detailed_issues, prs, devs, now=REF_DATE)

    # Collect detected keys from all category findings in breakdown
    detected_blocked = set()
    detected_overdue = set()
    detected_overloaded = set()
    detected_stuck_prs = set()

    for category in evaluation.breakdown:
        for finding in category.findings:
            if finding.rule_id == "RULE_BLOCKED_ISSUE":
                detected_blocked.update(finding.affected_keys)
            elif finding.rule_id == "RULE_OVERDUE_ISSUE":
                detected_overdue.update(finding.affected_keys)
            elif finding.rule_id in {"RULE_DEV_OVERLOAD", "RULE_DEVELOPER_OVERLOAD"}:
                dev_name = finding.metadata.get("developer_name") or finding.affected_keys[0]
                detected_overloaded.add(dev_name)
            elif finding.rule_id in {"RULE_PR_NO_REVIEW", "RULE_PR_FAILING_CI"}:
                for k in finding.affected_keys:
                    if k.startswith("PR #"):
                        detected_stuck_prs.add(k)

    categories = [
        ("Blocked Issues", expected_blocked, detected_blocked),
        ("Overdue Issues", expected_overdue, detected_overdue),
        ("Overloaded Devs", expected_overloaded, detected_overloaded),
        ("Stuck Pull Requests", expected_stuck_prs, detected_stuck_prs),
    ]

    total_tp = 0
    total_fp = 0
    total_fn = 0

    print("=" * 70)
    print("SPRINTMATE RISK ENGINE EVALUATION REPORT")
    print(f"Sprint: {evaluation.sprint_name} | Overall Score: {evaluation.overall_score}/100 ({evaluation.risk_level})")
    print("=" * 70)
    print(f"{'Category':<22} | {'Expected':<10} | {'Detected':<10} | {'Prec':<7} | {'Recall':<7} | {'F1':<7}")
    print("-" * 70)

    for name, exp, det in categories:
        tp = len(exp.intersection(det))
        fp = len(det - exp)
        fn = len(exp - det)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 1.0

        print(f"{name:<22} | {len(exp):<10} | {len(det):<10} | {prec:<7.2f} | {rec:<7.2f} | {f1:<7.2f}")

    overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 1.0

    print("-" * 70)
    print(f"{'OVERALL AGGREGATE':<22} | {total_tp + total_fn:<10} | {total_tp + total_fp:<10} | {overall_prec:<7.2f} | {overall_rec:<7.2f} | {overall_f1:<7.2f}")
    print("=" * 70)

    return {
        "precision": overall_prec,
        "recall": overall_rec,
        "f1": overall_f1,
        "overall_score": evaluation.overall_score,
        "risk_level": evaluation.risk_level,
    }


if __name__ == "__main__":
    asyncio.run(run_risk_evaluation())
