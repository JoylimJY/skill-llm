import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create realistic directory structure for a wellness tech startup project
dirs = [
    "scripts",
    "references",
    "reports/daily",
    "reports/weekly",
    "reports/archive",
    "config",
    "data/raw",
    "data/processed",
    "logs",
    "templates",
    "tests",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Create the actual skill script: scripts/daily_briefing.py ---
daily_briefing_script = r"""#!/usr/bin/env python3
"""
daily_briefing_script += r"""
Personal daily briefing generator.
Usage: python3 daily_briefing.py --location Columbus --output briefing.json
"""
daily_briefing_script += r"""

import argparse
import json
import sys
from datetime import datetime, timezone

def generate_briefing(location="Columbus"):
    briefing = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'location': location,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'weekday': datetime.now().strftime('%A'),
        'sections': []
    }

    briefing['sections'].append({
        'title': '\U0001f305 Good Morning!',
        'content': 'Start your day with focus and intention.',
        'type': 'motivation'
    })

    briefing['sections'].append({
        'title': '\U0001f321 Weather Check',
        'content': f'Check the weather in {location} before heading out. Plan your day accordingly.',
        'type': 'weather'
    })

    briefing['sections'].append({
        'title': '\U0001f3af Today\'s Focus',
        'content': 'Top 3 priorities:\n1. _______________________________________\n2. _______________________________________\n3. _______________________________________\n\nTip: Start with the hardest task first.',
        'type': 'priorities'
    })

    briefing['sections'].append({
        'title': '\u2705 Daily Habits',
        'content': 'Today\'s habits:\n\u25a1 Morning routine (exercise, meditation, journal)\n\u25a1 Hydration goals (8 glasses)\n\u25a1 Learning time (30 min reading/course)\n\u25a1 Evening review (what went well?)',
        'type': 'habits'
    })

    briefing['sections'].append({
        'title': '\U0001f49a Self-Care',
        'content': 'Remember:\n\u2022 Take breaks and rest your eyes\n\u2022 Step away from screens for 5 min/hour\n\u2022 Stay hydrated\n\u2022 End work at a reasonable time',
        'type': 'selfcare'
    })

    briefing['sections'].append({
        'title': '\U0001f319 Evening Review',
        'content': 'Before bed:\n1. What did I accomplish today?\n2. What am I grateful for?\n3. What could I have done better?\n4. Tomorrow\'s top priority?',
        'type': 'reflection'
    })

    return briefing

def format_briefing(briefing):
    output = f"\U0001f4cb Daily Briefing - {briefing['date']} ({briefing['weekday']})\n\n"
    for section in briefing['sections']:
        output += f"{section['title']}\n"
        output += section['content'] + "\n"
        output += "\n"
    return output

def save_briefing(briefing, output_file='daily_briefing.json'):
    with open(output_file, 'w') as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)
    print(f"Saved briefing to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate personal daily briefing')
    parser.add_argument('--location', default='Columbus', help='Your location for weather context')
    parser.add_argument('--output', default='daily_briefing.json', help='Output file')
    parser.add_argument('--summary', action='store_true', help='Print human-readable summary')

    args = parser.parse_args()

    briefing = generate_briefing(args.location)

    if args.summary:
        print(format_briefing(briefing))

    save_briefing(briefing, args.output)

if __name__ == '__main__':
    main()
"""

with open(os.path.join(workspace, "scripts", "daily_briefing.py"), "w") as f:
    f.write(daily_briefing_script)

# --- Distractor files ---

# references/productivity.md
with open(os.path.join(workspace, "references", "productivity.md"), "w") as f:
    f.write("# Productivity Tips\n\nFocus on deep work. Batch similar tasks. Use time blocking.\n")

# config/settings.json - outdated/wrong config that should NOT be used as output
with open(os.path.join(workspace, "config", "settings.json"), "w") as f:
    json.dump({"location": "Denver", "output": "old_briefing.json", "timezone": "UTC"}, f, indent=2)

# reports/daily/sample_report.json - distractor with wrong structure
with open(os.path.join(workspace, "reports", "daily", "sample_report.json"), "w") as f:
    json.dump({"date": "2024-01-01", "summary": "Old report", "items": []}, f, indent=2)

# reports/weekly/week_summary.txt
with open(os.path.join(workspace, "reports", "weekly", "week_summary.txt"), "w") as f:
    f.write("Week 1 summary: team met all targets. Morale high.\n")

# reports/archive/2024_briefing.json - distractor with partial structure
with open(os.path.join(workspace, "reports", "archive", "2024_briefing.json"), "w") as f:
    json.dump({
        "date": "2024-03-15",
        "location": "Austin",
        "sections": [{"title": "Morning", "content": "Wake up", "type": "motivation"}]
    }, f, indent=2)

# data/raw/employees.csv
with open(os.path.join(workspace, "data", "raw", "employees.csv"), "w") as f:
    f.write("name,office,timezone\nAlice,Austin,America/Chicago\nBob,Austin,America/Chicago\n")

# data/processed/team_schedule.json
with open(os.path.join(workspace, "data", "processed", "team_schedule.json"), "w") as f:
    json.dump({"week": "2025-W01", "standups": ["Monday 9am", "Wednesday 9am", "Friday 9am"]}, f)

# logs/app.log
with open(os.path.join(workspace, "logs", "app.log"), "w") as f:
    f.write("[INFO] 2025-01-01 07:00:01 - Briefing generated for Columbus\n")
    f.write("[INFO] 2025-01-02 07:00:01 - Briefing generated for Columbus\n")

# templates/briefing_template.txt - intentionally incomplete/wrong
with open(os.path.join(workspace, "templates", "briefing_template.txt"), "w") as f:
    f.write("Date: {date}\nLocation: {location}\n[SECTIONS GO HERE]\n")

# tests/test_briefing.py - a distractor test file
with open(os.path.join(workspace, "tests", "test_briefing.py"), "w") as f:
    f.write("""# Placeholder test file
def test_placeholder():
    assert True
""")

# config/cron_examples.txt
with open(os.path.join(workspace, "config", "cron_examples.txt"), "w") as f:
    f.write("0 7 * * * python3 scripts/daily_briefing.py --location Columbus\n")

print("Workspace initialized successfully.")