#!/usr/bin/env python3
import sys
import json
import subprocess
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ── CHECK 1: Correct story selected (US-002, not US-003 or US-004) ────────────
# We verify this via git log and prd.json state

# Check git log for commit message
try:
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=workspace, capture_output=True, text=True, check=True
    )
    log = result.stdout.strip()
    
    # Must have a commit for US-002
    has_us002_commit = bool(re.search(r'feat: US-002 - Remove placeholder TODO comment from cli\.ts', log))
    # Must NOT have commits for US-003 or US-004 (one story per iteration)
    has_us003_commit = bool(re.search(r'feat: US-003', log))
    has_us004_commit = bool(re.search(r'feat: US-004', log))
    
    add_check(
        "Correct story selected (US-002 by priority=2, skipping passes=true US-001)",
        has_us002_commit,
        f"Git log:\n{log}\nFound US-002 commit: {has_us002_commit}"
    )
    add_check(
        "One story per iteration (no US-003 or US-004 commits)",
        not has_us003_commit and not has_us004_commit,
        f"US-003 commit found: {has_us003_commit}, US-004 commit found: {has_us004_commit}",
        weight=1.0
    )
except Exception as e:
    add_check("Git log readable", False, f"Exception: {e}")
    add_check("One story per iteration", False, "Could not read git log")

# ── CHECK 2: Correct commit message format ────────────────────────────────────
try:
    result = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=workspace, capture_output=True, text=True, check=True
    )
    commit_subjects = result.stdout.strip().split("\n")
    
    expected_msg = "feat: US-002 - Remove placeholder TODO comment from cli.ts"
    exact_match = expected_msg in commit_subjects
    
    add_check(
        "Commit message format: 'feat: [ID] - [Title]' exactly",
        exact_match,
        f"Expected: '{expected_msg}'\nActual commit subjects: {commit_subjects[:5]}"
    )
except Exception as e:
    add_check("Commit message format", False, f"Exception: {e}")

# ── CHECK 3: Correct git branch ───────────────────────────────────────────────
try:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=workspace, capture_output=True, text=True, check=True
    )
    current_branch = result.stdout.strip()
    expected_branch = "ralph/filter-feature"
    
    add_check(
        f"Git branch is '{expected_branch}' (from prd.json.branchName)",
        current_branch == expected_branch,
        f"Expected branch: '{expected_branch}', Actual: '{current_branch}'"
    )
except Exception as e:
    add_check("Git branch check", False, f"Exception: {e}")

# ── CHECK 4: TODO comment removed from src/cli.ts ─────────────────────────────
try:
    cli_ts = (workspace / "src" / "cli.ts").read_text()
    
    todo_removed = "// TODO:" not in cli_ts
    add_check(
        "TODO comment removed from src/cli.ts",
        todo_removed,
        f"'// TODO:' found in cli.ts: {not todo_removed}\nFile snippet:\n{cli_ts[:500]}"
    )
    
    # Original content still intact (listTasks function preserved)
    has_list_tasks = "export function listTasks" in cli_ts or "function listTasks" in cli_ts
    add_check(
        "listTasks function preserved in cli.ts",
        has_list_tasks,
        f"listTasks present: {has_list_tasks}"
    )
except Exception as e:
    add_check("cli.ts readable", False, f"Exception: {e}")
    add_check("listTasks preserved", False, "Could not read cli.ts")

# ── CHECK 5: Quality checks would pass on committed code ──────────────────────
try:
    lint_result = subprocess.run(
        ["node", "tools/lint_check.js"],
        cwd=workspace, capture_output=True, text=True
    )
    lint_passed = lint_result.returncode == 0
    add_check(
        "Lint check passes on final code",
        lint_passed,
        f"Return code: {lint_result.returncode}\nStdout: {lint_result.stdout}\nStderr: {lint_result.stderr}"
    )
except Exception as e:
    add_check("Lint check", False, f"Exception: {e}")

try:
    typecheck_result = subprocess.run(
        ["node", "tools/type_check.js"],
        cwd=workspace, capture_output=True, text=True
    )
    typecheck_passed = typecheck_result.returncode == 0
    add_check(
        "Typecheck passes on final code",
        typecheck_passed,
        f"Return code: {typecheck_result.returncode}\nStdout: {typecheck_result.stdout}\nStderr: {typecheck_result.stderr}"
    )
