import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "app/components/ui",
    "app/components/calendar",
    "app/services/location",
    "app/services/notification",
    "app/config",
    "app/assets/icons",
    "app/assets/fonts",
    "data/cities/europe",
    "data/cities/asia",
    "data/cities/middleeast",
    "logs/2025",
    "scripts/deprecated",
    "tests/unit",
    "tests/integration",
    "docs/api",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor files
distractor_files = {
    "app/components/ui/PrayerCard.jsx": "// Prayer card component placeholder\nexport default function PrayerCard() { return null; }",
    "app/components/calendar/RamadanCalendar.tsx": "// TODO: Implement Ramadan calendar\nconst RamadanCalendar = () => {};",
    "app/services/location/geoip.py": "# GeoIP service stub\ndef get_location(ip): return {'city': 'Unknown', 'country': 'XX'}",
    "app/services/notification/push.js": "// Push notification service\nconst sendReminder = (msg) => console.log(msg);",
    "app/config/app.json": json.dumps({
        "appName": "RamadanCompanion",
        "version": "2.1.4",
        "defaultLang": "en",
        "supportedCities": 142,
        "apiTimeout": 5000
    }, indent=2),
    "app/assets/icons/moon.svg": "<svg><!-- moon icon --></svg>",
    "app/assets/fonts/arabic-font.css": "/* Arabic font face declarations */",
    "data/cities/europe/uk.json": json.dumps({"cities": ["London", "Manchester", "Birmingham"], "timezone": "Europe/London"}, indent=2),
    "data/cities/europe/france.json": json.dumps({"cities": ["Paris", "Lyon", "Marseille"], "timezone": "Europe/Paris"}, indent=2),
    "data/cities/asia/turkey.json": json.dumps({"cities": ["Istanbul", "Ankara", "Izmir"], "timezone": "Europe/Istanbul"}, indent=2),
    "data/cities/middleeast/egypt.json": json.dumps({"cities": ["Cairo", "Alexandria", "Giza"], "timezone": "Africa/Cairo"}, indent=2),
    "data/cities/middleeast/uae.json": json.dumps({"cities": ["Dubai", "Abu Dhabi", "Sharjah"], "timezone": "Asia/Dubai"}, indent=2),
    "logs/2025/app.log": "2025-03-01 17:45:00 INFO Prayer times fetched for Istanbul\n2025-03-01 17:45:01 INFO Response: 200 OK\n2025-03-02 04:10:00 INFO Sahur reminder sent\n",
    "scripts/deprecated/old_prayer_calc.sh": "#!/bin/bash\n# DEPRECATED - do not use\necho 'This script is deprecated'",
    "tests/unit/test_location.py": "import pytest\ndef test_london_timezone():\n    assert True  # placeholder",
    "tests/integration/test_api.py": "import pytest\ndef test_prayer_api_response():\n    pass  # TODO",
    "docs/api/endpoints.md": "# API Endpoints\n## GET /prayer-times\nReturns prayer times for a given city.\n## Parameters\n- city: string\n- date: YYYY-MM-DD\n- lang: language code",
    "app/config/cities_override.json": json.dumps({
        "overrides": {
            "london": {"lat": 51.5074, "lon": -0.1278},
            "cairo": {"lat": 30.0444, "lon": 31.2357}
        }
    }, indent=2),
    ".env.example": "API_KEY=your_key_here\nDEFAULT_CITY=Istanbul\nDEFAULT_LANG=tr\nMOCK_API=false",
    "package.json": json.dumps({
        "name": "ramadan-companion",
        "version": "2.1.4",
        "scripts": {"start": "node index.js", "test": "jest"}
    }, indent=2),
    "requirements.txt": "flask==3.0.0\nrequests==2.31.0\npytz==2024.1\npython-dateutil==2.9.0\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── Task context file: a product requirements document ──────────────────────
prd_content = """\
# Ramadan Companion App - Content Pipeline Task

## Task ID: CP-2024-031
## Assigned: Backend Integration Team
## Priority: HIGH

### Objective
Generate standardized prayer time data cards for the following cities and languages,
to be consumed by the mobile app's content rendering pipeline.

### Required Outputs
The content pipeline expects two output files to be placed anywhere accessible:

1. File: london_en_prayercard.txt
   - City: London
   - Language: English
   - Date: 2026-03-15 (a Sunday in Ramadan 2026)

2. File: cairo_ar_prayercard.txt
   - City: Cairo  
   - Language: Arabic
   - Date: 2026-03-15

### Notes
- The Ramadan times skill is available in the workspace under the `skill/` directory.
- Both files must be generated using the skill (not hardcoded).
- The output format must match exactly what the skill produces.
- The mock API server will be running on localhost:5722 during generation.
- Do NOT use external internet APIs - the mock server handles all requests.

### Acceptance Criteria
- Files are present with correct naming
- Content follows the skill's standard output format
- Countdown ("time until iftar") must be present in each file
- Language-specific formatting must be correct
"""

with open(os.path.join(workspace, "TASK_BRIEF.md"), "w") as f:
    f.write(prd_content)

# ── Skill config that points to mock API ────────────────────────────────────
os.makedirs(os.path.join(workspace, "skill"), exist_ok=True)

skill_config = {
    "name": "ramadan-times",
    "version": "1.0.0",
    "api": {
        "primary": "http://localhost:5722/api/sunrise-sunset",
        "fallback": "http://localhost:5722/api/prayer-times",
        "timeout": 10
    },
    "defaults": {
        "location": "Istanbul",
        "language": "tr"
    },
    "mock_mode": True
}

with open(os.path.join(workspace, "skill/config.json"), "w") as f:
    json.dump(skill_config, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for _ in _[2])} files")