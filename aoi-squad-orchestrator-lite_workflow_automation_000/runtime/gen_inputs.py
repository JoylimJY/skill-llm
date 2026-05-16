import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")

# --- Deeply nested distractor directory structure ---
dirs = [
    "ops/mission_logs/2025",
    "ops/mission_logs/2026",
    "ops/configs/teams",
    "ops/configs/presets_archive",
    "reports/q1",
    "reports/q2",
    "reports/drafts",
    "tooling/legacy",
    "tooling/current",
    "docs/internal",
    "docs/external",
    "staging/alpha",
    "staging/beta",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "ops/mission_logs/2025/alpha_op.log": "Operation ALPHA completed. Team: Falcon, Hawk, Eagle.\nStatus: SUCCESS\n",
    "ops/mission_logs/2026/beta_op.log": "Operation BETA initiated. Team: Wolf, Fox, Bear.\nStatus: PENDING\n",
    "ops/configs/teams/legacy_team.json": json.dumps({
        "team": "legacy",
        "members": ["agent_x", "agent_y", "agent_z"],
        "preset": "old-format-v1"
    }, indent=2),
    "ops/configs/presets_archive/preset_v0.json": json.dumps({
        "preset": "analyst-coder-tester",
        "deprecated": True,
        "reason": "Replaced in 2024 reorganization"
    }, indent=2),
    "ops/configs/presets_archive/preset_list_old.txt": "analyst-coder-tester\nplanner-executor-watcher\n",
    "reports/q1/summary.txt": "Q1 Operations Summary\n- 3 missions completed\n- 1 mission ongoing\n- Team efficiency: 87%\n",
    "reports/q2/summary.txt": "Q2 Operations Summary\n- 5 missions completed\n- 2 missions aborted\n- Team efficiency: 91%\n",
    "reports/drafts/mission_brief_draft.txt": "DRAFT - Vulnerability Assessment Mission\nObjective: Assess perimeter security.\nTeam composition: TBD\nTimeline: 2 weeks\n",
    "tooling/legacy/run_team.sh": "#!/bin/bash\n# DEPRECATED - do not use\necho 'Legacy team runner - EOL 2024'\n",
    "tooling/current/notes.txt": "Current tooling notes:\n- Use the new squad orchestrator for all team assignments\n- Reference S-DNA: AOI-2026-0215-SDNA-SQUAD01\n",
    "docs/internal/team_naming_policy.txt": "Team Naming Policy v3.2\nAll team members must be assigned operational aliases.\nAliases must not reveal real identities.\nUpdate the team registry before mission kickoff.\n",
    "docs/external/compliance_checklist.txt": "Pre-mission compliance checklist:\n[ ] Team identities confirmed\n[ ] Roles assigned\n[ ] Mission brief generated and stored\n[ ] Report filed in /reports/\n",
    "staging/alpha/config_alpha.json": json.dumps({
        "stage": "alpha",
        "team_preset": "builder-security-operator",
        "status": "awaiting_config"
    }, indent=2),
    "staging/beta/config_beta.json": json.dumps({
        "stage": "beta",
        "team_preset": "researcher-writer-editor",
        "status": "archived"
    }, indent=2),
}

for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.write_text(content)

# --- Messy/outdated local data store (wrong names, needs correction via CLI) ---
# This simulates a pre-existing but stale squad_names.json — agent should NOT
# directly edit this; they must use the CLI which updates it properly.
openclaw_dir = pathlib.Path.home() / ".openclaw" / "aoi"
openclaw_dir.mkdir(parents=True, exist_ok=True)

stale_squad_names = {
    "planner-builder-reviewer": {
        "planner": "Stale Planner Name",
        "builder": "Stale Builder Name",
        "reviewer": "Stale Reviewer Name"
    },
    "researcher-writer-editor": {
        "researcher": "Stale Researcher Name",
        "writer": "Stale Writer Name",
        "editor": "Stale Editor Name"
    },
    "builder-security-operator": {
        "builder": "Stale Builder Name",
        "security": "Stale Security Name",
        "operator": "Stale Operator Name"
    }
}
(openclaw_dir / "squad_names.json").write_text(json.dumps(stale_squad_names, indent=2))

print("Workspace initialized with distractor files and stale squad_names.json.")