import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor directory structure ---
dirs = [
    "scripts",
    "docs/internal",
    "docs/specs",
    "config/envs",
    "config/legacy",
    "src/core",
    "src/adapters",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "logs/2024",
    "logs/2023",
    "artifacts/builds",
    "artifacts/reports",
    ".openclaw",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/internal/onboarding.txt": "Welcome to the team. Please read all docs before starting.\nAsk your manager for tool access.\n",
    "docs/specs/agent_capabilities_v1.md": "# Agent Capabilities\n\n## Overview\nThis document describes planned agent capabilities.\n\n## Status\n- Search: PLANNED\n- Weather: INSTALLED\n- Translation: PLANNED\n",
    "docs/specs/capability_gap_analysis.csv": "capability,status,priority\nweb_search,missing,high\ntranslation,missing,medium\ncalendar,missing,low\n",
    "config/envs/production.env": "ENV=production\nLOG_LEVEL=warn\nMAX_RETRIES=3\n",
    "config/envs/staging.env": "ENV=staging\nLOG_LEVEL=debug\nMAX_RETRIES=5\n",
    "config/legacy/old_skill_registry.json": json.dumps({
        "registry_version": "0.1",
        "skills": [
            {"name": "weather-checker", "version": "0.0.1", "deprecated": True},
            {"name": "search-v1", "version": "0.0.2", "deprecated": True}
        ]
    }, indent=2),
    "src/core/agent_runner.py": "class AgentRunner:\n    def __init__(self, skills_dir):\n        self.skills_dir = skills_dir\n    def load_skills(self):\n        pass\n",
    "src/adapters/skill_adapter.py": "class SkillAdapter:\n    def wrap(self, skill):\n        return {'wrapped': True, 'skill': skill}\n",
    "src/utils/logger.py": "import logging\nlogger = logging.getLogger('agent')\n",
    "tests/unit/test_runner.py": "def test_placeholder():\n    assert True\n",
    "tests/integration/test_skills.py": "# TODO: add integration tests for installed skills\n",
    "logs/2024/deploy.log": "2024-01-10 deployment started\n2024-01-10 skills directory initialized\n2024-01-11 weather skill installed\n",
    "logs/2023/errors.log": "2023-12-01 ERROR skill load failed: search not found\n2023-12-02 ERROR timeout fetching skill manifest\n",
    "artifacts/builds/build_manifest.json": json.dumps({
        "build_id": "b-20240115",
        "timestamp": "2024-01-15T09:00:00Z",
        "included_skills": []
    }, indent=2),
    "artifacts/reports/last_audit.json": json.dumps({
        "audit_date": "2024-01-01",
        "installed_skills": [],
        "note": "Outdated. Re-run audit to get current state."
    }, indent=2),
    ".openclaw/.keep": "",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the usage.sh script (per SKILL.md it already exists in workspace/scripts/) ---
# This is the proprietary entry point described in SKILL.md
# The script is supposed to "already exist" per SKILL.md ("All scripts mentioned in the SKILL.md already exist")
# However, it depends on the `skillhub` CLI which must be installed at runtime.
# We create a stub that will be activated by setup_script once skillhub is installed.

usage_sh_content = r"""#!/usr/bin/env bash
# usage.sh - Skillhub action dispatcher
# Usage: ./scripts/usage.sh '<json>'

set -e

INPUT="$1"

if [ -z "$INPUT" ]; then
  echo "Error: No JSON input provided." >&2
  echo "Usage: $0 '<json>'" >&2
  exit 1
fi

ACTION=$(echo "$INPUT" | jq -r '.action // empty')

if [ -z "$ACTION" ]; then
  echo "Error: 'action' field is required in JSON input." >&2
  exit 1
fi

case "$ACTION" in
  search)
    QUERY=$(echo "$INPUT" | jq -r '.query // ""')
    LIMIT=$(echo "$INPUT" | jq -r '.limit // 20')
    JSON_FLAG=$(echo "$INPUT" | jq -r '.json // false')
    TIMEOUT=$(echo "$INPUT" | jq -r '.timeout // 6')
    ARGS="search"
    if [ -n "$QUERY" ]; then ARGS="$ARGS $QUERY"; fi
    if [ "$JSON_FLAG" = "true" ]; then ARGS="$ARGS --json"; fi
    ARGS="$ARGS --limit $LIMIT --timeout $TIMEOUT"
    skillhub --skip-self-upgrade $ARGS
    ;;
  install)
    SLUG=$(echo "$INPUT" | jq -r '.slug // empty')
    if [ -z "$SLUG" ]; then
      echo "Error: 'slug' is required for install action." >&2
      exit 1
    fi
    FORCE=$(echo "$INPUT" | jq -r '.force // false')
    ARGS="install $SLUG"
    if [ "$FORCE" = "true" ]; then ARGS="$ARGS --force"; fi
    skillhub --skip-self-upgrade $ARGS
    ;;
  upgrade)
    SLUG=$(echo "$INPUT" | jq -r '.slug // empty')
    CHECK_ONLY=$(echo "$INPUT" | jq -r '.check_only // false')
    TIMEOUT=$(echo "$INPUT" | jq -r '.timeout // 20')
    ARGS="upgrade"
    if [ -n "$SLUG" ] && [ "$SLUG" != "null" ]; then ARGS="$ARGS $SLUG"; fi
    if [ "$CHECK_ONLY" = "true" ]; then ARGS="$ARGS --check-only"; fi
    ARGS="$ARGS --timeout $TIMEOUT"
    skillhub --skip-self-upgrade $ARGS
    ;;
  list)
    skillhub --skip-self-upgrade list
    ;;
  self-upgrade)
    CHECK_ONLY=$(echo "$INPUT" | jq -r '.check_only // false')
    CURRENT_VERSION=$(echo "$INPUT" | jq -r '.current_version // empty')
    ARGS="self-upgrade"
    if [ "$CHECK_ONLY" = "true" ]; then ARGS="$ARGS --check-only"; fi
    if [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" != "null" ]; then
      ARGS="$ARGS --current-version $CURRENT_VERSION"
    fi
    skillhub $ARGS
    ;;
  *)
    echo "Error: Unknown action '$ACTION'." >&2
    exit 1
    ;;
esac
"""

usage_sh_path = os.path.join(workspace, "scripts/usage.sh")
with open(usage_sh_path, "w") as f:
    f.write(usage_sh_content)

os.chmod(usage_sh_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# --- Create a task brief (business context, no technical hints) ---
task_brief = """INTERNAL MEMO — Agent Capability Expansion Project
Date: 2024-01-15
From: Engineering Lead
To: Agent Infrastructure Team

We need to expand our agent's toolkit with a web search skill.

Tasks:
1. Discover what search-related skills are available in the skill store.
2. Install the most relevant "search" skill (you'll know it when you see it).
3. After installation, produce a current inventory of all installed skills.
4. Save the inventory to a file named `skill_inventory.json` so we can track it.

The inventory file must capture the full structured data returned by the listing tool.
"""

with open(os.path.join(workspace, "docs/internal/task_brief.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Directory structure created at: {workspace}")