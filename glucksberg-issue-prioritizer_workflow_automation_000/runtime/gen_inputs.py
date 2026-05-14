#!/usr/bin/env python3
"""
Generate a realistic workspace for the issue-prioritizer skill evaluation.
Creates a mock `gh` CLI binary, distractor files, and project structure.
"""
import os
import json
import stat

WORKSPACE = "/workspace"

# ── distractor directory tree ────────────────────────────────────────────────
dirs = [
    "src/core", "src/cli", "src/utils", "src/pipeline",
    "tests/unit", "tests/integration",
    "docs/api", "docs/guides",
    "scripts", ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

distractor_files = {
    "src/core/pipeline.py":
        "class Pipeline:\n    def run(self): pass\n    def status(self): return 0\n",
    "src/core/connect.py":
        "def connect(host, timeout=None):\n    import socket\n    s = socket.socket()\n    s.connect((host, 9000))\n",
    "src/cli/main.py":
        "import argparse\ndef main(): pass\n",
    "src/cli/status.py":
        "def show_status(pipeline_id):\n    pct = pipeline_id / 100  # bug on line 47\n    return pct\n",
    "src/utils/config.py":
        "import json\ndef load_config(path):\n    with open(path) as f:\n        return json.load(f)\n",
    "src/pipeline/executor.py":
        "import threading\ndef execute_parallel(tasks):\n    threads = [threading.Thread(target=t) for t in tasks]\n    for t in threads: t.start()\n",
    "tests/unit/test_pipeline.py":
        "def test_run(): assert True\n",
    "tests/integration/test_connect.py":
        "def test_connect(): pass\n",
    "docs/api/reference.md":
        "# API Reference\n\n## connect\n\nConnect to a datapipe endpoint.\n",
    "docs/guides/kubernetes.md":
        "# Kubernetes Deployment\n\nSet `DATAPIPE_HOST` environment variable.\n",
    "scripts/release.sh":
        "#!/bin/bash\necho 'Building release...'\n",
    ".github/workflows/ci.yml":
        "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "pyproject.toml":
        '[project]\nname = "datapipe-cli"\nversion = "0.3.1"\n',
    "CHANGELOG.md":
        "# Changelog\n\n## 0.3.1\n- fix: handle empty config files\n",
}

for relpath, content in distractor_files.items():
    fpath = os.path.join(WORKSPACE, relpath)
    with open(fpath, "w") as f:
        f.write(content)

# ── mock `gh` CLI ─────────────────────────────────────────────────────────────
# Issues data (raw JSON as `gh issue list` would return)
ISSUES = [
    {
        "number": 10,
        "title": "Fix crash when empty credentials are passed",
        "body": "The CLI crashes with a NullPointerException whenever empty credentials are provided to the auth module. Stack trace included. This is reproducible 100% of the time with `datapipe auth login --user '' --pass ''`.",
        "labels": [{"name": "bug"}],
        "createdAt": "2024-01-10T10:00:00Z",
        "comments": 3,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/10"
    },
    {
        "number": 20,
        "title": "Update documentation for pipeline connect command",
        "body": "The docs for `pipeline connect` are outdated and missing the new --region flag introduced in 0.3.0.",
        "labels": [{"name": "documentation"}],
        "createdAt": "2024-01-15T09:00:00Z",
        "comments": 1,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/20"
    },
    {
        "number": 30,
        "title": "Add --timeout flag to connect command",
        "body": "When connecting to slow endpoints the CLI hangs indefinitely. Proposed solution: add a `--timeout` flag that passes the value to the underlying HTTP client. Simple one-line change in `src/core/connect.py`. Steps to reproduce: run `datapipe connect slow-host` and wait 30 seconds until the process hangs.",
        "labels": [{"name": "enhancement"}],
        "createdAt": "2024-01-20T11:00:00Z",
        "comments": 5,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/30"
    },
    {
        "number": 40,
        "title": "Race condition in parallel pipeline execution causes data corruption",
        "body": "When running multiple pipelines in parallel, data gets corrupted between pipeline stages. The root cause is unknown — it appears to be a concurrency issue in the executor. Security implication: corrupted pipeline data may expose records belonging to other users. We need to investigate the threading model thoroughly.",
        "labels": [{"name": "bug"}, {"name": "security"}],
        "createdAt": "2024-01-18T14:00:00Z",
        "comments": 12,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/40"
    },
    {
        "number": 50,
        "title": "Rewrite entire datapipe core in Rust with blockchain-based audit trail",
        "body": "We should rewrite the entire datapipe core from scratch in Rust for 10x performance gains and add a blockchain-powered audit trail using an experimental consensus protocol. This would be an AI-powered migration assistant to help transition users.",
        "labels": [{"name": "enhancement"}],
        "createdAt": "2024-01-05T08:00:00Z",
        "comments": 2,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/50"
    },
    {
        "number": 60,
        "title": "Add input validation to pipeline config",
        "body": "Pipeline configs are not validated before execution. Proposed solution: build a comprehensive validation framework with JSON Schema definitions, a plugin architecture for custom validators, a validation DSL, and a config migration tool. This requires refactoring the entire config module across 6 new files and changing the config loading API.",
        "labels": [{"name": "enhancement"}],
        "createdAt": "2024-01-12T16:00:00Z",
        "comments": 4,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/60"
    },
    {
        "number": 70,
        "title": "How do I configure datapipe for Kubernetes deployment?",
        "body": "I'm trying to deploy datapipe in a Kubernetes cluster but I'm not sure how to configure the environment variables and secrets. Can someone help me understand the configuration options?",
        "labels": [{"name": "question"}],
        "createdAt": "2024-01-22T13:00:00Z",
        "comments": 0,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/70"
    },
    {
        "number": 80,
        "title": "Pipeline status command shows incorrect progress percentage",
        "body": "The `datapipe status` command occasionally shows progress percentages above 100% (e.g., 150%). The root cause is unknown and requires investigation into the progress calculation logic.",
        "labels": [{"name": "bug"}],
        "createdAt": "2024-01-19T10:00:00Z",
        "comments": 3,
        "url": "https://github.com/datapipe-org/datapipe-cli/issues/80"
    },
]

# PRs data
PRS = [
    {
        "number": 101,
        "title": "Fix null check for auth credentials",
        "body": "Adds proper null/empty check for credentials in auth module.\n\nfixes #10\n\nTested manually, all edge cases covered.",
        "url": "https://github.com/datapipe-org/datapipe-cli/pull/101"
    },
    {
        "number": 102,
        "title": "Update docs for pipeline connect command",
        "body": "Updates the pipeline connect documentation to include the new --region flag and corrects outdated examples.",
        "url": "https://github.com/datapipe-org/datapipe-cli/pull/102"
    },
]

# Write the mock gh script
GH_SCRIPT = r'''#!/usr/bin/env python3
"""Mock gh CLI for issue-prioritizer evaluation."""
import sys
import json
import os

ISSUES = ''' + json.dumps(ISSUES, indent=2) + r'''

PRS = ''' + json.dumps(PRS, indent=2) + r'''

def main():
    args = sys.argv[1:]

    # Handle: gh auth status
    if args and args[0] == 'auth':
        print("github.com: Logged in as mock-user")
        sys.exit(0)

    # Handle: gh issue list ...
    if len(args) >= 2 and args[0] == 'issue' and args[1] == 'list':
        # Parse --limit
        limit = 30
        if '--limit' in args:
            idx = args.index('--limit')
            try:
                limit = int(args[idx + 1])
            except (IndexError, ValueError):
                pass
        # Parse --repo (validate it's correct repo)
        repo = None
        if '--repo' in args:
            idx = args.index('--repo')
            try:
                repo = args[idx + 1]
            except IndexError:
                pass
        if repo and repo != 'datapipe-org/datapipe-cli':
            print(json.dumps([]))
            sys.exit(0)
        print(json.dumps(ISSUES[:limit]))
        sys.exit(0)

    # Handle: gh pr list ...
    if len(args) >= 2 and args[0] == 'pr' and args[1] == 'list':
        print(json.dumps(PRS))
        sys.exit(0)

    # Unknown command
    print(f"unknown command: {' '.join(args)}", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()
'''

gh_path = "/usr/local/bin/gh"
with open(gh_path, "w") as f:
    f.write(GH_SCRIPT)
os.chmod(gh_path, os.stat(gh_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Write a small reference file the agent should NOT need (distractor)
with open(os.path.join(WORKSPACE, "scripts", "triage_old.sh"), "w") as f:
    f.write("#!/bin/bash\n# Deprecated triage script\necho 'Use the issue-prioritizer skill instead'\n")

# Write a partial/broken notes file to confuse naive agents
with open(os.path.join(WORKSPACE, "triage_notes.txt"), "w") as f:
    f.write("Last triage: 2024-01-01\nIssues reviewed: 0\nNotes: Start fresh - all old scores invalid.\n")

print("Workspace and mock gh CLI created successfully.")
print(f"Issues: {len(ISSUES)}, PRs: {len(PRS)}")