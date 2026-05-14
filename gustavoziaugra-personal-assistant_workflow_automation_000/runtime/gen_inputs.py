import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the skill script structure (as it would exist in the skill) ---
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

references_dir = workspace / "references"
references_dir.mkdir(parents=True, exist_ok=True)

# Write the actual daily_briefing.py script (as defined in SKILL.md)
briefing_script = scripts_dir / "daily_briefing.py"
briefing_script.write_text('''#!/usr/bin/env python3
"""
Personal daily briefing generator.
Usage: python3 daily_briefing.py --location Columbus --output briefing.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone

def generate_briefing(location="Columbus"):
    briefing = {
        \'generated_at\': datetime.now(timezone.utc).isoformat(),
        \'location\': location,
        \'date\': datetime.now().strftime(\'%Y-%m-%d\'),
        \'weekday\': datetime.now().strftime(\'%A\'),
        \'sections\': []
    }

    briefing[\'sections\'].append({
        \'title\': \'\\U0001f305 Good Morning!\',
        \'content\': \'Start your day with focus and intention.\',
        \'type\': \'motivation\'
    })

    briefing[\'sections\'].append({
        \'title\': \'\\U0001f321 Weather Check\',
        \'content\': f\'Check the weather in {location} before heading out. Plan your day accordingly.\',
        \'type\': \'weather\'
    })

    briefing[\'sections\'].append({
        \'title\': \'\\U0001f3af Today\\\'s Focus\',
        \'content\': \'\'\'Top 3 priorities:
1. _______________________________________
2. _______________________________________
3. _______________________________________

Tip: Start with the hardest task first.\'\'\',
        \'type\': \'priorities\'
    })

    briefing[\'sections\'].append({
        \'title\': \'\\u2705 Daily Habits\',
        \'content\': \'\'\'Today\\\'s habits:
\\u25a1 Morning routine (exercise, meditation, journal)
\\u25a1 Hydration goals (8 glasses)
\\u25a1 Learning time (30 min reading/course)
\\u25a1 Evening review (what went well?)\'\'\',
        \'type\': \'habits\'
    })

    briefing[\'sections\'].append({
        \'title\': \'\\U0001f49a Self-Care\',
        \'content\': \'\'\'Remember:
\\u2022 Take breaks and rest your eyes
\\u2022 Step away from screens for 5 min/hour
\\u2022 Stay hydrated
\\u2022 End work at a reasonable time\'\'\',
        \'type\': \'selfcare\'
    })

    briefing[\'sections\'].append({
        \'title\': \'\\U0001f319 Evening Review\',
        \'content\': \'\'\'Before bed:
1. What did I accomplish today?
2. What am I grateful for?
3. What could I have done better?
4. Tomorrow\\\'s top priority?\'\'\',
        \'type\': \'reflection\'
    })

    return briefing

def format_briefing(briefing):
    output = f"\\U0001f4cb Daily Briefing - {briefing[\'date\']} ({briefing[\'weekday\']})\\n\\n"
    for section in briefing[\'sections\']:
        output += f"{section[\'title\']}\\n"
        output += section[\'content\'] + "\\n"
        output += "\\n"
    return output

def save_briefing(briefing, output_file=\'daily_briefing.json\'):
    with open(output_file, \'w\') as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)
    print(f"Saved briefing to {output_file}")

def main():
    parser = argparse.ArgumentParser(description=\'Generate personal daily briefing\')
    parser.add_argument(\'--location\', default=\'Columbus\', help=\'Your location for weather context\')
    parser.add_argument(\'--output\', default=\'daily_briefing.json\', help=\'Output file\')
    parser.add_argument(\'--summary\', action=\'store_true\', help=\'Print human-readable summary\')

    args = parser.parse_args()

    briefing = generate_briefing(args.location)

    if args.summary:
        print(format_briefing(briefing))

    save_briefing(briefing, args.output)

if __name__ == \'__main__\':
    main()
''')

# Write references/productivity.md (distractor)
(references_dir / "productivity.md").write_text("""# Productivity Tips

## Focus Techniques
- Pomodoro: 25 min work, 5 min break
- Time blocking: schedule focused blocks
- Single-tasking over multitasking

## Habit Building
- Start small: 2-minute rule
- Habit stacking: attach new to existing
- Track streaks visually

## Morning Rituals
- Avoid phone for first 30 minutes
- Hydrate before coffee
- Review your top 3 goals

## Evening Wind-Down
- No screens 1 hour before sleep
- Write tomorrow's top priority
- Practice gratitude
""")

