import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create the skills/merge-check directory structure ---
skills_dir = workspace / "skills" / "merge-check"
scripts_dir = skills_dir / "scripts"
references_dir = skills_dir / "references"
scripts_dir.mkdir(parents=True, exist_ok=True)
references_dir.mkdir(parents=True, exist_ok=True)

# --- Create the mock merge-check.sh script ---
# This is the critical mock: it returns controlled JSON for a severely problematic PR
pr_json_data = {
    "pr": {
        "number": 412,
        "title": "update stuff",
        "body": "<!-- Please fill out the PR template below -->\n\n## Summary\n\n## Testing\n\n## Checklist\n- [ ] Tests added\n- [ ] Docs updated",
        "author": "nova-contrib-88",
        "state": "open",
        "draft": True,
        "createdAt": "2024-11-15T09:00:00Z",
        "updatedAt": "2024-11-18T14:30:00Z",
        "labels": ["do-not-merge", "needs-rebase"],
        "reviewers": ["@paycore-bot"],
        "baseRefName": "main",
        "headRefName": "nova-contrib-88/update-stuff",
        "url": "https://github.com/paycore-oss/payment-sdk/pull/412",
        "linkedIssues": [],
        "mergedAt": None,
        "closedAt": None
    },
    "files": [
        {"filename": "src/core/transaction.py", "additions": 312, "deletions": 87, "status": "modified"},
        {"filename": "src/core/ledger.py", "additions": 198, "deletions": 45, "status": "modified"},
        {"filename": "src/api/routes/payments.py", "additions": 156, "deletions": 23, "status": "modified"},
        {"filename": "src/api/routes/refunds.py", "additions": 89, "deletions": 12, "status": "modified"},
        {"filename": "src/models/payment_intent.py", "additions": 201, "deletions": 67, "status": "modified"},
        {"filename": "src/models/settlement.py", "additions": 134, "deletions": 28, "status": "added"},
        {"filename": "src/utils/crypto.py", "additions": 78, "deletions": 0, "status": "added"},
        {"filename": "config/payment_limits.yaml", "additions": 34, "deletions": 11, "status": "modified"},
        {"filename": "tests/unit/test_transaction.py", "additions": 45, "deletions": 8, "status": "modified"},
        {"filename": "requirements.txt", "additions": 7, "deletions": 1, "status": "modified"},
        {"filename": "pyproject.toml", "additions": 5, "deletions": 2, "status": "modified"},
        {"filename": "docs/api_reference.md", "additions": 67, "deletions": 3, "status": "modified"},
        {"filename": "CHANGELOG.md", "additions": 12, "deletions": 0, "status": "modified"},
        {"filename": "src/compliance/pci_checks.py", "additions": 88, "deletions": 14, "status": "modified"},
        {"filename": ".github/workflows/ci.yml", "additions": 23, "deletions": 4, "status": "modified"}
    ],
    "diff_stats": {
        "additions": 1449,
        "deletions": 305,
        "changed_files": 15
    },
    "checks": [
        {"name": "ci/unit-tests", "status": "completed", "conclusion": "failure", "startedAt": "2024-11-18T14:31:00Z", "completedAt": "2024-11-18T14:45:00Z"},
        {"name": "ci/integration-tests", "status": "completed", "conclusion": "failure", "startedAt": "2024-11-18T14:31:00Z", "completedAt": "2024-11-18T15:02:00Z"},
        {"name": "ci/lint", "status": "completed", "conclusion": "success", "startedAt": "2024-11-18T14:31:00Z", "completedAt": "2024-11-18T14:38:00Z"},
        {"name": "ci/security-scan", "status": "completed", "conclusion": "failure", "startedAt": "2024-11-18T14:31:00Z", "completedAt": "2024-11-18T14:50:00Z"},
        {"name": "ci/coverage", "status": "completed", "conclusion": "success", "startedAt": "2024-11-18T14:31:00Z", "completedAt": "2024-11-18T14:40:00Z"}
    ],
    "reviews": [
        {
            "author": "dr-elena-vasquez",
            "state": "CHANGES_REQUESTED",
            "submittedAt": "2024-11-16T11:22:00Z",
            "body": "This PR needs significant rework. The transaction atomicity logic in ledger.py is broken and will cause double-charge scenarios. The settlement model is missing idempotency keys. Do not merge until these are fixed."
        },
        {
            "author": "paycore-bot",
            "state": "COMMENTED",
            "submittedAt": "2024-11-15T09:15:00Z",
            "body": "CLA check: Author nova-contrib-88 has NOT signed the Contributor License Agreement. Please sign at https://cla.paycore-oss.org before this PR can be merged."
        }
    ],
    "review_comments": [
        {"path": "src/core/ledger.py", "line": 145, "author": "dr-elena-vasquez", "body": "This is not atomic. You need to wrap lines 143-148 in a transaction block.", "createdAt": "2024-11-16T11:25:00Z"},
        {"path": "src/models/settlement.py", "line": 23, "author": "dr-elena-vasquez", "body": "Missing idempotency_key field — critical for PCI compliance.", "createdAt": "2024-11-16T11:28:00Z"},
        {"path": "src/utils/crypto.py", "line": 7, "author": "dr-elena-vasquez", "body": "Why is MD5 being used here? This is a financial system.", "createdAt": "2024-11-16T11:30:00Z"}
    ],
    "issue_comments": [
        {"author": "nova-contrib-88", "body": "I'll fix these soon.", "createdAt": "2024-11-17T08:00:00Z"},
    ],
    "commits": [
        {"sha": "a1b2c3d", "message": "wip", "author": "nova-contrib-88", "committedAt": "2024-11-15T08:50:00Z"},
        {"sha": "e4f5g6h", "message": "more changes", "author": "nova-contrib-88", "committedAt": "2024-11-15T09:00:00Z"},
        {"sha": "i7j8k9l", "message": "fix", "author": "nova-contrib-88", "committedAt": "2024-11-16T07:30:00Z"},
        {"sha": "m1n2o3p", "message": "stuff", "author": "nova-contrib-88", "committedAt": "2024-11-18T14:25:00Z"}
    ],
    "repo": {
        "owner": "paycore-oss",
        "name": "payment-sdk",
        "language": "Python",
        "defaultBranch": "main",
        "size": 18420,
        "openIssues": 34,
        "stargazers": 2871,
        "forks": 198
    },
    "author_history": {
        "author": "nova-contrib-88",
        "recentPRs": [],
        "mergedCount": 0,
        "closedCount": 0,
        "totalRecent": 0,
        "mergeRate": 0.0,
        "note": "No prior PR history in this repository — first-time contributor"
    },
    "has_codeowners": True,
    "has_contributing": True
}

