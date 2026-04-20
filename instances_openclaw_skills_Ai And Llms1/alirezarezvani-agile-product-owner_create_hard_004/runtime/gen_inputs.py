import json
from pathlib import Path

root = Path('.')

backlog = {
    "project": "Atlas Analytics",
    "team": "North Star Squad",
    "average_velocity": 28,
    "availability_factor": 0.9,
    "sprint_goal": "Improve dashboard usability and reduce reporting friction for end users",
    "items": [
        {"id": "US-101", "title": "Dashboard filters persist across refresh", "persona": "End User", "points": 5, "value": 5, "risk": 2, "effort": 3, "priority_hint": "High", "marker": "MARKER-FILTER-PERSIST"},
        {"id": "US-102", "title": "Export report to CSV", "persona": "Power User", "points": 3, "value": 4, "risk": 1, "effort": 2, "priority_hint": "High", "marker": "MARKER-EXPORT-CSV"},
        {"id": "US-103", "title": "Admin view for failed sync jobs", "persona": "Administrator", "points": 8, "value": 5, "risk": 4, "effort": 5, "priority_hint": "Medium", "marker": "MARKER-ADMIN-SYNC"},
        {"id": "US-104", "title": "Inline help tips on settings page", "persona": "New User", "points": 2, "value": 3, "risk": 1, "effort": 1, "priority_hint": "Medium", "marker": "MARKER-HELP-TIPS"},
        {"id": "US-105", "title": "Dark mode toggle", "persona": "Power User", "points": 3, "value": 2, "risk": 1, "effort": 2, "priority_hint": "Low", "marker": "MARKER-DARK-MODE"},
        {"id": "US-106", "title": "Search dashboard by customer name", "persona": "End User", "points": 5, "value": 5, "risk": 2, "effort": 4, "priority_hint": "High", "marker": "MARKER-DASH-SEARCH"},
        {"id": "US-107", "title": "Spike: investigate caching strategy", "persona": "Developer", "points": 2, "value": 2, "risk": 5, "effort": 2, "priority_hint": "Medium", "marker": "MARKER-CACHE-SPIKE"},
        {"id": "US-108", "title": "Bulk archive old reports", "persona": "Administrator", "points": 8, "value": 4, "risk": 3, "effort": 5, "priority_hint": "Low", "marker": "MARKER-BULK-ARCHIVE"},
        {"id": "US-109", "title": "Improve error message for failed exports", "persona": "End User", "points": 2, "value": 4, "risk": 1, "effort": 1, "priority_hint": "High", "marker": "MARKER-EXPORT-ERROR"}
    ]
}

(root / 'backlog.json').write_text(json.dumps(backlog, indent=2), encoding='utf-8')
(root / 'notes.txt').write_text(
    "Atlas Analytics planning notes\n"
    "Marker: RELEASE-NOTES-2025-Q2\n"
    "Goal: prepare sprint package with committed and stretch items.\n"
    "Reminder: keep language concise and stakeholder-friendly.\n",
    encoding='utf-8'
)
