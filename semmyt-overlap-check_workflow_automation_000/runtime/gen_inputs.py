#!/usr/bin/env python3
import os
import json
import stat

WORKSPACE = "/workspace"

# --- Create a realistic project directory structure (distractor files) ---
dirs = [
    "src/migrations",
    "src/cli",
    "src/core",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "docs/guides",
    ".github/workflows",
    "scripts",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

files = {
    "src/migrations/runner.py": """\
\"\"\"Migration runner core logic.\"\"\"
import os

class MigrationRunner:
    def __init__(self, db_url):
        self.db_url = db_url

    def run(self, direction='up'):
        raise NotImplementedError
""",
    "src/migrations/schema.py": """\
\"\"\"Schema management utilities.\"\"\"

def apply_schema(conn, schema_file):
    pass
""",
    "src/cli/main.py": """\
\"\"\"CLI entrypoint.\"\"\"
import argparse

def main():
    parser = argparse.ArgumentParser(description='dbmigrate CLI')
    parser.add_argument('command', choices=['up', 'down', 'status'])
    args = parser.parse_args()
""",
    "src/core/connection.py": """\
\"\"\"Database connection management.\"\"\"

class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self._pool = []
""",
    "src/core/lock.py": """\
\"\"\"Advisory lock implementation.\"\"\"

class MigrationLock:
    def acquire(self):
        pass
    def release(self):
        pass
""",
    "tests/unit/test_runner.py": """\
import pytest
from src.migrations.runner import MigrationRunner

def test_runner_init():
    r = MigrationRunner('sqlite://:memory:')
    assert r.db_url == 'sqlite://:memory:'
""",
    "tests/integration/test_schema.py": """\
import pytest

def test_schema_apply():
    pass
""",
    "docs/api/runner.md": "# Runner API\n\nDocumentation for the migration runner.\n",
    "docs/guides/quickstart.md": "# Quickstart\n\nGet started with dbmigrate.\n",
    ".github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -e .
      - run: pytest
""",
    "scripts/reset_db.sh": "#!/bin/bash\necho 'Resetting database...'\n",
    "config/defaults.yaml": "max_connections: 10\ntimeout: 30\nretry_count: 3\n",
    "setup.py": """\
from setuptools import setup, find_packages
setup(name='dbmigrate', version='0.1.0', packages=find_packages())
""",
    "CHANGELOG.md": """\
# Changelog

## 0.1.0
- Initial release
- Basic up/down migration support
""",
}

for filepath, content in files.items():
    full_path = os.path.join(WORKSPACE, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the mock `gh` binary ---
# This mock responds deterministically to the commands the agent should call.
# The mock tracks calls by writing to a log file so the eval script can verify them.

GH_MOCK_SCRIPT = r"""#!/usr/bin/env python3
import sys
import json
import os

LOG_FILE = "/workspace/.gh_call_log.jsonl"

def log_call(args):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({"args": args}) + "\n")

args = sys.argv[1:]
log_call(args)

cmd_str = " ".join(args)

# ── gh repo view ──────────────────────────────────────────────────────────────
if args[:3] == ["repo", "view", "--json"] and "nameWithOwner" in args:
    print("openforge/dbmigrate")
    sys.exit(0)

# ── gh search issues ──────────────────────────────────────────────────────────
if len(args) >= 2 and args[0] == "search" and args[1] == "issues":
    # Extract keywords from args (anything not starting with --)
    keywords = [a for a in args[2:] if not a.startswith("--") and a != "openforge/dbmigrate"]
    keyword_str = " ".join(keywords).lower()

    # Repo must be openforge/dbmigrate
    has_repo = "--repo" in args

    results = []

    # Relevant matches for "connection pool timeout" topic
    if any(k in keyword_str for k in ["connection", "pool", "timeout", "exhaust"]):
        results = [
            {"number": 342, "title": "Connection pool exhausted under high load", "state": "OPEN", "comments": 8},
            {"number": 287, "title": "Timeout errors when pool size exceeded", "state": "OPEN", "comments": 3},
            {"number": 201, "title": "DB connection leak in migration runner", "state": "CLOSED", "comments": 12},
        ]
    elif any(k in keyword_str for k in ["schema", "lock", "deadlock"]):
        results = [
            {"number": 310, "title": "Schema lock deadlock on concurrent migrations", "state": "OPEN", "comments": 5},
        ]
    else:
        results = []

    print(json.dumps(results))
    sys.exit(0)

# ── gh search prs ─────────────────────────────────────────────────────────────
if len(args) >= 2 and args[0] == "search" and args[1] == "prs":
    keywords = [a for a in args[2:] if not a.startswith("--") and a != "openforge/dbmigrate"]
    keyword_str = " ".join(keywords).lower()

    results = []

    if any(k in keyword_str for k in ["connection", "pool", "timeout", "exhaust"]):
        results = [
            {"number": 355, "title": "Fix: increase default connection pool size", "state": "OPEN", "comments": 2},
        ]
    elif any(k in keyword_str for k in ["schema", "lock", "deadlock"]):
        results = []
    else:
        results = []

    print(json.dumps(results))
    sys.exit(0)

# ── gh issue view ─────────────────────────────────────────────────────────────
if len(args) >= 2 and args[0] == "issue" and args[1] == "view":
    issue_num = None
    for a in args[2:]:
        try:
            issue_num = int(a)
            break
        except ValueError:
            pass

    if issue_num == 342:
        print("""number: 342
title: Connection pool exhausted under high load
state: OPEN
author: jsmith
comments: 8
body:
  When running more than 50 concurrent migrations, the connection pool gets
  exhausted and throws 'too many connections'. The default pool size of 10
  is too small for production workloads.

  Steps to reproduce:
  1. Set max_connections=10 in config
  2. Run 50 parallel migration jobs
  3. Observe error: ConnectionPoolExhausted

  This blocks our production deploy pipeline.
""")
    elif issue_num == 287:
        print("""number: 287
title: Timeout errors when pool size exceeded
state: OPEN
author: alee
comments: 3
body:
  Getting consistent timeout errors. Related to pool exhaustion.
  Seems like a duplicate of a broader connection management issue.
""")
    elif issue_num == 201:
        print("""number: 201
title: DB connection leak in migration runner
state: CLOSED
author: mwong
comments: 12
body:
  Fixed in v0.0.9 by properly closing connections in finally blocks.
  This is now resolved.
""")
    elif issue_num == 355:
        print("""number: 355
title: Fix: increase default connection pool size
state: OPEN
author: rkaur
comments: 2
body:
  Bumps default max_connections from 10 to 25 to address pool exhaustion
  reports. Related to #342.
""")
    else:
        print(f"issue {issue_num} not found")
        sys.exit(1)
    sys.exit(0)

# ── gh pr view ────────────────────────────────────────────────────────────────
if len(args) >= 2 and args[0] == "pr" and args[1] == "view":
    pr_num = None
    for a in args[2:]:
        try:
            pr_num = int(a)
            break
        except ValueError:
            pass

    if pr_num == 355:
        print("""number: 355
title: Fix: increase default connection pool size
state: OPEN
author: rkaur
comments: 2
body:
  Bumps default max_connections from 10 to 25 to address pool exhaustion
  reports. Related to #342.
""")
    else:
        print(f"pr {pr_num} not found")
        sys.exit(1)
    sys.exit(0)

# ── gh issue create / pr create ───────────────────────────────────────────────
if len(args) >= 2 and args[0] in ("issue", "pr") and args[2:3] == ["create"]:
    print(f"https://github.com/openforge/dbmigrate/{args[0]}s/999")
    sys.exit(0)

# ── gh issue comment ──────────────────────────────────────────────────────────
if len(args) >= 2 and args[0] == "issue" and args[1] == "comment":
    print("Comment posted.")
    sys.exit(0)

# Fallback
print(f"gh mock: unrecognized command: {cmd_str}", file=sys.stderr)
sys.exit(1)
"""

gh_mock_path = "/usr/local/bin/gh"
with open(gh_mock_path, "w") as f:
    f.write(GH_MOCK_SCRIPT)
os.chmod(gh_mock_path, os.stat(gh_mock_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# --- Initialize the git repo so `gh repo view` context works ---
os.chdir(WORKSPACE)
os.system("git init -q")
os.system("git remote add origin https://github.com/openforge/dbmigrate.git 2>/dev/null || true")

# --- Clear the call log to start fresh ---
log_path = os.path.join(WORKSPACE, ".gh_call_log.jsonl")
if os.path.exists(log_path):
    os.remove(log_path)

# --- Create the task brief ---
task_brief = """\
TASK BRIEF
==========
Project: openforge/dbmigrate (database migration CLI tool)

Reported problem:
  Our production deployment pipeline keeps failing because of connection pool
  exhaustion errors. When running more than 50 concurrent migration jobs,
  the system throws errors indicating too many open connections. The default
  pool size appears to be too small for production workloads.

Your job:
  Before filing a new bug report about this connection pool exhaustion issue,
  perform a full duplicate/overlap check against the project's existing
  issues and pull requests.

  Save your complete findings and recommendation to a file called:
    triage_report.md

  The report must include what you found and what action you recommend
  (e.g., comment on an existing thread vs. creating a new issue).
"""

with open(os.path.join(WORKSPACE, "task_brief.txt"), "w") as f:
    f.write(task_brief)

print("Workspace initialized successfully.")
print(f"Mock `gh` binary installed at: {gh_mock_path}")
print(f"Task brief written to: {WORKSPACE}/task_brief.txt")