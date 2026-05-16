import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Create the skills/lofy/assets/templates directory structure ──────────────
templates_dir = workspace / "skills" / "lofy" / "assets" / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)

# Template files that would be present after installing the skill
# These are the raw templates the agent should USE as a starting point,
# but the agent must properly initialize/customize them

(templates_dir / "AGENTS.md").write_text("""# Agent Behavior Rules
<!-- TEMPLATE: Customize for your agent -->
## Safety Rules
- Never share personal data in group contexts
- Always verify destructive actions

## Memory Protocol
<!-- Fill in memory protocol details -->

## Context Loading
<!-- Define what gets loaded when -->
""")

(templates_dir / "SOUL.md").write_text("""# Soul — Personality & Tone
<!-- TEMPLATE: Make this yours -->
Direct, casual, competent. No filler.
""")

(templates_dir / "IDENTITY.md").write_text("""# Identity
Name: Lofy
<!-- TEMPLATE: Rename if desired -->
""")

(templates_dir / "USER.md").write_text("""# User Profile
<!-- TEMPLATE: Fill in your info -->
Name: [YOUR NAME]
Timezone: [YOUR TIMEZONE]
Goals: [YOUR GOALS]
""")

(templates_dir / "HEARTBEAT.md").write_text("""# Heartbeat — Proactive Check Schedule
<!-- TEMPLATE: Configure your proactive checks -->
Polling interval: [SET INTERVAL]

## Checks
<!-- List proactive checks here -->
""")

(templates_dir / "MEMORY_SYSTEM.md").write_text("""# Memory System Architecture
<!-- TEMPLATE: Memory rules for the agent -->
## Layers
<!-- Define memory layers here -->
""")

(templates_dir / "TOOLS.md").write_text("""# Tools Configuration
<!-- TEMPLATE: Configure your integrations -->
## Integrations
- Google Workspace: [configure]
- Spotify: [configure]
- Home Assistant: [configure]
""")

# Data file templates
data_templates_dir = templates_dir / "data"
data_templates_dir.mkdir(exist_ok=True)

(data_templates_dir / "goals.json").write_text(json.dumps({
    "_template": True,
    "goals": [],
    "habits": [],
    "streaks": []
}, indent=2))

(data_templates_dir / "fitness.json").write_text(json.dumps({
    "_template": True,
    "workouts": [],
    "meals": [],
    "prs": []
}, indent=2))

(data_templates_dir / "applications.json").write_text(json.dumps({
    "_template": True,
    "applications": [],
    "pipeline": []
}, indent=2))

(data_templates_dir / "projects.json").write_text(json.dumps({
    "_template": True,
    "projects": [],
    "milestones": []
}, indent=2))

(data_templates_dir / "home-config.json").write_text(json.dumps({
    "_template": True,
    "scenes": [],
    "devices": []
}, indent=2))

# ── Create a realistic distractor file structure ──────────────────────────────

# Distractor: Old unrelated project files
old_project = workspace / "old_project"
old_project.mkdir(exist_ok=True)
(old_project / "main.py").write_text("# old project\nprint('hello')\n")
(old_project / "requirements.txt").write_text("requests==2.28.0\nflask==2.3.0\n")
(old_project / "config.yaml").write_text("debug: true\nport: 8080\n")

# Distractor: Some existing notes
notes = workspace / "notes"
notes.mkdir(exist_ok=True)
(notes / "meeting-2024-01-15.md").write_text("# Meeting Notes\n- Discussed Q1 roadmap\n- Action items TBD\n")
(notes / "ideas.md").write_text("# Random Ideas\n- Build a personal dashboard\n- Automate morning routine\n")
(notes / "shopping-list.txt").write_text("milk\neggs\nbread\ncoffee\n")

# Distractor: A half-initialized lofy attempt with WRONG structure
bad_attempt = workspace / "lofy_old"
bad_attempt.mkdir(exist_ok=True)
(bad_attempt / "memory.md").write_text("# Some old memories\n- I like coffee\n")  # Wrong filename/location
(bad_attempt / "user_profile.json").write_text('{"name": "Alex"}')  # Wrong format

# Distractor: Random log files
logs = workspace / "logs"
logs.mkdir(exist_ok=True)
(logs / "app.log").write_text("[2024-01-15 10:00:00] INFO: App started\n[2024-01-15 10:01:00] INFO: Connected\n")
(logs / "error.log").write_text("[2024-01-15 09:55:00] ERROR: Connection timeout\n")

# Distractor: A confusing partial MEMORY.md in wrong location
(workspace / "lofy_old" / "MEMORY.md").write_text("\n".join([f"- Memory entry {i}" for i in range(1, 150)]) + "\n")
# ^ This has 149 lines — over the 100-line limit — a trap for agents that copy it

# Distractor: skills directory with other skills
other_skill = workspace / "skills" / "other-skill"
other_skill.mkdir(parents=True, exist_ok=True)
(other_skill / "README.md").write_text("# Some other skill\nDoes something unrelated.\n")

# Distractor: A fake cron config that looks plausible but is wrong
(workspace / "cron.txt").write_text("0 9 * * * echo 'morning'\n0 21 * * * echo 'evening'\n")

# Distractor: package files
(workspace / "package.json").write_text(json.dumps({"name": "my-workspace", "version": "1.0.0"}, indent=2))
(workspace / ".gitignore").write_text("node_modules/\n*.pyc\n__pycache__/\n.env\n")

# ── Create a USER.md in workspace root with real user data ───────────────────
# The agent should have already customized this (we give them a pre-filled one)
(workspace / "USER.md").write_text("""# User Profile
Name: Jordan Rivera
Timezone: America/Chicago
Goals:
  - Run a half marathon by October
  - Launch side project by Q3
  - Read 24 books this year
Primary Channel: Telegram
Wake Time: 7:00 AM
Wind-down Time: 10:00 PM
""")

print("Workspace initialized. Structure:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")