import sys
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── 1. docs/workflow.md exists ─────────────────────────────────────────────
    workflow_path = ws / "docs" / "workflow.md"
    if not workflow_path.exists():
        checks.append(check("workflow_md_exists", False, "docs/workflow.md was not created"))
        # All subsequent checks will fail; return early with partial scoring
        score = sum(c["passed"] for c in checks) / 10
        return {"passed": False, "score": score, "checks": checks}

    try:
        workflow_content = workflow_path.read_text()
    except Exception as e:
        checks.append(check("workflow_md_readable", False, str(e)))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("workflow_md_exists", True, "docs/workflow.md found"))

    # ── 2. H1 heading contains project name ───────────────────────────────────
    has_project_name = bool(
        re.search(r"#\s+Workflow\s*[—\-–]\s*DataFlux", workflow_content, re.IGNORECASE)
    )
    checks.append(check(
        "heading_contains_project_name",
        has_project_name,
        "Expected '# Workflow — DataFlux' (or similar) as H1" if not has_project_name else "H1 heading correct"
    ))

    # ── 3. TDD Policy section present with "Moderate" label ───────────────────
    has_tdd_section = bool(re.search(r"##\s+TDD Policy", workflow_content, re.IGNORECASE))
    has_moderate = "Moderate" in workflow_content
    tdd_ok = has_tdd_section and has_moderate
    checks.append(check(
        "tdd_policy_moderate",
        tdd_ok,
        f"TDD section present: {has_tdd_section}, 'Moderate' keyword present: {has_moderate}"
    ))

    # ── 4. Test Framework section present AND identifies pytest ───────────────
    has_test_fw_section = bool(re.search(r"##\s+Test Framework", workflow_content, re.IGNORECASE))
    has_pytest = bool(re.search(r"pytest", workflow_content, re.IGNORECASE))
    test_fw_ok = has_test_fw_section and has_pytest
    checks.append(check(
        "test_framework_pytest",
        test_fw_ok,
        f"Test Framework section: {has_test_fw_section}, pytest mentioned: {has_pytest}"
    ))

    # ── 5. Commit Strategy section with "Conventional Commits" ────────────────
    has_commit_section = bool(re.search(r"##\s+Commit Strategy", workflow_content, re.IGNORECASE))
    has_conventional = bool(re.search(r"Conventional Commits", workflow_content, re.IGNORECASE))
    has_commit_format = bool(re.search(r"<type>.*<scope>.*<description>|type.*scope.*description", workflow_content, re.IGNORECASE))
    commit_ok = has_commit_section and has_conventional
    checks.append(check(
        "commit_strategy_conventional",
        commit_ok,
        f"Commit Strategy section: {has_commit_section}, 'Conventional Commits': {has_conventional}"
    ))

    # ── 6. Commit types listed (feat, fix, refactor, etc.) ────────────────────
    required_types = ["feat", "fix", "refactor", "test", "docs", "chore"]
    types_found = [t for t in required_types if t in workflow_content]
    types_ok = len(types_found) >= 5
    checks.append(check(
        "commit_types_listed",
        types_ok,
        f"Found {len(types_found)}/6 required commit types: {types_found}"
    ))

    # ── 7. Verification Checkpoints section present ───────────────────────────
    has_checkpoints = bool(re.search(r"##\s+Verification Checkpoints", workflow_content, re.IGNORECASE))
    has_test_step = bool(re.search(r"run tests?|pytest|all pass", workflow_content, re.IGNORECASE))
    has_lint_step = bool(re.search(r"run linter?|ruff|no errors", workflow_content, re.IGNORECASE))
    checkpoint_ok = has_checkpoints and has_test_step
    checks.append(check(
        "verification_checkpoints",
        checkpoint_ok,
        f"Checkpoints section: {has_checkpoints}, test step: {has_test_step}, lint step: {has_lint_step}"
    ))

    # ── 8. Branch Strategy section with proprietary branch naming ─────────────
    has_branch_section = bool(re.search(r"##\s+Branch Strategy", workflow_content, re.IGNORECASE))
    has_main = bool(re.search(r"`?main`?", workflow_content))
    # Proprietary trap: skill specifies feat/<track-id> NOT feature/<name>
    has_feat_branch = bool(re.search(r"feat/<track-id>|feat/", workflow_content))
    has_fix_branch = bool(re.search(r"fix/<description>|fix/", workflow_content))
    branch_ok = has_branch_section and has_main and (has_feat_branch or has_fix_branch)
    checks.append(check(
        "branch_strategy_correct",
        branch_ok,
        f"Branch section: {has_branch_section}, main: {has_main}, feat branch: {has_feat_branch}, fix branch: {has_fix_branch}"
    ))

    # ── 9. CLAUDE.md updated with workflow.md reference ───────────────────────
    claude_path = ws / "CLAUDE.md"
    claude_updated = False
    claude_detail = "CLAUDE.md could not be read"
    try:
        claude_content = claude_path.read_text()
        # Must reference workflow.md in Key Documents section
        has_key_docs = bool(re.search(r"Key Documents", claude_content, re.IGNORECASE))
        has_workflow_ref = bool(re.search(r"workflow\.md", claude_content, re.IGNORECASE))
        claude_updated = has_key_docs and has_workflow_ref
        claude_detail = f"Key Documents section: {has_key_docs}, workflow.md referenced: {has_workflow_ref}"
    except Exception as e:
        claude_detail = str(e)
    checks.append(check("claude_md_updated_with_workflow_ref", claude_updated, claude_detail))

    # ── 10. Python stack correctly identified (not generic placeholder) ────────
    # The agent must NOT leave {from package manifest} template placeholders
    has_placeholder = bool(re.search(r"\{from|from package manifest|<stack>|\{stack\}", workflow_content, re.IGNORECASE))
    no_placeholder = not has_placeholder
    checks.append(check(
        "no_unfilled_template_placeholders",
        no_placeholder,
        "Template placeholders remain unfilled" if has_placeholder else "No placeholders found"
    ))

    # ── Score ─────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(c["passed"] for c in checks)
    score = round(passed_count / total, 3)

    # Must pass at minimum: exists, TDD moderate, pytest, conventional commits, CLAUDE.md updated
    critical = [
        "workflow_md_exists",
        "tdd_policy_moderate",
        "test_framework_pytest",
        "commit_strategy_conventional",
        "claude_md_updated_with_workflow_ref",
        "branch_strategy_correct",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical
    )

    return {
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))