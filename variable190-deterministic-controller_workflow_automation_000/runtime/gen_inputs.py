import os
import random
import json

random.seed(42)

BASE = "/workspace"

# ── Skill folder (simulates installed skill) ──────────────────────────────────
skill_root = os.path.join(BASE, "skills", "deterministic-controller")
for d in ["templates", "docs", "examples"]:
    os.makedirs(os.path.join(skill_root, d), exist_ok=True)

# ── README.md ─────────────────────────────────────────────────────────────────
readme = """\
# Deterministic Controller for OpenClaw

This skill provides **evidence-gated**, deterministic orchestration templates for OpenClaw.

## Quick-Start

1. Copy `templates/HEARTBEAT.md` → your workspace root, replace `<TELEGRAM_GROUP_ID>`.
2. Copy `templates/ACTIVITIES.md` → your workspace root; set `Plan Path` to an existing sprint file.
3. Copy `templates/SPRINT_TEMPLATE.md` into your sprint folder as the base for new sprints.
4. Generate `openclaw.json` in your workspace root using the snippets in
   `docs/openclaw_config_snippets.md`.  The cron payload lives in `docs/poll_cron_payload.txt`.
5. Every ACTIVITIES item **must** carry an `Artifact:` line with an absolute or relative file path
   — completion is only accepted when the artifact path is present (evidence-gated).

## Concepts

| Concept | Description |
|---|---|
| HEARTBEAT | Periodic liveness check posted to a Telegram group |
| ACTIVITIES | Lean portfolio queue with optional external sprint-plan import |
| Plan Path | Field in ACTIVITIES.md pointing to an external `.sprint.md` file to import |
| poll_cron_payload | JSON fragment placed verbatim into `openclaw.json` under the `"cron"` key |
| Evidence-gate | An ACTIVITIES item cannot be marked DONE without an `Artifact:` path |
"""
with open(os.path.join(skill_root, "README.md"), "w") as f:
    f.write(readme)

# ── templates/HEARTBEAT.md ────────────────────────────────────────────────────
heartbeat_tpl = """\
# HEARTBEAT

## Target Group
Telegram Group ID: <TELEGRAM_GROUP_ID>

## Cadence
Every: <CADENCE_MINUTES> minutes

## Prompt
<HEARTBEAT_PROMPT>

## Notes
- This file is read by OpenClaw at each cadence tick.
- Changing `Telegram Group ID` takes effect on the next tick.
- Do NOT remove the `Telegram Group ID:` label; OpenClaw parses it by exact prefix match.
"""
with open(os.path.join(skill_root, "templates", "HEARTBEAT.md"), "w") as f:
    f.write(heartbeat_tpl)

# ── templates/ACTIVITIES.md ───────────────────────────────────────────────────
activities_tpl = """\
# ACTIVITIES

## Plan Path
<PLAN_PATH>

## Queue

<!-- FORMAT PER ITEM:
### [STATUS] Short title
Priority: HIGH | MEDIUM | LOW
Artifact: <relative-or-absolute path to output file>
Notes: free text
-->

### [BACKLOG] Example task
Priority: MEDIUM
Artifact: outputs/example_report.json
Notes: Replace this with real tasks imported from the sprint plan.
"""
with open(os.path.join(skill_root, "templates", "ACTIVITIES.md"), "w") as f:
    f.write(activities_tpl)

# ── templates/SPRINT_TEMPLATE.md ──────────────────────────────────────────────
sprint_tpl = """\
# Sprint: <SPRINT_NAME>

## Goal
<SPRINT_GOAL>

## Start Date
<START_DATE>

## End Date
<END_DATE>

## Tasks

| ID | Title | Owner | Status | Artifact |
|----|-------|-------|--------|----------|
| T-001 | <task title> | <owner> | BACKLOG | <artifact path> |

## Retrospective
<RETRO_NOTES>
"""
with open(os.path.join(skill_root, "templates", "SPRINT_TEMPLATE.md"), "w") as f:
    f.write(sprint_tpl)

# ── docs/poll_cron_payload.txt ────────────────────────────────────────────────
poll_cron_payload = """\
{
  "schedule": "*/5 * * * *",
  "action": "poll_activities",
  "target": "ACTIVITIES.md",
  "evidence_gate": true,
  "retry_on_missing_artifact": 3
}"""
with open(os.path.join(skill_root, "docs", "poll_cron_payload.txt"), "w") as f:
    f.write(poll_cron_payload)

# ── docs/openclaw_config_snippets.md ─────────────────────────────────────────
config_snippets = """\
# openclaw.json — Config Snippets

The agent expects a file named `openclaw.json` in the **workspace root** (NOT inside the skill folder).

## Required top-level keys

```json
{
  "heartbeat": {
    "prompt": "<string: the heartbeat message sent to Telegram>",
    "cadence_minutes": <integer>,
    "telegram_group_id": "<string: must match value in HEARTBEAT.md>"
  },
  "cron": <object: paste the ENTIRE contents of docs/poll_cron_payload.txt here as a parsed JSON object>,
  "activities_path": "ACTIVITIES.md",
  "sprint_template_path": "sprints/current.sprint.md"
}
```

### Rules
- `"cron"` value MUST be the verbatim parsed JSON object from `docs/poll_cron_payload.txt` — no additions, no omissions.
- `"cadence_minutes"` must be an **integer**, not a string.
- `"telegram_group_id"` must be a **string** (quote it even if it looks numeric).
- All four top-level keys (`heartbeat`, `cron`, `activities_path`, `sprint_template_path`) are mandatory.
"""
with open(os.path.join(skill_root, "docs", "openclaw_config_snippets.md"), "w") as f:
    f.write(config_snippets)

