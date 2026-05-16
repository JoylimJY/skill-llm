#!/usr/bin/env python3
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create the skill directory structure ──────────────────────────────────
skill_dir = workspace / "skills" / "claude-relay"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── 2. Create a realistic, deeply nested project tree ────────────────────────
projects_root = workspace / "dev_projects"

project_defs = {
    "payment-gateway":    ["src/api.py", "src/models.py", "tests/test_api.py", "README.md", "Makefile"],
    "user-auth-service":  ["src/auth.py", "src/tokens.py", "tests/test_auth.py", "docker-compose.yml"],
    "data-pipeline":      ["pipeline/ingest.py", "pipeline/transform.py", "pipeline/load.py", "config/settings.yaml"],
    "frontend-dashboard": ["src/App.jsx", "src/components/Chart.jsx", "package.json", "webpack.config.js"],
    "ml-scoring-engine":  ["models/scorer.py", "models/features.py", "notebooks/explore.ipynb", "requirements.txt"],
    "legacy-billing":     ["billing/invoice.py", "billing/rates.cfg", "billing/old_schema.sql"],
    "notification-svc":   ["handlers/email.py", "handlers/sms.py", "queue/worker.py"],
}

for project_name, files in project_defs.items():
    for rel_file in files:
        full_path = projects_root / project_name / rel_file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(f"# {project_name} / {rel_file}\n# auto-generated distractor file\n")

# Deeply nested distractor dirs
for i in range(3):
    deep = projects_root / f"archive_{i}" / "2023" / "q4" / f"sprint_{i+1}"
    deep.mkdir(parents=True, exist_ok=True)
    (deep / f"notes_{i}.txt").write_text(f"Sprint {i+1} notes\n")

# ── 3. Create a BROKEN / MESSY projects.map ──────────────────────────────────
# This file has wrong formats, stale entries, and is missing required entries.
# The agent must FIX/REBUILD it with correct name=/abs/path format.
broken_map_content = """\
# projects.map — relay alias configuration
# FORMAT REMINDER: alias -> /path  (DO NOT USE THIS FORMAT)
payment-gw -> /nonexistent/old/path/payment
  user-auth =    /also/wrong/path/  
# data-pipeline is intentionally omitted
FRONTEND = /wrong/case/path
legacy billing=/workspace/dev_projects/legacy-billing
# notification service
notif=
"""

(skill_dir / "projects.map").write_text(broken_map_content)

# Example map for reference (agent may study this)
(skill_dir / "projects.map.example").write_text(
    "# One entry per line: alias=absolute_path\n"
    "myapp=/home/user/projects/myapp\n"
    "api-server=/srv/api\n"
)

# ── 4. Create distractor config files ────────────────────────────────────────
(workspace / "config").mkdir(exist_ok=True)
(workspace / "config" / "relay.conf").write_text(
    "# Old relay config - deprecated\nROOT=/home/old_user/projects\n"
)
(workspace / "config" / "team_projects.csv").write_text(
    "project,owner,status\npayment-gateway,alice,active\nuser-auth-service,bob,active\ndata-pipeline,carol,active\n"
)

# ── 5. Create an environment hints file (distractor - wrong values) ───────────
(workspace / ".env.example").write_text(
    "# Example env - values here are WRONG/PLACEHOLDER\n"
    "CLAUDE_RELAY_ROOT=/home/user/projects\n"
    "CLAUDE_RELAY_MAP=/home/user/.relay/projects.map\n"
    "CLAUDE_BIN=/usr/local/bin/claude\n"
    "RELAY_WAIT=6\n"
)

# ── 6. Create the task specification file ────────────────────────────────────
task_spec = {
    "mission": "Configure the AI relay system for the platform team",
    "required_aliases": {
        "pay-gw":    "payment-gateway project folder under dev_projects",
        "auth-svc":  "user-auth-service project folder under dev_projects",
        "pipeline":  "data-pipeline project folder under dev_projects"
    },
    "audit_output": "relay_audit.json",
    "tests_required": [
        "Verify session handle for pay-gw alias",
        "Verify session handle for auth-svc alias",
        "Verify error code when sending to a non-running session"
    ]
}
(workspace / "task_spec.json").write_text(json.dumps(task_spec, indent=2))

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Projects root: {projects_root}")