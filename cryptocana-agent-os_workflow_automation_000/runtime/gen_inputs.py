import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create distractor directory structure for a logistics company project
dirs = [
    "warehouse-project/docs",
    "warehouse-project/reports",
    "warehouse-project/config",
    "warehouse-project/scripts",
    "warehouse-project/logs",
    "warehouse-project/archive/2023",
    "warehouse-project/archive/2024",
    "legacy-system/configs",
    "legacy-system/exports",
    "team-notes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "warehouse-project/docs/requirements.md": "# Warehouse Optimization Requirements\n\n- Reduce picking time by 30%\n- Integrate RFID scanners\n- Automated reorder triggers\n",
    "warehouse-project/docs/team-charter.md": "## Team Charter\nTeams: Planning, Design, Engineering, QA, Audit\n",
    "warehouse-project/reports/q3-progress.json": json.dumps({"quarter": "Q3", "progress": 67, "blocked": ["RFID integration"]}),
    "warehouse-project/config/old-workflow.json": json.dumps({"phases": ["plan", "build"], "deprecated": True}),
    "warehouse-project/config/team-map.yaml": "planning_team: alice\ndesign_team: bob\ndev_team: charlie\naudit_team: diana\n",
    "warehouse-project/scripts/migrate.sh": "#!/bin/bash\necho 'legacy migration script'\n",
    "warehouse-project/logs/execution.log": "2024-01-15 ERROR: task timeout\n2024-01-16 INFO: resumed\n",
    "warehouse-project/archive/2023/old-plan.txt": "Old warehouse layout plans from 2023.\n",
    "warehouse-project/archive/2024/rfid-specs.txt": "RFID scanner model: XR-2000\nFrequency: 915MHz\n",
    "legacy-system/configs/agent-config.json": json.dumps({"version": "0.0.1", "agents": [], "deprecated": True}),
    "legacy-system/exports/task-dump.csv": "task_id,name,status\n1,Plan layout,done\n2,Buy equipment,pending\n",
    "team-notes/standup-2024-11-01.txt": "Discussed blockers for RFID phase. Charlie out sick.\n",
    "team-notes/audit-checklist.txt": "[ ] Verify compliance docs\n[ ] Check inventory counts\n[ ] Sign off on RFID install\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# The agent's main task: create a Node.js script to run the agent-os framework
# We provide a BROKEN/INCOMPLETE starter script with wrong capabilities and missing custom template
# The agent must fix and complete it properly
broken_script = """\
// warehouse-orchestration.js
// TODO: This script needs to be completed to set up the warehouse project orchestration system.
// It should use the agent-os framework installed in /workspace/node_modules/agent-os

// Requirements (from business spec):
// - Project ID: "warehouse-opt-2024"
// - Three teams:
//     * ID: "logistics", Name: "🚚 Logistics", Capabilities: ["planning", "research"]
//     * ID: "engineering", Name: "⚙️ Engineering", Capabilities: ["development", "design"]
//     * ID: "compliance", Name: "📋 Compliance", Capabilities: ["audit", "planning"]
// - Run a project with goal: "Optimize warehouse operations with RFID automation"
// - Task types to execute: planning, development, audit
// - The "audit" phase needs a CUSTOM task template with these 3 steps:
//     Step 1: "Review compliance requirements" - 20 minutes
//     Step 2: "Validate system outputs" - 30 minutes  
//     Step 3: "Sign off on deliverables" - 15 minutes
// - After completion, print the final status as JSON

const { AgentOS } = require('agent-os');
// INCOMPLETE - fill in the rest
"""

with open(os.path.join(workspace, "warehouse-orchestration.js"), "w") as f:
    f.write(broken_script)

# Also create a misleading old attempt that uses wrong API
wrong_attempt = """\
// old-attempt.js - DO NOT USE - wrong API calls
const AgentOS = require('agent-os');  // wrong import
const system = new AgentOS();  // missing project ID

system.addAgent('logistics', ['planning']);  // addAgent doesn't exist
system.addAgent('engineering', ['development']);
system.addAgent('compliance', ['audit']);

system.start('Optimize warehouse');  // start() doesn't exist
"""

with open(os.path.join(workspace, "warehouse-project/scripts/old-attempt.js"), "w") as f:
    f.write(wrong_attempt)

print("Workspace generated successfully.")
print(f"Files created in {workspace}")