except Exception as e:
    add_check("Typecheck", False, f"Exception: {e}")

# ── CHECK 6: prd.json correctly updated ──────────────────────────────────────
try:
    prd = json.loads((workspace / "prd.json").read_text())
    
    stories_by_id = {s["id"]: s for s in prd["userStories"]}
    
    # US-002 must be passes=true (boolean, not string)
    us002 = stories_by_id.get("US-002", {})
    us002_passes = us002.get("passes")
    us002_correct = us002_passes is True  # strict boolean check
    
    add_check(
        "US-002 passes set to true (boolean) in prd.json",
        us002_correct,
        f"US-002.passes = {repr(us002_passes)} (type: {type(us002_passes).__name__})"
    )
    
    # US-001 must still be passes=true
    us001 = stories_by_id.get("US-001", {})
    us001_intact = us001.get("passes") is True
    
    # US-003 and US-004 must still be passes=false
    us003 = stories_by_id.get("US-003", {})
    us004 = stories_by_id.get("US-004", {})
    others_unchanged = (us003.get("passes") is False) and (us004.get("passes") is False)
    
    add_check(
        "Other stories' passes fields unchanged in prd.json",
        us001_intact and others_unchanged,
        f"US-001.passes={repr(us001.get('passes'))}, US-003.passes={repr(us003.get('passes'))}, US-004.passes={repr(us004.get('passes'))}"
    )
    
    # prd.json structure preserved (project, branchName, description)
    structure_ok = (
        "project" in prd and
        "branchName" in prd and
        "description" in prd and
        prd["branchName"] == "ralph/filter-feature"
    )
    add_check(
        "prd.json structure fully preserved",
        structure_ok,
        f"project: {'project' in prd}, branchName: {prd.get('branchName')}, description: {'description' in prd}"
    )

except json.JSONDecodeError as e:
    add_check("prd.json valid JSON", False, f"JSON parse error: {e}")
    add_check("Other stories unchanged", False, "Could not parse prd.json")
    add_check("prd.json structure preserved", False, "Could not parse prd.json")
except Exception as e:
    add_check("prd.json readable", False, f"Exception: {e}")
    add_check("Other stories unchanged", False, f"Exception: {e}")
    add_check("prd.json structure preserved", False, f"Exception: {e}")

# ── CHECK 7: progress.txt appended (not overwritten) ─────────────────────────
try:
    progress = (workspace / "progress.txt").read_text()
    
    # Original content must still be present
    has_original_header = "# Better Ralph Progress" in progress
    has_codebase_patterns = "## Codebase Patterns" in progress
    has_us001_block = "## 2024-01-15T10:00:00 - US-001" in progress
    
    add_check(
        "progress.txt original content preserved (not overwritten)",
        has_original_header and has_codebase_patterns and has_us001_block,
        f"Header present: {has_original_header}, Codebase Patterns present: {has_codebase_patterns}, US-001 block present: {has_us001_block}"
    )
    
    # New US-002 block appended
    has_us002_block = "US-002" in progress
    
    # Check the new block comes AFTER the original US-001 block
    us001_pos = progress.find("## 2024-01-15T10:00:00 - US-001")
    us002_pos = progress.find("US-002", us001_pos + 1) if us001_pos >= 0 else -1
    appended_correctly = us001_pos >= 0 and us002_pos > us001_pos
    
    add_check(
        "progress.txt has US-002 block appended after existing content",
        has_us002_block and appended_correctly,
        f"US-002 block found: {has_us002_block}, Appended after US-001: {appended_correctly}\nFull progress.txt length: {len(progress)} chars"
    )
    
    # New block must have the --- separator
    # Find the US-002 section
    us002_section_start = progress.find("US-002", us001_pos + 1 if us001_pos >= 0 else 0)
    if us002_section_start >= 0:
        us002_section = progress[us002_section_start:]
        has_separator = "---" in us002_section
    else:
        has_separator = False
    
    add_check(
        "progress.txt new block has '---' separator",
        has_separator,
        f"'---' found in US-002 section: {has_separator}"
    )

except Exception as e:
    add_check("progress.txt readable", False, f"Exception: {e}")
    add_check("progress.txt original preserved", False, f"Exception: {e}")
    add_check("progress.txt new block format", False, f"Exception: {e}")

# ── Final score ───────────────────────────────────────────────────────────────
final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))