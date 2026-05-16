import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Distractor directory tree ────────────────────────────────────────────────
distractor_dirs = [
    "projects/alpha/src",
    "projects/alpha/tests",
    "projects/beta/docs",
    "projects/beta/config",
    "archive/2023/Q4",
    "archive/2024/Q1",
    "scripts/utils",
    "scripts/deploy",
    "logs/system",
    "logs/app",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "projects/alpha/src/main.py": "# main entry\nprint('hello')\n",
    "projects/alpha/src/config.yaml": "env: production\ndebug: false\n",
    "projects/alpha/tests/test_main.py": "def test_nothing(): pass\n",
    "projects/beta/docs/overview.md": "# Beta Project\nThis is beta.\n",
    "projects/beta/config/settings.json": '{"timeout": 30, "retries": 3}\n',
    "archive/2023/Q4/report.txt": "Q4 2023 archived report.\n",
    "archive/2024/Q1/notes.md": "# Q1 Notes\nNothing here.\n",
    "scripts/utils/helper.sh": "#!/bin/bash\necho 'helper'\n",
    "scripts/deploy/run.sh": "#!/bin/bash\necho 'deploy'\n",
    "logs/system/syslog.txt": "Jan 1 00:00:00 kernel: boot\n",
    "logs/app/app.log": "2024-01-01 INFO Application started\n",
    "projects/alpha/README_DRAFT.txt": "Draft notes, not final.\n",
    "projects/beta/TODO.txt": "TODO: finish integration\n",
}
for rel, content in distractor_files.items():
    p = workspace / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── Agent A: the workspace config files (to be exported) ────────────────────
agents_md_content = """\
# Agent Workspace Rules

## General
- Always respond in the user's language.
- Prefer concise answers unless depth is requested.

## Code Style
- Use 4-space indentation for Python.
- Prefer f-strings over .format().

## Workflow
- Break large tasks into smaller steps.
- Confirm before destructive actions.
"""

soul_md_content = """\
# Soul Configuration

## Personality
I am a calm, methodical assistant who values precision over speed.
I approach every problem with curiosity and structured thinking.

## Core Values
- Honesty above all else.
- Respect user autonomy.
- Never fabricate information.

## Communication Style
- Use clear, direct sentences.
- Avoid jargon unless the user is technical.
"""

tools_md_content = """\
# Tools Configuration

## Available Tools
- bash: execute shell commands
- python_repl: run Python code snippets
- file_editor: read and write files

## Notes
- Prefer python_repl for data transformations.
- Use bash for system-level operations.
- Always validate output before passing to next step.
"""

identity_md_content = """\
# Identity

## Name
AgentAlpha

## Version
2.1.0

## Creator
Clawic Labs

## Purpose
General-purpose assistant optimized for engineering tasks.
"""

memory_md_content = """\
# Memory

## User Preferences
- Prefers dark mode in all interfaces.
- Usually works between 09:00–18:00 UTC+8.
- Favorite language: Python.

## Past Interactions
- 2024-03-01: Helped refactor authentication module.
- 2024-03-15: Discussed deployment strategies for K8s.

## Personal Notes
- User's name: Zhang Wei.
- Team size: 5 engineers.
"""

# Write Agent A's core config files to workspace root
(workspace / "AGENTS.md").write_text(agents_md_content, encoding="utf-8")
(workspace / "SOUL.md").write_text(soul_md_content, encoding="utf-8")
(workspace / "TOOLS.md").write_text(tools_md_content, encoding="utf-8")
(workspace / "IDENTITY.md").write_text(identity_md_content, encoding="utf-8")
(workspace / "MEMORY.md").write_text(memory_md_content, encoding="utf-8")

# ── Agent B: a pre-built ability package file to be imported from ───────────
# This simulates a received ability package from another agent.
# Format follows the exact SKILL.md template.
agent_b_package = """\
# 能力包：AgentBeta
- 版本：1.0
- 导出时间：2024-06-01 10:00:00
- 来源：AgentBeta / Clawic Labs

---

## AGENTS.md
# Agent Workspace Rules (Beta)

## General
- Always respond in English regardless of user language.
- Prefer verbose, deeply explained answers.

## Code Style
- Use 2-space indentation.
- Prefer arrow functions in JavaScript.

## Workflow
- Document every step before executing.
- Validate inputs strictly.

---

## SOUL.md
# Soul Configuration (Beta)

## Personality
I am an enthusiastic, creative assistant who thrives on brainstorming.
I love exploring unconventional solutions and lateral thinking.

## Core Values
- Creativity is the highest virtue.
- Encourage experimentation.
- Embrace ambiguity.

## Communication Style
- Use vivid metaphors.
- Pepper responses with examples and analogies.

---

## TOOLS.md
# Tools Configuration (Beta)

## Available Tools
- web_search: search the internet
- code_interpreter: run arbitrary code
- image_gen: generate images from prompts

## Notes
- Prefer web_search for up-to-date information.
- Use code_interpreter for complex calculations.

---

## IDENTITY.md
# Identity (Beta)

## Name
AgentBeta

## Version
3.0.0

## Creator
Beta Team

## Purpose
Creative ideation assistant optimized for product teams.

---

## MEMORY.md
# Memory (Beta)

## User Preferences
- Prefers light mode.
- Works in EST timezone.

## Past Interactions
- 2024-05-10: Helped design a new onboarding flow.
- 2024-05-20: Brainstormed names for a new product.

## Personal Notes
- User's name: Alex Rivera.
- Team size: 12 members.
"""

(workspace / "agent_b_package.md").write_text(agent_b_package, encoding="utf-8")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")