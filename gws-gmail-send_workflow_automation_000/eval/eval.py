import sys
import json
import re
from pathlib import Path

def load_calls(workspace):
    log_path = Path(workspace) / ".gws_mock" / "calls.log"
    calls = []
    if not log_path.exists():
        return calls
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    calls.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return calls

def find_send_calls(calls):
    """Find all gmail +send invocations (excluding --dry-run and --draft)."""
    send_calls = []
    for call in calls:
        args = call.get("args", [])
        if len(args) >= 2 and args[0] == "gmail" and args[1] == "+send":
            if "--dry-run" not in args and "--draft" not in args:
                send_calls.append(args)
    return send_calls

def parse_args(args):
    """Parse a list of CLI args into a structured dict."""
    result = {
        "to": [],
        "subject": None,
        "body": None,
        "from": None,
        "cc": [],
        "bcc": [],
        "html": False,
        "attachments": [],
        "draft": False,
        "dry_run": False,
    }
    i = 2  # skip 'gmail' and '+send'
    while i < len(args):
        arg = args[i]
        if arg == "--to" and i+1 < len(args):
            result["to"] = [e.strip() for e in args[i+1].split(",")]
            i += 2
        elif arg == "--subject" and i+1 < len(args):
            result["subject"] = args[i+1]
            i += 2
        elif arg == "--body" and i+1 < len(args):
            result["body"] = args[i+1]
            i += 2
        elif arg == "--from" and i+1 < len(args):
            result["from"] = args[i+1]
            i += 2
        elif arg == "--cc" and i+1 < len(args):
            result["cc"] = [e.strip() for e in args[i+1].split(",")]
            i += 2
        elif arg == "--bcc" and i+1 < len(args):
            result["bcc"] = [e.strip() for e in args[i+1].split(",")]
            i += 2
        elif arg in ("--html",):
            result["html"] = True
            i += 1
        elif arg == "--draft":
            result["draft"] = True
            i += 1
        elif arg == "--dry-run":
            result["dry_run"] = True
            i += 1
        elif arg in ("-a", "--attach") and i+1 < len(args):
            result["attachments"].append(args[i+1])
            i += 2
        else:
            i += 1
    return result

def check_attachment_basename(attachment_path, expected_basename):
    """Check if the attachment path ends with the expected filename."""
    return Path(attachment_path).name == expected_basename

def run_eval(workspace):
    checks = []
    workspace = Path(workspace)

    # --- Load call log ---
    try:
        calls = load_calls(workspace)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "log_readable", "passed": False, "detail": f"Could not read call log: {e}"}]
        }

    send_calls_raw = find_send_calls(calls)

    # Check 1: At least one actual send call was made
    check_has_send = {
        "name": "send_call_exists",
        "passed": len(send_calls_raw) > 0,
        "detail": f"Found {len(send_calls_raw)} non-dry-run, non-draft send call(s)."
    }
    checks.append(check_has_send)

    if not send_calls_raw:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # Use the most recent valid send call
    parsed = parse_args(send_calls_raw[-1])

    # Check 2: Correct primary recipients (both required)
    required_to = {"investors@acmecorp.com", "board-notify@partners.vc"}
    actual_to = set(parsed["to"])
    to_match = required_to.issubset(actual_to)
    checks.append({
        "name": "correct_to_recipients",
        "passed": to_match,
        "detail": f"Expected TO to contain {sorted(required_to)}, got {sorted(actual_to)}."
    })

    # Check 3: Correct subject
    expected_subject = "Acme Corp Q3 2024 Investor Update"
    subject_match = parsed["subject"] == expected_subject
    checks.append({
        "name": "correct_subject",
        "passed": subject_match,
        "detail": f"Expected subject '{expected_subject}', got '{parsed['subject']}'."
    })

    # Check 4: HTML flag is set (body is HTML content)
    checks.append({
        "name": "html_flag_set",
        "passed": parsed["html"],
        "detail": "The --html flag must be set because the body contains HTML markup."
    })

    # Check 5: Body contains key HTML content (not wrapped in <html>/<body> tags)
    body = parsed["body"] or ""
    has_html_content = bool(re.search(r'<[bh][0-9rpea]', body, re.IGNORECASE))
    has_no_html_wrapper = not bool(re.search(r'<html|<body', body, re.IGNORECASE))
    body_correct = has_html_content and has_no_html_wrapper
    checks.append({
        "name": "html_body_no_wrapper_tags",
        "passed": body_correct,
        "detail": f"Body must contain HTML fragment tags but NO <html>/<body> wrapper. has_html_content={has_html_content}, has_no_html_wrapper={has_no_html_wrapper}. Body snippet: '{body[:120]}'"
    })

    # Check 6: CC recipients correct
    required_cc = {"legal-review@acmecorp.com", "compliance@acmecorp.com"}
    actual_cc = set(parsed["cc"])
    cc_match = required_cc.issubset(actual_cc)
    checks.append({
        "name": "correct_cc_recipients",
        "passed": cc_match,
        "detail": f"Expected CC to contain {sorted(required_cc)}, got {sorted(actual_cc)}."
    })

    # Check 7: BCC recipients correct
    required_bcc = {"ceo-blind@acmecorp.com", "cfo-blind@acmecorp.com"}
    actual_bcc = set(parsed["bcc"])
    bcc_match = required_bcc.issubset(actual_bcc)
    checks.append({
        "name": "correct_bcc_recipients",
        "passed": bcc_match,
        "detail": f"Expected BCC to contain {sorted(required_bcc)}, got {sorted(actual_bcc)}."
    })

    # Check 8: Correct from alias
    expected_from = "marketing-noreply@acmecorp.com"
    from_match = parsed["from"] == expected_from
    checks.append({
        "name": "correct_from_alias",
        "passed": from_match,
        "detail": f"Expected --from '{expected_from}', got '{parsed['from']}'."
    })

    # Check 9: Both attachments are present (using -a/-attach repeated)
    expected_pdf = "Q3_2024_Investor_Report.pdf"
    expected_png = "acme_corp_logo.png"
    attachments = parsed["attachments"]
    
    pdf_attached = any(check_attachment_basename(a, expected_pdf) for a in attachments)
    png_attached = any(check_attachment_basename(a, expected_png) for a in attachments)
    
    checks.append({
        "name": "pdf_report_attached",
        "passed": pdf_attached,
        "detail": f"Expected attachment '{expected_pdf}'. Found attachments: {attachments}."
    })
    checks.append({
        "name": "logo_png_attached",
        "passed": png_attached,
        "detail": f"Expected attachment '{expected_png}'. Found attachments: {attachments}."
    })

    # Check 10: Attachments were specified using repeated -a/--attach flags (not comma-separated)
    # This verifies that the agent used the proprietary multi-attach syntax
    raw_args = send_calls_raw[-1]
    attach_flag_count = sum(1 for a in raw_args if a in ("-a", "--attach"))
    multi_attach_correct = attach_flag_count >= 2
    checks.append({
        "name": "multiple_attach_flags_used",
        "passed": multi_attach_correct,
        "detail": f"Attachments must use -a/--attach flag MULTIPLE TIMES (not comma-separated). Found {attach_flag_count} -a/--attach flag(s)."
    })

    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))