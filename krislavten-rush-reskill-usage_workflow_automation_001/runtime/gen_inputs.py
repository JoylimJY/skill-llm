import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create the main project directory
project_dir = os.path.join(workspace, "platform-engineering", "ai-workspace")
os.makedirs(project_dir, exist_ok=True)

# Create deeply nested distractor files
distractor_structure = {
    "src/agents/planner/config.yaml": "model: gpt-4\ntemp: 0.7\nmax_tokens: 2048\n",
    "src/agents/coder/config.yaml": "model: claude-3-5\ntemp: 0.3\n",
    "src/agents/reviewer/settings.json": json.dumps({"role": "reviewer", "enabled": True}),
    "src/pipelines/data_ingest.py": "# Data ingestion pipeline\nimport os\n\ndef ingest(path):\n    pass\n",
    "src/pipelines/transform.py": "# Transform stage\ndef transform(data): return data\n",
    "src/utils/helpers.py": "def log(msg): print(msg)\n",
    "src/utils/validators.py": "def validate(obj): return True\n",
    "docs/architecture.md": "# Architecture\nThis project uses a multi-agent approach.\n",
    "docs/onboarding.md": "# Onboarding\nWelcome to the team.\n",
    "tests/test_pipeline.py": "import pytest\ndef test_stub(): pass\n",
    "tests/test_agents.py": "import pytest\ndef test_agent_config(): pass\n",
    ".env.example": "DATABASE_URL=postgres://localhost/mydb\nDEBUG=false\n",
    "Makefile": "all:\n\techo 'use make targets'\n\ntest:\n\tpytest tests/\n",
    "pyproject.toml": '[project]\nname = "ai-workspace"\nversion = "0.1.0"\n',
    "docker-compose.yml": "version: '3.8'\nservices:\n  app:\n    image: python:3.11\n",
}

for rel_path, content in distractor_structure.items():
    full_path = os.path.join(project_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Create a deliberately broken/incomplete skills.json that the agent must fix/replace
# This simulates a partially attempted setup that is wrong
broken_skills_json = {
    "skills": {
        "old-util": "https://github.com/some/old-repo"  # Wrong format, missing version
    },
    # Missing: registries, defaults entirely
    "version": "1"  # Wrong field, not part of reskill spec
}

with open(os.path.join(project_dir, "skills.json"), "w") as f:
    json.dump(broken_skills_json, f, indent=2)

# Create a stale/wrong skills.lock to confuse
stale_lock = {
    "lockfileVersion": 1,
    "skills": {
        "old-util": {
            "resolved": "https://github.com/some/old-repo",
            "commit": "deadbeef"
        }
    }
}

with open(os.path.join(project_dir, "skills.lock"), "w") as f:
    json.dump(stale_lock, f, indent=2)

# Create an agent requirements spec doc (business context doc, not a hint)
requirements_doc = """# AI Workspace — Skill Management Requirements

## Team Setup Requirements

Our platform team has decided to standardize AI agent skill management using
the reskill package manager.

### Configuration Requirements

1. Custom Internal Registry:
   - Alias: corp
   - URL: https://gitlab.corp-internal.example.com

2. Storage Configuration:
   - Skills should be stored in: .agent-skills (not the default)
   - Installation mode: copy (not symlink, for deployment immutability)

3. Target Agents:
   - claude-code
   - codex

### Skills to Track

| Skill Name   | Source                                              | Notes                         |
|--------------|-----------------------------------------------------|-------------------------------|
| api-gateway  | nicepkg/reskill monorepo, subpath: skills/api-gateway, version: v1.2.0 | From GitHub |
| corp-toolkit | corp registry alias, repo: devops/agent-tools       | Pin to 'stable' branch        |

### Personal/Untracked Skill

The lead developer also wants to install a personal skill globally that should
NOT be tracked in the project config file:
- Source: github:nicepkg/reskill (default branch, no version pin)
- This must NOT appear in skills.json

"""

with open(os.path.join(project_dir, "docs", "skill_requirements.md"), "w") as f:
    f.write(requirements_doc)

print(f"Workspace created at: {project_dir}")
print("Files created:")
for root, dirs, files in os.walk(project_dir):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), project_dir)
        print(f"  {rel}")