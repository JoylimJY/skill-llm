import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)

# Create marker content for verification
MARKER_TEAM_MEMBER = "team-member-alice-johnson-senior-dev"
MARKER_KANBAN_TASK = "implement-biometric-authentication-epic"
MARKER_SPRINT_NAME = "Sprint-23-Mobile-Banking-Q4"
MARKER_CHART_DATA = "velocity-chart-fintech-metrics"
MARKER_THEME_TOGGLE = "dark-light-theme-switcher"

# Create project requirements file
requirements = {
    "project_name": "DevTracker Pro",
    "company": "FinTech Solutions Inc",
    "required_features": [
        "Kanban board with drag-and-drop functionality",
        "Team member management with avatars and roles",
        "Sprint planning calendar with date selection",
        "Analytics dashboard with velocity and burndown charts",
        "Dark/light theme toggle",
        "Responsive design for mobile and desktop",
        "Professional styling avoiding AI-generated patterns"
    ],
    "sample_data": {
        "team_members": [
            {"id": 1, "name": "Alice Johnson", "role": "Senior Developer", "avatar": "AJ", "marker": MARKER_TEAM_MEMBER},
            {"id": 2, "name": "Bob Chen", "role": "Frontend Developer", "avatar": "BC"},
            {"id": 3, "name": "Carol Davis", "role": "UX Designer", "avatar": "CD"},
            {"id": 4, "name": "David Wilson", "role": "DevOps Engineer", "avatar": "DW"},
            {"id": 5, "name": "Eva Martinez", "role": "Product Manager", "avatar": "EM"}
        ],
        "kanban_columns": ["Backlog", "In Progress", "Code Review", "Testing", "Done"],
        "tasks": [
            {"id": 1, "title": "Implement biometric authentication", "status": "In Progress", "assignee": "Alice Johnson", "priority": "High", "marker": MARKER_KANBAN_TASK},
            {"id": 2, "title": "Design transaction history UI", "status": "Code Review", "assignee": "Bob Chen", "priority": "Medium"},
            {"id": 3, "title": "Set up CI/CD pipeline", "status": "Done", "assignee": "David Wilson", "priority": "High"},
            {"id": 4, "title": "User research for mobile app", "status": "Testing", "assignee": "Carol Davis", "priority": "Low"},
            {"id": 5, "title": "API rate limiting implementation", "status": "Backlog", "assignee": "Alice Johnson", "priority": "Medium"}
        ],
        "current_sprint": {
            "name": MARKER_SPRINT_NAME,
            "start_date": "2024-01-15",
            "end_date": "2024-01-29",
            "goal": "Complete mobile banking authentication features"
        },
        "analytics_data": {
            "velocity": [8, 12, 10, 15, 13, 11],
            "burndown": [45, 38, 32, 28, 20, 15, 8, 0],
            "marker": MARKER_CHART_DATA
        },
        "theme_marker": MARKER_THEME_TOGGLE
    }
}

with open('project_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

# Create validation markers file
markers = {
    "expected_markers": [
        MARKER_TEAM_MEMBER,
        MARKER_KANBAN_TASK,
        MARKER_SPRINT_NAME,
        MARKER_CHART_DATA,
        MARKER_THEME_TOGGLE
    ]
}

with open('validation_markers.json', 'w') as f:
    json.dump(markers, f, indent=2)

print("Generated project requirements and validation markers")