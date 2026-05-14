import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []

    # --- Locate the report file ---
    # The prompt asks for cron_audit_report.txt
    report_files = list(Path(workspace).rglob("cron_audit_report.txt"))

    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "cron_audit_report.txt not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": f"Cannot read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    lines = [l for l in content.splitlines() if l.strip() != ""]
    total_lines = len(content.splitlines())  # including blank lines

    # --- CHECK 1: Line count (10-25 lines total including blanks) ---
    line_count_ok = 10 <= total_lines <= 25
    checks.append({
        "name": "line_count_10_to_25",
        "passed": line_count_ok,
        "detail": f"Report has {total_lines} lines (blank included). Required: 10–25."
    })

    # --- CHECK 2: TOTALS section present ---
    has_totals = any("TOTALS" in l or ("enabled" in l.lower() and "disabled" in l.lower()) for l in lines)
    checks.append({
        "name": "section_totals_present",
        "passed": has_totals,
        "detail": "Report must contain a TOTALS line with enabled/disabled counts."
    })

    # CHECK 2b: Correct totals (13 enabled, 2 disabled, 15 total)
    totals_correct = False
    for l in lines:
        # Look for 13 enabled and 2 disabled anywhere on totals line
        if re.search(r'13\s*enabled', l, re.IGNORECASE) and re.search(r'2\s*disabled', l, re.IGNORECASE):
            totals_correct = True
            break
        if re.search(r'enabled[^\d]*13', l, re.IGNORECASE) and re.search(r'disabled[^\d]*2', l, re.IGNORECASE):
            totals_correct = True
            break
        if '13' in l and '2' in l and ('enabled' in l.lower() or 'TOTAL' in l.upper()):
            totals_correct = True
            break
    checks.append({
        "name": "totals_values_correct",
        "passed": totals_correct,
        "detail": "Report must state 13 enabled and 2 disabled jobs."
    })

    # --- CHECK 3: TOP RISKS section (must list 1–5 risks) ---
    has_risks_section = any("TOP RISK" in l.upper() or "RISK" in l.upper() for l in lines)
    checks.append({
        "name": "section_top_risks_present",
        "passed": has_risks_section,
        "detail": "Report must contain a TOP RISKS section."
    })

    # Count risk bullet lines
    risk_lines = [l for l in lines if re.match(r'\s*[-*•]\s+', l) or re.match(r'\s+- ', l)]
    risk_count_ok = 1 <= len(risk_lines) <= 5
    checks.append({
        "name": "top_risks_count_1_to_5",
        "passed": risk_count_ok,
        "detail": f"Found {len(risk_lines)} risk bullet lines. Required: 1–5."
    })

    # --- CHECK 4: All 5 risk categories covered ---
    full_text = content.upper()

    has_duplicate = "DUPLICATE" in full_text or "DUPLICATE_PURPOSE" in full_text
    checks.append({
        "name": "risk_duplicate_purpose_detected",
        "passed": has_duplicate,
        "detail": "Must flag DUPLICATE_PURPOSE (billing_sync_primary/backup/legacy share same purpose)."
    })

    has_spam = "SPAM" in full_text or "NOTIFICATION" in full_text or "ANNOUNCE" in full_text or "BROADCAST" in full_text
    checks.append({
        "name": "risk_notification_spam_detected",
        "passed": has_spam,
        "detail": "Must flag NOTIFICATION_SPAM (4 broadcast/announce jobs)."
    })

    has_cadence = "CADENCE" in full_text or "HEAVY" in full_text or "FREQUENT" in full_text or "COST RISK" in full_text
    checks.append({
        "name": "risk_heavy_cadence_detected",
        "passed": has_cadence,
        "detail": "Must flag HEAVY_CADENCE (metrics_scrape_realtime and heartbeat_ping run < 5 min)."
    })

    has_failures = "FAILURE" in full_text or "FLAKY" in full_text or "CONSECUTIVE" in full_text or "REPEATED" in full_text
    checks.append({
        "name": "risk_repeated_failures_detected",
        "passed": has_failures,
        "detail": "Must flag REPEATED_FAILURES (external_payment_reconcile and crm_user_sync)."
    })

    has_env = "VAULT" in full_text or "MISSING" in full_text or "ENV" in full_text or "PREREQUISITE" in full_text
    checks.append({
        "name": "risk_missing_env_detected",
        "passed": has_env,
        "detail": "Must flag MISSING_ENV (vault_secret_rotation needs absent prod_secrets.vault)."
    })

    # --- CHECK 5: RECOMMENDED ACTIONS section ---
    has_actions = any("RECOMMEND" in l.upper() or "ACTION" in l.upper() for l in lines)
    checks.append({
        "name": "section_recommended_actions_present",
        "passed": has_actions,
        "detail": "Report must contain a RECOMMENDED ACTIONS section."
    })

    # CHECK 5b: Preferred remediation types (delivery=none, slow cadence, digest)
    preferred_remediation = (
        "DELIVERY" in full_text or
        "NONE" in full_text or
        "SLOW" in full_text or
        "CADENCE" in full_text or
        "DIGEST" in full_text
    )
    checks.append({
        "name": "actions_use_preferred_remediations",
        "passed": preferred_remediation,
        "detail": "Recommended actions must prefer: delivery=none, slow cadence, or add digest job (not delete/hard-disable)."
    })

    # --- CHECK 6: APPLY PLAN section present ---
    has_apply_plan = any("APPLY" in l.upper() or "PLAN" in l.upper() or "PATCH" in l.upper() for l in lines)
    checks.append({
        "name": "section_apply_plan_present",
        "passed": has_apply_plan,
        "detail": "Report must contain an APPLY PLAN section listing patches."
    })

    # --- CHECK 7: Lite guardrail - NOT APPLIED / not auto-executed ---
    has_not_applied = (
        "NOT APPLIED" in full_text or
        "NOT EXECUTED" in full_text or
        "NOT AUTO" in full_text or
        "LITE MODE" in full_text or
        "REPORT ONLY" in full_text or
        "NO CHANGES APPLIED" in full_text
    )
    checks.append({
        "name": "lite_guardrail_no_auto_apply",
        "passed": has_not_applied,
        "detail": "Apply plan must explicitly state patches are NOT applied/executed (Lite mode guardrail)."
    })

    # --- CHECK 8: No evidence of actual file modification (the script must not have been modified) ---
    # Ensure cron_jobs.json has not been altered (all 15 jobs still there)
    try:
        cron_path = Path(workspace) / "cron_jobs.json"
        with open(cron_path) as f:
            cron_data = json.load(f)
        job_count_intact = len(cron_data) == 15
        checks.append({
            "name": "cron_jobs_not_modified",
            "passed": job_count_intact,
            "detail": f"cron_jobs.json must remain unmodified (15 jobs). Found: {len(cron_data)}."
        })
    except Exception as e:
        checks.append({
            "name": "cron_jobs_not_modified",
            "passed": False,
            "detail": f"Could not verify cron_jobs.json integrity: {e}"
        })

    # --- Score computation ---
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Must pass critical checks to overall pass
    critical = [
        "report_file_exists",
        "line_count_10_to_25",
        "section_totals_present",
        "section_top_risks_present",
        "section_apply_plan_present",
        "lite_guardrail_no_auto_apply",
        "risk_duplicate_purpose_detected",
        "risk_repeated_failures_detected",
        "risk_missing_env_detected",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))