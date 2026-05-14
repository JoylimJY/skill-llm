#!/usr/bin/env python3
"""
Evaluation script for the repository audit task.
Checks that audit_report.json was correctly produced using tea CLI.
"""
import sys
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ------------------------------------------------------------------ #
    # CHECK 0: audit_report.json exists
    # ------------------------------------------------------------------ #
    report_candidates = list(workspace.rglob("audit_report.json"))
    
    def check_file_exists():
        if not report_candidates:
            return False, "audit_report.json not found anywhere under workspace"
        return True, f"Found at {report_candidates[0]}"
    
    checks.append(run_check("audit_report.json exists", check_file_exists))
    
    if not report_candidates:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    report_path = report_candidates[0]
    
    # Load the report
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "audit_report.json is valid JSON", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    checks.append({"name": "audit_report.json is valid JSON", "passed": True, "detail": "Parsed successfully"})

    # ------------------------------------------------------------------ #
    # CHECK 1: tea login was configured (tea logins should show a login)
    # ------------------------------------------------------------------ #
    def check_tea_login():
        try:
            result = subprocess.run(
                ["tea", "logins"],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout + result.stderr
            if result.returncode == 0 and ("localhost" in output or "local" in output.lower() or "3000" in output):
                return True, f"tea login configured: {output.strip()[:200]}"
            return False, f"tea logins output unexpected: {output.strip()[:200]}"
        except Exception as e:
            return False, f"tea logins failed: {e}"
    
    checks.append(run_check("tea login configured for local server", check_tea_login))

    # ------------------------------------------------------------------ #
    # CHECK 2: open_issues field - correct open issues (3 open: #1,#3,#4)
    # ------------------------------------------------------------------ #
    def check_open_issues():
        if "open_issues" not in report:
            return False, "Field 'open_issues' missing from report"
        
        oi = report["open_issues"]
        if not isinstance(oi, list):
            return False, f"open_issues should be a list, got {type(oi)}"
        
        if len(oi) != 3:
            return False, f"Expected 3 open issues (issue #2 was closed), got {len(oi)}: {oi}"
        
        # Each entry must have number (int) and title (str)
        for entry in oi:
            if not isinstance(entry, dict):
                return False, f"Each issue entry must be a dict, got: {entry}"
            if "number" not in entry:
                return False, f"Issue entry missing 'number' field: {entry}"
            if "title" not in entry:
                return False, f"Issue entry missing 'title' field: {entry}"
        
        numbers = sorted([e["number"] for e in oi])
        # Issues 1, 3, 4 should be open (2 was closed)
        if numbers != [1, 3, 4]:
            return False, f"Expected open issue numbers [1,3,4], got {numbers}"
        
        # Verify titles match expected content
        title_map = {e["number"]: e["title"] for e in oi}
        expected_titles = {
            1: "Fix memory leak in sparse matrix solver",
            3: "Documentation update for v0.4 API",
            4: "CI pipeline fails on ARM builds",
        }
        for num, expected_title in expected_titles.items():
            actual = title_map.get(num, "")
            if expected_title.lower() not in actual.lower() and actual.lower() not in expected_title.lower():
                # Allow partial match - check for key keywords
                keywords = expected_title.lower().split()[:3]
                if not any(kw in actual.lower() for kw in keywords):
                    return False, f"Issue #{num} title mismatch: expected '{expected_title}', got '{actual}'"
        
        return True, f"open_issues correct: {numbers}"
    
    checks.append(run_check("open_issues field is correct (3 open, correct numbers+titles)", check_open_issues))

    # ------------------------------------------------------------------ #
    # CHECK 3: open_prs field - correct open PRs (PRs 1 and 3 are open; PR 2 closed)
    # ------------------------------------------------------------------ #
    def check_open_prs():
        if "open_prs" not in report:
            return False, "Field 'open_prs' missing from report"
        
        prs = report["open_prs"]
        if not isinstance(prs, list):
            return False, f"open_prs should be a list, got {type(prs)}"
        
        if len(prs) != 2:
            return False, f"Expected 2 open PRs (PR #2 was closed), got {len(prs)}: {prs}"
        
        for entry in prs:
            if not isinstance(entry, dict):
                return False, f"Each PR entry must be a dict, got: {entry}"
            for field in ["number", "title", "author"]:
                if field not in entry:
                    return False, f"PR entry missing '{field}' field: {entry}"
        
        numbers = sorted([e["number"] for e in prs])
        if numbers != [1, 3]:
            return False, f"Expected open PR numbers [1,3], got {numbers}"
        
        # Verify authors are set (non-empty)
        for pr in prs:
            if not pr.get("author"):
                return False, f"PR #{pr.get('number')} has empty author"
        
        return True, f"open_prs correct: PRs {numbers} with authors"
    
    checks.append(run_check("open_prs field is correct (2 open PRs, number+title+author)", check_open_prs))

    # ------------------------------------------------------------------ #
    # CHECK 4: pr_details for PR #3 (must use tea api or tea pr)
    # ------------------------------------------------------------------ #
    def check_pr_details():
        if "pr_details" not in report:
            return False, "Field 'pr_details' missing from report"
        
        details = report["pr_details"]
        if not isinstance(details, dict):
            return False, f"pr_details should be a dict, got {type(details)}"
        
        for field in ["title", "state", "author"]:
            if field not in details:
                return False, f"pr_details missing '{field}' field"
        
        # PR #3 is the docs update PR, state is open
        title = details.get("title", "")
        state = details.get("state", "")
        author = details.get("author", "")
        
        # Title should reference docs/API
        if not ("docs" in title.lower() or "api" in title.lower() or "v0.4" in title.lower() or "reference" in title.lower()):
            return False, f"pr_details title doesn't match PR #3 (docs/API PR): '{title}'"
        
        if state.lower() not in ("open", "opened"):
            return False, f"PR #3 should be open, got state='{state}'"
        
        if not author:
            return False, "pr_details author is empty"
        
        return True, f"pr_details correct: title='{title}', state='{state}', author='{author}'"
    
    checks.append(run_check("pr_details for PR #3 is correct (title/state/author)", check_pr_details))

    # ------------------------------------------------------------------ #
    # CHECK 5: ci_secrets - must list all 3 secret names
    # ------------------------------------------------------------------ #
    def check_ci_secrets():
        if "ci_secrets" not in report:
            return False, "Field 'ci_secrets' missing from report"
        
        secrets = report["ci_secrets"]
        if not isinstance(secrets, list):
            return False, f"ci_secrets should be a list, got {type(secrets)}"
        
        expected_secrets = {"DEPLOY_SSH_KEY", "PYPI_API_TOKEN", "CODECOV_TOKEN"}
        actual_secrets = set(str(s).strip() for s in secrets)
        
        missing = expected_secrets - actual_secrets
        extra = actual_secrets - expected_secrets
        
        if missing:
            return False, f"Missing secrets: {missing}. Got: {actual_secrets}"
        
        if extra:
            return False, f"Unexpected extra secrets: {extra}. Got: {actual_secrets}"
        
        return True, f"ci_secrets correct: {sorted(actual_secrets)}"
    
    checks.append(run_check("ci_secrets contains all 3 expected secret names", check_ci_secrets))

    # ------------------------------------------------------------------ #
    # CHECK 6: ci_variables - must list all 3 variable names
    # ------------------------------------------------------------------ #
    def check_ci_variables():
        if "ci_variables" not in report:
            return False, "Field 'ci_variables' missing from report"
        
        variables = report["ci_variables"]
        if not isinstance(variables, list):
            return False, f"ci_variables should be a list, got {type(variables)}"
        
        expected_vars = {"PYTHON_VERSION", "DOCKER_REGISTRY", "MAX_WORKERS"}
        actual_vars = set(str(v).strip() for v in variables)
        
        missing = expected_vars - actual_vars
        extra = actual_vars - expected_vars
        
        if missing:
            return False, f"Missing variables: {missing}. Got: {actual_vars}"
        
        if extra:
            return False, f"Unexpected extra variables: {extra}. Got: {actual_vars}"
        
        return True, f"ci_variables correct: {sorted(actual_vars)}"
    
    checks.append(run_check("ci_variables contains all 3 expected variable names", check_ci_variables))

    # ------------------------------------------------------------------ #
    # CHECK 7: Verify tea was actually used (shell history or tea config)
    # ------------------------------------------------------------------ #
    def check_tea_was_used():
        # Check that tea login config exists (tea stores it in ~/.config/tea)
        tea_config_paths = [
            Path.home() / ".config" / "tea" / "config.yml",
            Path("/root/.config/tea/config.yml"),
            Path("/root/.tea/config.yml"),
        ]
        for p in tea_config_paths:
            if p.exists():
                content = p.read_text()
                if "localhost" in content or "3000" in content:
                    return True, f"tea config found at {p} with local server reference"
        
        # Also check bash history
        history_paths = [Path("/root/.bash_history"), Path("/root/.zsh_history")]
        for hp in history_paths:
            if hp.exists():
                hist = hp.read_text(errors="replace")
                if "tea" in hist and ("issue" in hist or "pulls" in hist or "api" in hist or "actions" in hist):
                    return True, f"tea commands found in {hp}"
        
        return False, "No evidence of tea CLI usage found (config or history)"
    
    checks.append(run_check("tea CLI was used (config/history evidence)", check_tea_was_used))

    # ------------------------------------------------------------------ #
    # Final scoring
    # ------------------------------------------------------------------ #
    # Weights: file_exists=5%, valid_json=5%, tea_login=10%, 
    #          open_issues=20%, open_prs=20%, pr_details=15%, 
    #          ci_secrets=15%, ci_variables=15%, tea_used=5% (bonus)
    weights = [0.05, 0.05, 0.10, 0.20, 0.20, 0.15, 0.15, 0.15, 0.05]
    
    score = sum(w for c, w in zip(checks, weights) if c["passed"])
    # Cap at 1.0
    score = min(score, 1.0)
    
    # Must pass all core data checks to "pass"
    core_checks = checks[2:8]  # tea_login through ci_variables
    overall_passed = all(c["passed"] for c in core_checks)
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()