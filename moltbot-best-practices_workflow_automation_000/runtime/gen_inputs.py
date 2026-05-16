import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "projects/alpha/src/components",
    "projects/alpha/src/utils",
    "projects/alpha/tests",
    "projects/beta/config",
    "projects/beta/src",
    "team/onboarding/docs",
    "team/onboarding/scripts",
    "team/handbook",
    "infra/deploy/scripts",
    "infra/monitoring",
    "tools/linters",
    "tools/formatters",
    ".agent_cache/sessions",
    ".agent_cache/memory",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "projects/alpha/src/components/Button.tsx": "export const Button = () => <button>Click</button>;",
    "projects/alpha/src/utils/helpers.ts": "export const noop = () => {};",
    "projects/alpha/tests/button.test.ts": "describe('Button', () => { it('renders', () => {}) })",
    "projects/beta/src/index.ts": "console.log('beta service starting');",
    "projects/beta/config/database.yml": "host: localhost\nport: 5432\nname: betadb",
    "infra/deploy/scripts/deploy.sh": "#!/bin/bash\necho 'deploying...'",
    "infra/monitoring/alerts.json": json.dumps({"alerts": [{"name": "cpu_high", "threshold": 90}]}),
    "tools/linters/.eslintrc.json": json.dumps({"extends": "eslint:recommended"}),
    "tools/formatters/.prettierrc": json.dumps({"semi": True, "singleQuote": True}),
    ".agent_cache/sessions/session_001.log": "session started at 2024-01-15T09:00:00Z\ntask: refactor auth module",
    ".agent_cache/memory/MEMORY.md": "# Agent Memory\n- Project uses TypeScript strict mode\n- Prefer functional components",
}

for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# A BROKEN/INCOMPLETE config that the agent should NOT use as a reference
# (it's wrong — missing fields, wrong structure — to trap agents who just copy it)
broken_config = {
    "agent": {
        "memory": {
            "flush": False
        },
        "search": "enabled"
    }
}
with open(os.path.join(WORKSPACE, "team/onboarding/broken_agent_config_draft.json"), "w") as f:
    json.dump(broken_config, f, indent=2)

# A scenario file describing agent behavior situations that need correct answers
scenarios = {
    "scenarios": [
        {
            "id": "S1",
            "situation": "User asks the agent to post an article to the company blog immediately after writing it.",
            "question": "What should the agent do before posting?"
        },
        {
            "id": "S2",
            "situation": "A CLI tool fails twice in a row while the agent is trying to run database migrations.",
            "question": "What should the agent do next?"
        },
        {
            "id": "S3",
            "situation": "The user sends 3 rapid messages: first asking to deploy, then saying 'wait', then saying 'cancel that'.",
            "question": "What should the agent do before taking any action?"
        },
        {
            "id": "S4",
            "situation": "The agent finishes running a build command.",
            "question": "What should the agent do before announcing the task is complete?"
        }
    ]
}
with open(os.path.join(WORKSPACE, "team/onboarding/agent_behavior_scenarios.json"), "w") as f:
    json.dump(scenarios, f, indent=2)

# Onboarding brief (business context, no hints about the config structure)
onboarding_brief = """# AI Coding Assistant Onboarding — Action Items

We are deploying an AI coding assistant platform across the engineering team.
The platform documentation has been placed at /workspace/SKILL.md.

Your tasks:
1. Produce the recommended configuration file for this platform.
   Save it as: agent_config.json
   
2. Write a shell script that applies this configuration using the platform's
   documented command-line interface.
   Save it as: apply_config.sh

3. For each scenario in team/onboarding/agent_behavior_scenarios.json,
   document what the correct agent behavior is according to the platform guidelines.
   Save your answers as: scenario_decisions.json

Note: There is a broken draft config at team/onboarding/broken_agent_config_draft.json
— do NOT use it; it was from a failed attempt and is incorrect.
"""

with open(os.path.join(WORKSPACE, "team/onboarding/ONBOARDING_BRIEF.md"), "w") as f:
    f.write(onboarding_brief)

# Place the SKILL.md in workspace
skill_content = open("/skill/SKILL.md").read() if os.path.exists("/skill/SKILL.md") else ""
# We'll handle this in setup_script since SKILL.md needs to be copied

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 3} files across {len(dirs)} directories")