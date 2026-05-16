#!/usr/bin/env python3
"""
Evaluation script for the Gmail Label Manager skill task.
Checks that the agent correctly ran script.sh which:
1. Searched for unread emails
2. Searched for archived emails from the same sender (is:archived from:...)
3. Applied the correct label (A_Personal/Newsletter - most frequent A_ label)
4. Removed CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD labels
5. Archived the email by removing INBOX

The mock gog CLI logs all calls to /workspace/logs/gog_calls.log
"""

import sys
import json
import re
from pathlib import Path


def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []

    # ── Load the gog call log ──────────────────────────────────────────────
    gog_log_path = ws / "logs" / "gog_calls.log"
    try:
        gog_calls_raw = gog_log_path.read_text()
        gog_calls = [line.strip() for line in gog_calls_raw.splitlines() if line.strip()]
    except FileNotFoundError:
        checks.append({
            "name": "gog_call_log_exists",
            "passed": False,
            "detail": f"gog call log not found at {gog_log_path}. Did the agent run script.sh?"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    except Exception as e:
        checks.append({
            "name": "gog_call_log_readable",
            "passed": False,
            "detail": f"Failed to read gog call log: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "gog_call_log_exists",
        "passed": True,
        "detail": f"gog call log found with {len(gog_calls)} calls"
    })

    # ── Check 1: Searched for unread emails ───────────────────────────────
    unread_search_found = any(
        "gmail" in call and "messages" in call and "search" in call
        and "is:unread" in call
        and "--json" in call
        for call in gog_calls
    )
    checks.append({
        "name": "searched_unread_emails",
        "passed": unread_search_found,
        "detail": (
            "Found call to search for unread emails with --json flag"
            if unread_search_found
            else f"No unread email search found. Calls were: {gog_calls[:5]}"
        )
    })

    # ── Check 2: Fetched full thread content ──────────────────────────────
    thread_get_found = any(
        "gmail" in call and "thread" in call and "get" in call
        and "thread_abc123" in call
        and "--full" in call and "--json" in call
        for call in gog_calls
    )
    checks.append({
        "name": "fetched_thread_content",
        "passed": thread_get_found,
        "detail": (
            "Found call to get thread content with --full --json"
            if thread_get_found
            else f"No thread get call found for thread_abc123. Calls: {gog_calls}"
        )
    })

    # ── Check 3: Searched archived emails from sender ─────────────────────
    # Must use is:archived from:"newsletter@updates.example.com" pattern
    archived_search_found = any(
        "gmail" in call and "messages" in call and "search" in call
        and "is:archived" in call
        and "newsletter@updates.example.com" in call
        and "--json" in call
        for call in gog_calls
    )
    checks.append({
        "name": "searched_archived_emails_from_sender",
        "passed": archived_search_found,
        "detail": (
            "Found call to search archived emails from sender using is:archived filter"
            if archived_search_found
            else f"No archived email search from sender found. Calls: {gog_calls}"
        )
    })

    # ── Check 4: Applied correct label (A_Personal/Newsletter) ───────────
    # Must NOT apply A_Work/Updates (appears only once, less frequent)
    correct_label_applied = any(
        "gmail" in call and "thread" in call and "modify" in call
        and "thread_abc123" in call
        and "--add" in call
        and "A_Personal/Newsletter" in call
        for call in gog_calls
    )
    wrong_label_applied = any(
        "gmail" in call and "thread" in call and "modify" in call
        and "thread_abc123" in call
        and "--add" in call
        and "A_Work/Updates" in call
        for call in gog_calls
    )
    checks.append({
        "name": "applied_correct_label",
        "passed": correct_label_applied and not wrong_label_applied,
        "detail": (
            "Correctly applied A_Personal/Newsletter (most frequent archived label)"
            if correct_label_applied and not wrong_label_applied
            else (
                "Applied wrong label A_Work/Updates instead of A_Personal/Newsletter"
                if wrong_label_applied
                else f"Did not apply A_Personal/Newsletter label. Calls: {gog_calls}"
            )
        )
    })

    # ── Check 5: Removed CATEGORY/UNREAD labels (REMOVE_LABELS constant) ─
    # Must remove exactly: CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD
    remove_labels_found = any(
        "gmail" in call and "thread" in call and "modify" in call
        and "thread_abc123" in call
        and "--remove" in call
        and "CATEGORY_UPDATES" in call
        and "CATEGORY_PROMOTIONS" in call
        and "UNREAD" in call
        for call in gog_calls
    )
    # Make sure INBOX was NOT removed in this same call (it must be separate)
    remove_labels_not_inbox = any(
        "gmail" in call and "thread" in call and "modify" in call
        and "thread_abc123" in call
        and "--remove" in call
        and "CATEGORY_UPDATES" in call
        and "CATEGORY_PROMOTIONS" in call
        and "UNREAD" in call
        and "INBOX" not in call
        for call in gog_calls
    )
    checks.append({
        "name": "removed_category_unread_labels",
        "passed": remove_labels_found,
        "detail": (
            "Found call to remove CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD labels"
            if remove_labels_found
            else f"Did not find removal of CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD. Calls: {gog_calls}"
        )
    })

    checks.append({
        "name": "remove_labels_separate_from_inbox",
        "passed": remove_labels_not_inbox,
        "detail": (
            "CATEGORY/UNREAD labels removed in a separate call from INBOX removal (correct separation)"
            if remove_labels_not_inbox
            else "INBOX was bundled with CATEGORY/UNREAD label removal, should be a separate archive call"
        )
    })

    # ── Check 6: Archived by removing INBOX label separately ──────────────
    archive_found = any(
        "gmail" in call and "thread" in call and "modify" in call
        and "thread_abc123" in call
        and "--remove" in call
        and "INBOX" in call
        and "CATEGORY_UPDATES" not in call  # must be separate from remove_labels
        for call in gog_calls
    )
    checks.append({
        "name": "archived_email_removing_inbox",
        "passed": archive_found,
        "detail": (
            "Found separate call to archive email by removing INBOX label"
            if archive_found
            else f"Did not find separate INBOX removal (archive). Calls: {gog_calls}"
        )
    })

    # ── Check 7: Order of operations ──────────────────────────────────────
    # add label → remove labels → remove INBOX (archive)
    # Find indices of these calls
    try:
        add_label_idx = next(
            i for i, call in enumerate(gog_calls)
            if "gmail" in call and "thread" in call and "modify" in call
            and "thread_abc123" in call and "--add" in call
            and "A_Personal/Newsletter" in call
        )
        remove_labels_idx = next(
            i for i, call in enumerate(gog_calls)
            if "gmail" in call and "thread" in call and "modify" in call
            and "thread_abc123" in call and "--remove" in call
            and "CATEGORY_UPDATES" in call and "INBOX" not in call
        )
        archive_idx = next(
            i for i, call in enumerate(gog_calls)
            if "gmail" in call and "thread" in call and "modify" in call
            and "thread_abc123" in call and "--remove" in call
            and "INBOX" in call and "CATEGORY_UPDATES" not in call
        )
        order_correct = add_label_idx < remove_labels_idx < archive_idx
        checks.append({
            "name": "correct_operation_order",
            "passed": order_correct,
            "detail": (
                f"Operations in correct order: add_label({add_label_idx}) < remove_labels({remove_labels_idx}) < archive({archive_idx})"
                if order_correct
                else f"Operations out of order: add_label={add_label_idx}, remove_labels={remove_labels_idx}, archive={archive_idx}"
            )
        })
    except StopIteration:
        checks.append({
            "name": "correct_operation_order",
            "passed": False,
            "detail": "Could not verify order: one or more required operations were not found"
        })

    # ── Check 8: Script log exists (proves script.sh was run) ─────────────
    script_log = ws / "logs" / "gmail-label-log.txt"
    try:
        log_content = script_log.read_text()
        log_has_content = len(log_content.strip()) > 0
        log_mentions_processing = "Processing" in log_content or "Gmail Manager" in log_content
        checks.append({
            "name": "script_log_generated",
            "passed": log_has_content and log_mentions_processing,
            "detail": (
                "script.sh generated a log file with processing information"
                if log_has_content and log_mentions_processing
                else f"Log file empty or missing expected content. Content preview: {log_content[:200]}"
            )
        })
    except FileNotFoundError:
        checks.append({
            "name": "script_log_generated",
            "passed": False,
            "detail": f"No script log found at {script_log}"
        })
    except Exception as e:
        checks.append({
            "name": "script_log_generated",
            "passed": False,
            "detail": f"Error reading script log: {e}"
        })

    # ── Final scoring ──────────────────────────────────────────────────────
    critical_checks = [
        "searched_archived_emails_from_sender",
        "applied_correct_label",
        "removed_category_unread_labels",
        "archived_email_removing_inbox",
    ]
    all_checks = [c["name"] for c in checks]
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    passed = len(passed_checks)
    score = passed / total if total > 0 else 0.0

    # All critical checks must pass
    critical_passed = all(
        any(c["name"] == crit and c["passed"] for c in checks)
        for crit in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))