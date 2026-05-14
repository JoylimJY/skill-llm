#!/usr/bin/env python3
import sys
import json
import os
import subprocess
import re
from pathlib import Path

workspace = sys.argv[1]
checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": str(detail)})
    return passed

def run(cmd, cwd=workspace):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

# ── CHECK 1: Correct git branch ──────────────────────────────────────────────
try:
    rc, stdout, stderr = run(["git", "branch", "--show-current"])
    current_branch = stdout.strip()
    check(
        "Git branch is ralph/task-manager-features",
        current_branch == "ralph/task-manager-features",
        f"Current branch: '{current_branch}'"
    )
except Exception as e:
    check("Git branch is ralph/task-manager-features", False, str(e))

# ── CHECK 2: Commit message format ───────────────────────────────────────────
try:
    rc, stdout, stderr = run(["git", "log", "--oneline", "-5"])
    commit_log = stdout.strip()
    # Must contain exactly: feat: US-001 - Add --version flag to CLI
    expected_commit = "feat: US-001 - Add --version flag to CLI"
    found = expected_commit in commit_log
    check(
        f"Commit message is exactly '{expected_commit}'",
        found,
        f"Recent commits:\n{commit_log}"
    )
except Exception as e:
    check("Commit message format", False, str(e))

# ── CHECK 3: --version flag works correctly ──────────────────────────────────
try:
    rc, stdout, stderr = run(["node", "src/cli.js", "--version"])
    # Read expected version from package.json
    with open(Path(workspace) / "package.json") as f:
        pkg = json.load(f)
    expected_version = pkg["version"]  # "2.4.1"
    output = stdout.strip()
    version_correct = (output == expected_version) and rc == 0
    check(
        f"node src/cli.js --version prints '{expected_version}' and exits 0",
        version_correct,
        f"exit_code={rc} stdout='{output}' stderr='{stderr.strip()}'"
    )
except Exception as e:
    check("--version flag implementation", False, str(e))

# ── CHECK 4: Implementation uses CommonJS (not ES modules) ───────────────────
try:
    cli_path = Path(workspace) / "src" / "cli.js"
    cli_content = cli_path.read_text()
    # Must not use ES module syntax
    has_es_import = bool(re.search(r'^\s*import\s+', cli_content, re.MULTILINE))
    has_es_export = bool(re.search(r'^\s*export\s+(default\s+)?', cli_content, re.MULTILINE))
    # Should use require
    has_require = "require(" in cli_content
    cjs_ok = has_require and not has_es_import and not has_es_export
    check(
        "Implementation uses CommonJS require() not ES module import/export",
        cjs_ok,
        f"has_require={has_require}, has_es_import={has_es_import}, has_es_export={has_es_export}"
    )
except Exception as e:
    check("CommonJS pattern from Codebase Patterns", False, str(e))

# ── CHECK 5: npm test passes ──────────────────────────────────────────────────
try:
    rc, stdout, stderr = run(["npm", "test", "--", "--forceExit"])
    all_output = stdout + stderr
    tests_passed = rc == 0
    check(
        "npm test passes (all tests including --version tests)",
        tests_passed,
        f"exit_code={rc}\n{all_output[-800:]}"
    )
except Exception as e:
    check("npm test passes", False, str(e))

# ── CHECK 6: npm run lint passes ─────────────────────────────────────────────
try:
    rc, stdout, stderr = run(["npm", "run", "lint"])
    lint_passed = rc == 0
    check(
        "npm run lint passes with no errors",
        lint_passed,
        f"exit_code={rc}\nstdout={stdout[-400:]}\nstderr={stderr[-400:]}"
    )
except Exception as e:
    check("npm run lint passes", False, str(e))