# --- Distractor files to make environment realistic and noisy ---

# Team config directory
team_dir = workspace / "team"
team_dir.mkdir(exist_ok=True)

offices = [
    {"city": "Austin", "timezone": "America/Chicago", "team_size": 12},
    {"city": "Denver", "timezone": "America/Denver", "team_size": 8},
]
(team_dir / "offices.json").write_text(json.dumps(offices, indent=2))

(team_dir / "team_roster.csv").write_text(
    "name,office,role\n"
    "Alice Chen,Austin,Engineer\n"
    "Bob Martinez,Denver,Designer\n"
    "Carol White,Austin,PM\n"
    "Dan Lee,Denver,Engineer\n"
)

# Logs directory with old briefings (wrong format - distractor)
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)

old_briefing_bad = {
    "date": "2025-01-10",
    "location": "Austin",
    "notes": "This is an old non-standard format",
    "tasks": ["task1", "task2"]
}
(logs_dir / "old_briefing_2025-01-10.json").write_text(json.dumps(old_briefing_bad, indent=2))

(logs_dir / "app.log").write_text(
    "[INFO] 2025-01-10 07:01:00 Briefing generation started\n"
    "[INFO] 2025-01-10 07:01:01 Location: Austin\n"
    "[WARN] 2025-01-10 07:01:02 Weather API unavailable\n"
    "[INFO] 2025-01-10 07:01:02 Briefing saved\n"
)

# Config directory
config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "app_config.yaml").write_text(
    "app:\n"
    "  name: daily-briefing-service\n"
    "  version: 1.2.0\n"
    "  default_location: Columbus\n"
    "schedule:\n"
    "  morning: '0 7 * * *'\n"
    "  evening: '0 21 * * *'\n"
    "  timezone: America/New_York\n"
)

(config_dir / "locations.txt").write_text(
    "# Supported office locations\n"
    "Columbus\n"
    "Austin\n"
    "Denver\n"
    "Seattle\n"
    "Miami\n"
    "Tokyo\n"
    "Berlin\n"
)

# Automation directory (distractor)
automation_dir = workspace / "automation"
automation_dir.mkdir(exist_ok=True)

(automation_dir / "cron_example.sh").write_text(
    "#!/bin/bash\n"
    "# Example cron setup - DO NOT USE DIRECTLY\n"
    "# openclaw cron add --schedule '0 7 * * *' --tz 'America/New_York' --message 'Generate my daily briefing'\n"
    "echo 'Cron example - not executable'\n"
)

(automation_dir / "deploy_notes.txt").write_text(
    "Deployment notes v1.2\n"
    "- Updated briefing format to include selfcare section\n"
    "- Added --location parameter support\n"
    "- Fixed weekday detection bug on Sundays\n"
)

# Tests directory (distractor)
tests_dir = workspace / "tests"
tests_dir.mkdir(exist_ok=True)

(tests_dir / "test_briefing_stub.py").write_text(
    "# Stub test file - incomplete\n"
    "# TODO: Add actual test cases\n"
    "def test_placeholder():\n"
    "    pass\n"
)

# Output directory that should NOT be pre-populated with correct answers
output_dir = workspace / "output"
output_dir.mkdir(exist_ok=True)
(output_dir / ".gitkeep").write_text("")

# A misleading partial briefing (wrong structure, missing fields)
(output_dir / "partial_draft.json").write_text(json.dumps({
    "location": "Seattle",
    "sections": [
        {"title": "Morning", "content": "Wake up", "type": "motivation"}
    ]
}, indent=2))

# README at top level - but intentionally vague and unhelpful for the task
(workspace / "README.md").write_text(
    "# Daily Briefing Service\n\n"
    "Internal productivity tooling for distributed teams.\n\n"
    "See `references/productivity.md` for tips.\n"
    "See `config/` for configuration files.\n"
    "Contact: ops-team@company.internal\n"
)

print("Workspace setup complete.")
print(f"Files created in {workspace}")