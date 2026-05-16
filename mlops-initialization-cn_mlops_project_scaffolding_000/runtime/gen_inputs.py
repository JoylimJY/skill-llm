import os
import random
import stat

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
os.makedirs(WORKSPACE, exist_ok=True)

# ── 1. Distractor directory tree ──────────────────────────────────────────────
distractor_structure = {
    "legacy_experiments/run_001/metrics.csv": "epoch,loss,acc\n1,0.9,0.55\n2,0.7,0.68\n",
    "legacy_experiments/run_001/config.yaml": "lr: 0.001\nbatch_size: 32\nepochs: 10\n",
    "legacy_experiments/run_002/notes.txt": "Tried dropout=0.3, overfitting reduced slightly.\n",
    "legacy_experiments/archived/old_model.pkl.info": "# This file is a placeholder\n",
    "data/raw/compounds_sample.csv": "smiles,activity\nCC(=O)Oc1ccccc1,0.82\nCCO,0.12\n",
    "data/processed/.gitkeep": "",
    "data/external/pubchem_ids.txt": "\n".join(str(random.randint(1000, 9999)) for _ in range(20)) + "\n",
    "notebooks/EDA_v1.ipynb": '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}\n',
    "notebooks/baseline_model_draft.ipynb": '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}\n',
    "docs/architecture_overview.md": "# Architecture\n\nTBD — pending project scaffold.\n",
    "team_standards/coding_guidelines.txt": (
        "All new ML projects must:\n"
        "- Use a src/ package layout\n"
        "- Track dependencies with a lock file\n"
        "- Include IDE configuration for VS Code\n"
        "- Be initialized as a git repository\n"
        "- Include scikit-learn, pandas, and numpy as core dependencies\n"
    ),
    "team_standards/onboarding_checklist.txt": (
        "[ ] Bootstrap project using team toolchain\n"
        "[ ] Add standard ML dependencies\n"
        "[ ] Confirm reproducible environment lock file exists\n"
        "[ ] Push to version control\n"
    ),
    ".env.example": "MLFLOW_TRACKING_URI=http://localhost:5000\nDATA_PATH=/data/raw\n",
    "tmp/scratch_notes.txt": "Project name decided: drug-discovery-model\n",
}

for rel_path, content in distractor_structure.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── 2. Create the skill workspace (scripts + references) ──────────────────────
# The SKILL.md says these scripts/references ALREADY EXIST in the workspace.
# We simulate the skill's repository being present at /workspace (the agent's CWD).

scripts_dir = os.path.join(WORKSPACE, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

references_dir = os.path.join(WORKSPACE, "references")
os.makedirs(references_dir, exist_ok=True)

# ── init-project.sh ──────────────────────────────────────────────────────────
init_script = r"""#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${1:?Usage: init-project.sh <project-name>}"
PROJECT_DIR="$(pwd)/${PROJECT_NAME}"

echo "==> Creating project: ${PROJECT_NAME}"
mkdir -p "${PROJECT_DIR}/src/${PROJECT_NAME//-/_}"
mkdir -p "${PROJECT_DIR}/.vscode"

# pyproject.toml via uv
cd "${PROJECT_DIR}"
uv init --name "${PROJECT_NAME}" --no-readme 2>/dev/null || true

# Ensure src layout: move any auto-created hello.py into src
if [ -f "${PROJECT_DIR}/hello.py" ]; then
    mv "${PROJECT_DIR}/hello.py" "${PROJECT_DIR}/src/${PROJECT_NAME//-/_}/__init__.py" 2>/dev/null || true
fi
touch "${PROJECT_DIR}/src/${PROJECT_NAME//-/_}/__init__.py" 2>/dev/null || true

# .gitignore
cat > "${PROJECT_DIR}/.gitignore" << 'GITIGNORE_EOF'
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/
build/
*.log
.env
mlruns/
data/
models/
*.pkl
*.pt
*.onnx
.DS_Store
GITIGNORE_EOF

# VS Code settings
cp "$(dirname "$0")/../references/vscode-settings.json" "${PROJECT_DIR}/.vscode/settings.json"

# Git init
cd "${PROJECT_DIR}"
git init -q
git add .
git commit -q -m "chore: initial project scaffold [skip ci]"

echo "==> Done. Project ready at: ${PROJECT_DIR}"
"""

with open(os.path.join(scripts_dir, "init-project.sh"), "w") as f:
    f.write(init_script)

os.chmod(os.path.join(scripts_dir, "init-project.sh"),
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── references/pyproject.toml ────────────────────────────────────────────────
ref_pyproject = """\
[project]
name = "example-mlops-project"
version = "0.1.0"
description = "Example MLOps project"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true

[tool.uv]
dev-dependencies = []
"""
with open(os.path.join(references_dir, "pyproject.toml"), "w") as f:
    f.write(ref_pyproject)

# ── references/vscode-settings.json ─────────────────────────────────────────
ref_vscode = """\
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
"""
with open(os.path.join(references_dir, "vscode-settings.json"), "w") as f:
    f.write(ref_vscode)

print(f"Workspace prepared at: {WORKSPACE}")
print("Distractor files created:", len(distractor_structure))
print("Skill scripts + references installed.")