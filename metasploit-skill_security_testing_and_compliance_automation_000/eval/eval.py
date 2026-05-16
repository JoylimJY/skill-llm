import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # =========================================================
    # CHECK 1: RC file exists at the correct location
    # =========================================================
    rc_path = workspace / "engagements" / "q2_audit" / "q2_fintrack_assessment.rc"
    rc_exists = rc_path.exists()
    checks.append(check(
        "rc_file_exists_at_correct_path",
        rc_exists,
        f"Expected: {rc_path} | Found: {rc_exists}"
    ))

    rc_content = ""
    if rc_exists:
        try:
            rc_content = rc_path.read_text()
        except Exception as e:
            checks.append(check("rc_file_readable", False, str(e)))

    # =========================================================
    # CHECK 2: RC uses correct module
    # =========================================================
    correct_module = "exploit/linux/http/fintrack_upload_rce"
    module_ok = correct_module in rc_content
    checks.append(check(
        "rc_correct_module",
        module_ok,
        f"Expected module '{correct_module}' in rc. Content snippet: {rc_content[:300]}"
    ))

    # =========================================================
    # CHECK 3: RC uses correct target host (RHOSTS)
    # =========================================================
    rhosts_ok = "10.14.22.7" in rc_content and any(
        line.strip().lower().startswith("set rhosts") and "10.14.22.7" in line
        for line in rc_content.splitlines()
    )
    checks.append(check(
        "rc_correct_rhosts",
        rhosts_ok,
        f"Expected 'set RHOSTS 10.14.22.7' in rc. Snippet: {rc_content[:400]}"
    ))

    # =========================================================
    # CHECK 4: RC uses correct port (RPORT 8443)
    # =========================================================
    rport_ok = any(
        line.strip().lower().startswith("set rport") and "8443" in line
        for line in rc_content.splitlines()
    )
    checks.append(check(
        "rc_correct_rport",
        rport_ok,
        f"Expected 'set RPORT 8443' in rc."
    ))

    # =========================================================
    # CHECK 5: RC uses architecture-appropriate payload
    # Linux x86_64 HTTP target -> must use linux/x64/meterpreter/reverse_tcp
    # MUST NOT use windows payload or x86 (wrong arch) payload
    # =========================================================
    payload_lines = [
        line for line in rc_content.splitlines()
        if line.strip().lower().startswith("set payload")
    ]
    payload_ok = False
    payload_detail = "No payload line found."
    if payload_lines:
        pl = payload_lines[0].lower()
        # Must be linux/x64/meterpreter/reverse_tcp (arch-correct for linux x86_64)
        if "linux/x64/meterpreter/reverse_tcp" in pl:
            payload_ok = True
            payload_detail = f"Correct payload: {payload_lines[0]}"
        elif "linux/x86/meterpreter" in pl:
            payload_detail = f"Wrong architecture (x86 not x64): {payload_lines[0]}"
        elif "windows" in pl:
            payload_detail = f"Wrong OS (windows payload for linux target): {payload_lines[0]}"
        else:
            payload_detail = f"Unexpected payload: {payload_lines[0]}"
    checks.append(check(
        "rc_correct_payload_architecture",
        payload_ok,
        payload_detail
    ))

    # =========================================================
    # CHECK 6: RC sets LHOST correctly (10.14.22.1)
    # MUST NOT use stale values like 192.168.1.50 or 10.0.0.99
    # =========================================================
    lhost_lines = [
        line for line in rc_content.splitlines()
        if line.strip().lower().startswith("set lhost")
    ]
    lhost_ok = False
    lhost_detail = "No LHOST line found."
    if lhost_lines:
        if "10.14.22.1" in lhost_lines[0]:
            lhost_ok = True
            lhost_detail = f"Correct LHOST: {lhost_lines[0]}"
        else:
            lhost_detail = f"Wrong LHOST (possibly stale config): {lhost_lines[0]}"
    checks.append(check("rc_correct_lhost", lhost_ok, lhost_detail))

    # =========================================================
    # CHECK 7: RC sets LPORT correctly (5555)
    # =========================================================
    lport_lines = [
        line for line in rc_content.splitlines()
        if line.strip().lower().startswith("set lport")
    ]
    lport_ok = False
    lport_detail = "No LPORT line found."
    if lport_lines:
        if "5555" in lport_lines[0]:
            lport_ok = True
            lport_detail = f"Correct LPORT: {lport_lines[0]}"
        else:
            lport_detail = f"Wrong LPORT (possibly stale config): {lport_lines[0]}"
    checks.append(check("rc_correct_lport", lport_ok, lport_detail))

    # =========================================================
    # CHECK 8: RC sets TARGETURI to /portal/upload
    # This is the bespoke --set option for HTTP modules
    # =========================================================
    targeturi_ok = any(
        "set targeturi" in line.lower() and "/portal/upload" in line
        for line in rc_content.splitlines()
    )
    checks.append(check(
        "rc_targeturi_set_correctly",
        targeturi_ok,
        f"Expected 'set TARGETURI /portal/upload' in rc. Content: {rc_content[:500]}"
    ))

    # =========================================================
    # CHECK 9: RC includes 'check' command (check-first workflow)
    # =========================================================
    check_cmd_ok = any(
        line.strip().lower() == "check"
        for line in rc_content.splitlines()
    )
    checks.append(check(
        "rc_includes_check_command",
        check_cmd_ok,
        f"Expected bare 'check' line in rc for check-first workflow."
    ))

    # =========================================================
    # CHECK 10: RC uses 'exploit -j' (background job, not plain 'run')
    # This tests the --job flag from build_rc.py
    # =========================================================
    job_ok = any(
        line.strip().lower() == "exploit -j"
        for line in rc_content.splitlines()
    )
    plain_run_only = any(
        line.strip().lower() == "run"
        for line in rc_content.splitlines()
    ) and not job_ok
    
    job_detail = ""
    if job_ok:
        job_detail = "Found 'exploit -j' for background job execution."
    elif plain_run_only:
        job_detail = "Found 'run' but not 'exploit -j'. --job flag was likely not used."
    else:
        job_detail = "Neither 'exploit -j' nor 'run' found."
    checks.append(check("rc_uses_background_job", job_ok, job_detail))

    # =========================================================
    # CHECK 11: 'check' appears BEFORE 'exploit -j' in rc
    # =========================================================
    lines_list = rc_content.splitlines()
    check_idx = next((i for i, l in enumerate(lines_list) if l.strip().lower() == "check"), None)
    exploit_idx = next((i for i, l in enumerate(lines_list) if l.strip().lower() == "exploit -j"), None)
    order_ok = (check_idx is not None and exploit_idx is not None and check_idx < exploit_idx)
    checks.append(check(
        "rc_check_before_exploit",
        order_ok,
        f"check at line {check_idx}, exploit -j at line {exploit_idx}. Must be check before exploit."
    ))

    # =========================================================
    # CHECK 12: Report file exists at correct path
    # =========================================================
    report_path = workspace / "engagements" / "q2_audit" / "reports" / "q2_fintrack_report.txt"
    report_exists = report_path.exists()
    checks.append(check(
        "report_file_exists_at_correct_path",
        report_exists,
        f"Expected: {report_path} | Found: {report_exists}"
    ))

    report_content = ""
    if report_exists:
        try:
            report_content = report_path.read_text().lower()
        except Exception as e:
            checks.append(check("report_file_readable", False, str(e)))

    # =========================================================
    # CHECK 13: Report contains all 5 required sections from workflow.md template
    # Sections: Objective, Procedure, Result, Impact, Remediation
    # =========================================================
    required_sections = ["objective", "procedure", "result", "impact", "remediation"]
    missing_sections = [s for s in required_sections if s not in report_content]
    sections_ok = len(missing_sections) == 0
    checks.append(check(
        "report_contains_all_required_sections",
        sections_ok,
        f"Missing sections: {missing_sections}. Required: {required_sections}"
    ))

    # =========================================================
    # CHECK 14: Report references the target host and module
    # =========================================================
    report_references_target = "10.14.22.7" in report_content
    report_references_module = "fintrack_upload_rce" in report_content or "fintrack" in report_content
    report_content_ok = report_references_target and report_references_module
    checks.append(check(
        "report_references_target_and_module",
        report_content_ok,
        f"Target referenced: {report_references_target}, Module referenced: {report_references_module}"
    ))

    # =========================================================
    # CHECK 15: Report references the RC script or commands (Procedure section has reproducible steps)
    # =========================================================
    rc_referenced = (
        "q2_fintrack_assessment.rc" in report_path.read_text() if report_exists else False
    ) or (
        "build_rc.py" in report_path.read_text() if report_exists else False
    )
    checks.append(check(
        "report_procedure_references_reproducible_commands",
        rc_referenced,
        "Procedure section should reference the rc script or build_rc.py invocation for reproducibility."
    ))

    # =========================================================
    # Scoring
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = (
        # Hard requirements: RC file correctness and report completeness
        checks[0]["passed"] and   # rc exists
        checks[1]["passed"] and   # correct module
        checks[4]["passed"] and   # correct payload arch
        checks[8]["passed"] and   # check command
        checks[9]["passed"] and   # exploit -j
        checks[10]["passed"] and  # check before exploit
        checks[11]["passed"] and  # report exists
        checks[12]["passed"]      # report has all 5 sections
    )

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()