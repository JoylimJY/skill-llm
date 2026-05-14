import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Simulate a messy pre-existing project workspace ---

# Distractor: Old project notes
(workspace / "project_notes").mkdir(exist_ok=True)
(workspace / "project_notes" / "kickoff_meeting.txt").write_text(
    "Kickoff meeting notes - Jan 2024\n- Assign agents\n- Set up storage\n- Define workflows\n"
)
(workspace / "project_notes" / "agent_roster_draft.txt").write_text(
    "Agents: coordinator, editor, renderer, sound, marketing\n(Draft - not finalized)\n"
)

# Distractor: Outdated agent config
(workspace / "old_configs").mkdir(exist_ok=True)
(workspace / "old_configs" / "agents_v0.json").write_text(json.dumps({
    "team": ["agent1", "agent2"],
    "storage": "/mnt/old_nas",
    "version": "0.0.1"
}, indent=2))
(workspace / "old_configs" / "deprecated_backup.sh").write_text(
    "#!/bin/bash\n# DEPRECATED - do not use\nscp -r /workspace user@oldnas:/backups/\n"
)

# Distractor: Fake SSH keys (incomplete/wrong)
(workspace / "ssh_stuff").mkdir(exist_ok=True)
(workspace / "ssh_stuff" / "README_NOT_REAL.txt").write_text(
    "These are placeholder references only. Do not use.\n"
)
(workspace / "ssh_stuff" / "fake_key.pub").write_text(
    "ssh-rsa AAAAB3NzaC1yc2EAAAA placeholder@example\n"
)

# Distractor: Random media project files
media_dir = workspace / "media_project_alpha"
media_dir.mkdir(exist_ok=True)
for fname in ["scene_01.mp4.stub", "audio_mix_draft.wav.stub", "render_queue.txt", "credits_template.docx.stub"]:
    (media_dir / fname).write_text(f"Stub file for {fname} - binary content not included\n")

# Distractor: Partial/wrong agent directory (wrong schema)
(workspace / "partial_agent_dir.json").write_text(json.dumps({
    "team_members": {
        "coordinator": "/agents/coordinator",
        "editor": "/agents/editor"
    },
    "note": "This is incomplete and uses wrong schema"
}, indent=2))

# Distractor: A cron-like file with wrong format
(workspace / "old_cron_attempt.json").write_text(json.dumps({
    "cron": "0 3 * * *",
    "task": "backup",
    "target": "all-agents",
    "note": "Wrong format - not compatible"
}, indent=2))

# Distractor: Agent role descriptions (not the real directory)
(workspace / "agent_roles.txt").write_text(
    "coordinator - Coordinator agent, manages workflows\n"
    "editor      - Video Editor, handles editing tasks\n"
    "renderer    - Rendering agent, handles GPU render jobs\n"
    "sound       - Sound design and mixing\n"
    "marketing   - Marketing and distribution\n"
)

# The mock NAS home directory (simulated local SSH target)
nas_home = Path("/nas_home")
nas_home.mkdir(parents=True, exist_ok=True)

# Put some existing unrelated files in nas_home to act as distractor
(nas_home / "welcome.txt").write_text("Welcome to MediaProd NAS. Authorized access only.\n")
(nas_home / "system_info.txt").write_text(
    "NAS Model: SynologyDS923+\nDSM: 7.2\nSSH: enabled\n"
)

# Write the task brief (business context only, no technical hints)
task_brief = """
# MediaProd Storage Infrastructure — Setup Brief

## Context
Our AI agent team for MediaProd consists of five agents:
- coordinator (Coordinator)
- editor (Video Editor)
- renderer (Renderer)
- sound (Sound Engineer)
- marketing (Marketing)

The "coordinator" agent is designated as our File Master.

## NAS Access
The NAS is accessible at: nas-user@localhost
The NAS home directory is: /nas_home (already set up as the SSH home)
SSH is pre-configured (no password needed for this environment).

## What we need
1. The correct folder structure set up on the NAS for all five agents plus shared and backup directories.
2. A proper agent directory configuration file placed in the right location on the NAS.
3. A nightly backup scheduler configuration file (backup-cron.json) placed in the workspace root (/workspace/).

## Agent for backup target
Use nas-user@localhost as the NAS target in any backup commands.
"""
(workspace / "TASK_BRIEF.md").write_text(task_brief.strip())

print("Workspace and mock NAS initialized successfully.")
print(f"Workspace: {workspace}")
print(f"Mock NAS home: {nas_home}")