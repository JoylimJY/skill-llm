import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "docs/api",
    "docs/guides",
    "docs/internal",
    "src/core",
    "src/utils",
    "src/plugins",
    "tests/unit",
    "tests/integration",
    "scripts/deploy",
    "scripts/lint",
    "assets/images",
    "assets/icons",
    ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/api/endpoints.txt": "GET /api/v1/users\nPOST /api/v1/users\nDELETE /api/v1/users/{id}\n",
    "docs/guides/quickstart.txt": "Install dependencies, then run `npm start`.\n",
    "docs/internal/notes.txt": "Internal note: migration planned for Q3.\n",
    "src/core/engine.py": "class Engine:\n    def run(self): pass\n",
    "src/utils/helpers.py": "def slugify(s): return s.lower().replace(' ', '-')\n",
    "src/plugins/auth.py": "class AuthPlugin:\n    def authenticate(self, token): return True\n",
    "tests/unit/test_engine.py": "def test_run(): assert True\n",
    "tests/integration/test_api.py": "def test_endpoint(): pass\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
    "scripts/lint/lint.sh": "#!/bin/bash\nflake8 src/\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "assets/icons/icon_list.txt": "icon-home.svg\nicon-user.svg\nicon-settings.svg\n",
}

for rel_path, content in distractor_files.items():
    with open(os.path.join(workspace, rel_path), "w") as f:
        f.write(content)

# --- The core problem input: a messy brief for the landing page ---
# This is raw content that the agent must use to compose the final Markdown document.
# It has real URLs, link targets, and code snippets — all the ingredients to trigger
# every formatting rule in the skill.

brief_content = """\
PROJECT: NexusFlow — A lightweight event-driven workflow engine for Python.

SECTIONS TO INCLUDE:
1. Title: "NexusFlow — Event-Driven Workflows for Python"
2. Short description: "NexusFlow lets you compose, schedule, and observe event-driven pipelines with minimal boilerplate."
3. Quick Install (code block, bash): pip install nexusflow
4. Links to include:
   - GitHub repo: https://github.com/nexusflow/nexusflow
   - Documentation site: https://nexusflow.readthedocs.io
   - PyPI page: https://pypi.org/project/nexusflow
   - Discord community: https://discord.gg/nexusflow
5. A short usage example (code block, Python):
   from nexusflow import Pipeline
   p = Pipeline()
   p.add_step("fetch", fetch_data)
   p.run()
6. Mention bare URL in a sentence like: "Latest release notes are at https://github.com/nexusflow/nexusflow/releases，please check before upgrading."
7. A footer note with another bare URL: "Join our mailing list at https://nexusflow.io/mailing-list.欢迎订阅。"
8. All links above should be clickable Markdown links (use the link text provided or sensible defaults).

TARGET FILE: landing_page.md
The output must be the raw, copyable Markdown source — wrapped so that the whole document
can be pasted directly into any wiki or CMS without rendering artifacts.
"""

with open(os.path.join(workspace, "docs/landing_brief.txt"), "w", encoding="utf-8") as f:
    f.write(brief_content)

# A second distractor file that intentionally uses "wrong" formatting to mislead
distractor_md_wrong = """\
```
# OldProject

[Docs](https://old.example.com) — see also https://old.example.com/blog,for updates.
```
"""
with open(os.path.join(workspace, "docs/internal/old_draft.txt"), "w", encoding="utf-8") as f:
    f.write(distractor_md_wrong)

print("Workspace generated successfully.")