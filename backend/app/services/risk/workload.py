from typing import Any


def calculate_developer_workloads(
    developers: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    include_done: bool = False,
) -> list[dict[str, Any]]:
    """Compute workload, capacity, and utilization per developer."""
    workload_map: dict[int, dict[str, Any]] = {}

    for dev in developers:
        dev_id = dev["id"]
        workload_map[dev_id] = {
            "id": dev_id,
            "name": dev["name"],
            "email": dev.get("email"),
            "role": dev.get("role"),
            "team_id": dev.get("team_id"),
            "team_name": dev.get("team_name"),
            "skills": dev.get("skills", []),
            "weekly_capacity_points": dev.get("weekly_capacity_points", 8),
            "assigned_points": 0,
            "assigned_issues_count": 0,
            "assigned_issue_keys": [],
            "available_capacity_points": 0,
            "utilization_ratio": 0.0,
            "is_overloaded": False,
        }

    for issue in issues:
        assignee_id = issue.get("assignee_id")
        if not assignee_id or assignee_id not in workload_map:
            continue

        status = issue.get("status")
        if not include_done and status in {"DONE", "COMPLETED"}:
            continue

        pts = issue.get("story_points", 0)
        entry = workload_map[assignee_id]
        entry["assigned_points"] += pts
        entry["assigned_issues_count"] += 1
        entry["assigned_issue_keys"].append(issue["key"])

    result = []
    for entry in workload_map.values():
        cap = entry["weekly_capacity_points"]
        pts = entry["assigned_points"]
        ratio = pts / max(cap, 1)
        entry["utilization_ratio"] = round(ratio, 2)
        entry["available_capacity_points"] = max(0, cap - pts)
        entry["is_overloaded"] = pts > cap
        result.append(entry)

    # Sort by assigned_points descending
    result.sort(key=lambda d: d["assigned_points"], reverse=True)
    return result


def find_reassignment_candidates(
    required_skills: list[str],
    story_points: int,
    workload_summary: list[dict[str, Any]],
    exclude_developer_id: int | None = None,
) -> list[dict[str, Any]]:
    """Rank developer candidates by skill match overlap and available capacity."""
    candidates = []

    for dev in workload_summary:
        if exclude_developer_id and dev["id"] == exclude_developer_id:
            continue

        dev_skills = set(s.lower() for s in dev.get("skills", []))
        req_skills = set(s.lower() for s in required_skills)
        matched = dev_skills.intersection(req_skills)

        # Candidate must have at least one matching skill or belong to the team
        if not matched:
            continue

        available_cap = dev.get("available_capacity_points", 0)
        can_fit = available_cap >= story_points

        # Score candidates: skill match count * 10 + available capacity points
        candidate_score = (len(matched) * 10) + available_cap
        if can_fit:
            candidate_score += 25

        candidates.append(
            {
                "developer_id": dev["id"],
                "developer_name": dev["name"],
                "email": dev.get("email"),
                "matched_skills": list(matched),
                "available_capacity_points": available_cap,
                "current_utilization_ratio": dev.get("utilization_ratio", 0.0),
                "can_fit_points": can_fit,
                "score": candidate_score,
            }
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