mock_script_content = f'''#!/usr/bin/env bash
# Mock merge-check script for paycore-oss/payment-sdk#412
echo '{json.dumps(pr_json_data)}'
'''

merge_check_script = scripts_dir / "merge-check.sh"
merge_check_script.write_text(mock_script_content)
os.chmod(merge_check_script, 0o755)

# --- Create the rejection-taxonomy.md reference ---
rejection_taxonomy_content = """# PR Rejection Vector Taxonomy

## Category A: Hard Blockers (Immediate Rejection Signals)
These factors alone are sufficient to predict rejection or non-merge:

### A1. Draft Status
- A PR marked as Draft will NOT be merged in its current state
- Draft = explicit signal that the author considers it unready
- Verdict contribution: -40 points from mergeability score

### A2. Blocking Labels
- Labels like `do-not-merge`, `wip`, `needs-rebase`, `hold`, `blocked` are explicit non-merge signals
- Each blocking label: -15 points

### A3. Failed CI / Automated Gates
- Any failed check run is a hard blocker in most repos
- Security scan failures are especially critical in security-sensitive codebases
- Each failed check: -10 points
- Security/compliance check failure: -20 points additional

### A4. Unaddressed Changes Requested
- An unresolved `CHANGES_REQUESTED` review from any reviewer = strong blocker
- If from a maintainer or CODEOWNER: -35 points
- If from any reviewer: -25 points

### A5. CLA/DCO Not Signed
- If the repo requires CLA/DCO and it's not signed: legal blocker
- -30 points

## Category B: Strong Risk Factors

### B1. PR Size (LOC)
- <400 LOC: +10 points (favorable)
- 400-1000 LOC: -10 points (reviewer fatigue risk)
- >1000 LOC: -25 points (danger zone, high stall/rejection probability)

### B2. Staleness
- <7 days: 0 points
- 7-14 days: -5 points (monitor)
- 15-30 days: -15 points (concern)
- >30 days: -25 points (likely abandoned)

### B3. File Spread
- >10 files across >4 directories: -10 points (scope creep risk)

### B4. First-Time Contributor
- No prior merged PRs in repo: -10 points (higher scrutiny)
- 0% historical merge rate: -15 points

### B5. Missing or Unfollowed PR Template
- Template fields left empty/unfilled: -10 points

### B6. No Linked Issue
- Missing issue reference for non-trivial changes: -5 points

### B7. Poor Commit Hygiene
- WIP/vague commit messages: -5 points

### B8. New Dependencies Introduced
- Any new dependency added: -8 points per new dep (high friction)

## Category C: CODEOWNERS Signals

### C1. CODEOWNERS file exists but owner not assigned as reviewer
- -15 points (required reviewers not looped in)

### C2. CODEOWNERS file exists and owner has CHANGES_REQUESTED
- Multiplies Category A4 penalty by 1.5x

## Score Interpretation
- Start at 100 points
- Apply all applicable deductions
- >80: 🟢 High (likely to merge)
- 40-80: 🟡 Medium (addressable concerns)
- <40: 🔴 Low (significant blockers, unlikely to merge without major rework)
"""