# ── CHECK 7: prd.json — only US-001 marked passed ────────────────────────────
try:
    with open(Path(workspace) / "prd.json") as f:
        prd = json.load(f)
    stories = {s["id"]: s for s in prd["userStories"]}

    us001_passed = stories.get("US-001", {}).get("passes") is True
    us002_still_false = stories.get("US-002", {}).get("passes") is False
    us003_still_true = stories.get("US-003", {}).get("passes") is True

    check(
        "prd.json: US-001 passes=true",
        us001_passed,
        f"US-001 passes={stories.get('US-001', {}).get('passes')}"
    )
    check(
        "prd.json: US-002 still passes=false (not touched)",
        us002_still_false,
        f"US-002 passes={stories.get('US-002', {}).get('passes')}"
    )
    check(
        "prd.json: US-003 still passes=true (not touched)",
        us003_still_true,
        f"US-003 passes={stories.get('US-003', {}).get('passes')}"
    )
    check(
        "prd.json: branchName preserved",
        prd.get("branchName") == "ralph/task-manager-features",
        f"branchName={prd.get('branchName')}"
    )
except Exception as e:
    check("prd.json state", False, str(e))

# ── CHECK 8: progress.txt appended (not overwritten) ─────────────────────────
try:
    progress_path = Path(workspace) / "progress.txt"
    progress_content = progress_path.read_text()

    # Must still contain the original Codebase Patterns section
    has_patterns_section = "## Codebase Patterns" in progress_content
    # Must still contain the original US-003 entry
    has_old_entry = "US-003" in progress_content
    # Must contain a new entry for US-001
    has_new_entry = "US-001" in progress_content
    # Must start with the original header (not been overwritten from scratch only)
    has_header = "# Better Ralph Progress" in progress_content

    check(
        "progress.txt still contains original Codebase Patterns section",
        has_patterns_section,
        f"has_patterns={has_patterns_section}"
    )
    check(
        "progress.txt still contains original US-003 entry (not overwritten)",
        has_old_entry,
        f"has_US-003={has_old_entry}"
    )
    check(
        "progress.txt has new US-001 progress block appended",
        has_new_entry,
        f"has_US-001={has_new_entry}"
    )
    check(
        "progress.txt preserves original header",
        has_header,
        f"has_header={has_header}"
    )

    # The new US-001 block must appear AFTER the old US-003 block
    idx_003 = progress_content.find("US-003")
    idx_001_new = progress_content.rfind("US-001")  # last occurrence (appended)
    if idx_003 > 0 and idx_001_new > 0:
        appended_after = idx_001_new > idx_003
    else:
        appended_after = False
    check(
        "progress.txt: US-001 block appears after original US-003 block (appended, not prepended)",
        appended_after,
        f"idx_US-003={idx_003}, idx_US-001_last={idx_001_new}"
    )
except Exception as e:
    check("progress.txt append check", False, str(e))

# ── CHECK 9: Story selection correctness (US-002 NOT implemented) ─────────────
try:
    # US-002 is about --help flag. If agent implemented US-002 instead of US-001, catch it.
    rc, stdout, stderr = run(["node", "src/cli.js", "--help"])
    # --help should NOT be implemented (or if it accidentally works it's a bonus, not penalized)
    # The real check is that US-002 passes=false in prd.json (already checked above)
    # Additional check: the commit should NOT mention US-002
    rc2, log_out, _ = run(["git", "log", "--oneline", "-5"])
    us002_not_committed = "US-002" not in log_out
    check(
        "Agent implemented US-001 (not US-002) — no US-002 commit present",
        us002_not_committed,
        f"git log: {log_out}"
    )
except Exception as e:
    # If --help crashes, that's fine — we only care about US-002 not being committed
    try:
        rc2, log_out, _ = run(["git", "log", "--oneline", "-5"])
        us002_not_committed = "US-002" not in log_out
        check(
            "Agent implemented US-001 (not US-002) — no US-002 commit present",
            us002_not_committed,
            f"git log: {log_out}"
        )
    except Exception as e2:
        check("Story selection: US-001 chosen over US-002", False, str(e2))

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = all(c["passed"] for c in checks)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))