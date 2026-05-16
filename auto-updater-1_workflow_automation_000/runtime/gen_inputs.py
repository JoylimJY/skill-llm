import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    "ops/cron_configs",
    "ops/logs/2024-01",
    "ops/logs/2024-02",
    "ops/scripts/legacy",
    "ops/scripts/current",
    "bot_system/config",
    "bot_system/skills/prd",
    "bot_system/skills/browser",
    "bot_system/skills/gemini",
    "bot_system/skills/himalaya",
    "bot_system/skills/peekaboo",
    "reports/monthly",
    "reports/weekly",
    "infra/deploy",
    "infra/monitoring",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "ops/logs/2024-01/update.log": "2024-01-15 04:00:01 - Update check started\n2024-01-15 04:00:12 - No updates found\n",
    "ops/logs/2024-02/update.log": "2024-02-10 04:00:01 - Update check started\n2024-02-10 04:00:45 - Updated prd 2.0.2 -> 2.0.3\n",
    "ops/scripts/legacy/old_updater.sh": "#!/bin/bash\n# DEPRECATED - old manual update script\napt-get update && apt-get upgrade -y\n",
    "ops/cron_configs/old_cron.txt": "# Old cron format - DO NOT USE\n30 3 * * * /usr/local/bin/update.sh\n",
    "bot_system/config/network.json": json.dumps({"host": "localhost", "port": 8080, "timeout": 30}, indent=2),
    "bot_system/config/logging.json": json.dumps({"level": "INFO", "file": "/var/log/bot.log", "rotate": True}, indent=2),
    "bot_system/skills/prd/manifest.json": json.dumps({"name": "prd", "version": "2.0.3", "description": "Product requirements helper"}, indent=2),
    "bot_system/skills/browser/manifest.json": json.dumps({"name": "browser", "version": "1.2.0", "description": "Web browsing skill"}, indent=2),
    "bot_system/skills/gemini/manifest.json": json.dumps({"name": "gemini", "version": "1.5.2", "description": "Gemini AI integration"}, indent=2),
    "bot_system/skills/himalaya/manifest.json": json.dumps({"name": "himalaya", "version": "0.9.1", "description": "Email client skill"}, indent=2),
    "bot_system/skills/peekaboo/manifest.json": json.dumps({"name": "peekaboo", "version": "2.1.0", "description": "Screen peek skill"}, indent=2),
    "reports/monthly/jan_summary.txt": "January maintenance summary\n- 2 skills updated\n- 0 errors\n",
    "reports/weekly/week04.txt": "Week 4 report: All systems nominal.\n",
    "infra/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying services...'\n",
    "infra/monitoring/health_check.sh": "#!/bin/bash\ncurl -s http://localhost:8080/health\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# THE CORE PROBLEM: version data file that the agent must use to generate the update summary
# This contains messy, real-world-style data with before/after versions
version_data = {
    "bot_version": {
        "previous": "v2026.1.9",
        "current": "v2026.1.10"
    },
    "skills_updated": [
        {"name": "prd", "from": "2.0.3", "to": "2.0.4"},
        {"name": "browser", "from": "1.2.0", "to": "1.2.1"},
        {"name": "nano-banana-pro", "from": "3.1.0", "to": "3.1.2"}
    ],
    "skills_current": ["gemini", "sag", "things-mac", "himalaya", "peekaboo"],
    "errors": []
}

(workspace / "ops" / "update_results.json").write_text(json.dumps(version_data, indent=2))

# A partial, broken cron setup script that needs to be REPLACED (not fixed) by the agent
broken_setup = """#!/bin/bash
# INCOMPLETE - missing critical flags, do not use
clawdbot cron add \\
  --name "Daily Auto-Update" \\
  --cron "0 4 * * *"
"""
(workspace / "ops" / "scripts" / "current" / "broken_setup.sh").write_text(broken_setup)

# A stub config file that is WRONG - agent must create the correct one
wrong_config = {"cron": {"enabled": "yes"}}  # wrong type, should be bool false
(workspace / "bot_system" / "config" / "wrong_cron_config.json").write_text(json.dumps(wrong_config, indent=2))

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")