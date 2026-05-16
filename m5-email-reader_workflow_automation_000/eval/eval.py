import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── Find inbox_report.json anywhere in workspace ─────────────────────────
    candidates = list(ws.rglob("inbox_report.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "inbox_report.json exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })
    if not file_found:
        return checks

    report_path = candidates[0]
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "inbox_report.json is valid JSON", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "inbox_report.json is valid JSON", "passed": True, "detail": "Parsed successfully"})

    # ── Check 1: total_emails = 12 ───────────────────────────────────────────
    try:
        total = report.get("total_emails")
        passed = int(total) == 12
        checks.append({
            "name": "total_emails == 12",
            "passed": passed,
            "detail": f"Got: {total}"
        })
    except Exception as e:
        checks.append({"name": "total_emails == 12", "passed": False, "detail": str(e)})

    # ── Check 2: recent_subjects — 5 most recent (indices 12..8) ─────────────
    EXPECTED_RECENT_SUBJECTS = [
        "Support ticket #5521 resolved",   # index 12
        "Upcoming feature release",         # index 11
        "Invoice #1003 payment received",   # index 10
        "Security alert: new login",        # index 9
        "Subscription renewal",             # index 8
    ]
    try:
        recent = report.get("recent_subjects", [])
        # Accept list of strings OR list of dicts with 'subject' key
        def extract_subject(item):
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                return item.get("subject", "")
            return str(item)

        recent_subjects = [extract_subject(x) for x in recent]
        # Must have exactly 5 entries
        count_ok = len(recent_subjects) == 5
        # Must match expected subjects (order matters: newest first)
        subjects_match = recent_subjects == EXPECTED_RECENT_SUBJECTS
        # Partial credit: check if all 5 correct subjects appear regardless of order
        subjects_match_any_order = sorted(recent_subjects) == sorted(EXPECTED_RECENT_SUBJECTS)
        
        passed = count_ok and subjects_match
        detail = (
            f"Count: {len(recent_subjects)} (need 5). "
            f"Order-correct match: {subjects_match}. "
            f"Any-order match: {subjects_match_any_order}. "
            f"Got: {recent_subjects}"
        )
        checks.append({"name": "recent_subjects: 5 correct subjects (newest first)", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "recent_subjects: 5 correct subjects", "passed": False, "detail": str(e)})

    # ── Check 3: invoice_emails — must contain indices 3, 6, 10 ─────────────
    EXPECTED_INVOICE_INDICES = {3, 6, 10}
    try:
        invoices = report.get("invoice_emails", [])
        def get_index(item):
            if isinstance(item, dict):
                return item.get("index")
            return None
        found_indices = set(get_index(e) for e in invoices if get_index(e) is not None)
        passed = EXPECTED_INVOICE_INDICES == found_indices
        checks.append({
            "name": "invoice_emails contains exactly indices {3, 6, 10}",
            "passed": passed,
            "detail": f"Expected: {EXPECTED_INVOICE_INDICES}, Got: {found_indices}"
        })
        # Also verify bodies are present (full content, not just headers)
        bodies_present = all(
            isinstance(e, dict) and e.get("body") and len(e["body"]) > 0
            for e in invoices
        )
        checks.append({
            "name": "invoice_emails items include body content (full email)",
            "passed": bodies_present,
            "detail": f"All have non-empty body: {bodies_present}"
        })
    except Exception as e:
        checks.append({"name": "invoice_emails check", "passed": False, "detail": str(e)})

    # ── Check 4: oldest_invoice_full — must be index 3, full body ───────────
    try:
        oldest = report.get("oldest_invoice_full")
        if isinstance(oldest, dict):
            idx_ok  = oldest.get("index") == 3
            subj_ok = "Invoice #1001" in str(oldest.get("subject", ""))
            body_ok = oldest.get("body") and "$2,500" in str(oldest.get("body", ""))
            from_ok = oldest.get("from") == "billing@vendorco.com"
            passed  = idx_ok and subj_ok and body_ok and from_ok
            detail  = (f"index=={oldest.get('index')}(need 3), "
                       f"subject contains 'Invoice #1001': {subj_ok}, "
                       f"body contains '$2,500': {body_ok}, "
                       f"from correct: {from_ok}")
        else:
            passed = False
            detail = f"oldest_invoice_full is not a dict: {type(oldest)}"

        checks.append({
            "name": "oldest_invoice_full is email index 3 with full body",
            "passed": passed,
            "detail": detail
        })
    except Exception as e:
        checks.append({"name": "oldest_invoice_full check", "passed": False, "detail": str(e)})

    # ── Check 5: .email_config placed in scripts/ directory ─────────────────
    try:
        config_in_scripts = (ws / "scripts" / ".email_config").exists()
        # The root-level .email_config is a distractor with wrong credentials
        # and the script only reads scripts/.email_config
        checks.append({
            "name": "scripts/.email_config was created (correct config location)",
            "passed": config_in_scripts,
            "detail": f"scripts/.email_config exists: {config_in_scripts}"
        })
        if config_in_scripts:
            import configparser
            cfg = configparser.ConfigParser()
            cfg.read(ws / "scripts" / ".email_config")
            user_ok  = cfg.get("email", "user",  fallback="") == "support@company163.com"
            pass_ok  = cfg.get("email", "pass_", fallback="") == "AUTHCODE_XK9mP2"
            key_ok   = "pass_" in cfg["email"] if "email" in cfg else False  # must use pass_ not password
            checks.append({
                "name": "scripts/.email_config has correct credentials with 'pass_' key",
                "passed": user_ok and pass_ok and key_ok,
                "detail": f"user_ok={user_ok}, pass_ok={pass_ok}, key_is_pass_={key_ok}"
            })
            # Check file permissions are 600
            mode = oct(os.stat(ws / "scripts" / ".email_config").st_mode)[-3:]
            perms_ok = mode == "600"
            checks.append({
                "name": "scripts/.email_config has permissions 600",
                "passed": perms_ok,
                "detail": f"Actual permissions: {mode}"
            })
    except Exception as e:
        checks.append({"name": "scripts/.email_config checks", "passed": False, "detail": str(e)})

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    # All checks must pass for overall pass
    overall = all(c["passed"] for c in checks)
    result = {
        "passed": overall,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()