(references_dir / "rejection-taxonomy.md").write_text(rejection_taxonomy_content)

# --- Create distractor files ---

# Fake project source tree
(workspace / "paycore-oss" / "payment-sdk" / "src" / "core").mkdir(parents=True, exist_ok=True)
(workspace / "paycore-oss" / "payment-sdk" / "src" / "api").mkdir(parents=True, exist_ok=True)
(workspace / "paycore-oss" / "payment-sdk" / "tests").mkdir(parents=True, exist_ok=True)

distractor_files = {
    "paycore-oss/payment-sdk/src/core/transaction.py": "# Transaction core logic\nclass Transaction:\n    pass\n",
    "paycore-oss/payment-sdk/src/core/ledger.py": "# Ledger management\nclass Ledger:\n    pass\n",
    "paycore-oss/payment-sdk/src/api/routes.py": "# API routes\n",
    "paycore-oss/payment-sdk/tests/test_core.py": "# Core tests\n",
    "paycore-oss/payment-sdk/pyproject.toml": "[tool.pytest]\naddopts = '-v'\n",
    "paycore-oss/payment-sdk/requirements.txt": "cryptography==41.0.0\nrequests==2.31.0\n",
    "paycore-oss/payment-sdk/CHANGELOG.md": "# Changelog\n\n## v2.1.0\n- Various fixes\n",
    "paycore-oss/payment-sdk/.github/CODEOWNERS": "# Code owners\n* @dr-elena-vasquez\n/src/compliance/ @pci-review-team @dr-elena-vasquez\n",
    "paycore-oss/payment-sdk/CONTRIBUTING.md": "# Contributing\n\nPlease sign the CLA before contributing.\n",
    "paycore-oss/payment-sdk/config/payment_limits.yaml": "max_transaction_usd: 50000\nmin_transaction_usd: 0.01\n",
    "paycore-oss/payment-sdk/.github/pull_request_template.md": "## Summary\n\n## Testing\n\n## Checklist\n- [ ] Tests added\n- [ ] Docs updated\n",
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- Create a fake PR backlog (distractor) ---
pr_backlog_dir = workspace / "pr_backlog"
pr_backlog_dir.mkdir(exist_ok=True)
(pr_backlog_dir / "pr_409_summary.txt").write_text("PR #409: Add webhook retry logic. Merged 2024-11-10. Author: core-team.\n")
(pr_backlog_dir / "pr_410_summary.txt").write_text("PR #410: Fix typo in docs. Merged 2024-11-12. Author: doc-bot.\n")
(pr_backlog_dir / "pr_411_summary.txt").write_text("PR #411: Dependency upgrade. Closed without merge 2024-11-14. Author: renovate-bot.\n")

# --- Create a fake internal review checklist (distractor, incomplete) ---
(workspace / "internal_review_checklist.txt").write_text(
    "Internal Review Checklist\n"
    "=========================\n"
    "1. Does the PR have a linked issue?\n"
    "2. Are all CI checks green?\n"
    "3. Has the author addressed reviewer feedback?\n"
    "4. Is the PR description complete?\n"
    "Note: This checklist is incomplete and does not reflect all merge criteria.\n"
)

# --- Create a scripts directory with other fake scripts (distractors) ---
other_scripts = workspace / "scripts"
other_scripts.mkdir(exist_ok=True)
(other_scripts / "lint-check.sh").write_text("#!/usr/bin/env bash\necho 'Running lint...'\nflake8 src/\n")
(other_scripts / "deploy.sh").write_text("#!/usr/bin/env bash\necho 'Deploying...'\n")

print("Workspace setup complete.")
print(f"Mock merge-check.sh created at: {merge_check_script}")
print(f"Rejection taxonomy created at: {references_dir / 'rejection-taxonomy.md'}")