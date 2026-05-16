#!/usr/bin/env python3
"""
Generate the sandbox workspace for the reskill multi-step task.
Creates:
- A realistic project structure with distractor files
- Two bare git repos (acting as mock skill repos) served locally
- Each repo contains a valid SKILL.md (required by reskill)
- A partially set up project directory missing skills.json
"""

import os
import subprocess
import json
import random
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ─── 1. Create distractor project files ────────────────────────────────────────
dirs = [
    "src/components",
    "src/agents",
    "src/utils",
    "docs/architecture",
    "docs/api",
    "tests/unit",
    "tests/integration",
    "config/envs",
    "scripts",
    ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

distractor_files = {
    "src/components/AgentRouter.ts": "// AgentRouter: routes requests to appropriate AI agents\nexport class AgentRouter {}",
    "src/agents/PlannerAgent.ts": "// PlannerAgent: decomposes tasks into subtasks\nexport class PlannerAgent {}",
    "src/agents/CoderAgent.ts": "// CoderAgent: generates code from specs\nexport class CoderAgent {}",
    "src/utils/logger.ts": "export const log = (msg: string) => console.log(`[${new Date().toISOString()}] ${msg}`);",
    "src/utils/retry.ts": "export async function retry<T>(fn: () => Promise<T>, n=3): Promise<T> { for(let i=0;i<n;i++) try{ return await fn(); }catch(e){ if(i===n-1) throw e; } throw new Error(); }",
    "docs/architecture/overview.md": "# Architecture Overview\n\nThis project uses a multi-agent pipeline with planning and coding agents.\n\n## Components\n- AgentRouter\n- PlannerAgent\n- CoderAgent",
    "docs/api/endpoints.md": "# API Reference\n\n## POST /run\nTriggers the agent pipeline.\n\n## GET /status\nReturns current run status.",
    "tests/unit/planner.test.ts": "import { PlannerAgent } from '../../src/agents/PlannerAgent';\ndescribe('PlannerAgent', () => { it('should decompose tasks', () => {}); });",
    "tests/integration/router.test.ts": "describe('AgentRouter integration', () => { it('routes to correct agent', () => {}); });",
    "config/envs/development.json": json.dumps({"LOG_LEVEL": "debug", "MAX_AGENTS": 3, "TIMEOUT_MS": 5000}, indent=2),
    "config/envs/production.json": json.dumps({"LOG_LEVEL": "warn", "MAX_AGENTS": 10, "TIMEOUT_MS": 2000}, indent=2),
    "scripts/build.sh": "#!/bin/bash\nnpm run build\necho 'Build complete'",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: npm test",
    "package.json": json.dumps({
        "name": "multi-agent-workspace",
        "version": "0.1.0",
        "description": "AI agent orchestration project",
        "scripts": {"build": "tsc", "test": "jest"},
        "devDependencies": {"typescript": "^5.0.0", "jest": "^29.0.0"}
    }, indent=2),
    "tsconfig.json": json.dumps({
        "compilerOptions": {"target": "ES2020", "module": "commonjs", "strict": True, "outDir": "./dist"},
        "include": ["src/**/*"]
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Make build script executable
os.chmod(os.path.join(WORKSPACE, "scripts/build.sh"), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

# ─── 2. Create mock skill git repos ────────────────────────────────────────────
# We'll create two bare git repos that reskill can clone from via file:// protocol
# Each must have a valid SKILL.md

REPOS_DIR = "/opt/mock-skill-repos"
os.makedirs(REPOS_DIR, exist_ok=True)

def create_skill_repo(repo_name, skill_name, skill_description, skill_version="1.0.0"):
    """Create a bare git repo with a valid SKILL.md for reskill."""
    work_dir = f"/tmp/skill-work-{repo_name}"
    bare_dir = os.path.join(REPOS_DIR, f"{repo_name}.git")
    
    os.makedirs(work_dir, exist_ok=True)
    
    # Init working repo
    subprocess.run(["git", "init", work_dir], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=work_dir, check=True, capture_output=True)
    
    # Create SKILL.md (required by reskill)
    skill_md = f"""---
name: {skill_name}
description: {skill_description}
version: {skill_version}
author: test-team
tags:
  - test
  - agent
---

# {skill_name}

{skill_description}

## Usage

This skill provides capabilities for AI agents.

## Examples

```bash
# Example usage
echo "Using {skill_name}"
```
"""
    skill_md_path = os.path.join(work_dir, "SKILL.md")
    with open(skill_md_path, "w") as f:
        f.write(skill_md)
    
    # Create skill.json (metadata)
    skill_json = {
        "name": skill_name,
        "version": skill_version,
        "description": skill_description
    }
    with open(os.path.join(work_dir, "skill.json"), "w") as f:
        json.dump(skill_json, f, indent=2)
    
    # Create some content files
    with open(os.path.join(work_dir, "instructions.md"), "w") as f:
        f.write(f"# Instructions for {skill_name}\n\nFollow these steps to use this skill effectively.\n")
    
    # Add, commit, tag
    subprocess.run(["git", "add", "-A"], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Initial commit for {skill_name}"], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(["git", "tag", f"v{skill_version}"], cwd=work_dir, check=True, capture_output=True)
    
    # Clone to bare repo
    subprocess.run(["git", "clone", "--bare", work_dir, bare_dir], check=True, capture_output=True)
    
    # Cleanup work dir
    subprocess.run(["rm", "-rf", work_dir], check=True, capture_output=True)
    
    return bare_dir

# Create two skill repos
repo1_path = create_skill_repo(
    repo_name="code-review-skill",
    skill_name="code-review",
    skill_description="Automated code review guidelines and checklists for AI agents",
    skill_version="2.1.0"
)

repo2_path = create_skill_repo(
    repo_name="test-generation-skill", 
    skill_name="test-generation",
    skill_description="Test case generation strategies and templates for AI agents",
    skill_version="1.3.0"
)

print(f"Created mock skill repos:")
print(f"  Repo 1: {repo1_path}")
print(f"  Repo 2: {repo2_path}")

# ─── 3. Write a task context file (NOT a hint, just project metadata) ──────────
task_context = {
    "project": "multi-agent-workspace",
    "team": "AI Engineering",
    "ai_assistants_in_use": ["claude-code", "codex"],
    "skill_sources": {
        "code_review": f"file://{repo1_path}",
        "test_generation": f"file://{repo2_path}"
    },
    "portability_requirement": "copy",
    "note": "This file documents the project's AI assistant configuration requirements."
}

with open(os.path.join(WORKSPACE, "config/project-ai-config.json"), "w") as f:
    json.dump(task_context, f, indent=2)

# ─── 4. Write setup notes for the evaluator (not visible to agent) ─────────────
eval_notes = {
    "repo1_path": repo1_path,
    "repo2_path": repo2_path,
    "skill1_name": "code-review",
    "skill2_name": "test-generation",
    "expected_agents": ["claude-code", "codex"],
    "expected_mode": "copy"
}

with open("/tmp/eval_notes.json", "w") as f:
    json.dump(eval_notes, f, indent=2)

print("\nWorkspace setup complete!")
print(f"Workspace directory: {WORKSPACE}")
print(f"Files created: {len(distractor_files)} distractor files")
print("\nAgent task: Set up reskill for this project following the project-ai-config.json requirements")