# ── examples/setup_prompt.md ──────────────────────────────────────────────────
setup_prompt_ex = """\
# Example: Setup Prompt for OpenClaw

Paste this into your orchestrator chat to bootstrap a new workspace:

> "Set up HEARTBEAT.md with group ID -1001234567890, cadence 10 minutes, prompt 'Fleet status nominal'.
>  Set ACTIVITIES.md Plan Path to sprints/current.sprint.md.
>  Generate openclaw.json with all required keys."
"""
with open(os.path.join(skill_root, "examples", "setup_prompt.md"), "w") as f:
    f.write(setup_prompt_ex)

# ── examples/project_to_sprint_prompt.md ──────────────────────────────────────
proj_sprint_ex = """\
# Example: Project-to-Sprint Conversion Prompt

> "Convert the project brief at docs/project_brief.md into a sprint plan at sprints/current.sprint.md
>  using the SPRINT_TEMPLATE.md. Populate ACTIVITIES.md with the resulting tasks."
"""
with open(os.path.join(skill_root, "examples", "project_to_sprint_prompt.md"), "w") as f:
    f.write(proj_sprint_ex)

# ── Project workspace (what the agent should populate) ────────────────────────
project_root = os.path.join(BASE, "robotics-fleet-workspace")
os.makedirs(project_root, exist_ok=True)

# Distractor files ─────────────────────────────────────────────────────────────
distractors = {
    "old_config.json": json.dumps({"version": 1, "deprecated": True, "heartbeat_group": 99999}, indent=2),
    "notes.txt": "Talk to DevOps about cron schedule. Ask Alice about Telegram group.\n",
    "requirements.txt": "requests==2.31.0\npyyaml==6.0\n",
    ".env.example": "TELEGRAM_TOKEN=your_token_here\nGROUP_ID=your_group_id\n",
    "deploy/Makefile": "deploy:\n\techo 'deploy not configured'\n",
    "deploy/README.txt": "Deployment notes — placeholder\n",
    "sprints/archive/sprint_01.sprint.md": """\
# Sprint: Fleet Alpha
## Goal
Initial sensor calibration.
## Start Date
2024-01-10
## End Date
2024-01-24
## Tasks
| ID | Title | Owner | Status | Artifact |
|----|-------|-------|--------|----------|
| T-001 | Calibrate lidar | Bob | DONE | outputs/lidar_calib.json |
## Retrospective
Went well. Lidar drift fixed.
""",
    "outputs/.gitkeep": "",
    "logs/deploy.log": "[2024-03-01 08:00] Deploy OK\n[2024-03-01 08:05] Heartbeat missed\n",
    "docs/project_brief.md": """\
# Robotics Fleet — Q2 Deployment Brief

## Objective
Deploy 12 autonomous claw units to Warehouse B by end of Q2.

## Key Deliverables
- Sensor calibration report: outputs/q2_sensor_calib.json
- Fleet status dashboard config: outputs/dashboard_config.yaml
- Deployment sign-off checklist: outputs/deploy_checklist.md

## Owner
Alice Chen <alice@robofleet.example>

## Telegram Monitoring Group
Group ID: -1009988776655
Heartbeat cadence: 15 minutes
Heartbeat message: "RoboFleet Q2 deployment heartbeat — all systems nominal."
""",
    "docs/legacy_heartbeat.md": """\
# OLD HEARTBEAT (deprecated)
Telegram Group ID: -1000000000001
Cadence: 30 minutes
Do not use — replaced by HEARTBEAT.md from skill.
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(project_root, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Partially filled sprint file the agent must reference ────────────────────────
current_sprint = """\
# Sprint: Q2 Fleet Deployment

## Goal
Complete sensor calibration and deploy 12 claw units to Warehouse B.

## Start Date
2024-04-01

## End Date
2024-04-14

## Tasks

| ID | Title | Owner | Status | Artifact |
|----|-------|-------|--------|----------|
| T-001 | Sensor calibration for all 12 units | Alice | BACKLOG | outputs/q2_sensor_calib.json |
| T-002 | Generate dashboard config | Bob | BACKLOG | outputs/dashboard_config.yaml |
| T-003 | Complete deployment sign-off checklist | Alice | BACKLOG | outputs/deploy_checklist.md |

## Retrospective
TBD
"""
sprint_path = os.path.join(project_root, "sprints", "current.sprint.md")
os.makedirs(os.path.dirname(sprint_path), exist_ok=True)
with open(sprint_path, "w") as f:
    f.write(current_sprint)

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Project root: {project_root}")