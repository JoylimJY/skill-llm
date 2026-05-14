import sys
import json
import os

def load_db(workspace):
    db_path = os.path.join(workspace, "emails_db.json")
    with open(db_path, "r") as f:
        return json.load(f)

def find_message_by_thread(db, thread_id):
    for msg in db["messages"]:
        if msg["threadId"] == thread_id:
            return msg
    return None

def run_eval(workspace):
    checks = []
    overall_passed = True

    try:
        db = load_db(workspace)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "load_emails_db", "passed": False, "detail": f"Could not load emails_db.json: {e}"}]
        }

    target = find_message_by_thread(db, "thread_001")
    if target is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "find_target_thread", "passed": False, "detail": "thread_001 not found in emails_db.json"}]
        }

    labels = target.get("labels", [])
    archived = target.get("archived", False)

    # -----------------------------------------------------------------------
    # CHECK 1: Correct label applied (A_Personal/Finance)
    # Must come from archived emails only — not from inbox email with A_Work/Billing
    # -----------------------------------------------------------------------
    correct_label = "A_Personal/Finance"
    wrong_label = "A_Work/Billing"

    check1_passed = correct_label in labels
    check1_detail = (
        f"Label '{correct_label}' found in thread_001 labels: {labels}"
        if check1_passed
        else f"Expected label '{correct_label}' NOT found in thread_001 labels: {labels}. "
             f"Agent may have incorrectly used inbox-sourced label '{wrong_label}' or found no label."
    )
    checks.append({"name": "correct_label_applied_from_archived_history", "passed": check1_passed, "detail": check1_detail})

    # -----------------------------------------------------------------------
    # CHECK 2: Wrong label NOT applied (trap: A_Work/Billing from inbox email)
    # -----------------------------------------------------------------------
    check2_passed = wrong_label not in labels
    check2_detail = (
        f"Correctly did NOT apply inbox-sourced label '{wrong_label}'"
        if check2_passed
        else f"FAIL: Agent incorrectly applied '{wrong_label}' which came from a non-archived inbox email — should be ignored."
    )
    checks.append({"name": "inbox_label_not_used_as_pattern", "passed": check2_passed, "detail": check2_detail})

    # -----------------------------------------------------------------------
    # CHECK 3: UNREAD label removed
    # -----------------------------------------------------------------------
    check3_passed = "UNREAD" not in labels
    check3_detail = (
        "UNREAD label successfully removed"
        if check3_passed
        else f"UNREAD label still present in labels: {labels}"
    )
    checks.append({"name": "unread_label_removed", "passed": check3_passed, "detail": check3_detail})

    # -----------------------------------------------------------------------
    # CHECK 4: CATEGORY_UPDATES label removed
    # -----------------------------------------------------------------------
    check4_passed = "CATEGORY_UPDATES" not in labels
    check4_detail = (
        "CATEGORY_UPDATES label successfully removed"
        if check4_passed
        else f"CATEGORY_UPDATES label still present in labels: {labels}"
    )
    checks.append({"name": "category_updates_label_removed", "passed": check4_passed, "detail": check4_detail})

    # -----------------------------------------------------------------------
    # CHECK 5: INBOX label removed (archiving done correctly via --remove INBOX)
    # -----------------------------------------------------------------------
    check5_passed = "INBOX" not in labels and archived is True
    check5_detail = (
        "INBOX label removed and message marked as archived"
        if check5_passed
        else f"Message not properly archived. INBOX in labels: {'INBOX' in labels}, archived flag: {archived}. Labels: {labels}"
    )
    checks.append({"name": "email_archived_by_inbox_label_removal", "passed": check5_passed, "detail": check5_detail})

    # -----------------------------------------------------------------------
    # CHECK 6: No spurious labels added (only A_Personal/Finance should have been added)
    # -----------------------------------------------------------------------
    original_labels_set = {"INBOX", "UNREAD", "CATEGORY_UPDATES"}
    current_labels_set = set(labels)
    expected_final_labels = {correct_label}
    # Any label that is in current but was not original and is not the correct one
    spurious = current_labels_set - original_labels_set - expected_final_labels
    check6_passed = len(spurious) == 0
    check6_detail = (
        "No spurious labels added"
        if check6_passed
        else f"Unexpected labels were added: {spurious}"
    )
    checks.append({"name": "no_spurious_labels_added", "passed": check6_passed, "detail": check6_detail})

    # -----------------------------------------------------------------------
    # CHECK 7: Other emails untouched (thread_097, thread_099, etc.)
    # -----------------------------------------------------------------------
    untouched_ok = True
    untouched_detail = "All unrelated emails remain untouched"
    thread_097 = find_message_by_thread(db, "thread_097")
    if thread_097:
        # Should still have INBOX, A_Work/Billing and NOT be archived
        if thread_097.get("archived", False):
            untouched_ok = False
            untouched_detail = "thread_097 (inbox email from same sender) was incorrectly archived"
        if "A_Work/Billing" not in thread_097.get("labels", []):
            untouched_ok = False
            untouched_detail = "thread_097 label A_Work/Billing was incorrectly removed"
    checks.append({"name": "unrelated_emails_untouched", "passed": untouched_ok, "detail": untouched_detail})

    # -----------------------------------------------------------------------
    # Compute overall score
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)

    # Must pass critical checks 1, 2, 3, 4, 5 to fully pass
    critical_checks = [checks[0], checks[1], checks[2], checks[3], checks[4]]
    overall_passed = all(c["passed"] for c in critical_checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))