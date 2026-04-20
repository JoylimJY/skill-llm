from pathlib import Path
import json

backlog = {
    "sprint_goal_marker": "SPRINT-GOAL-ALPHA-42",
    "team_velocity": 30,
    "availability_factor": 0.9,
    "capacity_marker": "CAPACITY-MARKER-17",
    "stories": [
        {"id": "US-101", "title": "View dashboard metrics", "points": 5, "priority": "High", "bucket": "committed"},
        {"id": "US-102", "title": "Export report to PDF", "points": 3, "priority": "High", "bucket": "committed"},
        {"id": "US-103", "title": "Search by keyword", "points": 5, "priority": "Medium", "bucket": "committed"},
        {"id": "US-104", "title": "Customize widget layout", "points": 5, "priority": "Medium", "bucket": "committed"},
        {"id": "US-105", "title": "Theme toggle", "points": 2, "priority": "Low", "bucket": "stretch"},
        {"id": "US-106", "title": "Print view", "points": 2, "priority": "Low", "bucket": "stretch"}
    ]
}

Path("backlog.json").write_text(json.dumps(backlog, indent=2), encoding="utf-8")
Path("instructions.txt").write_text(
    "Use the backlog.json file to draft a sprint plan note. Include the sprint goal marker and capacity marker exactly once.",
    encoding="utf-8",
)
