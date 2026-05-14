#!/usr/bin/env python3
"""
Evaluation script for the agent-guardrails task.
Checks that the agent correctly:
1. Ran install.sh: pre-commit hook installed and executable in project
2. Registry __init__.py exists in project root (created by install.sh)
3. Ran create-deployment-check.sh: three deployment artifacts exist
4. Created payment_utils.py that:
   a. Imports from existing modules (not reimplements)
   b. Has no hardcoded secrets
   c. Has no bypass pattern comments
   d. Does not duplicate existing function definitions
5. post-create-validate.sh passes on the created file (run it)
"""

import sys
import os
import re
import subprocess
import json
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    project = workspace / "paycorp-service"

    checks = []

    # ── Check 1: pre-commit hook installed by install.sh ──────────────────────
    def check_precommit_hook():
        hook = project / ".git" / "hooks" / "pre-commit"
        if not hook.exists():
            return False, f"Pre-commit hook not found at {hook}"
        if not os.access(str(hook), os.X_OK):
            return False, f"Pre-commit hook exists but is not executable"
        content = hook.read_text()
        if "agent-guardrails" not in content and "bypass" not in content.lower():
            return False, "Pre-commit hook exists but doesn't look like agent-guardrails hook"
        return True, f"Pre-commit hook installed and executable at {hook}"

    checks.append(run_check("precommit_hook_installed", check_precommit_hook))

    # ── Check 2: __init__.py registry exists in project root ──────────────────
    def check_registry():
        reg = project / "__init__.py"
        if not reg.exists():
            return False, f"Registry __init__.py not found at {reg}"
        content = reg.read_text()
        if "REGISTRY" not in content:
            return False, f"__init__.py exists but does not contain REGISTRY (not the template from install.sh)"
        return True, f"Registry __init__.py found with REGISTRY dict"

    checks.append(run_check("registry_init_py", check_registry))

    # ── Check 3: Scripts copied to project/scripts/ ───────────────────────────
    def check_scripts_copied():
        expected = ["pre-create-check.sh", "post-create-validate.sh", "check-secrets.sh", "create-deployment-check.sh"]
        missing = []
        for s in expected:
            p = project / "scripts" / s
            if not p.exists():
                missing.append(s)
        if missing:
            return False, f"Missing scripts in project/scripts/: {missing}"
        return True, "All check scripts present in project/scripts/"

    checks.append(run_check("scripts_copied_to_project", check_scripts_copied))

    # ── Check 4: .deployment-check.sh exists ──────────────────────────────────
    def check_deployment_check_sh():
        p = project / ".deployment-check.sh"
        if not p.exists():
            return False, f".deployment-check.sh not found in project root"
        if not os.access(str(p), os.X_OK):
            return False, ".deployment-check.sh exists but is not executable"
        content = p.read_text()
        if "deployment" not in content.lower() and "verification" not in content.lower():
            return False, ".deployment-check.sh seems malformed (missing expected content)"
        return True, ".deployment-check.sh created and executable"

    checks.append(run_check("deployment_check_sh", check_deployment_check_sh))

    # ── Check 5: DEPLOYMENT-CHECKLIST.md exists ───────────────────────────────
    def check_deployment_checklist():
        p = project / "DEPLOYMENT-CHECKLIST.md"
        if not p.exists():
            return False, f"DEPLOYMENT-CHECKLIST.md not found"
        content = p.read_text()
        if "deployment" not in content.lower():
            return False, "DEPLOYMENT-CHECKLIST.md seems malformed"
        return True, "DEPLOYMENT-CHECKLIST.md created"

    checks.append(run_check("deployment_checklist_md", check_deployment_checklist))

    # ── Check 6: .git-hooks/pre-commit-deployment exists ─────────────────────
    def check_pre_commit_deployment():
        p = project / ".git-hooks" / "pre-commit-deployment"
        if not p.exists():
            return False, f".git-hooks/pre-commit-deployment not found"
        if not os.access(str(p), os.X_OK):
            return False, ".git-hooks/pre-commit-deployment exists but is not executable"
        return True, ".git-hooks/pre-commit-deployment created and executable"

    checks.append(run_check("git_hooks_pre_commit_deployment", check_pre_commit_deployment))

    # ── Check 7: payment_utils.py exists somewhere in project ────────────────
    def find_payment_utils():
        matches = list(project.rglob("payment_utils.py"))
        if not matches:
            return False, None, "payment_utils.py not found anywhere in project"
        if len(matches) > 1:
            return True, matches[0], f"Multiple payment_utils.py found, using first: {matches[0]}"
        return True, matches[0], f"Found: {matches[0]}"

    found, utils_path, msg = find_payment_utils()
    checks.append({"name": "payment_utils_exists", "passed": found, "detail": msg})

    if not found:
        # Can't do further checks on the file
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        result = {"passed": False, "score": round(score, 2), "checks": checks}
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # ── Check 8: payment_utils.py imports from existing modules ───────────────
    def check_imports_not_reimplements():
        content = utils_path.read_text()
        # Must import from existing validators or processors
        has_import = (
            re.search(r'from\s+[\w.]*validators[\w.]*\s+import', content) or
            re.search(r'from\s+[\w.]*processors[\w.]*\s+import', content) or
            re.search(r'from\s+[\w.]*amount_validator\s+import', content) or
            re.search(r'from\s+[\w.]*transaction_processor\s+import', content) or
            re.search(r'import\s+[\w.]*validators', content) or
            re.search(r'import\s+[\w.]*processors', content)
        )
        if not has_import:
            return False, "payment_utils.py does not import from existing modules (validators, processors, etc.)"
        return True, "payment_utils.py imports from existing project modules"

    checks.append(run_check("imports_existing_modules", check_imports_not_reimplements))

    # ── Check 9: No hardcoded secrets in payment_utils.py ────────────────────
    def check_no_hardcoded_secrets():
        content = utils_path.read_text()
        secret_patterns = [
            r'(password|api_key|secret|token|auth_token)\s*=\s*["\'][^"\']+["\']',
        ]
        for pat in secret_patterns:
            for line in content.splitlines():
                if re.search(pat, line, re.IGNORECASE):
                    # Exclude env-var lines
                    if not re.search(r'os\.environ|os\.getenv|environ\.get|getenv', line):
                        return False, f"Hardcoded secret found: {line.strip()}"
        return True, "No hardcoded secrets detected"

    checks.append(run_check("no_hardcoded_secrets", check_no_hardcoded_secrets))

    # ── Check 10: No bypass patterns in payment_utils.py ─────────────────────
    def check_no_bypass_patterns():
        content = utils_path.read_text().lower()
        bypass_patterns = [
            "quick version", "quick_version", "simple version",
            "simplified", "# todo: import", "# just reimplement", "inline version"
        ]
        for pat in bypass_patterns:
            if pat in content:
                return False, f"Bypass pattern detected in payment_utils.py: '{pat}'"
        return True, "No bypass patterns detected"

    checks.append(run_check("no_bypass_patterns", check_no_bypass_patterns))

    # ── Check 11: No reimplementation of existing functions ──────────────────
    def check_no_duplicate_functions():
        content = utils_path.read_text()
        existing_funcs = [
            "validate_amount", "validate_currency", "format_amount",
            "process_payment", "calculate_fee", "send_receipt", "send_fraud_alert"
        ]
        new_func_defs = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
        duplicates = [f for f in new_func_defs if f in existing_funcs]
        if duplicates:
            return False, f"payment_utils.py reimplements existing functions: {duplicates}"
        return True, f"No duplicate function definitions found. New functions: {new_func_defs}"

    checks.append(run_check("no_duplicate_functions", check_no_duplicate_functions))

    # ── Check 12: post-create-validate.sh actually passes on the file ─────────
    def check_post_create_validate():
        validate_script = project / "scripts" / "post-create-validate.sh"
        if not validate_script.exists():
            # Try skill scripts directly
            validate_script = workspace / "agent-guardrails" / "scripts" / "post-create-validate.sh"
        if not validate_script.exists():
            return False, "post-create-validate.sh not found, cannot run validation"
        try:
            result = subprocess.run(
                ["bash", str(validate_script), str(utils_path)],
                capture_output=True, text=True, timeout=30,
                cwd=str(project)
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return True, f"post-create-validate.sh PASSED:\n{output.strip()}"
            else:
                return False, f"post-create-validate.sh FAILED (exit {result.returncode}):\n{output.strip()}"
        except subprocess.TimeoutExpired:
            return False, "post-create-validate.sh timed out"
        except Exception as e:
            return False, f"Error running post-create-validate.sh: {e}"

    checks.append(run_check("post_create_validate_passes", check_post_create_validate))

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical = {"precommit_hook_installed", "deployment_check_sh", "deployment_checklist_md",
                "git_hooks_pre_commit_deployment", "payment_utils_exists",
                "no_hardcoded_secrets", "no_bypass_patterns", "post_create_validate_passes"}

    total_weight = 0
    passed_weight = 0
    for c in checks:
        w = 2.0 if c["name"] in critical else 1.0
        total_weight += w
        if c["passed"]:
            passed_weight += w

    score = round(passed_weight / total_weight, 3) if total_weight > 0 else 0.0
    all_critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = all_critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()