#!/usr/bin/env python3
"""
Evaluation script for the code-review-helper task.
Checks three output files produced by the agent:
  1. security_audit.json   -- security-only, critical severity, JSON format
  2. auth_review.md        -- markdown review filtered to src/auth/ files
  3. pr_template.md        -- thorough PR review template
"""

import sys
import json
import re
from pathlib import Path

def find_file(workspace: Path, name: str) -> Path | None:
    """Search workspace recursively for a file by exact name."""
    matches = list(workspace.rglob(name))
    if matches:
        return matches[0]
    return None

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── CHECK 1: security_audit.json exists ──────────────────────────────────
    max_score += 1.0
    f = find_file(workspace, "security_audit.json")
    if f:
        checks.append({"name": "security_audit.json exists", "passed": True,
                        "detail": f"Found at {f}"})
        total_score += 1.0
    else:
        checks.append({"name": "security_audit.json exists", "passed": False,
                        "detail": "File security_audit.json not found anywhere in workspace"})

    # ── CHECK 2: security_audit.json is valid JSON ────────────────────────────
    max_score += 1.0
    audit_data = None
    if f:
        try:
            text = f.read_text()
            audit_data = json.loads(text)
            checks.append({"name": "security_audit.json is valid JSON", "passed": True,
                            "detail": "Parsed successfully"})
            total_score += 1.0
        except Exception as e:
            checks.append({"name": "security_audit.json is valid JSON", "passed": False,
                            "detail": f"JSON parse error: {e}"})
    else:
        checks.append({"name": "security_audit.json is valid JSON", "passed": False,
                        "detail": "File missing, skipping"})

    # ── CHECK 3: security_audit.json contains ONLY critical security findings ─
    max_score += 2.0
    if audit_data:
        try:
            findings = audit_data.get("findings", [])
            # Must have findings key
            has_findings_key = isinstance(findings, list)
            # All findings must be security category
            all_security = all(
                f.get("category", "").lower() == "security"
                for f in findings
            ) if findings else False
            # All findings must be critical severity
            all_critical = all(
                f.get("severity", "").lower() == "critical"
                for f in findings
            ) if findings else False
            # Must have at least the 3 critical security findings (SEC-001, SEC-002, SEC-003)
            ids = {f.get("id", "") for f in findings}
            has_required = {"SEC-001", "SEC-002", "SEC-003"}.issubset(ids)
            # Must NOT contain warning or info items
            no_non_critical = not any(
                f.get("severity", "").lower() in ("warning", "info")
                for f in findings
            )
            # Must NOT contain non-security categories
            no_other_cat = not any(
                f.get("category", "").lower() != "security"
                for f in findings
            )

            passed = (has_findings_key and all_security and all_critical
                      and has_required and no_non_critical and no_other_cat)

            detail = (
                f"findings_key={has_findings_key}, all_security={all_security}, "
                f"all_critical={all_critical}, required_ids={has_required}, "
                f"no_non_critical={no_non_critical}, no_other_cat={no_other_cat}, "
                f"ids_found={ids}"
            )
            checks.append({
                "name": "security_audit.json: only critical security findings",
                "passed": passed,
                "detail": detail
            })
            if passed:
                total_score += 2.0
        except Exception as e:
            checks.append({
                "name": "security_audit.json: only critical security findings",
                "passed": False,
                "detail": f"Error: {e}"
            })
    else:
        checks.append({
            "name": "security_audit.json: only critical security findings",
            "passed": False,
            "detail": "Audit data unavailable"
        })

    # ── CHECK 4: security_audit.json JSON format (not markdown/text) ─────────
    max_score += 1.0
    if f and audit_data is not None:
        # The root must have "findings" array — confirms --output json was used
        is_json_fmt = isinstance(audit_data, dict) and "findings" in audit_data
        checks.append({
            "name": "security_audit.json uses JSON output format",
            "passed": is_json_fmt,
            "detail": f"Root keys: {list(audit_data.keys()) if isinstance(audit_data, dict) else 'N/A'}"
        })
        if is_json_fmt:
            total_score += 1.0
    else:
        checks.append({
            "name": "security_audit.json uses JSON output format",
            "passed": False,
            "detail": "File or data unavailable"
        })

    # ── CHECK 5: auth_review.md exists ───────────────────────────────────────
    max_score += 1.0
    md_f = find_file(workspace, "auth_review.md")
    if md_f:
        checks.append({"name": "auth_review.md exists", "passed": True,
                        "detail": f"Found at {md_f}"})
        total_score += 1.0
    else:
        checks.append({"name": "auth_review.md exists", "passed": False,
                        "detail": "File auth_review.md not found anywhere in workspace"})

    # ── CHECK 6: auth_review.md is markdown format (has # headings) ──────────
    max_score += 1.0
    md_text = None
    if md_f:
        try:
            md_text = md_f.read_text()
            is_md = "# Code Review Report" in md_text or "##" in md_text
            checks.append({
                "name": "auth_review.md is in markdown format",
                "passed": is_md,
                "detail": f"First 200 chars: {md_text[:200]}"
            })
            if is_md:
                total_score += 1.0
        except Exception as e:
            checks.append({
                "name": "auth_review.md is in markdown format",
                "passed": False,
                "detail": f"Error reading file: {e}"
            })
    else:
        checks.append({
            "name": "auth_review.md is in markdown format",
            "passed": False,
            "detail": "File missing"
        })

    # ── CHECK 7: auth_review.md filtered to auth files only ──────────────────
    max_score += 2.0
    if md_text:
        try:
            # Must contain auth file references
            has_auth_ref = "src/auth/" in md_text
            # Must NOT contain non-auth src files (payment, api, services, utils, migrations)
            has_other_files = any(
                pat in md_text
                for pat in [
                    "src/payment/", "src/api/", "src/services/",
                    "src/utils/", "migrations/"
                ]
            )
            passed = has_auth_ref and not has_other_files
            checks.append({
                "name": "auth_review.md filtered to src/auth/ files only",
                "passed": passed,
                "detail": (
                    f"has_auth_ref={has_auth_ref}, "
                    f"has_other_files={has_other_files}"
                )
            })
            if passed:
                total_score += 2.0
        except Exception as e:
            checks.append({
                "name": "auth_review.md filtered to src/auth/ files only",
                "passed": False,
                "detail": f"Error: {e}"
            })
    else:
        checks.append({
            "name": "auth_review.md filtered to src/auth/ files only",
            "passed": False,
            "detail": "Markdown content unavailable"
        })

    # ── CHECK 8: pr_template.md exists ───────────────────────────────────────
    max_score += 1.0
    tmpl_f = find_file(workspace, "pr_template.md")
    if tmpl_f:
        checks.append({"name": "pr_template.md exists", "passed": True,
                        "detail": f"Found at {tmpl_f}"})
        total_score += 1.0
    else:
        checks.append({"name": "pr_template.md exists", "passed": False,
                        "detail": "File pr_template.md not found anywhere in workspace"})

    # ── CHECK 9: pr_template.md is thorough style (has Architecture, Rollback) -
    max_score += 2.0
    tmpl_text = None
    if tmpl_f:
        try:
            tmpl_text = tmpl_f.read_text()
            # Thorough template must contain sections NOT in standard/minimal
            has_architecture = "Architecture" in tmpl_text or "architecture" in tmpl_text
            has_rollback = "Rollback" in tmpl_text or "rollback" in tmpl_text
            has_deployment = "Deployment" in tmpl_text or "deployment" in tmpl_text
            has_documentation = "Documentation" in tmpl_text or "documentation" in tmpl_text
            # Standard sections that all styles have
            has_security = "Security" in tmpl_text
            has_tests = "Tests" in tmpl_text or "Test" in tmpl_text
            # Must have ALL thorough-only sections
            passed = (has_architecture and has_rollback and has_deployment
                      and has_documentation and has_security and has_tests)
            checks.append({
                "name": "pr_template.md is thorough style",
                "passed": passed,
                "detail": (
                    f"architecture={has_architecture}, rollback={has_rollback}, "
                    f"deployment={has_deployment}, documentation={has_documentation}, "
                    f"security={has_security}, tests={has_tests}"
                )
            })
            if passed:
                total_score += 2.0
        except Exception as e:
            checks.append({
                "name": "pr_template.md is thorough style",
                "passed": False,
                "detail": f"Error: {e}"
            })
    else:
        checks.append({
            "name": "pr_template.md is thorough style",
            "passed": False,
            "detail": "File missing"
        })

    # ── CHECK 10: pr_template.md has checkbox format (from template flag) ─────
    max_score += 1.0
    if tmpl_text:
        has_checkboxes = "- [ ]" in tmpl_text
        checks.append({
            "name": "pr_template.md contains review checkboxes",
            "passed": has_checkboxes,
            "detail": f"Checkbox pattern found: {has_checkboxes}"
        })
        if has_checkboxes:
            total_score += 1.0
    else:
        checks.append({
            "name": "pr_template.md contains review checkboxes",
            "passed": False,
            "detail": "File missing"
        })

    # ── BONUS CHECK: security_audit.json references correct branches ──────────
    max_score += 1.0
    if audit_data and isinstance(audit_data, dict):
        head_val = audit_data.get("head", "")
        base_val = audit_data.get("base", "")
        # The task specifies develop -> feature/payment-service
        correct_base = "develop" in base_val
        correct_head = "feature/payment-service" in head_val or "HEAD" in head_val
        passed = correct_base and correct_head
        checks.append({
            "name": "security_audit.json references correct branches",
            "passed": passed,
            "detail": f"base='{base_val}', head='{head_val}'"
        })
        if passed:
            total_score += 1.0
    else:
        checks.append({
            "name": "security_audit.json references correct branches",
            "passed": False,
            "detail": "Audit data unavailable or malformed"
        })

    # ── Final score ───────────────────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed_overall = score >= 0.75 and all(
        c["passed"]
        for c in checks
        if c["name"] in {
            "security_audit.json exists",
            "security_audit.json is valid JSON",
            "security_audit.json: only critical security findings",
            "security_audit.json uses JSON output format",
            "auth_review.md exists",
            "auth_review.md is in markdown format",
            "pr_template.md exists",
            "pr_template.md is thorough style",
        }
    )

    return {"passed": passed_overall, "score": score, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace argument provided"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))