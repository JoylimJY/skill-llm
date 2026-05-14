import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep distractor directory structure ---
distractor_dirs = [
    "projects/iot-platform/integrations/legacy",
    "projects/iot-platform/integrations/active",
    "projects/iot-platform/config",
    "projects/iot-platform/docs",
    "projects/smart-home/modules/heating",
    "projects/smart-home/modules/lighting",
    "projects/smart-home/scripts",
    "tools/audit",
    "tools/search",
    "archive/deprecated-skills",
    "archive/old-configs",
    "notes",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files simulating a messy real engineering workspace
distractor_files = {
    "projects/iot-platform/integrations/legacy/old_homebridge.json": json.dumps({
        "name": "homebridge-legacy",
        "version": "0.1.0",
        "deprecated": True,
        "reason": "Replaced by HA integration"
    }, indent=2),
    "projects/iot-platform/integrations/legacy/zigbee_adapter.yaml": "name: zigbee2mqtt\nport: /dev/ttyUSB0\nbaud: 115200\n",
    "projects/iot-platform/integrations/active/influxdb_config.json": json.dumps({
        "host": "localhost",
        "port": 8086,
        "database": "homelab"
    }, indent=2),
    "projects/iot-platform/config/device_map.csv": "device_id,room,type\n001,living_room,light\n002,bedroom,thermostat\n003,kitchen,sensor\n",
    "projects/iot-platform/docs/architecture.md": "# IoT Platform Architecture\n\nThis document describes the integration layer.\n\n## Components\n- Device registry\n- Event bus\n- Skill runner\n",
    "projects/smart-home/modules/heating/thermostat.py": "class Thermostat:\n    def set_temp(self, t):\n        pass\n",
    "projects/smart-home/modules/lighting/dimmer.js": "module.exports = { dim: (level) => console.log(`Dimming to ${level}`) };\n",
    "projects/smart-home/scripts/startup.sh": "#!/bin/bash\necho 'Starting smart home services...'\n",
    "tools/audit/old_skill_list.txt": "homeassistant\ngithub\nweather\n# This list is outdated - do not use\n",
    "tools/search/fuzzy_test.py": "# Old fuzzy matching test - abandoned\ndef jaccard(a, b):\n    sa, sb = set(a), set(b)\n    return len(sa & sb) / len(sa | sb)\n",
    "archive/deprecated-skills/skill-templates-v1.json": json.dumps({
        "version": "1.0",
        "files": ["index.js", "package.json"],
        "note": "Legacy template format"
    }, indent=2),
    "archive/old-configs/install_history.json": json.dumps({
        "installed": ["homeassistant@1.0", "github@2.1"],
        "date": "2023-01-01"
    }, indent=2),
    "notes/integration_ideas.txt": "Ideas for new skills:\n- spotify streaming control\n- calendar sync with caldav\n- wake-on-lan for media server\n",
    "projects/iot-platform/integrations/active/mqtt_bridge.js": "const mqtt = require('mqtt');\n// connects to local broker\n",
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- Task brief: a non-technical document explaining what needs to be done ---
task_brief = """TASK BRIEF - IoT Skill Catalog Audit
======================================
Date: 2025-01-15
Requested by: Platform Engineering Lead

We need to audit our available skill catalog and scaffold a new integration.

DELIVERABLES REQUIRED:

1. catalog_audit.json
   A JSON file containing the full list of skill names available in the built-in
   catalog. The field should be called "skills" and contain an array of skill name strings.
   Also include a "total_count" field with the integer count.

2. search_report.json
   Run the following queries through the skill search system and record results.
   For each query, record whether any results were returned (i.e., passed the
   relevance threshold) and what the top result was (if any), including its score.
   
   Queries to test:
   - "youtube"
   - "email"  
   - "zzzyyyxxx"
   - "speaker music"
   
   Format each entry with: query, results_found (bool), top_skill (str or null),
   top_score (int or null, as percentage integer e.g. 85 for 85%)

3. scaffold_summary.json
   Use the skill management tooling to scaffold a new skill called "spotify-connect".
   Then record which files were generated inside the new skill directory.
   Format: { "skill_name": "spotify-connect", "files_created": ["list", "of", "filenames"] }

All three files should be placed anywhere discoverable in the workspace.
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files in {len(distractor_dirs)} directories.")
print("Task brief written to /workspace/TASK_BRIEF.txt")