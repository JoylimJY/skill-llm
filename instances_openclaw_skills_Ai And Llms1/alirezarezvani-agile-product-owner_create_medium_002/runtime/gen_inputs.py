from pathlib import Path
import json

root = Path('.')

backlog = {
    "team": "Orchid Squad",
    "base_velocity": 30,
    "availability_factor": 0.9,
    "sprint_days": 10,
    "goal_theme": "Improve dashboard usefulness and reduce support friction",
    "stories": [
        {
            "id": "US-101",
            "title": "View key dashboard metrics",
            "points": 5,
            "priority": "High",
            "persona": "End User",
            "benefit": "so that users can track progress without exporting data",
            "acceptance": [
                "Given the user has access, when they open the dashboard, then key metrics are visible.",
                "Given data is unavailable, when the dashboard loads, then a friendly empty state is shown.",
                "Given the dashboard is opened, when the content renders, then it completes within 2 seconds."
            ],
            "invest": ["Independent", "Valuable", "Testable"]
        },
        {
            "id": "US-102",
            "title": "Export dashboard summary to CSV",
            "points": 3,
            "priority": "High",
            "persona": "Power User",
            "benefit": "so that reports can be shared with stakeholders",
            "acceptance": [
                "Given the user has visible metrics, when they click export, then a CSV download starts.",
                "Given export fails, when the system responds with an error, then a clear message is shown.",
                "Given a file is generated, when the export completes, then the filename includes the current date."
            ],
            "invest": ["Independent", "Negotiable", "Testable"]
        },
        {
            "id": "US-103",
            "title": "Add dashboard filters by date range",
            "points": 5,
            "priority": "Medium",
            "persona": "End User",
            "benefit": "so that users can review recent activity quickly",
            "acceptance": [
                "Given the user is on the dashboard, when they choose a date range, then the metrics update.",
                "Given an invalid range is selected, when the form is submitted, then validation is displayed.",
                "Given filters are applied, when the page refreshes, then the selection is preserved."
            ],
            "invest": ["Valuable", "Estimable", "Testable"]
        },
        {
            "id": "US-104",
            "title": "Improve search performance",
            "points": 8,
            "priority": "Medium",
            "persona": "Power User",
            "benefit": "so that frequent searches feel responsive",
            "acceptance": [
                "Given a search query is entered, when results load, then the response time is under 2 seconds.",
                "Given the search service is slow, when a timeout occurs, then the user sees a helpful retry message.",
                "Given the user uses keyboard navigation, when moving through results, then focus is visible."
            ],
            "invest": ["Valuable", "Small", "Testable"]
        },
        {
            "id": "US-105",
            "title": "Admin audit log overview",
            "points": 5,
            "priority": "High",
            "persona": "Administrator",
            "benefit": "so that admins can review sensitive actions",
            "acceptance": [
                "Given an admin opens the page, when the audit log loads, then the latest actions are displayed.",
                "Given no records exist, when the page is opened, then an empty state appears.",
                "Given the admin filters by action type, when results return, then only matching events are shown."
            ],
            "invest": ["Independent", "Valuable", "Testable"]
        },
        {
            "id": "US-106",
            "title": "Enable instant search caching",
            "points": 3,
            "priority": "Low",
            "persona": "Developer",
            "benefit": "so that repeated searches are faster",
            "acceptance": [
                "Given the cache is warm, when the same search repeats, then the cached response is used.",
                "Given cache data expires, when a new request arrives, then fresh results are fetched.",
                "Given caching is unavailable, when the feature runs, then search still works without errors."
            ],
            "invest": ["Negotiable", "Small", "Testable"]
        }
    ]
}

(root / 'backlog.json').write_text(json.dumps(backlog, indent=2), encoding='utf-8')
(root / 'references.txt').write_text(
    "Marker: INVEST-READY\nMarker: SPRINT-CAPACITY-90\nMarker: DASHBOARD-RELEASE-Q2\n",
    encoding='utf-8'
)
