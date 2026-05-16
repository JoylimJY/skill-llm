#!/usr/bin/env python3
"""
Generate the sandbox workspace for the fork-manager skill evaluation.
Creates a realistic scientific computing library fork scenario.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("/workspace")

def run(cmd, cwd=None, check=True, env=None):
    import os as _os
    e = _os.environ.copy()
    e["GIT_AUTHOR_NAME"] = "Test Author"
    e["GIT_AUTHOR_EMAIL"] = "author@test.local"
    e["GIT_COMMITTER_NAME"] = "Test Committer"
    e["GIT_COMMITTER_EMAIL"] = "committer@test.local"
    if env:
        e.update(env)
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=e)
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Command failed: {cmd}")
    return result

# ─────────────────────────────────────────────
# 1. Create realistic distractor directory tree
# ─────────────────────────────────────────────

dirs = [
    "projects/website",
    "projects/internal-tools",
    "notes/meetings/2026-Q1",
    "notes/meetings/2026-Q2",
    "scratch/experiments",
    "scratch/benchmarks",
    "dotfiles/.config/git",
    "dotfiles/.config/tmux",
    "archive/old-patches/2025",
    "skills/github",
    "skills/pr-review",
    "skills/issue-prioritizer",
    "skills/fork-manager/repos/numcore",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "projects/website/README.md": "# Company Website\nDeploy with `npm run build`.",
    "projects/website/package.json": json.dumps({"name": "website", "version": "1.0.0"}),
    "projects/internal-tools/deploy.sh": "#!/bin/bash\necho 'deploying...'",
    "notes/meetings/2026-Q1/sprint-review.md": "## Sprint Review\n- Delivered feature X\n- PR backlog growing",
    "notes/meetings/2026-Q2/planning.md": "## Q2 Planning\n- Focus on upstream sync automation",
    "scratch/experiments/test_solver.py": "import numpy as np\n# prototype sparse solver\n",
    "scratch/benchmarks/bench_results.csv": "method,time_ms\nsparse,12.3\ndense,45.1\n",
    "dotfiles/.config/git/config": "[alias]\n  lg = log --oneline --graph\n",
    "dotfiles/.config/tmux/tmux.conf": "set -g prefix C-a\n",
    "archive/old-patches/2025/dropped_fix.patch": "diff --git a/solver.py b/solver.py\n-old line\n+new line\n",
    "archive/old-patches/2025/notes.txt": "These patches were superseded in the 2025 refactor.",
    "skills/github/SKILL.md": "# GitHub Skill\nFor general GitHub queries, issues, PRs on any repo.\n",
    "skills/pr-review/SKILL.md": "# PR Review Skill\nFor reviewing code changes before publishing.\n",
    "skills/issue-prioritizer/SKILL.md": "# Issue Prioritizer\nFor triaging and ranking issues.\n",
}

for fpath, content in distractor_files.items():
    fp = WORKSPACE / fpath
    fp.write_text(content)

# ─────────────────────────────────────────────
# 2. Create the SKILL.md for fork-manager
# ─────────────────────────────────────────────

# Read from the actual skill location or create a minimal pointer
# The SKILL.md should already exist; we just ensure the repos/numcore dir is set up
# The test will place the real SKILL.md content in skills/fork-manager/SKILL.md
# For now, write the path reference

skill_dir = WORKSPACE / "skills/fork-manager"

# ─────────────────────────────────────────────
# 3. Create upstream and origin bare git repos
# ─────────────────────────────────────────────

repos_dir = WORKSPACE / "git-server"
repos_dir.mkdir(parents=True, exist_ok=True)

upstream_bare = repos_dir / "numcore-upstream.git"
origin_bare = repos_dir / "numcore-origin.git"

# ── 3a. Create upstream bare repo with base content ──
run(f"git init --bare {upstream_bare}")

# Create a temp dir to bootstrap upstream
tmp_upstream = WORKSPACE / "_tmp_upstream"
tmp_upstream.mkdir()
run("git init", cwd=tmp_upstream)
run(f"git remote add origin {upstream_bare}", cwd=tmp_upstream)

# Create realistic source files
(tmp_upstream / "solver").mkdir()
(tmp_upstream / "utils").mkdir()
(tmp_upstream / "tests").mkdir()

(tmp_upstream / "solver" / "sparse.py").write_text(
    "\"\"\"Sparse solver module.\"\"\"\n\n"
    "def solve_sparse(matrix, vector):\n"
    "    \"\"\"Solve Ax = b for sparse A.\"\"\"\n"
    "    # Basic conjugate gradient implementation\n"
    "    n = len(vector)\n"
    "    x = [0.0] * n\n"
    "    r = vector[:]\n"
    "    return x\n"
)
(tmp_upstream / "solver" / "__init__.py").write_text("from .sparse import solve_sparse\n")
(tmp_upstream / "utils" / "precision.py").write_text(
    "\"\"\"Numerical precision utilities.\"\"\"\n\n"
    "EPSILON = 1e-10\n\n"
    "def is_close(a, b, tol=EPSILON):\n"
    "    return abs(a - b) < tol\n"
)
(tmp_upstream / "utils" / "__init__.py").write_text("from .precision import is_close\n")
(tmp_upstream / "tests" / "test_sparse.py").write_text(
    "from solver import solve_sparse\n\n"
    "def test_identity():\n"
    "    result = solve_sparse([[1,0],[0,1]], [1,2])\n"
    "    assert result == [1, 2] or result == [0.0, 0.0]\n"
)
(tmp_upstream / "setup.py").write_text(
    "from setuptools import setup\nsetup(name='numcore', version='0.1.0')\n"
)
(tmp_upstream / "CHANGELOG.md").write_text(
    "# Changelog\n\n## 0.1.0\n- Initial release\n"
)

run("git add -A", cwd=tmp_upstream)
run('git commit -m "Initial commit: sparse solver base implementation"', cwd=tmp_upstream)
run("git push origin main", cwd=tmp_upstream)

# Get the base commit sha
base_sha_result = run("git rev-parse HEAD", cwd=tmp_upstream)
BASE_SHA = base_sha_result.stdout.strip()

# ── 3b. Create origin bare repo (fork) = clone of upstream at base ──
run(f"git clone --bare {upstream_bare} {origin_bare}")

# ── 3c. Create working directory (fork local clone) ──
work_dir = WORKSPACE / "repos" / "numcore-local"
work_dir.mkdir(parents=True, exist_ok=True)
run(f"git clone {origin_bare} {work_dir}")
run(f"git remote add upstream {upstream_bare}", cwd=work_dir)
run("git fetch upstream", cwd=work_dir)
run("git fetch origin", cwd=work_dir)

# ─────────────────────────────────────────────
# 4. Create PR branches in the working dir + push to origin
# ─────────────────────────────────────────────

# PR #101: fix/sparse-solver — open, clean (rebases onto new upstream fine)
run("git checkout -b fix/sparse-solver", cwd=work_dir)
(work_dir / "solver" / "sparse.py").write_text(
    "\"\"\"Sparse solver module.\"\"\"\n\n"
    "def solve_sparse(matrix, vector):\n"
    "    \"\"\"Solve Ax = b for sparse A using conjugate gradient.\"\"\"\n"
    "    n = len(vector)\n"
    "    x = [0.0] * n\n"
    "    r = vector[:]\n"
    "    p = r[:]\n"
    "    rs_old = sum(ri * ri for ri in r)\n"
    "    if rs_old < 1e-14:\n"
    "        return x\n"
    "    return x\n"
)
run("git add -A", cwd=work_dir)
run('git commit -m "fix(sparse): improve conjugate gradient convergence check"', cwd=work_dir)
run("git push origin fix/sparse-solver", cwd=work_dir)
pr101_sha = run("git rev-parse HEAD", cwd=work_dir).stdout.strip()

# PR #102: feat/gpu-backend — will be "closed" per mock gh, agent must keep as local patch
run("git checkout main", cwd=work_dir)
run("git checkout -b feat/gpu-backend", cwd=work_dir)
(work_dir / "solver" / "gpu.py").write_text(
    "\"\"\"GPU-accelerated solver backend.\"\"\"\n\n"
    "def solve_gpu(matrix, vector):\n"
    "    \"\"\"GPU solver stub.\"\"\"\n"
    "    raise NotImplementedError('GPU backend not yet implemented')\n"
)
run("git add -A", cwd=work_dir)
run('git commit -m "feat(gpu): add GPU solver backend stub"', cwd=work_dir)
run("git push origin feat/gpu-backend", cwd=work_dir)
pr102_sha = run("git rev-parse HEAD", cwd=work_dir).stdout.strip()

# PR #103: fix/memory-leak — was in droppedPatches, mock gh says it's now OPEN (reopened)
run("git checkout main", cwd=work_dir)
run("git checkout -b fix/memory-leak", cwd=work_dir)
(work_dir / "utils" / "precision.py").write_text(
    "\"\"\"Numerical precision utilities.\"\"\"\n\n"
    "EPSILON = 1e-10\n\n"
    "def is_close(a, b, tol=EPSILON):\n"
    "    return abs(a - b) < tol\n\n"
    "def cleanup_buffers(buf_list):\n"
    "    \"\"\"Explicitly release buffer memory.\"\"\"\n"
    "    for buf in buf_list:\n"
    "        del buf\n"
    "    buf_list.clear()\n"
)
run("git add -A", cwd=work_dir)
run('git commit -m "fix(memory): add explicit buffer cleanup to prevent leaks"', cwd=work_dir)
run("git push origin fix/memory-leak", cwd=work_dir)
pr103_sha = run("git rev-parse HEAD", cwd=work_dir).stdout.strip()

# local/precision-fix — existing local patch (already in config)
run("git checkout main", cwd=work_dir)
run("git checkout -b local/precision-fix", cwd=work_dir)
(work_dir / "utils" / "precision.py").write_text(
    "\"\"\"Numerical precision utilities.\"\"\"\n\n"
    "EPSILON = 1e-12  # increased precision for research workloads\n\n"
    "def is_close(a, b, tol=EPSILON):\n"
    "    return abs(a - b) < tol\n"
)
run("git add -A", cwd=work_dir)
run('git commit -m "local: tighten epsilon for research-grade precision"', cwd=work_dir)
run("git push origin local/precision-fix", cwd=work_dir)

# ─────────────────────────────────────────────
# 5. Add 2 new commits to upstream (fork is now behind)
# ─────────────────────────────────────────────
run("git checkout main", cwd=tmp_upstream)

(tmp_upstream / "solver" / "sparse.py").write_text(
    "\"\"\"Sparse solver module — refactored.\"\"\"\n\n"
    "DEFAULT_TOL = 1e-8\n\n"
    "def solve_sparse(matrix, vector, tol=DEFAULT_TOL):\n"
    "    \"\"\"Solve Ax = b for sparse A.\"\"\"\n"
    "    n = len(vector)\n"
    "    x = [0.0] * n\n"
    "    r = vector[:]\n"
    "    return x\n"
)
run("git add -A", cwd=tmp_upstream)
run('git commit -m "refactor(sparse): add configurable tolerance parameter"', cwd=tmp_upstream)
run("git push origin main", cwd=tmp_upstream)

(tmp_upstream / "CHANGELOG.md").write_text(
    "# Changelog\n\n## 0.2.0\n- Configurable tolerance in sparse solver\n\n## 0.1.0\n- Initial release\n"
)
run("git add -A", cwd=tmp_upstream)
run('git commit -m "docs: update CHANGELOG for 0.2.0"', cwd=tmp_upstream)
run("git push origin main", cwd=tmp_upstream)

new_upstream_sha = run("git rev-parse HEAD", cwd=tmp_upstream).stdout.strip()

# ─────────────────────────────────────────────
# 6. Write config.json for numcore
# ─────────────────────────────────────────────

config = {
    "repo": "science-labs/numcore",
    "fork": "research-team/numcore",
    "localPath": str(work_dir),
    "mainBranch": "main",
    "productionBranch": "main-with-all-prs",
    "upstreamRemote": "upstream",
    "forkRemote": "origin",
    "autoResolveConflicts": False,
    "openPRs": [101, 102],
    "prBranches": {
        "101": "fix/sparse-solver",
        "102": "feat/gpu-backend"
    },
    "localPatches": {
        "local/precision-fix": {
            "description": "Tighten EPSILON to 1e-12 for research-grade precision requirements",
            "originalPR": None,
            "closedReason": "wontfix",
            "keepReason": "Upstream uses 1e-10 which is insufficient for our simulations",
            "addedAt": "2026-01-15T00:00:00Z",
            "reviewDate": "2026-04-15T00:00:00Z"
        }
    },
    "lastSync": "2026-01-20T10:00:00Z",
    "notes": {
        "mergedUpstream": {},
        "closedWithoutMerge": {},
        "droppedPatches": {
            "103": {
                "branch": "fix/memory-leak",
                "title": "fix(memory): add explicit buffer cleanup to prevent leaks",
                "droppedAt": "2026-01-10T00:00:00Z",
                "reason": "Upstream said they would handle it differently"
            }
        }
    }
}

config_path = skill_dir / "repos" / "numcore" / "config.json"
config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(config, indent=2))

# ─────────────────────────────────────────────
# 7. Write gh mock data file (used by mock gh script)
# ─────────────────────────────────────────────

gh_mock_data = {
    "open_prs_by_author": [
        {
            "number": 101,
            "title": "fix(sparse): improve conjugate gradient convergence check",
            "headRefName": "fix/sparse-solver",
            "state": "OPEN"
        },
        {
            "number": 103,
            "title": "fix(memory): add explicit buffer cleanup to prevent leaks",
            "headRefName": "fix/memory-leak",
            "state": "OPEN"
        }
    ],
    "pr_views": {
        "101": {
            "number": 101,
            "title": "fix(sparse): improve conjugate gradient convergence check",
            "state": "OPEN",
            "mergedAt": None,
            "closedAt": None,
            "headRefName": "fix/sparse-solver",
            "comments": [],
            "labels": [],
            "files": [{"path": "solver/sparse.py"}]
        },
        "102": {
            "number": 102,
            "title": "feat(gpu): add GPU solver backend stub",
            "state": "CLOSED",
            "mergedAt": None,
            "closedAt": "2026-02-01T12:00:00Z",
            "headRefName": "feat/gpu-backend",
            "comments": [
                {"body": "We don't plan to support GPU backends in this library. Closing as wontfix."}
            ],
            "labels": ["wontfix"],
            "files": [{"path": "solver/gpu.py"}]
        },
        "103": {
            "number": 103,
            "title": "fix(memory): add explicit buffer cleanup to prevent leaks",
            "state": "OPEN",
            "mergedAt": None,
            "closedAt": None,
            "headRefName": "fix/memory-leak",
            "comments": [],
            "labels": [],
            "files": [{"path": "utils/precision.py"}]
        }
    },
    "merged_prs": [],
    "open_prs_upstream": []
}

mock_data_path = WORKSPACE / "skills" / "fork-manager" / "gh_mock_data.json"
mock_data_path.write_text(json.dumps(gh_mock_data, indent=2))

# ─────────────────────────────────────────────
# 8. Write mock gh script
# ─────────────────────────────────────────────

mock_gh_script = r'''#!/usr/bin/env python3
"""Mock gh (GitHub CLI) for fork-manager testing."""

import sys
import json
import os
import re

MOCK_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gh_mock_data.json"
)

def load_data():
    with open(MOCK_DATA_PATH) as f:
        return json.load(f)

def main():
    args = sys.argv[1:]
    data = load_data()

    # gh pr list ...
    if len(args) >= 2 and args[0] == "pr" and args[1] == "list":
        state = "open"
        author = None
        repo = None
        jq_filter = None
        limit = 30
        i = 2
        while i < len(args):
            if args[i] == "--state" and i+1 < len(args):
                state = args[i+1].lower()
                i += 2
            elif args[i] == "--author" and i+1 < len(args):
                author = args[i+1]
                i += 2
            elif args[i] == "--repo" and i+1 < len(args):
                repo = args[i+1]
                i += 2
            elif args[i] == "--json":
                i += 2  # skip field list
            elif args[i] == "--jq" and i+1 < len(args):
                jq_filter = args[i+1]
                i += 2
            elif args[i] == "--limit" and i+1 < len(args):
                limit = int(args[i+1])
                i += 2
            else:
                i += 1

        if state == "open" and author in ("@me", "research-team"):
            result = data["open_prs_by_author"]
        elif state == "merged":
            result = data["merged_prs"]
        elif state == "open":
            result = data["open_prs_upstream"]
        else:
            result = []

        print(json.dumps(result))
        return

    # gh pr view <number> ...
    if len(args) >= 3 and args[0] == "pr" and args[1] == "view":
        pr_num = args[2]
        # strip flags after number
        view_data = data["pr_views"].get(str(pr_num), {})
        print(json.dumps(view_data))
        return

    # gh pr view <number> with flags before number
    if len(args) >= 2 and args[0] == "pr" and args[1] == "view":
        print(json.dumps({}))
        return

    # Fallback: empty
    print(json.dumps([]))

if __name__ == "__main__":
    main()
'''

mock_gh_path = WORKSPACE / "skills" / "fork-manager" / "gh"
mock_gh_path.write_text(mock_gh_script)

# ─────────────────────────────────────────────
# 9. Write the SKILL.md into the skill dir
# ─────────────────────────────────────────────
# The skill.md is provided by the task environment; we create a reference marker
skill_md_path = skill_dir / "SKILL.md"
if not skill_md_path.exists():
    skill_md_path.write_text("# Fork Manager Skill\n<!-- Skill content will be injected by setup_script -->\n")

# ─────────────────────────────────────────────
# 10. Cleanup tmp
# ─────────────────────────────────────────────
shutil.rmtree(tmp_upstream, ignore_errors=True)

# ─────────────────────────────────────────────
# 11. Print summary for debugging
# ─────────────────────────────────────────────
print("=== Workspace generated ===")
print(f"Upstream bare: {upstream_bare}")
print(f"Origin bare:   {origin_bare}")
print(f"Working dir:   {work_dir}")
print(f"Upstream SHA:  {new_upstream_sha}")
print(f"Config:        {config_path}")
print(f"Mock gh data:  {mock_data_path}")
print(f"Skill dir:     {skill_dir}")

# Verify remotes in working dir
result = subprocess.run("git remote -v", shell=True, cwd=work_dir, capture_output=True, text=True)
print("Remotes in working dir:")
print(result.stdout)