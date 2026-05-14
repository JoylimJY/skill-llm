#!/usr/bin/env python3
import os
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# === 1. Create the claude-relay skill directory structure ===
skill_dir = workspace / "skills" / "claude-relay"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# relay.sh is already present per SKILL.md — we create a placeholder note
# but the setup_script will copy/create the real one.
# Actually per directive: "All scripts mentioned in the SKILL.md already exist in the workspace"
# So we just create the structure and the setup_script will handle relay.sh.

# Create a messy/incomplete projects.map (wrong format — agent must fix or create correctly)
broken_map = skill_dir / "projects.map"
broken_map.write_text(
    "# This file has wrong formatting\n"
    "payment-service: /workspace/projects/payment-service\n"  # wrong format (colon not =)
    "auth_gateway /workspace/projects/auth-gateway\n"        # missing =
    "# TODO: add more projects\n"
)

# Create a projects.map.example for reference
example_map = skill_dir / "projects.map.example"
example_map.write_text(
    "# Format: alias=absolute_path\n"
    "myapp=/home/user/projects/myapp\n"
    "backend=/home/user/work/backend-service\n"
)

# === 2. Create realistic project directories ===
projects_root = workspace / "projects"

# Project 1: "My-WebApp" (has special chars in name — tests sanitization)
webapp_dir = projects_root / "My-WebApp"
webapp_dir.mkdir(parents=True, exist_ok=True)
(webapp_dir / "package.json").write_text('{"name": "my-webapp", "version": "1.0.0"}')
(webapp_dir / "src").mkdir(exist_ok=True)
(webapp_dir / "src" / "index.js").write_text("console.log('hello');")
(webapp_dir / ".env").write_text("NODE_ENV=production\n")

# Project 2: "data--pipeline" (double dash — tests sanitize stripping of double underscores)
pipeline_dir = projects_root / "data--pipeline"
pipeline_dir.mkdir(parents=True, exist_ok=True)
(pipeline_dir / "main.py").write_text("print('pipeline')")
(pipeline_dir / "requirements.txt").write_text("pandas\nnumpy\n")
(pipeline_dir / "config").mkdir(exist_ok=True)
(pipeline_dir / "config" / "settings.yaml").write_text("batch_size: 100\n")

# Project 3: a deeply nested project to act as distractor
nested = projects_root / "infrastructure" / "k8s" / "monitoring"
nested.mkdir(parents=True, exist_ok=True)
(nested / "prometheus.yaml").write_text("global:\n  scrape_interval: 15s\n")

# Project 4: another distractor
api_dir = projects_root / "api-gateway"
api_dir.mkdir(parents=True, exist_ok=True)
(api_dir / "go.mod").write_text("module api-gateway\n\ngo 1.21\n")
(api_dir / "main.go").write_text('package main\n\nfunc main() {}\n')

# === 3. Distractor files throughout workspace ===
distractor_dirs = [
    workspace / "docs",
    workspace / "logs",
    workspace / "tmp",
    workspace / "archive" / "2023",
    workspace / "scripts",
    workspace / "config" / "envs",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

(workspace / "docs" / "architecture.md").write_text("# Architecture\nSee confluence.\n")
(workspace / "docs" / "runbook.md").write_text("# Runbook\n## Deploy\nRun deploy.sh\n")
(workspace / "logs" / "relay.log").write_text("2024-01-01 session started\n2024-01-02 session stopped\n")
(workspace / "tmp" / "scratch.txt").write_text("temp notes\n")
(workspace / "archive" / "2023" / "old_projects.map").write_text("oldapp=/home/old/app\n")
(workspace / "scripts" / "deploy.sh").write_text("#!/bin/bash\necho deploying\n")
(workspace / "config" / "envs" / "production.env").write_text("ENV=prod\nDEBUG=false\n")
(workspace / "config" / "envs" / "staging.env").write_text("ENV=staging\nDEBUG=true\n")

# Extra distractors
(workspace / "README_OLD.txt").write_text("old readme, ignore\n")
(workspace / "Makefile").write_text("all:\n\techo done\n")
(workspace / "projects" / "orphaned_script.sh").write_text("#!/bin/bash\necho orphan\n")

# === 4. Create the task specification file ===
task_spec = workspace / "task_briefing.txt"
task_spec.write_text("""PLATFORM ENGINEERING TASK BRIEFING
====================================

We have two microservice projects that need to be registered and tested
in our terminal relay system:

Project A: Located at /workspace/projects/My-WebApp
  - Should be accessible via the short alias: webapp

Project B: Located at /workspace/projects/data--pipeline  
  - Should be accessible via the short alias: pipeline

REQUIRED DELIVERABLE: session_audit.json

After setting up the aliases and running the relay workflow for both projects,
produce a file called session_audit.json documenting the results.

The audit must include:
  - For each project alias: the computed tmux session name
  - Whether the start, send, and stop operations succeeded
  - The exit code observed when attempting to send a message to a 
    project that has NOT been started yet (use alias "webapp" for this test,
    before starting it)
  - Any output captured from the tail operation

Constraints:
  - The relay system's projects.map file is currently malformed and must be corrected
  - Use the alias names (webapp, pipeline) for all relay operations
  - The CLAUDE_RELAY_ROOT should point to /workspace/projects
  - Set CLAUDE_BIN to /workspace/mock_claude.sh
""")

print(f"Workspace prepared at: {workspace}")
print(f"Projects created: My-WebApp, data--pipeline")
print(f"Skill dir: {skill_dir}")