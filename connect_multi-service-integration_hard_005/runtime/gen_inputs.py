import json
from datetime import datetime, timezone

issues = [
    {"id": 101, "title": "Login page crashes on mobile", "labels": ["bug", "mobile"], "created_at": "2024-01-15T10:00:00Z", "body": "The login page throws a JS error on iOS 17."},
    {"id": 102, "title": "Add dark mode support", "labels": ["enhancement", "ui"], "created_at": "2024-01-16T11:00:00Z", "body": "Users are requesting a dark mode toggle."},
    {"id": 103, "title": "API timeout on large payloads", "labels": ["bug", "performance"], "created_at": "2024-01-17T12:00:00Z", "body": "Requests exceeding 10MB timeout after 30s."},
    {"id": 104, "title": "Update README with setup instructions", "labels": ["documentation"], "created_at": "2024-01-18T09:00:00Z", "body": "README is outdated and missing Docker steps."},
    {"id": 105, "title": "Memory leak in worker thread", "labels": ["bug", "critical"], "created_at": "2024-01-19T14:00:00Z", "body": "Worker threads consume 2GB RAM after 6 hours."},
    {"id": 106, "title": "Improve search performance", "labels": ["enhancement"], "created_at": "2024-01-20T08:30:00Z", "body": "Full-text search takes 4s on large datasets."},
    {"id": 107, "title": "CSV export produces malformed output", "labels": ["bug"], "created_at": "2024-01-21T15:45:00Z", "body": "Special characters break CSV column alignment."}
]

config = {
    "slack_channel": "#engineering-alerts",
    "email_recipient": "devteam@example.com",
    "summary_prefix": "WEEKLY-BUG-DIGEST"
}

with open('issues.json', 'w') as f:
    json.dump(issues, f, indent=2)

with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('Generated issues.json and config.json')
