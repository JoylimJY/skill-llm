#!/usr/bin/env python3
"""
Generate the sandbox workspace for the repository audit task.
Creates a realistic project directory with distractor files.
The actual Gitea server will be seeded in setup_script.sh.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create a realistic, deeply nested directory structure ---

dirs = [
    "scicomp-project/src/core",
    "scicomp-project/src/utils",
    "scicomp-project/src/legacy",
    "scicomp-project/tests/unit",
    "scicomp-project/tests/integration",
    "scicomp-project/docs/api",
    "scicomp-project/docs/guides",
    "scicomp-project/infra/ci",
    "scicomp-project/infra/docker",
    "scicomp-project/reports/q1",
    "scicomp-project/reports/q2",
    "scicomp-project/scripts",
    "scicomp-project/.git/refs",  # fake git dir
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant to the task
distractor_files = {
    "scicomp-project/src/core/solver.py": """\
import numpy as np

def solve_linear_system(A, b):
    \"\"\"Solve Ax = b using numpy linalg.\"\"\"
    return np.linalg.solve(A, b)

def eigendecompose(M):
    \"\"\"Compute eigenvalues and eigenvectors.\"\"\"
    return np.linalg.eig(M)
""",
    "scicomp-project/src/utils/io_helpers.py": """\
import json
import csv
from pathlib import Path

def load_config(path):
    with open(path) as f:
        return json.load(f)

def write_csv(data, path):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
""",
    "scicomp-project/src/legacy/old_solver.py": """\
# DEPRECATED: Use src/core/solver.py instead
def legacy_solve(matrix, vector):
    # This uses Gaussian elimination (slow)
    pass
""",
    "scicomp-project/tests/unit/test_solver.py": """\
import pytest
from src.core.solver import solve_linear_system
import numpy as np

def test_basic_solve():
    A = np.array([[2, 1], [1, 3]])
    b = np.array([5, 10])
    x = solve_linear_system(A, b)
    assert np.allclose(np.dot(A, x), b)
""",
    "scicomp-project/tests/integration/test_pipeline.py": """\
import pytest

def test_full_pipeline():
    # Integration test for end-to-end pipeline
    assert True  # placeholder
""",
    "scicomp-project/docs/api/endpoints.md": """\
# API Endpoints

## POST /solve
Submit a linear system for solving.

## GET /status
Check solver status.
""",
    "scicomp-project/docs/guides/quickstart.md": """\
# Quickstart Guide

1. Install dependencies: `pip install -r requirements.txt`
2. Run solver: `python -m src.core.solver`
3. View results in `reports/`
""",
    "scicomp-project/infra/ci/pipeline_old.yml": """\
# OLD PIPELINE - DO NOT USE
stages:
  - test
  - build
  - deploy

test:
  script:
    - pytest tests/
""",
    "scicomp-project/infra/docker/Dockerfile.dev": """\
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "src.core.solver"]
""",
    "scicomp-project/scripts/migrate_data.sh": """\
#!/bin/bash
# Data migration script for v1 -> v2
echo "Migrating data..."
python3 scripts/migrate.py --from v1 --to v2
echo "Done."
""",
    "scicomp-project/reports/q1/summary.txt": """\
Q1 Report
---------
Issues resolved: 14
PRs merged: 8
Open issues remaining: 7
""",
    "scicomp-project/reports/q2/notes.txt": """\
Q2 Notes
--------
Need to audit CI secrets before public release.
Several PRs still open from contractors.
""",
    "scicomp-project/.git/refs/HEAD": "ref: refs/heads/main\n",
    "scicomp-project/requirements.txt": """\
numpy>=1.24.0
scipy>=1.10.0
pytest>=7.0.0
requests>=2.28.0
""",
    "scicomp-project/setup.py": """\
from setuptools import setup, find_packages
setup(
    name='scicomp-project',
    version='0.3.1',
    packages=find_packages(src='src'),
)
""",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# Write a task instruction file that describes what the agent needs to produce
# (business context only, no tool hints)
task_context = """\
AUDIT TASK
==========

You are performing a repository health audit for the 'scicomp' organization's
'neurosolver' repository on the internal forge server.

The server connection details and credentials have been pre-configured in:
  /workspace/server_credentials.json

Your goal: produce a file called audit_report.json in /workspace/
See /workspace/audit_spec.json for the exact fields required.
"""

(workspace / "TASK.txt").write_text(task_context)

# Write audit spec - tells the agent WHAT fields to collect, not HOW
audit_spec = {
    "description": "Produce audit_report.json with the following structure",
    "output_file": "audit_report.json",
    "required_fields": {
        "open_issues": {
            "type": "array",
            "description": "List of open issues, each with 'number' (int) and 'title' (string)"
        },
        "open_prs": {
            "type": "array",
            "description": "List of open pull requests, each with 'number' (int), 'title' (string), and 'author' (string)"
        },
        "pr_details": {
            "type": "object",
            "description": "Details for PR #3 specifically: 'title' (string), 'state' (string), 'author' (string)"
        },
        "ci_secrets": {
            "type": "array",
            "description": "Names of all repository Action secrets (strings)"
        },
        "ci_variables": {
            "type": "array",
            "description": "Names of all repository Action variables (strings)"
        }
    }
}

(workspace / "audit_spec.json").write_text(json.dumps(audit_spec, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")