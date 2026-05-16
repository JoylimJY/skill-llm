import sys
import os
import json
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # ─── Helper ───────────────────────────────────────────────────────────────
    def check(name, condition, detail):
        nonlocal passed_all
        result = bool(condition)
        if not result:
            passed_all = False
        checks.append({"name": name, "passed": result, "detail": detail})
        return result

    # ─── 1. Find the output JSON report file ──────────────────────────────────
    report_files = list(Path(workspace).rglob("audit_report.json"))
    
    if not report_files:
        check("report_file_exists", False, "No 'audit_report.json' found anywhere in workspace")
        return passed_all, checks

    report_path = report_files[0]
    check("report_file_exists", True, f"Found report at {report_path}")

    # ─── 2. Parse the JSON report ─────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        check("report_valid_json", False, f"Failed to parse JSON: {e}")
        return passed_all, checks

    check("report_valid_json", True, "JSON parsed successfully")

    # ─── 3. Check required top-level fields ────────────────────────────────────
    has_findings = "findings" in report
    check("has_findings_field", has_findings, 
          "Report must have 'findings' array" if not has_findings else "findings field present")

    has_exit_code = "exit_code" in report
    check("has_exit_code_field", has_exit_code,
          "Report must have 'exit_code' field" if not has_exit_code else "exit_code field present")

    has_severity = "severity_classification" in report
    check("has_severity_classification_field", has_severity,
          "Report must have 'severity_classification' field mapping exit_code to human label" 
          if not has_severity else "severity_classification field present")

    if not has_findings or not has_exit_code:
        return passed_all, checks

    # ─── 4. Severity classification must match exit_code ─────────────────────
    exit_code = report.get("exit_code")
    sev_class = report.get("severity_classification", "")
    
    EXPECTED_SEVERITY = {0: "clean", 1: "warning", 2: "critical"}
    expected_sev = EXPECTED_SEVERITY.get(exit_code, None)
    
    if expected_sev is not None:
        sev_ok = isinstance(sev_class, str) and expected_sev.lower() in sev_class.lower()
        check("severity_classification_correct", sev_ok,
              f"exit_code={exit_code} should map to severity containing '{expected_sev}', got '{sev_class}'")
    else:
        check("severity_classification_correct", False, 
              f"exit_code={exit_code} is unexpected")

    # ─── 5. vendor and node_modules directories were SKIPPED ─────────────────
    findings = report.get("findings", [])
    
    vendor_leaked = any(
        "/vendor/" in f.get("file", "") 
        for f in findings
    )
    check("vendor_dir_skipped", not vendor_leaked,
          "vendor/ directory findings leaked into report — should have been skipped via --skip-dir" 
          if vendor_leaked else "vendor/ directory correctly skipped")

    node_modules_leaked = any(
        "/node_modules/" in f.get("file", "") 
        for f in findings
    )
    check("node_modules_dir_skipped", not node_modules_leaked,
          "node_modules/ directory findings leaked into report — should have been skipped via --skip-dir"
          if node_modules_leaked else "node_modules/ correctly skipped")

    # ─── 6. Dockerfile-privileged finding in image-converter IS whitelisted ───
    # The task requires whitelisting: dockerfile-privileged for build.Dockerfile
    priv_finding_present = any(
        f.get("rule") == "dockerfile-privileged" and "build.Dockerfile" in f.get("file", "")
        for f in findings
    )
    check("dockerfile_privileged_whitelisted", not priv_finding_present,
          "dockerfile-privileged finding for image-converter/scripts/build.Dockerfile should be whitelisted but is present"
          if priv_finding_present else "dockerfile-privileged correctly whitelisted for build.Dockerfile")

    # ─── 7. Critical findings ARE detected (not all suppressed) ───────────────
    critical_findings = [f for f in findings if f.get("severity") == "critical"]
    has_criticals = len(critical_findings) > 0
    check("critical_findings_present", has_criticals,
          f"Expected critical findings (pipe-execution, env-exfiltration, sensitive-file-leak, cloud-credential-access, typosquat), found {len(critical_findings)}"
          if not has_criticals else f"Found {len(critical_findings)} critical findings")

    # ─── 8. Specific expected critical rules are detected ────────────────────
    found_rules = {f.get("rule") for f in findings}
    
    expected_critical_rules = ["pipe-execution", "env-exfiltration", "sensitive-file-leak", "cloud-credential-access"]
    found_expected = [r for r in expected_critical_rules if r in found_rules]
    
    check("key_critical_rules_detected", len(found_expected) >= 3,
          f"Expected at least 3 of {expected_critical_rules} to be found. Got: {found_expected}")

    # ─── 9. Warning-level findings detected ───────────────────────────────────
    warning_findings = [f for f in findings if f.get("severity") == "warning"]
    check("warning_findings_present", len(warning_findings) > 0,
          f"Expected warning-level findings (dangerous-permissions, covert-exec-python). Found {len(warning_findings)}"
          if len(warning_findings) == 0 else f"Found {len(warning_findings)} warning findings")

    # ─── 10. exit_code is 2 (critical) given unwhitelisted critical findings ──
    check("exit_code_is_critical", exit_code == 2,
          f"With unwhitelisted critical findings remaining, exit_code must be 2, got {exit_code}")

    # ─── 11. Whitelist file was used (format: rule_id:filename_pattern) ──────
    whitelist_files = list(Path(workspace).rglob("whitelist.txt"))
    has_whitelist = len(whitelist_files) > 0
    check("whitelist_file_created", has_whitelist,
          "No whitelist.txt found — agent must create one with correct rule_id:pattern format"
          if not has_whitelist else f"Whitelist found at {whitelist_files[0]}")

    if has_whitelist:
        try:
            with open(whitelist_files[0]) as wf:
                content = wf.read()
            # Correct format: lines like "dockerfile-privileged:build.Dockerfile"
            has_correct_entry = any(
                "dockerfile-privileged" in line and "build.Dockerfile" in line
                for line in content.splitlines()
                if not line.strip().startswith("#") and ":" in line
            )
            check("whitelist_correct_format", has_correct_entry,
                  f"Whitelist must contain an entry like 'dockerfile-privileged:build.Dockerfile'. Content was:\n{content[:500]}"
                  if not has_correct_entry else "Whitelist correctly contains dockerfile-privileged:build.Dockerfile entry")
        except Exception as e:
            check("whitelist_correct_format", False, f"Error reading whitelist: {e}")

    # ─── Score ────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    return passed_all, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        passed_all, score, checks = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }))
        sys.exit(0)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()