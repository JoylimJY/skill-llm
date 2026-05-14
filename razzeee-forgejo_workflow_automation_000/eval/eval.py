#!/usr/bin/env python3
"""
Evaluation script for the aerospace compliance snapshot task.
Checks that the agent:
1. Registered a tea login pointing to the local mock Forgejo instance
2. Listed open issues from aeroquality/nav-core and included them in the output
3. Retrieved PR #3 metadata via tea api or tea pr
4. Produced a correctly structured compliance_snapshot.json
"""
import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    passed_all = True

    # ------------------------------------------------------------------ #
    # CHECK 1: compliance_snapshot.json exists somewhere in workspace      #
    # ------------------------------------------------------------------ #
    snapshot_files = list(Path(workspace).rglob("compliance_snapshot.json"))
    file_found = len(snapshot_files) > 0
    checks.append({
        "name": "compliance_snapshot.json exists",
        "passed": file_found,
        "detail": f"Found {len(snapshot_files)} file(s): {[str(p) for p in snapshot_files]}" if file_found else "File not found anywhere in workspace."
    })
    if not file_found:
        passed_all = False
        # Still run remaining checks to give partial credit
        snapshot_data = {}
        snapshot_path = None
    else:
        snapshot_path = snapshot_files[0]
        try:
            with open(snapshot_path, "r") as f:
                snapshot_data = json.load(f)
        except Exception as e:
            checks.append({
                "name": "compliance_snapshot.json is valid JSON",
                "passed": False,
                "detail": f"Failed to parse JSON: {e}"
            })
            passed_all = False
            snapshot_data = {}

    # ------------------------------------------------------------------ #
    # CHECK 2: JSON is valid (only if file was found and parse succeeded)  #
    # ------------------------------------------------------------------ #
    if file_found and snapshot_data:
        checks.append({
            "name": "compliance_snapshot.json is valid JSON",
            "passed": True,
            "detail": f"Parsed successfully from {snapshot_path}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 3: Open issues section present with correct count              #
    # Expected: 3 open issues in aeroquality/nav-core                      #
    # ------------------------------------------------------------------ #
    issues_section = None
    issues_found = False
    issues_count_ok = False

    if snapshot_data:
        # Accept flexible key names: "issues", "open_issues", "defects", etc.
        for key in ["issues", "open_issues", "defect_tickets", "defects", "open_defects"]:
            if key in snapshot_data:
                issues_section = snapshot_data[key]
                break

        if issues_section is not None:
            issues_found = True
            if isinstance(issues_section, list):
                issues_count_ok = len(issues_section) == 3
                issues_count_detail = f"Found {len(issues_section)} open issues (expected 3)"
            elif isinstance(issues_section, dict):
                # might be a dict with "count" or similar
                count = issues_section.get("count", issues_section.get("total", -1))
                issues_count_ok = count == 3
                issues_count_detail = f"Found count={count} (expected 3)"
            else:
                issues_count_detail = f"Issues section has unexpected type: {type(issues_section)}"
        else:
            issues_count_detail = f"No issues section found in JSON keys: {list(snapshot_data.keys())}"

    checks.append({
        "name": "Open issues section present in snapshot",
        "passed": issues_found,
        "detail": "Issues section found" if issues_found else f"Missing issues section. Keys: {list(snapshot_data.keys()) if snapshot_data else 'N/A'}"
    })
    if not issues_found:
        passed_all = False

    checks.append({
        "name": "Exactly 3 open issues reported",
        "passed": issues_count_ok,
        "detail": issues_count_detail if issues_section is not None else "Issues section missing"
    })
    if not issues_count_ok:
        passed_all = False

    # ------------------------------------------------------------------ #
    # CHECK 4: Issue titles are correct (at least 2 of 3 must match)       #
    # ------------------------------------------------------------------ #
    expected_issue_titles = [
        "Kalman filter divergence under high-G maneuver",
        "Unchecked return value in position_update()",
        "Missing boundary check in altitude parser",
    ]
    matched_titles = 0
    found_titles = []

    if isinstance(issues_section, list):
        for issue in issues_section:
            if isinstance(issue, dict):
                title = issue.get("title", "")
                found_titles.append(title)
                for et in expected_issue_titles:
                    if et.lower() in title.lower() or title.lower() in et.lower():
                        matched_titles += 1
                        break
    
    titles_ok = matched_titles >= 2
    checks.append({
        "name": "Issue titles match expected open defects (at least 2/3)",
        "passed": titles_ok,
        "detail": f"Matched {matched_titles}/3 titles. Found: {found_titles}"
    })
    if not titles_ok:
        passed_all = False

    # ------------------------------------------------------------------ #
    # CHECK 5: PR #3 metadata present                                       #
    # ------------------------------------------------------------------ #
    pr_section = None
    pr_found = False

    if snapshot_data:
        for key in ["pull_request", "pr", "pull_requests", "change_request", "pr_3", "pr3",
                    "pull_request_3", "change_request_3"]:
            if key in snapshot_data:
                val = snapshot_data[key]
                # If it's a list, look for PR #3
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and item.get("number") == 3:
                            pr_section = item
                            break
                elif isinstance(val, dict):
                    # Could be PR #3 directly or a container
                    if val.get("number") == 3:
                        pr_section = val
                    else:
                        # might have nested PR
                        for sub_key in ["3", "pr3", "details"]:
                            if sub_key in val and isinstance(val[sub_key], dict):
                                if val[sub_key].get("number") == 3:
                                    pr_section = val[sub_key]
                if pr_section:
                    break

        # Also check if there's a top-level "number": 3 anywhere
        if pr_section is None:
            # Deep search for PR number=3
            def find_pr3(obj, depth=0):
                if depth > 4:
                    return None
                if isinstance(obj, dict):
                    if obj.get("number") == 3 and "title" in obj:
                        return obj
                    for v in obj.values():
                        result = find_pr3(v, depth + 1)
                        if result:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_pr3(item, depth + 1)
                        if result:
                            return result
                return None
            pr_section = find_pr3(snapshot_data)

        pr_found = pr_section is not None

    checks.append({
        "name": "PR #3 metadata present in snapshot",
        "passed": pr_found,
        "detail": f"PR #3 found: {json.dumps(pr_section)[:200] if pr_section else 'Not found'}"
    })
    if not pr_found:
        passed_all = False

    # ------------------------------------------------------------------ #
    # CHECK 6: PR #3 has correct title, state, author                      #
    # ------------------------------------------------------------------ #
    pr_fields_ok = False
    pr_detail = "PR section not found"

    if pr_section:
        pr_title = pr_section.get("title", "")
        pr_state = pr_section.get("state", "")
        pr_user = pr_section.get("user", {})
        if isinstance(pr_user, dict):
            pr_login = pr_user.get("login", "")
        elif isinstance(pr_user, str):
            pr_login = pr_user
        else:
            pr_login = ""

        title_ok = "altitude" in pr_title.lower() or "boundary" in pr_title.lower() or "fix" in pr_title.lower()
        state_ok = "open" in pr_state.lower()
        user_ok = "j.smith" in pr_login.lower() or "smith" in pr_login.lower()

        pr_fields_ok = title_ok and state_ok and user_ok
        pr_detail = (
            f"title='{pr_title}' (ok={title_ok}), "
            f"state='{pr_state}' (ok={state_ok}), "
            f"user='{pr_login}' (ok={user_ok})"
        )

    checks.append({
        "name": "PR #3 has correct title/state/author fields",
        "passed": pr_fields_ok,
        "detail": pr_detail
    })
    if not pr_fields_ok:
        passed_all = False

    # ------------------------------------------------------------------ #
    # CHECK 7: tea login is configured for local instance                   #
    # ------------------------------------------------------------------ #
    tea_login_ok = False
    tea_login_detail = "Could not verify tea login"
    try:
        result = subprocess.run(
            ["tea", "logins"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        # Check that some login pointing to localhost:3000 exists
        if "localhost:3000" in output or "3000" in output:
            tea_login_ok = True
            tea_login_detail = f"Login to localhost:3000 found in tea logins output"
        else:
            tea_login_detail = f"No localhost:3000 login found. Output: {output[:300]}"
    except Exception as e:
        tea_login_detail = f"Error running 'tea logins': {e}"

    checks.append({
        "name": "tea login configured for local Forgejo instance",
        "passed": tea_login_ok,
        "detail": tea_login_detail
    })
    if not tea_login_ok:
        passed_all = False

    # ------------------------------------------------------------------ #
    # CHECK 8: Snapshot references correct repo                             #
    # ------------------------------------------------------------------ #
    repo_referenced = False
    repo_detail = "Repo reference not found"

    if snapshot_data:
        snapshot_str = json.dumps(snapshot_data).lower()
        if "aeroquality" in snapshot_str or "nav-core" in snapshot_str or "nav_core" in snapshot_str:
            repo_referenced = True
            repo_detail = "Repository 'aeroquality/nav-core' referenced in snapshot"
        else:
            repo_detail = f"Repository name not found in snapshot. Keys: {list(snapshot_data.keys())}"

    checks.append({
        "name": "Snapshot references aeroquality/nav-core repository",
        "passed": repo_referenced,
        "detail": repo_detail
    })
    if not repo_referenced:
        passed_all = False

    # ------------------------------------------------------------------ #
    # Scoring                                                               #
    # ------------------------------------------------------------------ #
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace arg", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))