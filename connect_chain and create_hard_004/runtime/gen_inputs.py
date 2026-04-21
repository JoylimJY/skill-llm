import json
import datetime

def generate_issues():
    base_date = datetime.datetime(2024, 6, 10, 12, 0, 0)  # Fixed date for determinism
    issues = [
        {
            "title": "Crash on startup",
            "body": "The app crashes immediately when starting. Steps to reproduce are...",
            "labels": ["bug"],
            "created_at": (base_date - datetime.timedelta(days=i)).isoformat() + "Z",
            "state": "open"
        }
        for i in range(3)
    ] + [
        {
            "title": "Feature request: dark mode",
            "body": "Many users want a dark mode for the UI.",
            "labels": ["enhancement"],
            "created_at": (base_date - datetime.timedelta(days=10)).isoformat() + "Z",
            "state": "open"
        }
    ]
    with open("github_issues.json", "w") as f:
        json.dump(issues, f, indent=2)

generate_issues()
