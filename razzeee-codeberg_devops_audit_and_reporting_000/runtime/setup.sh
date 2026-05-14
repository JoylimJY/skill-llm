`." This is ALLOWED.

**Decision: PROCEED** - We will run a local Gitea instance, pre-populate it with issues, PRs, and other data, and have the agent use `tea` CLI against this local instance.

2. **Core Workflow:** Chain these features:
   - **Login configuration**: Agent must configure `tea login add` with the local server URL and token
   - **Issue querying + API exploration**: Use `tea issues` and `tea api` with `jq` to extract specific issue/PR metadata
   - **Cross-referencing data**: Query PRs, check specific PR details, and extract secrets/variables from actions - then write a consolidated JSON report

3. **The Proprietary Trap:** 
   - The `--login` flag must be used with a specific login name configured via `tea login add --name`
   - The `tea api` command with `jq` pipeline for field extraction is non-obvious
   - The exact command syntax `tea api repos/owner/repo/pulls/55 | jq '.field'` is bespoke
   - Using `tea actions secrets list` and `tea actions variables list` - these are specific subcommand chains not obvious without the docs

4. **Obfuscation Strategy:** Frame it as a "repository health audit" task where the agent needs to gather data from a project management system and produce a structured JSON report. Describe it in terms of needing to inventory open issues, PR states, and CI configuration (secrets/variables) without mentioning `tea`, Codeberg, or any specific CLI commands.

5. **Industry Context:** Open-source software project governance / DevOps audit for a scientific computing team.
</holistic_design>

<dockerfile>
FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    python3 \
    python3-pip \
    golang-go \
    sqlite3 \
    ca-certificates \
    gnupg \
    lsb-release \
    supervisor \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install tea CLI via go
RUN go install code.gitea.io/tea@latest
RUN cp /root/go/bin/tea /usr/local/bin/tea

# Install Gitea (Forgejo-compatible) as local mock server
RUN wget -q -O /usr/local/bin/gitea \
    "https://dl.gitea.com/gitea/1.21.11/gitea-1.21.11-linux-amd64" \
    && chmod +x /usr/local/bin/gitea

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace
</dockerfile>

<gen_inputs_script>
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
</gen_inputs_script>

<setup_script>
#!/bin/bash
set -e

echo "=== Starting Gitea mock server setup ==="

# Create gitea runtime directories
mkdir -p /opt/gitea/{data,log,config,repos,custom}
mkdir -p /opt/gitea/data/{repositories,attachments,avatars}

# Create minimal Gitea app.ini config
cat > /opt/gitea/config/app.ini << 'EOF'
[DEFAULT]
RUN_USER = root
RUN_MODE = prod

[server]
HTTP_PORT = 3000
DOMAIN = localhost
ROOT_URL = http://localhost:3000/
DISABLE_SSH = true

[database]
DB_TYPE = sqlite3
PATH = /opt/gitea/data/gitea.db

[repository]
ROOT = /opt/gitea/data/repositories

[security]
INSTALL_LOCK = true
SECRET_KEY = audit_secret_key_fixed_42
INTERNAL_TOKEN = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2OTAwMDAwMDB9.fixed

[log]
ROOT_PATH = /opt/gitea/log
LEVEL = Error

[actions]
ENABLED = true

[admin]
DISABLE_REGULAR_ORG_CREATION = false
EOF

# Start Gitea in background
GITEA_WORK_DIR=/opt/gitea gitea web --config /opt/gitea/config/app.ini &
GITEA_PID=$!
echo "Gitea started with PID $GITEA_PID"

# Wait for Gitea to be ready
echo "Waiting for Gitea to become available..."
for i in $(seq 1 60); do
    if curl -s http://localhost:3000/api/v1/version > /dev/null 2>&1; then
        echo "Gitea is up!"
        break
    fi
    sleep 2
    echo "  attempt $i/60..."
done

# Check it's really up
curl -s http://localhost:3000/api/v1/version | jq .

# Create admin user
GITEA_WORK_DIR=/opt/gitea gitea admin user create \
    --config /opt/gitea/config/app.ini \
    --username auditadmin \
    --password "Audit@2024!" \
    --email "admin@scicomp.local" \
    --admin \
    --must-change-password=false 2>/dev/null || echo "Admin user may already exist"

# Generate admin API token
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:3000/api/v1/users/auditadmin/tokens" \
    -H "Content-Type: application/json" \
    -u "auditadmin:Audit@2024!" \
    -d '{"name": "audit-token", "scopes": ["write:issue", "write:repository", "write:user", "write:organization", "write:admin"]}' \
    | jq -r '.sha1')

echo "Admin token: $ADMIN_TOKEN"

# Create organization 'scicomp'
curl -s -X POST "http://localhost:3000/api/v1/orgs" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"username": "scicomp", "visibility": "public", "repo_admin_change_team_access": true}' \
    | jq .name

# Create repository 'neurosolver' under scicomp
curl -s -X POST "http://localhost:3000/api/v1/orgs/scicomp/repos" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "neurosolver", "description": "Scientific computing solver", "auto_init": true, "default_branch": "main"}' \
    | jq .full_name

sleep 2

# Create issues
echo "Creating issues..."
curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Fix memory leak in sparse matrix solver", "body": "The sparse matrix solver leaks memory under load.", "labels": []}' \
    | jq .number

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Add GPU acceleration support", "body": "Request to add CUDA backend for performance.", "labels": []}' \
    | jq .number

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Documentation update for v0.4 API", "body": "Public API docs are outdated.", "labels": []}' \
    | jq .number

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "CI pipeline fails on ARM builds", "body": "ARM64 runner produces failures in integration tests.", "labels": []}' \
    | jq .number

# Close one issue (to test that open filter works)
curl -s -X PATCH "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues/2" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"state": "closed"}' | jq .state

# Create branches for PRs
echo "Creating branches for PRs..."
# Get main branch SHA
MAIN_SHA=$(curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/branches/main" \
    -H "Authorization: token $ADMIN_TOKEN" | jq -r '.commit.id')

echo "Main SHA: $MAIN_SHA"

# Create feature branches
curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/branches" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"new_branch_name\": \"fix/memory-leak\", \"old_branch_name\": \"main\"}" | jq .name

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/branches" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"new_branch_name\": \"feature/gpu-backend\", \"old_branch_name\": \"main\"}" | jq .name

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/branches" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"new_branch_name\": \"docs/api-update\", \"old_branch_name\": \"main\"}" | jq .name

# Add a commit to each branch to make them different from main
for branch in "fix/memory-leak" "feature/gpu-backend" "docs/api-update"; do
    # Get current file SHA
    FILE_SHA=$(curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/contents/README.md" \
        -H "Authorization: token $ADMIN_TOKEN" \
        -G --data-urlencode "ref=$branch" | jq -r '.sha')
    
    CONTENT=$(echo "# Neurosolver - branch: $branch" | base64 -w 0)
    
    curl -s -X PUT "http://localhost:3000/api/v1/repos/scicomp/neurosolver/contents/README.md" \
        -H "Authorization: token $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"Update README for $branch\", \"content\": \"$CONTENT\", \"sha\": \"$FILE_SHA\", \"branch\": \"$branch\"}" \
        | jq .content.name
done

sleep 1

# Create Pull Requests
echo "Creating pull requests..."
curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/pulls" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Fix: resolve memory leak in sparse matrix allocator", "body": "Resolves #1 by implementing proper RAII patterns.", "head": "fix/memory-leak", "base": "main"}' \
    | jq .number

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/pulls" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Feature: CUDA-accelerated tensor operations", "body": "Adds GPU backend using CUDA 12.x.", "head": "feature/gpu-backend", "base": "main"}' \
    | jq .number

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/pulls" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Docs: comprehensive v0.4 API reference update", "body": "Brings docs up to date with the new solver interface.", "head": "docs/api-update", "base": "main"}' \
    | jq .number

# Close PR #2 (to test open filter)
curl -s -X PATCH "http://localhost:3000/api/v1/repos/scicomp/neurosolver/pulls/2" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"state": "closed"}' | jq .state

# Create Actions Secrets
echo "Creating Actions secrets..."
curl -s -X PUT "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/secrets/DEPLOY_SSH_KEY" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"data": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ..."}' \
    | echo "Secret DEPLOY_SSH_KEY: $?"

curl -s -X PUT "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/secrets/PYPI_API_TOKEN" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"data": "pypi-AgEIcHlwaS5vcmcCJ..."}' \
    | echo "Secret PYPI_API_TOKEN: $?"

curl -s -X PUT "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/secrets/CODECOV_TOKEN" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"data": "abc123codecov..."}' \
    | echo "Secret CODECOV_TOKEN: $?"

# Create Actions Variables
echo "Creating Actions variables..."
curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/variables" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "PYTHON_VERSION", "value": "3.11"}' \
    | echo "Variable PYTHON_VERSION: $?"

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/variables" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "DOCKER_REGISTRY", "value": "registry.scicomp.internal"}' \
    | echo "Variable DOCKER_REGISTRY: $?"

curl -s -X POST "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/variables" \
    -H "Authorization: token $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "MAX_WORKERS", "value": "8"}' \
    | echo "Variable MAX_WORKERS: $?"

# Write server credentials for the agent
cat > /workspace/server_credentials.json << EOF
{
  "server_url": "http://localhost:3000",
  "token": "$ADMIN_TOKEN",
  "login_name": "local-forge",
  "organization": "scicomp",
  "repository": "neurosolver",
  "full_repo": "scicomp/neurosolver"
}
EOF

echo "=== Setup complete ==="
echo "Gitea running at http://localhost:3000"
echo "Credentials written to /workspace/server_credentials.json"
cat /workspace/server_credentials.json

# Verify data was created
echo ""
echo "=== Verification ==="
echo "Open Issues:"
curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/issues?state=open&type=issues" \
    -H "Authorization: token $ADMIN_TOKEN" | jq '[.[] | {number: .number, title: .title}]'

echo "Open PRs:"
curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/pulls?state=open" \
    -H "Authorization: token $ADMIN_TOKEN" | jq '[.[] | {number: .number, title: .title}]'

echo "Secrets:"
curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/secrets" \
    -H "Authorization: token $ADMIN_TOKEN" | jq '[.[] | .name]'

echo "Variables:"
curl -s "http://localhost:3000/api/v1/repos/scicomp/neurosolver/actions/variables" \
    -H "Authorization: token $ADMIN_TOKEN" | jq '[.[] | .name]'