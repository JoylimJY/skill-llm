import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    UPLOADS_FILE = "/tmp/gws_uploads.json"
    INVOCATIONS_LOG = "/tmp/gws_invocations.log"
    
    # Expected values from upload_ticket.json
    EXPECTED_FOLDER_ID = "1XkZpQ9mRtYvN3wBcDfGhJ2sLpOuEa4K"
    EXPECTED_ARCHIVE_NAME = "FY2024_Q3_Earnings_ARCHIVE.pptx"
    # The actual expected name from the ticket:
    EXPECTED_ARCHIVE_NAME_EXACT = "FY2024_Q3_Earnings_Presentation_ARCHIVE.pptx"
    EXPECTED_SOURCE_FILE = str(Path(workspace_dir) / "finance" / "q3_2024" / "approved" / "q3_earnings_FINAL.pptx")
    EXPECTED_ACCOUNT = "finance-bot@acmecorp.com"

    # --- Check 1: gws was invoked at all ---
    try:
        with open(INVOCATIONS_LOG) as f:
            invocation_lines = [l.strip() for l in f.readlines() if l.strip()]
        
        gws_called = len(invocation_lines) > 0
        checks.append({
            "name": "gws_was_invoked",
            "passed": gws_called,
            "detail": f"Found {len(invocation_lines)} gws invocation(s): {invocation_lines[:3]}" if gws_called else "No gws invocations found in log."
        })
    except Exception as e:
        checks.append({
            "name": "gws_was_invoked",
            "passed": False,
            "detail": f"Could not read invocation log: {e}"
        })

    # --- Check 2: Upload record exists ---
    uploads = []
    try:
        with open(UPLOADS_FILE) as f:
            uploads = json.load(f)
        
        has_uploads = len(uploads) > 0
        checks.append({
            "name": "upload_record_exists",
            "passed": has_uploads,
            "detail": f"Found {len(uploads)} upload record(s)." if has_uploads else "No upload records found. gws drive +upload was never successfully called."
        })
    except Exception as e:
        checks.append({
            "name": "upload_record_exists",
            "passed": False,
            "detail": f"Could not read uploads log: {e}"
        })
        # No point continuing
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    if not uploads:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # Use the most recent upload record
    record = uploads[-1]

    # --- Check 3: Correct source file was uploaded ---
    try:
        uploaded_path = record.get("file_path", "")
        # Accept absolute or relative paths pointing to the correct file
        correct_source = (
            uploaded_path == EXPECTED_SOURCE_FILE or
            uploaded_path.endswith("finance/q3_2024/approved/q3_earnings_FINAL.pptx")
        )
        checks.append({
            "name": "correct_source_file",
            "passed": correct_source,
            "detail": f"Uploaded file path: '{uploaded_path}'. Expected path ending in 'finance/q3_2024/approved/q3_earnings_FINAL.pptx'."
        })
    except Exception as e:
        checks.append({
            "name": "correct_source_file",
            "passed": False,
            "detail": f"Error checking source file: {e}"
        })

    # --- Check 4: --parent flag set to correct folder ID ---
    try:
        parent_id = record.get("parent_id", None)
        correct_parent = (parent_id == EXPECTED_FOLDER_ID)
        checks.append({
            "name": "correct_parent_folder_id",
            "passed": correct_parent,
            "detail": f"parent_id used: '{parent_id}'. Expected: '{EXPECTED_FOLDER_ID}'."
        })
    except Exception as e:
        checks.append({
            "name": "correct_parent_folder_id",
            "passed": False,
            "detail": f"Error checking parent_id: {e}"
        })

    # --- Check 5: --name flag set to correct archive filename ---
    try:
        uploaded_name = record.get("uploaded_name", "")
        correct_name = (uploaded_name == EXPECTED_ARCHIVE_NAME_EXACT)
        checks.append({
            "name": "correct_archive_filename",
            "passed": correct_name,
            "detail": f"uploaded_name: '{uploaded_name}'. Expected: '{EXPECTED_ARCHIVE_NAME_EXACT}'."
        })
    except Exception as e:
        checks.append({
            "name": "correct_archive_filename",
            "passed": False,
            "detail": f"Error checking uploaded name: {e}"
        })

    # --- Check 6: --account flag used correctly (from gws-shared requirement) ---
    try:
        used_account = record.get("account", "")
        correct_account = (used_account == EXPECTED_ACCOUNT)
        checks.append({
            "name": "correct_account_used",
            "passed": correct_account,
            "detail": f"Account used: '{used_account}'. Expected: '{EXPECTED_ACCOUNT}'."
        })
    except Exception as e:
        checks.append({
            "name": "correct_account_used",
            "passed": False,
            "detail": f"Error checking account: {e}"
        })

    # --- Check 7: Verify the +upload subcommand syntax was used (not some workaround) ---
    try:
        with open(INVOCATIONS_LOG) as f:
            all_invocations = f.read()
        
        used_plus_upload = "+upload" in all_invocations
        checks.append({
            "name": "used_plus_upload_subcommand",
            "passed": used_plus_upload,
            "detail": f"'+upload' found in invocations: {used_plus_upload}. Raw log excerpt: {all_invocations[:300]}"
        })
    except Exception as e:
        checks.append({
            "name": "used_plus_upload_subcommand",
            "passed": False,
            "detail": f"Error reading invocation log: {e}"
        })

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total if total > 0 else 0.0

    # Overall pass: all critical checks must pass
    critical_checks = [
        "correct_source_file",
        "correct_parent_folder_id",
        "correct_archive_filename",
        "correct_account_used",
        "used_plus_upload_subcommand",
    ]
    all_critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    result = {
        "passed": all_critical_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)