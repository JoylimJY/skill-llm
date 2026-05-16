import os
import json
import random
import stat

random.seed(42)

BASE = "/workspace"

# ── 1. Create the cursor-agent-system toolkit directory structure ──────────────
toolkit_root = os.path.join(BASE, "cursor-agent-system")
scripts_dir  = os.path.join(toolkit_root, "scripts")

# Create scripts dir (present), but deliberately OMIT status/, tasks/, logs/
os.makedirs(scripts_dir, exist_ok=True)
# NOTE: status/, tasks/, logs/ are intentionally NOT created — agent must create them

# Create the required shell scripts (stubs, as per SKILL.md they "already exist")
script_names = [
    "spawn-cursor.sh",
    "check-status.sh",
    "attach-session.sh",
    "send-command.sh",
    "kill-session.sh",
    "common.sh",
]
for sname in script_names:
    spath = os.path.join(scripts_dir, sname)
    with open(spath, "w") as f:
        f.write(f"#!/usr/bin/env bash\n# stub: {sname}\necho '{{\"ok\":true}}'\n")
    os.chmod(spath, os.stat(spath).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ── 2. Create a BROKEN openclaw.json (wrong field names, missing fields) ───────
broken_config = {
    # Wrong: uses "toolkit_root" (snake_case) instead of "toolkitRoot" (camelCase)
    "toolkit_root": toolkit_root,
    # Wrong: uses "project_path" instead of "defaultProjectPath"
    "project_path": "/home/dev/projects/fintech-api",
    # Wrong: uses "mode" instead of "executionMode"
    "mode": "direct",
    # Wrong: uses "timeout" instead of "timeoutMs", and it's a string not a number
    "timeout": "60000",
    # Missing "shell" sub-object entirely
}
config_path = os.path.join(BASE, "openclaw.json")
with open(config_path, "w") as f:
    json.dump(broken_config, f, indent=2)

# ── 3. Create extensions directory structure (as referenced in SKILL.md) ───────
ext_dir = os.path.join(BASE, "extensions", "openclaw-cursor-agent", "examples")
os.makedirs(ext_dir, exist_ok=True)

# Distractor: a plausible-looking but irrelevant config example
with open(os.path.join(ext_dir, "example-config.json"), "w") as f:
    json.dump({
        "pluginId": "openclaw-cursor-agent",
        "toolkitPath": "/opt/cursor-agent",  # intentionally wrong field name
        "mode": "wsl",
    }, f, indent=2)

# ── 4. Create docs directory ───────────────────────────────────────────────────
docs_dir = os.path.join(BASE, "docs")
os.makedirs(docs_dir, exist_ok=True)
with open(os.path.join(docs_dir, "usage-guide.md"), "w") as f:
    f.write("# Usage Guide\n\nSee index.js for full configuration reference.\n")

# ── 5. Distractor files (deeply nested, realistic fintech project) ─────────────
src_dir = os.path.join(BASE, "fintech-api", "src")
os.makedirs(os.path.join(src_dir, "auth"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "payments", "processors"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "ledger", "reconciliation"), exist_ok=True)
os.makedirs(os.path.join(BASE, "fintech-api", "tests", "integration"), exist_ok=True)
os.makedirs(os.path.join(BASE, "fintech-api", ".github", "workflows"), exist_ok=True)

distractor_files = {
    os.path.join(src_dir, "auth", "jwt.py"): "# JWT authentication module\nimport jwt\n",
    os.path.join(src_dir, "auth", "oauth2.py"): "# OAuth2 flow\n",
    os.path.join(src_dir, "payments", "processors", "stripe.py"): "# Stripe integration\n",
    os.path.join(src_dir, "payments", "processors", "wire.py"): "# Wire transfer processor\n",
    os.path.join(src_dir, "ledger", "reconciliation", "daily.py"): "# Daily reconciliation job\n",
    os.path.join(src_dir, "ledger", "reconciliation", "monthly.py"): "# Monthly reconciliation\n",
    os.path.join(BASE, "fintech-api", "tests", "integration", "test_payments.py"): "# integration tests\n",
    os.path.join(BASE, "fintech-api", ".github", "workflows", "ci.yml"): "name: CI\non: [push]\n",
    os.path.join(BASE, "fintech-api", "requirements.txt"): "fastapi==0.104.1\njwt==1.3.1\n",
    os.path.join(BASE, "fintech-api", "pyproject.toml"): "[tool.pytest]\ntestpaths = ['tests']\n",
}
for fpath, content in distractor_files.items():
    with open(fpath, "w") as f:
        f.write(content)

# ── 6. Create the task specification file the agent must read ─────────────────
# This defines the exact inputs for the spawn and kill scenarios the agent must document
task_spec = {
    "scenario_description": (
        "A background coding task needs to be launched for the fintech-api project. "
        "The task is named 'refactor-auth' and the description is "
        "'Refactor the JWT authentication module to use RS256 instead of HS256'. "
        "The project path is '/workspace/fintech-api'. "
        "Priority is 'high' and estimated duration is '30min'. "
        "After the task completes, it must be killed with session name 'cursor-refactor-auth-001', "
        "using both force and purge options."
    ),
    "spawn_inputs": {
        "taskName": "refactor-auth",
        "taskDescription": "Refactor the JWT authentication module to use RS256 instead of HS256",
        "projectPath": "/workspace/fintech-api",
        "priority": "high",
        "eta": "30min"
    },
    "kill_inputs": {
        "sessionQuery": "cursor-refactor-auth-001",
        "force": True,
        "purge": True
    }
}
with open(os.path.join(BASE, "task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace initialized.")
print(f"Toolkit root: {toolkit_root}")
print(f"Scripts present: {script_names}")
print(f"Missing runtime dirs: status/, tasks/, logs/")
print(f"Broken config written to: {config_path}")